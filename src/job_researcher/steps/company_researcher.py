import json

from job_researcher.models import CompanySnapshot
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a company research analyst. Research companies and provide structured summaries.
Focus on information relevant to a job seeker: funding stage, team size, tech stack, engineering culture, and employee sentiment.
Always respond with valid JSON."""

USER_PROMPT_TEMPLATE = """Research the company "{company}" and provide:
- stage: Funding stage (Seed, Series A/B/C, Public, Bootstrapped, etc.)
- size: Approximate number of engineers or total employees
- tech_stack: Technologies they use (from job posts, blog posts, GitHub)
- culture_signals: Engineering culture indicators (remote-friendly, open-source, blog, etc.)
- glassdoor_sentiment: General employee sentiment and rating if available
- recent_news: Notable recent news (funding, launches, acquisitions, layoffs)

Respond with JSON only."""


async def research_company(
    gemini: GeminiService, company: str
) -> CompanySnapshot:
    response = await gemini.generate(
        USER_PROMPT_TEMPLATE.format(company=company),
        system_instruction=SYSTEM_PROMPT,
        response_schema=CompanySnapshot,
        thinking_budget=1024,
        use_google_search=True,
    )

    data = json.loads(response)
    return CompanySnapshot(**data)
