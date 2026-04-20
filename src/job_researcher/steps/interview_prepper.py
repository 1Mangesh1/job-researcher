import json
import re

from job_researcher.models import InterviewPrepReport, JobDescription
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are an interview coach with web search access. For a given role and company, surface the most likely interview questions and how to prepare.

Ground answers in real sources: Glassdoor, Blind, levels.fyi, company engineering blogs, recent candidate interview reports. Prefer specifics over generic advice.

Categories: behavioral, technical, system_design, company_specific, coding."""

USER_PROMPT = """Target role: {title} at {company}
Tech stack: {tech_stack}
Experience level: {experience_level}

Research recent interview reports and produce 8-10 likely questions spanning the categories.

Return a JSON object with exactly these fields:
{{
  "role": "{title}",
  "company": "{company}",
  "overview": "2-3 sentence summary of interview style, loop structure, and difficulty for this role",
  "questions": [
    {{
      "question": "...",
      "category": "behavioral|technical|system_design|company_specific|coding",
      "prep_strategy": "Concrete 2-3 sentence prep approach",
      "resource_hint": "Specific resource/topic to study (e.g. 'Review Uber's Cadence workflow engine')"
    }}
  ],
  "study_plan": ["5-7 ordered bullets for a 1-week prep sprint"]
}}

Respond with JSON only, no markdown fences."""


def _extract_json(raw: str) -> dict:
    s = (raw or "").strip()
    if not s:
        raise ValueError("Empty response from Gemini")
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if fenced:
        return json.loads(fenced.group(1).strip())
    match = re.search(r"\{[\s\S]*\}", s)
    if match:
        return json.loads(match.group(0))
    raise ValueError(f"Could not extract JSON: {s[:200]}")


async def prepare_interview(
    gemini: GeminiService, jd: JobDescription
) -> InterviewPrepReport:
    prompt = USER_PROMPT.format(
        title=jd.title,
        company=jd.company,
        tech_stack=", ".join(jd.tech_stack) or "not specified",
        experience_level=jd.experience_level,
    )

    # google_search + response_schema are mutually exclusive in Gemini; parse JSON manually.
    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        use_google_search=True,
        thinking_budget=-1,
    )

    data = _extract_json(response)
    data.setdefault("role", jd.title)
    data.setdefault("company", jd.company)
    return InterviewPrepReport(**data)
