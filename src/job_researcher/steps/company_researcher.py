import json
import re

from job_researcher.models import CompanySnapshot
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a company research analyst. Research companies and provide structured summaries.
Focus on information relevant to a job seeker: funding stage, team size, tech stack, engineering culture, and employee sentiment.
Always respond with valid JSON."""

USER_PROMPT_TEMPLATE = """Research the company "{company}" and return JSON matching EXACTLY this shape:
{{
  "stage": "Funding stage (Seed, Series A/B/C, Public, Bootstrapped, etc.)",
  "size": "Approximate number of engineers or total employees",
  "tech_stack": ["list", "of", "technologies"],
  "culture_signals": "Engineering culture indicators (remote-friendly, open-source, blog, etc.)",
  "glassdoor_sentiment": "General employee sentiment and rating if available",
  "recent_news": ["list", "of", "notable", "recent", "news"]
}}

Respond with JSON only. No markdown fences, no commentary."""


def _extract_json(raw: str) -> dict:
    s = raw.strip()
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


async def research_company(
    gemini: GeminiService, company: str
) -> CompanySnapshot:
    # Gemini rejects response_schema (JSON mime) + google_search tool in the
    # same call. Ask for JSON in the prompt and parse defensively instead.
    response = await gemini.generate(
        USER_PROMPT_TEMPLATE.format(company=company),
        system_instruction=SYSTEM_PROMPT,
        thinking_budget=1024,
        use_google_search=True,
    )

    data = _extract_json(response)
    return CompanySnapshot(**data)
