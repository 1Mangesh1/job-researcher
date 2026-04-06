import json

from job_researcher.models import JobDescription
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a job description parser. Extract structured information from job postings.
Always respond with valid JSON matching the requested schema. Be precise and thorough."""

USER_PROMPT_TEMPLATE = """Extract the following fields from this job description:
- title: Job title
- company: Company name
- location: Location (include remote status)
- requirements: List of required qualifications/skills
- nice_to_haves: List of preferred/optional qualifications
- tech_stack: List of technologies mentioned
- experience_level: Entry/Mid/Senior/Staff/Principal or range

Job description text:
---
{jd_text}
---

Respond with JSON only."""


async def parse_job_description(
    gemini: GeminiService, jd_text: str
) -> JobDescription:
    response = await gemini.generate(
        USER_PROMPT_TEMPLATE.format(jd_text=jd_text),
        system_instruction=SYSTEM_PROMPT,
        response_schema=JobDescription,
        thinking_budget=1024,
    )

    data = json.loads(response)
    data["raw_text"] = jd_text
    return JobDescription(**data)
