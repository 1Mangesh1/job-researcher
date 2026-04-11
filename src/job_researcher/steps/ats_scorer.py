import json

from job_researcher.models import ATSReport, Resume
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) scoring expert. Compare a resume against a job description and evaluate keyword match, relevance, and fit.

Return a JSON object with:
- score: integer 0-100 (overall ATS compatibility score)
- matched_keywords: list of keywords/phrases from the JD found in the resume
- missing_keywords: list of important JD keywords not present in the resume
- suggestions: list of actionable improvements to increase the ATS score

Be specific and practical in suggestions."""

USER_PROMPT_TEMPLATE = """## Resume
Name: {name}
Summary: {summary}
Skills: {skills}
Experience:
{experience}

## Job Description
{jd_text}

Score this resume against the job description. Return JSON only."""


async def score_resume(
    gemini: GeminiService,
    resume: Resume,
    jd_text: str,
) -> ATSReport:
    experience_text = "\n".join(
        f"- {exp.title} at {exp.company}: {', '.join(exp.bullets)}"
        for exp in resume.experience
    )
    skills_text = ", ".join(
        f"{cat}: {items}" for cat, items in resume.skills.items()
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        name=resume.name,
        summary=resume.summary,
        skills=skills_text,
        experience=experience_text,
        jd_text=jd_text,
    )

    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        thinking_budget=1024,
    )

    data = json.loads(response)
    return ATSReport(**data)
