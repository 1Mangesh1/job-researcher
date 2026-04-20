import json

from job_researcher.models import JobDescription, Resume
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are an expert resume writer. Rewrite a candidate's resume for a target job using only facts from the original resume and the candidate's answers.

Rules:
- Never fabricate. Reframe existing experience to highlight relevance.
- Front-load the most relevant skills and experience. Strong action verbs, quantify where possible.
- Bullets: 1-2 lines each, max 7 per role. Summary: max 500 chars.
- Order skills by relevance; group by category (Languages, Frameworks, Cloud, etc.)."""

USER_PROMPT_TEMPLATE = """## Target Job
Title: {title}
Company: {company}
Requirements: {requirements}
Nice to haves: {nice_to_haves}
Tech stack: {tech_stack}

## Candidate's Original Resume
{resume_text}

## Candidate's Answers to Clarifying Questions
{answers_text}

Rewrite tailored for the target job. Incorporate the answers as additional experience/context."""

USER_PROMPT_CACHED = """## Target Job
Title: {title}
Company: {company}
Requirements: {requirements}
Nice to haves: {nice_to_haves}
Tech stack: {tech_stack}

## Candidate's Answers to Clarifying Questions
{answers_text}

Rewrite the cached resume tailored for the target job. Incorporate the answers as additional experience/context."""


async def tailor_resume(
    gemini: GeminiService,
    jd: JobDescription,
    resume_text: str,
    answers: dict[str, str],
    resume_cache: str | None = None,
) -> Resume:
    answers_text = "\n".join(
        f"Q: {qid}\nA: {answer}" for qid, answer in answers.items()
    )

    jd_fields = dict(
        title=jd.title,
        company=jd.company,
        requirements=", ".join(jd.requirements),
        nice_to_haves=", ".join(jd.nice_to_haves),
        tech_stack=", ".join(jd.tech_stack),
        answers_text=answers_text,
    )

    if resume_cache:
        prompt = USER_PROMPT_CACHED.format(**jd_fields)
    else:
        prompt = USER_PROMPT_TEMPLATE.format(resume_text=resume_text, **jd_fields)

    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        response_schema=Resume,
        thinking_budget=10240,
        cached_content=resume_cache,
    )

    data = json.loads(response)
    return Resume(**data)
