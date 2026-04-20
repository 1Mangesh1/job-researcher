"""
Agentic analyze flow.

Difference vs `Pipeline.analyze`:
  - A planner LLM call decides which tools to run and in what order.
  - An executor loop runs them and collects results into a working memory.
  - A synthesizer LLM produces the final Verdict from collected evidence.

Compared with a full ReAct agent this is deliberately shallow: the plan is
produced once up front (no re-plan loop yet). Reflection + re-plan is a TODO.
"""

import json
import re
import time
from typing import Any, Awaitable, Callable

from job_researcher.models import (
    AgentAnalyzeResponse,
    AgentPlan,
    AgentTrace,
    AnalysisMetadata,
    AgentToolName,
    CompanySnapshot,
    GitHubSummary,
    JobDescription,
    ResumeMatch,
    Verdict,
)
from job_researcher.services.embeddings import EmbeddingsService
from job_researcher.services.gemini import GeminiService
from job_researcher.steps.company_researcher import research_company
from job_researcher.steps.github_scanner import scan_github_org
from job_researcher.steps.jd_fetcher import fetch_job_page
from job_researcher.steps.jd_parser import parse_job_description
from job_researcher.steps.resume_comparator import compare_resume
from job_researcher.steps.verdict_generator import generate_verdict


TOOL_CATALOG = """Available tools:
- fetch_and_parse_jd: Fetch the job posting URL and extract structured fields
  (title, company, requirements, tech_stack). Must run first if a verdict is
  needed. Produces: jd.
- research_company: Use Gemini with Google Search grounding to build a company
  snapshot (funding, size, tech, culture). Requires: jd.company. Produces: company.
- scan_github: Hit the GitHub public API for the company's org to see primary
  languages + notable repos. Requires: jd.company. Produces: github. Skip if
  the company is obviously non-engineering or has no public GitHub presence.
- compare_resume: Embed jd.requirements and cosine-score against the cached
  resume chunks. Requires: jd + resume loaded. Produces: resume_match. Skip
  if resume_loaded is false (a zero-match stub will be used)."""


PLANNER_SYSTEM = """You are a planning agent. Given a user goal and a catalog of
tools, produce an ordered plan. Rules:
- Minimum plan for a job-fit verdict: fetch_and_parse_jd, research_company,
  compare_resume (if resume loaded). scan_github is optional — skip when the
  company is unlikely to have a meaningful public repo footprint.
- Every step must have a short `reason` explaining why it's needed.
- Do NOT include a final synthesis step — that runs automatically after your
  plan completes.
- Return valid JSON matching the schema. Nothing else."""


PLANNER_USER_TEMPLATE = """## Goal
{goal}

## Context
- job_url: {job_url}
- resume_loaded: {resume_loaded}

## Tools
{catalog}

Produce a minimal plan."""


