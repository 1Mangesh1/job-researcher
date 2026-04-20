import json

from job_researcher.models import ATSReport, Resume
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are an ATS (Applicant Tracking System) scoring expert. Compare resume vs JD for keyword match, relevance, and fit. Be specific and practical in suggestions."""

USER_PROMPT_TEMPLATE = """## Resume
Name: {name}
Summary: {summary}
Skills: {skills}
Experience:
{experience}

## Job Description
{jd_text}

Score this resume against the job description."""


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
        response_schema=ATSReport,
        thinking_budget=0,
        model="gemini-2.5-flash-lite",
    )

    data = json.loads(response)
    return ATSReport(**data)
