import json

from job_researcher.models import JobDescription
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a job description parser. Extract structured information from job postings.
Always respond with valid JSON matching the requested schema. Be precise and thorough."""

USER_PROMPT_TEMPLATE = """Extract structured fields from this job description. Include remote status in location. experience_level is one of Entry/Mid/Senior/Staff/Principal or a range.

Job description text:
---
{jd_text}
---"""


async def parse_job_description(
    gemini: GeminiService, jd_text: str
) -> JobDescription:
    response = await gemini.generate(
        USER_PROMPT_TEMPLATE.format(jd_text=jd_text),
        system_instruction=SYSTEM_PROMPT,
        response_schema=JobDescription,
        thinking_budget=0,
        model="gemini-2.5-flash-lite",
    )

    data = json.loads(response)
    data["raw_text"] = jd_text
    return JobDescription(**data)