class AnalyzeAgent:
    """Planner → Executor → Synthesizer over the existing step library."""

    def __init__(
        self,
        gemini: GeminiService,
        embeddings: EmbeddingsService,
        github_token: str | None,
        resume_chunks: list,
        resume_embeddings: list,
        resume_loaded: bool,
    ):
        self.gemini = gemini
        self.embeddings = embeddings
        self.github_token = github_token
        self.resume_chunks = resume_chunks
        self.resume_embeddings = resume_embeddings
        self.resume_loaded = resume_loaded

    async def plan(self, goal: str, job_url: str) -> AgentPlan:
        prompt = PLANNER_USER_TEMPLATE.format(
            goal=goal,
            job_url=job_url,
            resume_loaded=self.resume_loaded,
            catalog=TOOL_CATALOG,
        )
        raw = await self.gemini.generate(
            prompt,
            system_instruction=PLANNER_SYSTEM,
            response_schema=AgentPlan,
            thinking_budget=512,
        )
        data = json.loads(raw)
        return AgentPlan(**data)

    async def execute(self, plan: AgentPlan, job_url: str) -> tuple[dict[str, Any], list[dict]]:
        """Run plan steps in order. Returns (memory, trace)."""
        memory: dict[str, Any] = {}
        trace: list[dict] = []

        tools = self._build_tool_registry(job_url, memory)

        for step in plan.steps:
            name = step.tool.value
            start = time.time()
            try:
                result = await tools[name]()
                memory[name] = result
                trace.append({
                    "tool": name,
                    "reason": step.reason,
                    "status": "ok",
                    "elapsed_s": round(time.time() - start, 2),
                    "summary": self._summarize(result),
                })
            except Exception as e:
                trace.append({
                    "tool": name,
                    "reason": step.reason,
                    "status": "error",
                    "elapsed_s": round(time.time() - start, 2),
                    "error": str(e)[:200],
                })

        return memory, trace

    def _build_tool_registry(
        self, job_url: str, memory: dict[str, Any]
    ) -> dict[str, Callable[[], Awaitable[Any]]]:
        async def tool_fetch_and_parse_jd() -> JobDescription:
            raw = await fetch_job_page(job_url)
            jd = await parse_job_description(self.gemini, raw)
            return jd

        async def tool_research_company() -> CompanySnapshot:
            jd: JobDescription = memory["fetch_and_parse_jd"]
            return await research_company(self.gemini, jd.company)

        async def tool_scan_github() -> GitHubSummary:
            jd: JobDescription = memory["fetch_and_parse_jd"]
            slug = re.sub(r"[^a-z0-9-]", "", jd.company.lower().replace(" ", "-"))
            return await scan_github_org(slug, self.github_token)

        async def tool_compare_resume() -> ResumeMatch:
            if not self.resume_loaded:
                return ResumeMatch(overall_similarity=0.0, top_matches=[])
            jd: JobDescription = memory["fetch_and_parse_jd"]
            return await compare_resume(
                self.embeddings,
                jd.requirements,
                self.resume_chunks,
                self.resume_embeddings,
            )

        return {
            AgentToolName.FETCH_AND_PARSE_JD.value: tool_fetch_and_parse_jd,
            AgentToolName.RESEARCH_COMPANY.value: tool_research_company,
            AgentToolName.SCAN_GITHUB.value: tool_scan_github,
            AgentToolName.COMPARE_RESUME.value: tool_compare_resume,
        }

    def _summarize(self, result: Any) -> str:
        if isinstance(result, JobDescription):
            return f"{result.title} at {result.company} — {len(result.requirements)} reqs"
        if isinstance(result, CompanySnapshot):
            return f"{result.stage}, {result.size}"
        if isinstance(result, GitHubSummary):
            return f"{result.total_public_repos} repos, langs={result.primary_languages[:3]}"
        if isinstance(result, ResumeMatch):
            return f"overall_similarity={result.overall_similarity:.2f}"
        return type(result).__name__

    async def synthesize(self, memory: dict[str, Any]) -> Verdict:
        jd = memory.get("fetch_and_parse_jd")
        if jd is None:
            raise RuntimeError("Planner skipped fetch_and_parse_jd — cannot synthesize verdict.")

        company = memory.get("research_company") or CompanySnapshot(
            stage="unknown", size="unknown", tech_stack=[],
            culture_signals="not researched", glassdoor_sentiment="unknown",
            recent_news=[],
        )
        github = memory.get("scan_github") or GitHubSummary()
        resume_match = memory.get("compare_resume") or ResumeMatch(
            overall_similarity=0.0, top_matches=[]
        )

        return await generate_verdict(self.gemini, jd, company, github, resume_match)

    async def run(self, job_url: str) -> AgentAnalyzeResponse:
        start = time.time()
        self.gemini.usage_by_model = {}
        self.gemini.call_count = 0

        goal = f"Produce a hiring-fit verdict for the candidate against {job_url}."

        plan = await self.plan(goal, job_url)
        memory, trace = await self.execute(plan, job_url)
        verdict = await self.synthesize(memory)

        elapsed = time.time() - start
        usage = self.gemini.get_usage()

        return AgentAnalyzeResponse(
            status="completed",
            verdict=verdict,
            trace=AgentTrace(plan=plan, executed=trace),
            metadata=AnalysisMetadata(
                analysis_time_seconds=round(elapsed, 2),
                llm_calls=usage["calls"],
                tokens_used={"input": usage["input"], "output": usage["output"]},
                estimated_cost_usd=self.gemini.estimated_cost(),
            ),
        )
