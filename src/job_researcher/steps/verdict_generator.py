import json

from job_researcher.models import (
    CompanySnapshot,
    GitHubSummary,
    JobDescription,
    ResumeMatch,
    Verdict,
)
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a career advisor AI. Given research data about a job posting, company, and a candidate's resume match analysis, produce a structured verdict on job fit.

Be honest and specific. Cite concrete evidence from the data provided. Don't inflate match scores — if there are real gaps, say so clearly.

Match tier guidelines:
- STRONG_MATCH (70-100): Core requirements align well, gaps are minor or learnable
- MODERATE_MATCH (45-69): Some alignment but notable gaps in key areas
- WEAK_MATCH (20-44): Few matching skills, significant gaps
- NO_MATCH (0-19): Fundamentally different skill set

Recommendation guidelines:
- APPLY: Strong or moderate match with closeable gaps
- CONSIDER: Moderate match, gaps are significant but role is interesting
- SKIP: Weak match or deal-breaker gaps"""

USER_PROMPT_TEMPLATE = """Analyze this job opportunity and produce a fit verdict.

## Job Description
{jd_json}

## Company Research
{company_json}

## GitHub Presence
{github_json}

## Resume Match Analysis
Overall similarity: {overall_similarity}
Requirement matches:
{match_details}

Populate company_snapshot from the Company Research section. Reasoning: 2-3 sentences."""


async def generate_verdict(
    gemini: GeminiService,
    jd: JobDescription,
    company: CompanySnapshot,
    github: GitHubSummary,
    resume_match: ResumeMatch,
) -> Verdict:
    match_details = "\n".join(
        f"- {m.get('requirement', 'N/A')}: score={m.get('score', 0)} (matched: {m.get('best_match', 'N/A')})"
        for m in resume_match.top_matches
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        jd_json=jd.model_dump_json(indent=2),
        company_json=company.model_dump_json(indent=2),
        github_json=github.model_dump_json(indent=2),
        overall_similarity=resume_match.overall_similarity,
        match_details=match_details,
    )

    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        response_schema=Verdict,
        thinking_budget=-1,
    )

    data = json.loads(response)

    # Ensure company_snapshot is from our research, not hallucinated
    data["company_snapshot"] = company.model_dump()

    return Verdict(**data)
