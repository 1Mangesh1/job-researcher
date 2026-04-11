import re
import time
import uuid
from dataclasses import dataclass, field

import numpy as np

from job_researcher.config import get_settings
from job_researcher.models import (
    AnalysisMetadata,
    AnalyzeResponse,
    JobDescription,
    Resume,
    ResumeMatch,
    ResumeStatus,
    TailorQuestion,
    TailorStartResponse,
)
from job_researcher.services.embeddings import EmbeddingsService
from job_researcher.services.gemini import GeminiService
from job_researcher.steps.company_researcher import research_company
from job_researcher.steps.github_scanner import scan_github_org
from job_researcher.steps.jd_fetcher import fetch_job_page
from job_researcher.steps.jd_parser import parse_job_description
from job_researcher.steps.resume_comparator import (
    chunk_text,
    compare_resume,
)
from job_researcher.steps.question_generator import generate_questions
from job_researcher.steps.resume_tailor import tailor_resume
from job_researcher.templates.minimal import render_minimal
from job_researcher.steps.verdict_generator import generate_verdict


@dataclass
class TailorSession:
    jd: JobDescription
    questions: list[TailorQuestion]
    resume_text: str


class Pipeline:
    def __init__(self):
        settings = get_settings()
        self.gemini = GeminiService(api_key=settings.gemini_api_key)
        self.embeddings = EmbeddingsService(
            account_id=settings.cf_account_id,
            api_token=settings.cf_api_token,
        )
        self.github_token = settings.github_token

        self.resume_chunks: list[str] = []
        self.resume_embeddings: list[np.ndarray] = []
        self.resume_loaded: bool = False
        self.resume_last_updated: str | None = None
        self._resume_cache: str | None = None
        self.resume_text: str = ""
        self._tailor_sessions: dict[str, TailorSession] = {}

    async def load_resume(self, text: str) -> ResumeStatus:
        self.resume_text = text
        self.resume_chunks = chunk_text(text)
        raw_embeddings = await self.embeddings.embed(self.resume_chunks)
        self.resume_embeddings = [np.array(e) for e in raw_embeddings]
        self.resume_loaded = True
        self.resume_last_updated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Cache resume text for Gemini (saves tokens on repeated analyses)
        try:
            self._resume_cache = await self.gemini.create_cache(
                contents=[f"Candidate Resume:\n\n{text}"],
                display_name="resume-cache",
            )
        except Exception:
            # Caching is optional optimization — continue without it
            self._resume_cache = None

        return self.get_resume_status()

    def get_resume_status(self) -> ResumeStatus:
        return ResumeStatus(
            resume_loaded=self.resume_loaded,
            chunks=len(self.resume_chunks),
            last_updated=self.resume_last_updated,
        )

    async def analyze(self, job_url: str) -> AnalyzeResponse:
        start = time.time()
        self.gemini.total_input_tokens = 0
        self.gemini.total_output_tokens = 0
        self.gemini.call_count = 0

        # Step 1: Fetch & Parse JD
        raw_text = await fetch_job_page(job_url)
        jd = await parse_job_description(self.gemini, raw_text)

        # Step 2: Company Research
        company = await research_company(self.gemini, jd.company)

        # Step 3: GitHub Scan
        org_slug = re.sub(r"[^a-z0-9-]", "", jd.company.lower().replace(" ", "-"))
        github = await scan_github_org(org_slug, self.github_token)

        # Step 4: Resume Comparison
        if self.resume_loaded:
            resume_match = await compare_resume(
                self.embeddings,
                jd.requirements,
                self.resume_chunks,
                self.resume_embeddings,
            )
        else:
            resume_match = ResumeMatch(overall_similarity=0.0, top_matches=[])

        # Step 5: Verdict
        verdict = await generate_verdict(
            self.gemini, jd, company, github, resume_match
        )

        elapsed = time.time() - start
        usage = self.gemini.get_usage()

        return AnalyzeResponse(
            status="completed",
            verdict=verdict,
            metadata=AnalysisMetadata(
                analysis_time_seconds=round(elapsed, 2),
                llm_calls=usage["calls"],
                tokens_used={"input": usage["input"], "output": usage["output"]},
                estimated_cost_usd=self.gemini.estimated_cost(),
            ),
        )

    async def tailor_start(self, job_url: str) -> TailorStartResponse:
        raw_text = await fetch_job_page(job_url)
        jd = await parse_job_description(self.gemini, raw_text)

        questions = await generate_questions(self.gemini, jd, self.resume_text)

        session_id = str(uuid.uuid4())
        self._tailor_sessions[session_id] = TailorSession(
            jd=jd,
            questions=questions,
            resume_text=self.resume_text,
        )

        return TailorStartResponse(
            session_id=session_id,
            questions=questions,
            job_summary=f"{jd.title} at {jd.company}",
        )

    async def tailor_generate(self, session_id: str, answers: dict[str, str]) -> bytes:
        session = self._tailor_sessions[session_id]  # Raises KeyError if not found

        tailored = await tailor_resume(
            self.gemini, session.jd, session.resume_text, answers
        )

        pdf_bytes = render_minimal(tailored)

        del self._tailor_sessions[session_id]

        return pdf_bytes
