import json

from job_researcher.models import JobDescription, TailorQuestion
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a career coach helping a candidate tailor their resume for a specific job.
Analyze the gap between the job requirements and the candidate's resume.
Generate 3-5 targeted questions that will help uncover hidden experience or transferable skills
the candidate might have but didn't include in their resume.

Focus on:
- Skills the JD requires that the resume doesn't mention
- Nice-to-haves where the candidate might have partial experience
- Projects or achievements that could be reframed to match the role

Return a JSON array of objects with fields: id, question, context.
- id: "q1", "q2", etc.
- question: The question to ask the candidate (conversational, specific)
- context: Why this question matters (what gap it addresses)"""

USER_PROMPT_TEMPLATE = """## Job Description
Title: {title}
Company: {company}
Requirements: {requirements}
Nice to haves: {nice_to_haves}
Tech stack: {tech_stack}
Experience level: {experience_level}

## Candidate's Current Resume
{resume_text}

Generate 3-5 targeted questions to help tailor this resume for this specific role.
Return JSON array only."""


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
        thinking_budget=1024,
    )

    data = json.loads(response)
    return [TailorQuestion(**q) for q in data]
