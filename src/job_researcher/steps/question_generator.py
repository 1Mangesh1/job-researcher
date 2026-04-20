import json

from job_researcher.models import JobDescription, TailorQuestion
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a career coach. Given a JD and candidate resume, generate 3-5 targeted questions to uncover hidden experience or transferable skills the resume doesn't surface.

Focus on: JD-required skills missing from resume, partial-match nice-to-haves, reframable projects.

For each question: id ("q1", "q2"...), conversational+specific question text, context explaining the gap it addresses."""

USER_PROMPT_TEMPLATE = """## Job Description
Title: {title}
Company: {company}
Requirements: {requirements}
Nice to haves: {nice_to_haves}
Tech stack: {tech_stack}
Experience level: {experience_level}

## Candidate's Current Resume
{resume_text}

Generate 3-5 targeted questions to help tailor this resume for this specific role."""


async def generate_questions(
    gemini: GeminiService,
    jd: JobDescription,
    resume_text: str,
) -> list[TailorQuestion]:
    prompt = USER_PROMPT_TEMPLATE.format(
        title=jd.title,
        company=jd.company,
        requirements=", ".join(jd.requirements),
        nice_to_haves=", ".join(jd.nice_to_haves),
        tech_stack=", ".join(jd.tech_stack),
        experience_level=jd.experience_level,
        resume_text=resume_text,
    )

    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        response_schema=list[TailorQuestion],
        thinking_budget=512,
        model="gemini-2.5-flash-lite",
    )

    data = json.loads(response)
    return [TailorQuestion(**q) for q in data]
