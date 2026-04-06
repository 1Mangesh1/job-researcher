# Job Research Agent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a FastAPI agentic pipeline that takes a job URL, autonomously researches the role/company, and returns a structured fit verdict against the user's resume.

**Architecture:** Deterministic 5-step pipeline orchestrated by FastAPI. Each step calls Gemini 2.5 Flash with focused prompts. Embeddings via Cloudflare Workers AI. No free-roaming agent — code controls flow, LLM does extraction/reasoning.

**Tech Stack:** FastAPI, google-genai (Gemini 2.5 Flash), httpx, BeautifulSoup4, Cloudflare Workers AI (bge-base-en-v1.5), numpy, pydantic, pytest

---

## Project Structure

```
job-researcher/
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/
│   └── job_researcher/
│       ├── __init__.py
│       ├── main.py                    # FastAPI app + routes
│       ├── config.py                  # pydantic-settings config
│       ├── models.py                  # All Pydantic schemas
│       ├── pipeline.py                # Orchestrator
│       ├── services/
│       │   ├── __init__.py
│       │   ├── gemini.py              # Gemini client wrapper
│       │   ├── embeddings.py          # CF Workers AI embeddings
│       │   └── github.py              # GitHub REST API client
│       └── steps/
│           ├── __init__.py
│           ├── jd_fetcher.py          # Fetch + parse job page
│           ├── jd_parser.py           # LLM: extract structured JD
│           ├── company_researcher.py  # LLM: grounded company research
│           ├── github_scanner.py      # GitHub org analysis
│           ├── resume_comparator.py   # Embed + cosine similarity
│           └── verdict_generator.py   # LLM: synthesize verdict
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_jd_fetcher.py
│   ├── test_jd_parser.py
│   ├── test_company_researcher.py
│   ├── test_github_scanner.py
│   ├── test_resume_comparator.py
│   ├── test_verdict_generator.py
│   ├── test_pipeline.py
│   └── test_api.py
└── data/                              # gitignored, holds resume
```

---

## Task 1: Project Bootstrap

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `src/job_researcher/__init__.py`
- Create: `src/job_researcher/main.py`
- Create: `src/job_researcher/services/__init__.py`
- Create: `src/job_researcher/steps/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Initialize git repo**

```bash
cd "/Users/mangeshbide/Mangesh/LAB/job researcher"
git init
```

**Step 2: Create pyproject.toml**

```toml
[project]
name = "job-researcher"
version = "0.1.0"
description = "Agentic pipeline that researches job postings and evaluates fit against your resume"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "google-genai>=1.0.0",
    "httpx>=0.27.0",
    "beautifulsoup4>=4.12.0",
    "numpy>=2.0.0",
    "pydantic>=2.9.0",
    "pydantic-settings>=2.5.0",
    "python-multipart>=0.0.9",
    "pypdf>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "respx>=0.22.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

**Step 3: Create .gitignore**

```
__pycache__/
*.pyc
.env
data/
.venv/
*.egg-info/
dist/
.pytest_cache/
```

**Step 4: Create .env.example**

```
GEMINI_API_KEY=your-gemini-api-key
CF_ACCOUNT_ID=your-cloudflare-account-id
CF_API_TOKEN=your-cloudflare-api-token
GITHUB_TOKEN=optional-for-higher-rate-limits
```

**Step 5: Create skeleton files**

`src/job_researcher/__init__.py`:
```python
```

`src/job_researcher/services/__init__.py`:
```python
```

`src/job_researcher/steps/__init__.py`:
```python
```

`tests/__init__.py`:
```python
```

`src/job_researcher/main.py`:
```python
from fastapi import FastAPI

app = FastAPI(title="Job Researcher", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

`tests/conftest.py`:
```python
import pytest
from httpx import ASGITransport, AsyncClient

from job_researcher.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

**Step 6: Install dependencies and run health check test**

```bash
cd "/Users/mangeshbide/Mangesh/LAB/job researcher"
uv sync --all-extras
```

**Step 7: Write smoke test**

`tests/test_api.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**Step 8: Run test to verify it passes**

```bash
uv run pytest tests/test_api.py::test_health -v
```

Expected: PASS

**Step 9: Commit**

```bash
git add pyproject.toml .gitignore .env.example src/ tests/
git commit -m "feat: bootstrap project with FastAPI skeleton and test infrastructure"
```

---

## Task 2: Config & Data Models

**Files:**
- Create: `src/job_researcher/config.py`
- Create: `src/job_researcher/models.py`
- Create: `tests/test_models.py`

**Step 1: Write failing test for config**

`tests/test_models.py`:
```python
import pytest
from job_researcher.config import Settings


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("CF_API_TOKEN", "test-token")
    settings = Settings()
    assert settings.gemini_api_key == "test-key"
    assert settings.cf_account_id == "test-account"
    assert settings.cf_api_token == "test-token"
    assert settings.github_token is None
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_models.py::test_settings_loads_from_env -v
```

Expected: FAIL — `cannot import name 'Settings'`

**Step 3: Implement config**

`src/job_researcher/config.py`:
```python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str
    cf_account_id: str
    cf_api_token: str
    github_token: str | None = None

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_models.py::test_settings_loads_from_env -v
```

Expected: PASS

**Step 5: Write failing tests for data models**

Add to `tests/test_models.py`:
```python
from job_researcher.models import (
    AnalyzeRequest,
    CompanySnapshot,
    JobDescription,
    MatchTier,
    Recommendation,
    Verdict,
)


def test_analyze_request_validates_url():
    req = AnalyzeRequest(job_url="https://example.com/jobs/123")
    assert str(req.job_url) == "https://example.com/jobs/123"


def test_job_description_schema():
    jd = JobDescription(
        title="Backend Engineer",
        company="Acme Corp",
        location="Remote",
        requirements=["Python", "FastAPI"],
        nice_to_haves=["Kubernetes"],
        tech_stack=["Python", "PostgreSQL"],
        experience_level="Mid-Senior",
        raw_text="Full job description text...",
    )
    assert jd.title == "Backend Engineer"
    assert len(jd.requirements) == 2


def test_company_snapshot_schema():
    snap = CompanySnapshot(
        stage="Series B",
        size="~120 engineers",
        tech_stack=["Python", "Go"],
        culture_signals="Strong open-source presence",
        glassdoor_sentiment="Positive (4.2/5)",
        recent_news=["Raised $50M Series B"],
    )
    assert snap.stage == "Series B"


def test_verdict_schema():
    verdict = Verdict(
        job_title="Backend Engineer",
        company="Acme Corp",
        match_score=72,
        match_tier=MatchTier.STRONG_MATCH,
        strengths=["Python experience"],
        gaps=["No K8s"],
        company_snapshot=CompanySnapshot(
            stage="Series B",
            size="~120",
            tech_stack=["Python"],
            culture_signals="Good",
            glassdoor_sentiment="4.2/5",
            recent_news=[],
        ),
        recommendation=Recommendation.APPLY,
        reasoning="Strong backend overlap.",
        application_tips=["Lead with Django experience"],
    )
    assert verdict.match_score == 72
    assert verdict.match_tier == MatchTier.STRONG_MATCH
    assert verdict.recommendation == Recommendation.APPLY
```

**Step 6: Run tests to verify they fail**

```bash
uv run pytest tests/test_models.py -v
```

Expected: FAIL — `cannot import name 'AnalyzeRequest'`

**Step 7: Implement all data models**

`src/job_researcher/models.py`:
```python
from enum import StrEnum

from pydantic import BaseModel, HttpUrl


class AnalyzeRequest(BaseModel):
    job_url: HttpUrl


class JobDescription(BaseModel):
    title: str
    company: str
    location: str
    requirements: list[str]
    nice_to_haves: list[str]
    tech_stack: list[str]
    experience_level: str
    raw_text: str


class CompanySnapshot(BaseModel):
    stage: str
    size: str
    tech_stack: list[str]
    culture_signals: str
    glassdoor_sentiment: str
    recent_news: list[str]


class GitHubSummary(BaseModel):
    org_url: str | None = None
    total_public_repos: int = 0
    primary_languages: list[str] = []
    notable_repos: list[str] = []
    activity_level: str = "unknown"
    open_source_signals: str = ""


class ResumeMatch(BaseModel):
    overall_similarity: float
    top_matches: list[dict[str, float]]


class MatchTier(StrEnum):
    STRONG_MATCH = "STRONG_MATCH"
    MODERATE_MATCH = "MODERATE_MATCH"
    WEAK_MATCH = "WEAK_MATCH"
    NO_MATCH = "NO_MATCH"


class Recommendation(StrEnum):
    APPLY = "APPLY"
    CONSIDER = "CONSIDER"
    SKIP = "SKIP"


class Verdict(BaseModel):
    job_title: str
    company: str
    match_score: int
    match_tier: MatchTier
    strengths: list[str]
    gaps: list[str]
    company_snapshot: CompanySnapshot
    recommendation: Recommendation
    reasoning: str
    application_tips: list[str]


class AnalysisMetadata(BaseModel):
    analysis_time_seconds: float
    llm_calls: int
    tokens_used: dict[str, int]
    estimated_cost_usd: float


class AnalyzeResponse(BaseModel):
    status: str
    verdict: Verdict
    metadata: AnalysisMetadata


class ResumeStatus(BaseModel):
    resume_loaded: bool
    chunks: int
    last_updated: str | None
```

**Step 8: Run tests to verify they pass**

```bash
uv run pytest tests/test_models.py -v
```

Expected: ALL PASS

**Step 9: Commit**

```bash
git add src/job_researcher/config.py src/job_researcher/models.py tests/test_models.py
git commit -m "feat: add config and all Pydantic data models"
```

---

## Task 3: Gemini Client Service

**Files:**
- Create: `src/job_researcher/services/gemini.py`
- Create: `tests/test_gemini_service.py`

**Step 1: Write failing test**

`tests/test_gemini_service.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from job_researcher.services.gemini import GeminiService


@pytest.fixture
def gemini_service():
    return GeminiService(api_key="test-key")


def test_gemini_service_init(gemini_service):
    assert gemini_service.api_key == "test-key"
    assert gemini_service.model == "gemini-2.5-flash"


def test_gemini_service_tracks_usage(gemini_service):
    assert gemini_service.total_input_tokens == 0
    assert gemini_service.total_output_tokens == 0
    assert gemini_service.call_count == 0
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_gemini_service.py -v
```

Expected: FAIL — `cannot import name 'GeminiService'`

**Step 3: Implement Gemini service**

`src/job_researcher/services/gemini.py`:
```python
from google import genai
from google.genai import types


class GeminiService:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0

    async def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        response_schema: type | None = None,
        thinking_budget: int | None = None,
        use_google_search: bool = False,
        cached_content: str | None = None,
    ) -> str:
        config_kwargs: dict = {}

        if system_instruction:
            config_kwargs["system_instruction"] = system_instruction

        if response_schema:
            config_kwargs["response_mime_type"] = "application/json"
            config_kwargs["response_schema"] = response_schema

        if thinking_budget is not None:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=thinking_budget
            )

        if use_google_search:
            config_kwargs["tools"] = [
                types.Tool(google_search=types.GoogleSearch())
            ]

        if cached_content:
            config_kwargs["cached_content"] = cached_content

        config = types.GenerateContentConfig(**config_kwargs)

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        if response.usage_metadata:
            self.total_input_tokens += response.usage_metadata.prompt_token_count or 0
            self.total_output_tokens += response.usage_metadata.candidates_token_count or 0
        self.call_count += 1

        return response.text

    def get_usage(self) -> dict:
        return {
            "input": self.total_input_tokens,
            "output": self.total_output_tokens,
            "calls": self.call_count,
        }

    def estimated_cost(self) -> float:
        # Gemini 2.5 Flash pricing (approximate):
        # Input: $0.15/1M tokens, Output: $0.60/1M tokens
        input_cost = (self.total_input_tokens / 1_000_000) * 0.15
        output_cost = (self.total_output_tokens / 1_000_000) * 0.60
        return round(input_cost + output_cost, 6)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_gemini_service.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/services/gemini.py tests/test_gemini_service.py
git commit -m "feat: add Gemini client service with usage tracking"
```

---

## Task 4: JD Fetcher & Parser (Pipeline Step 1)

**Files:**
- Create: `src/job_researcher/steps/jd_fetcher.py`
- Create: `src/job_researcher/steps/jd_parser.py`
- Create: `tests/test_jd_fetcher.py`
- Create: `tests/test_jd_parser.py`

### Part A: JD Fetcher

**Step 1: Write failing test for fetcher**

`tests/test_jd_fetcher.py`:
```python
import pytest
import respx
import httpx

from job_researcher.steps.jd_fetcher import fetch_job_page


SAMPLE_HTML = """
<html>
<head><title>Backend Engineer - Acme Corp</title></head>
<body>
  <nav>Home | Jobs | About</nav>
  <div class="job-description">
    <h1>Backend Engineer</h1>
    <p>We're looking for a Backend Engineer to join our team.</p>
    <h2>Requirements</h2>
    <ul>
      <li>3+ years Python experience</li>
      <li>Experience with FastAPI or Django</li>
    </ul>
    <h2>Nice to have</h2>
    <ul>
      <li>Kubernetes experience</li>
    </ul>
  </div>
  <footer>Copyright 2026</footer>
</body>
</html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_returns_text():
    respx.get("https://example.com/jobs/123").mock(
        return_value=httpx.Response(200, html=SAMPLE_HTML)
    )
    text = await fetch_job_page("https://example.com/jobs/123")
    assert "Backend Engineer" in text
    assert "3+ years Python experience" in text


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_strips_nav_and_footer():
    respx.get("https://example.com/jobs/123").mock(
        return_value=httpx.Response(200, html=SAMPLE_HTML)
    )
    text = await fetch_job_page("https://example.com/jobs/123")
    # Nav and footer should be stripped or minimized
    assert len(text) < len(SAMPLE_HTML)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_raises_on_error():
    respx.get("https://example.com/jobs/404").mock(
        return_value=httpx.Response(404)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_job_page("https://example.com/jobs/404")
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_jd_fetcher.py -v
```

Expected: FAIL — `cannot import name 'fetch_job_page'`

**Step 3: Implement JD fetcher**

`src/job_researcher/steps/jd_fetcher.py`:
```python
import httpx
from bs4 import BeautifulSoup


async def fetch_job_page(url: str) -> str:
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": "Mozilla/5.0 (job-researcher/0.1)"},
    ) as client:
        response = await client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_jd_fetcher.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/steps/jd_fetcher.py tests/test_jd_fetcher.py
git commit -m "feat: add JD fetcher with HTML cleanup"
```

### Part B: JD Parser

**Step 6: Write failing test for parser**

`tests/test_jd_parser.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock

from job_researcher.models import JobDescription
from job_researcher.steps.jd_parser import parse_job_description


SAMPLE_JD_TEXT = """
Backend Engineer
Acme Corp - San Francisco, CA (Remote OK)

About the role:
We're looking for a Backend Engineer to build our API platform.

Requirements:
- 3+ years of Python experience
- Experience with FastAPI or Django
- PostgreSQL knowledge

Nice to have:
- Kubernetes experience
- GraphQL

Tech stack: Python, FastAPI, PostgreSQL, Docker, AWS
"""


@pytest.mark.asyncio
async def test_parse_job_description():
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "title": "Backend Engineer",
        "company": "Acme Corp",
        "location": "San Francisco, CA (Remote OK)",
        "requirements": [
            "3+ years of Python experience",
            "Experience with FastAPI or Django",
            "PostgreSQL knowledge",
        ],
        "nice_to_haves": ["Kubernetes experience", "GraphQL"],
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience_level": "Mid-Senior",
        "raw_text": SAMPLE_JD_TEXT,
    })

    result = await parse_job_description(mock_gemini, SAMPLE_JD_TEXT)

    assert isinstance(result, JobDescription)
    assert result.title == "Backend Engineer"
    assert result.company == "Acme Corp"
    assert len(result.requirements) == 3
    assert "Python" in result.tech_stack
    mock_gemini.generate.assert_called_once()


@pytest.mark.asyncio
async def test_parse_job_description_passes_raw_text():
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "title": "SWE",
        "company": "Co",
        "location": "Remote",
        "requirements": [],
        "nice_to_haves": [],
        "tech_stack": [],
        "experience_level": "Unknown",
        "raw_text": SAMPLE_JD_TEXT,
    })

    result = await parse_job_description(mock_gemini, SAMPLE_JD_TEXT)
    assert result.raw_text == SAMPLE_JD_TEXT
```

**Step 7: Run tests to verify they fail**

```bash
uv run pytest tests/test_jd_parser.py -v
```

Expected: FAIL — `cannot import name 'parse_job_description'`

**Step 8: Implement JD parser**

`src/job_researcher/steps/jd_parser.py`:
```python
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
```

**Step 9: Run tests to verify they pass**

```bash
uv run pytest tests/test_jd_parser.py -v
```

Expected: PASS

**Step 10: Commit**

```bash
git add src/job_researcher/steps/jd_parser.py tests/test_jd_parser.py
git commit -m "feat: add JD parser with Gemini structured extraction"
```

---

## Task 5: Company Researcher (Pipeline Step 2)

**Files:**
- Create: `src/job_researcher/steps/company_researcher.py`
- Create: `tests/test_company_researcher.py`

**Step 1: Write failing test**

`tests/test_company_researcher.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock

from job_researcher.models import CompanySnapshot
from job_researcher.steps.company_researcher import research_company


@pytest.mark.asyncio
async def test_research_company():
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "stage": "Series B",
        "size": "~120 engineers",
        "tech_stack": ["Python", "Go", "PostgreSQL"],
        "culture_signals": "Strong open-source presence",
        "glassdoor_sentiment": "Positive (4.2/5)",
        "recent_news": ["Raised $50M Series B in Q1 2026"],
    })

    result = await research_company(mock_gemini, "Acme Corp")

    assert isinstance(result, CompanySnapshot)
    assert result.stage == "Series B"
    assert "Python" in result.tech_stack
    mock_gemini.generate.assert_called_once()

    # Verify grounded search was requested
    call_kwargs = mock_gemini.generate.call_args.kwargs
    assert call_kwargs.get("use_google_search") is True


@pytest.mark.asyncio
async def test_research_company_includes_company_in_prompt():
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "stage": "Unknown",
        "size": "Unknown",
        "tech_stack": [],
        "culture_signals": "",
        "glassdoor_sentiment": "No data",
        "recent_news": [],
    })

    await research_company(mock_gemini, "Obscure Startup Inc")

    call_args = mock_gemini.generate.call_args
    assert "Obscure Startup Inc" in call_args.args[0]
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_company_researcher.py -v
```

Expected: FAIL — `cannot import name 'research_company'`

**Step 3: Implement company researcher**

`src/job_researcher/steps/company_researcher.py`:
```python
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
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_company_researcher.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/steps/company_researcher.py tests/test_company_researcher.py
git commit -m "feat: add company researcher with Gemini grounded search"
```

---

## Task 6: GitHub Scanner (Pipeline Step 3)

**Files:**
- Create: `src/job_researcher/services/github.py`
- Create: `src/job_researcher/steps/github_scanner.py`
- Create: `tests/test_github_scanner.py`

**Step 1: Write failing test**

`tests/test_github_scanner.py`:
```python
import pytest
import respx
import httpx

from job_researcher.models import GitHubSummary
from job_researcher.steps.github_scanner import scan_github_org


SAMPLE_ORG_REPOS = [
    {
        "name": "api-server",
        "language": "Python",
        "stargazers_count": 230,
        "description": "Main API server",
        "pushed_at": "2026-04-01T10:00:00Z",
        "fork": False,
    },
    {
        "name": "frontend",
        "language": "TypeScript",
        "stargazers_count": 45,
        "description": "Web frontend",
        "pushed_at": "2026-03-28T10:00:00Z",
        "fork": False,
    },
    {
        "name": "go-sdk",
        "language": "Go",
        "stargazers_count": 800,
        "description": "Official Go SDK",
        "pushed_at": "2026-04-05T10:00:00Z",
        "fork": False,
    },
]


@pytest.mark.asyncio
@respx.mock
async def test_scan_github_org():
    respx.get("https://api.github.com/orgs/acmecorp/repos").mock(
        return_value=httpx.Response(200, json=SAMPLE_ORG_REPOS)
    )

    result = await scan_github_org("acmecorp")

    assert isinstance(result, GitHubSummary)
    assert result.total_public_repos == 3
    assert "Python" in result.primary_languages
    assert result.org_url == "https://github.com/acmecorp"


@pytest.mark.asyncio
@respx.mock
async def test_scan_github_org_not_found():
    respx.get("https://api.github.com/orgs/nonexistent/repos").mock(
        return_value=httpx.Response(404)
    )

    result = await scan_github_org("nonexistent")

    assert isinstance(result, GitHubSummary)
    assert result.total_public_repos == 0
    assert result.activity_level == "not found"


@pytest.mark.asyncio
@respx.mock
async def test_scan_github_org_identifies_notable_repos():
    respx.get("https://api.github.com/orgs/acmecorp/repos").mock(
        return_value=httpx.Response(200, json=SAMPLE_ORG_REPOS)
    )

    result = await scan_github_org("acmecorp")

    # go-sdk has 800 stars, should be notable
    assert "go-sdk" in result.notable_repos
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_github_scanner.py -v
```

Expected: FAIL — `cannot import name 'scan_github_org'`

**Step 3: Implement GitHub scanner**

`src/job_researcher/steps/github_scanner.py`:
```python
from collections import Counter

import httpx

from job_researcher.models import GitHubSummary

GITHUB_API = "https://api.github.com"
NOTABLE_STAR_THRESHOLD = 100


async def scan_github_org(
    org_name: str, token: str | None = None
) -> GitHubSummary:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        response = await client.get(
            f"{GITHUB_API}/orgs/{org_name}/repos",
            params={"per_page": 100, "sort": "pushed", "type": "sources"},
        )

    if response.status_code == 404:
        return GitHubSummary(activity_level="not found")

    response.raise_for_status()
    repos = response.json()

    if not repos:
        return GitHubSummary(
            org_url=f"https://github.com/{org_name}",
            activity_level="inactive",
        )

    # Count languages
    lang_counter = Counter(
        r["language"] for r in repos if r.get("language") and not r.get("fork")
    )

    # Find notable repos (by stars)
    notable = [r["name"] for r in repos if r.get("stargazers_count", 0) >= NOTABLE_STAR_THRESHOLD]

    # Activity level based on most recent push
    activity_level = "active" if repos else "inactive"

    return GitHubSummary(
        org_url=f"https://github.com/{org_name}",
        total_public_repos=len(repos),
        primary_languages=[lang for lang, _ in lang_counter.most_common(5)],
        notable_repos=notable,
        activity_level=activity_level,
        open_source_signals=f"{len(notable)} repos with {NOTABLE_STAR_THRESHOLD}+ stars",
    )
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_github_scanner.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/steps/github_scanner.py tests/test_github_scanner.py
git commit -m "feat: add GitHub org scanner"
```

---

## Task 7: Resume Service — Embeddings & Comparison (Pipeline Step 4)

**Files:**
- Create: `src/job_researcher/services/embeddings.py`
- Create: `src/job_researcher/steps/resume_comparator.py`
- Create: `tests/test_resume_comparator.py`

### Part A: Embeddings Service

**Step 1: Write failing test for embeddings**

`tests/test_resume_comparator.py`:
```python
import numpy as np
import pytest
import respx
import httpx

from job_researcher.services.embeddings import EmbeddingsService
from job_researcher.steps.resume_comparator import (
    chunk_text,
    compare_resume,
)

SAMPLE_EMBEDDING = [0.1] * 768  # bge-base-en-v1.5 outputs 768-dim vectors


@pytest.mark.asyncio
@respx.mock
async def test_embeddings_service_embed():
    respx.post(
        "https://api.cloudflare.com/client/v4/accounts/test-account/ai/run/@cf/bge-base-en-v1.5"
    ).mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "result": {"data": [SAMPLE_EMBEDDING, SAMPLE_EMBEDDING]},
        })
    )

    service = EmbeddingsService(account_id="test-account", api_token="test-token")
    result = await service.embed(["text one", "text two"])

    assert len(result) == 2
    assert len(result[0]) == 768


def test_chunk_text_splits_by_paragraphs():
    text = "Paragraph one about Python.\n\nParagraph two about FastAPI.\n\nParagraph three about Docker."
    chunks = chunk_text(text, max_chunk_size=50)
    assert len(chunks) >= 2
    assert all(len(c) <= 50 or "\n\n" not in c for c in chunks)


def test_chunk_text_handles_single_block():
    text = "Short resume"
    chunks = chunk_text(text, max_chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0] == "Short resume"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_resume_comparator.py -v
```

Expected: FAIL — `cannot import name 'EmbeddingsService'`

**Step 3: Implement embeddings service**

`src/job_researcher/services/embeddings.py`:
```python
import httpx

CF_AI_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/bge-base-en-v1.5"


class EmbeddingsService:
    def __init__(self, account_id: str, api_token: str):
        self.account_id = account_id
        self.api_token = api_token

    async def embed(self, texts: list[str]) -> list[list[float]]:
        url = CF_AI_URL.format(account_id=self.account_id)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {self.api_token}"},
                json={"text": texts},
            )
            response.raise_for_status()

        data = response.json()
        return data["result"]["data"]
```

**Step 4: Run test_embeddings_service_embed to verify it passes**

```bash
uv run pytest tests/test_resume_comparator.py::test_embeddings_service_embed -v
```

Expected: PASS

### Part B: Resume Comparator

**Step 5: Write failing test for comparator**

Add to `tests/test_resume_comparator.py`:
```python
@pytest.mark.asyncio
@respx.mock
async def test_compare_resume():
    # Mock: 2 calls — one for JD requirements, one for resume chunks (already embedded)
    respx.post(
        "https://api.cloudflare.com/client/v4/accounts/test-account/ai/run/@cf/bge-base-en-v1.5"
    ).mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "result": {"data": [SAMPLE_EMBEDDING]},
        })
    )

    service = EmbeddingsService(account_id="test-account", api_token="test-token")

    resume_chunks = ["3 years Python and FastAPI experience"]
    resume_embeddings = [np.array(SAMPLE_EMBEDDING)]

    jd_requirements = ["Python experience required"]

    result = await compare_resume(
        service, jd_requirements, resume_chunks, resume_embeddings
    )

    assert 0.0 <= result.overall_similarity <= 1.0
    assert len(result.top_matches) > 0
```

**Step 6: Implement resume comparator**

`src/job_researcher/steps/resume_comparator.py`:
```python
import numpy as np

from job_researcher.models import ResumeMatch
from job_researcher.services.embeddings import EmbeddingsService


def chunk_text(text: str, max_chunk_size: int = 500) -> list[str]:
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) + 2 > max_chunk_size:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        chunks.append(current)

    return chunks


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return float(dot / norm)


async def compare_resume(
    embeddings_service: EmbeddingsService,
    jd_requirements: list[str],
    resume_chunks: list[str],
    resume_embeddings: list[np.ndarray],
) -> ResumeMatch:
    # Embed JD requirements
    jd_vectors = await embeddings_service.embed(jd_requirements)

    # For each JD requirement, find best matching resume chunk
    top_matches: list[dict[str, float]] = []
    similarities: list[float] = []

    for i, jd_vec in enumerate(jd_vectors):
        jd_arr = np.array(jd_vec)
        best_score = 0.0
        best_chunk = ""

        for j, resume_vec in enumerate(resume_embeddings):
            score = cosine_similarity(jd_arr, resume_vec)
            if score > best_score:
                best_score = score
                best_chunk = resume_chunks[j][:100]

        similarities.append(best_score)
        top_matches.append({
            "requirement": jd_requirements[i],
            "best_match": best_chunk,
            "score": round(best_score, 3),
        })

    overall = float(np.mean(similarities)) if similarities else 0.0

    return ResumeMatch(
        overall_similarity=round(overall, 3),
        top_matches=top_matches,
    )
```

**Step 7: Run all resume comparator tests**

```bash
uv run pytest tests/test_resume_comparator.py -v
```

Expected: ALL PASS

**Step 8: Commit**

```bash
git add src/job_researcher/services/embeddings.py src/job_researcher/steps/resume_comparator.py tests/test_resume_comparator.py
git commit -m "feat: add embeddings service and resume comparator with cosine similarity"
```

---

## Task 8: Verdict Generator (Pipeline Step 5)

**Files:**
- Create: `src/job_researcher/steps/verdict_generator.py`
- Create: `tests/test_verdict_generator.py`

**Step 1: Write failing test**

`tests/test_verdict_generator.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock

from job_researcher.models import (
    CompanySnapshot,
    GitHubSummary,
    JobDescription,
    MatchTier,
    Recommendation,
    ResumeMatch,
    Verdict,
)
from job_researcher.steps.verdict_generator import generate_verdict


@pytest.fixture
def sample_jd():
    return JobDescription(
        title="Backend Engineer",
        company="Acme Corp",
        location="Remote",
        requirements=["Python", "FastAPI", "PostgreSQL"],
        nice_to_haves=["Kubernetes"],
        tech_stack=["Python", "FastAPI", "PostgreSQL", "Docker"],
        experience_level="Mid-Senior",
        raw_text="...",
    )


@pytest.fixture
def sample_company():
    return CompanySnapshot(
        stage="Series B",
        size="~120 engineers",
        tech_stack=["Python", "Go"],
        culture_signals="Good OSS presence",
        glassdoor_sentiment="4.2/5",
        recent_news=["Raised $50M"],
    )


@pytest.fixture
def sample_github():
    return GitHubSummary(
        org_url="https://github.com/acmecorp",
        total_public_repos=15,
        primary_languages=["Python", "Go"],
        notable_repos=["go-sdk"],
        activity_level="active",
        open_source_signals="1 repo with 100+ stars",
    )


@pytest.fixture
def sample_resume_match():
    return ResumeMatch(
        overall_similarity=0.78,
        top_matches=[
            {"requirement": "Python", "best_match": "5 years Python...", "score": 0.92},
            {"requirement": "FastAPI", "best_match": "Built APIs with FastAPI...", "score": 0.85},
        ],
    )


@pytest.mark.asyncio
async def test_generate_verdict(sample_jd, sample_company, sample_github, sample_resume_match):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "job_title": "Backend Engineer",
        "company": "Acme Corp",
        "match_score": 78,
        "match_tier": "STRONG_MATCH",
        "strengths": ["Strong Python experience"],
        "gaps": ["No Kubernetes experience"],
        "company_snapshot": sample_company.model_dump(),
        "recommendation": "APPLY",
        "reasoning": "Strong overlap in core skills.",
        "application_tips": ["Highlight FastAPI projects"],
    })

    result = await generate_verdict(
        mock_gemini, sample_jd, sample_company, sample_github, sample_resume_match
    )

    assert isinstance(result, Verdict)
    assert result.match_score == 78
    assert result.match_tier == MatchTier.STRONG_MATCH
    assert result.recommendation == Recommendation.APPLY

    # Verify high thinking budget was used
    call_kwargs = mock_gemini.generate.call_args.kwargs
    assert call_kwargs.get("thinking_budget", 0) >= 8192
```

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_verdict_generator.py -v
```

Expected: FAIL — `cannot import name 'generate_verdict'`

**Step 3: Implement verdict generator**

`src/job_researcher/steps/verdict_generator.py`:
```python
import json

from job_researcher.models import (
    CompanySnapshot,
    GitHubSummary,
    JobDescription,
    ResumeMatch,
    Verdict,
)
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are a career advisor AI. Given research data about a job posting, company, and a candidate's resume match analysis, produce a structured verdict on job fit.

Be honest and specific. Cite concrete evidence from the data provided. Don't inflate match scores — if there are real gaps, say so clearly.

Match tier guidelines:
- STRONG_MATCH (70-100): Core requirements align well, gaps are minor or learnable
- MODERATE_MATCH (45-69): Some alignment but notable gaps in key areas
- WEAK_MATCH (20-44): Few matching skills, significant gaps
- NO_MATCH (0-19): Fundamentally different skill set

Recommendation guidelines:
- APPLY: Strong or moderate match with closeable gaps
- CONSIDER: Moderate match, gaps are significant but role is interesting
- SKIP: Weak match or deal-breaker gaps"""

USER_PROMPT_TEMPLATE = """Analyze this job opportunity and produce a fit verdict.

## Job Description
{jd_json}

## Company Research
{company_json}

## GitHub Presence
{github_json}

## Resume Match Analysis
Overall similarity: {overall_similarity}
Requirement matches:
{match_details}

## Instructions
Produce a verdict with:
- match_score (0-100)
- match_tier (STRONG_MATCH/MODERATE_MATCH/WEAK_MATCH/NO_MATCH)
- strengths (list of specific strengths with evidence)
- gaps (list of specific gaps)
- company_snapshot (use company research data)
- recommendation (APPLY/CONSIDER/SKIP)
- reasoning (2-3 sentences synthesizing the analysis)
- application_tips (actionable advice if applying)

Respond with JSON only."""


async def generate_verdict(
    gemini: GeminiService,
    jd: JobDescription,
    company: CompanySnapshot,
    github: GitHubSummary,
    resume_match: ResumeMatch,
) -> Verdict:
    match_details = "\n".join(
        f"- {m.get('requirement', 'N/A')}: score={m.get('score', 0)} (matched: {m.get('best_match', 'N/A')})"
        for m in resume_match.top_matches
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        jd_json=jd.model_dump_json(indent=2),
        company_json=company.model_dump_json(indent=2),
        github_json=github.model_dump_json(indent=2),
        overall_similarity=resume_match.overall_similarity,
        match_details=match_details,
    )

    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        response_schema=Verdict,
        thinking_budget=10240,
    )

    data = json.loads(response)

    # Ensure company_snapshot is from our research, not hallucinated
    data["company_snapshot"] = company.model_dump()

    return Verdict(**data)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_verdict_generator.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/steps/verdict_generator.py tests/test_verdict_generator.py
git commit -m "feat: add verdict generator with high thinking budget"
```

---

## Task 9: Pipeline Orchestrator

**Files:**
- Create: `src/job_researcher/pipeline.py`
- Create: `tests/test_pipeline.py`

**Step 1: Write failing test**

`tests/test_pipeline.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import numpy as np

from job_researcher.models import AnalyzeResponse, Verdict
from job_researcher.pipeline import Pipeline


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("CF_API_TOKEN", "test-token")


@pytest.fixture
def pipeline(mock_settings):
    return Pipeline()


@pytest.mark.asyncio
async def test_pipeline_analyze_calls_all_steps(pipeline):
    sample_verdict = {
        "job_title": "SWE",
        "company": "Co",
        "match_score": 70,
        "match_tier": "STRONG_MATCH",
        "strengths": ["Python"],
        "gaps": [],
        "company_snapshot": {
            "stage": "A",
            "size": "50",
            "tech_stack": [],
            "culture_signals": "",
            "glassdoor_sentiment": "",
            "recent_news": [],
        },
        "recommendation": "APPLY",
        "reasoning": "Good fit.",
        "application_tips": [],
    }

    with (
        patch("job_researcher.pipeline.fetch_job_page", new_callable=AsyncMock) as mock_fetch,
        patch("job_researcher.pipeline.parse_job_description", new_callable=AsyncMock) as mock_parse,
        patch("job_researcher.pipeline.research_company", new_callable=AsyncMock) as mock_research,
        patch("job_researcher.pipeline.scan_github_org", new_callable=AsyncMock) as mock_github,
        patch("job_researcher.pipeline.compare_resume", new_callable=AsyncMock) as mock_compare,
        patch("job_researcher.pipeline.generate_verdict", new_callable=AsyncMock) as mock_verdict,
    ):
        mock_fetch.return_value = "Job text"
        mock_parse.return_value = MagicMock(
            company="Co",
            requirements=["Python"],
            raw_text="Job text",
        )
        mock_research.return_value = MagicMock()
        mock_github.return_value = MagicMock()
        mock_compare.return_value = MagicMock(overall_similarity=0.8, top_matches=[])
        mock_verdict.return_value = Verdict(**sample_verdict)

        # Set up resume state
        pipeline.resume_chunks = ["I know Python"]
        pipeline.resume_embeddings = [np.array([0.1] * 768)]

        result = await pipeline.analyze("https://example.com/jobs/1")

        assert isinstance(result, AnalyzeResponse)
        assert result.status == "completed"
        assert result.verdict.match_score == 70
        mock_fetch.assert_called_once()
        mock_parse.assert_called_once()
        mock_research.assert_called_once()
        mock_github.assert_called_once()
        mock_compare.assert_called_once()
        mock_verdict.assert_called_once()


def test_pipeline_has_no_resume_initially(pipeline):
    assert pipeline.resume_loaded is False
    assert pipeline.resume_chunks == []
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_pipeline.py -v
```

Expected: FAIL — `cannot import name 'Pipeline'`

**Step 3: Implement pipeline**

`src/job_researcher/pipeline.py`:
```python
import re
import time

import numpy as np

from job_researcher.config import get_settings
from job_researcher.models import (
    AnalysisMetadata,
    AnalyzeResponse,
    ResumeMatch,
    ResumeStatus,
)
from job_researcher.services.embeddings import EmbeddingsService
from job_researcher.services.gemini import GeminiService
from job_researcher.steps.company_researcher import research_company
from job_researcher.steps.github_scanner import scan_github_org
from job_researcher.steps.jd_fetcher import fetch_job_page
from job_researcher.steps.jd_parser import parse_job_description
from job_researcher.steps.resume_comparator import (
    chunk_text,
    compare_resume,
)
from job_researcher.steps.verdict_generator import generate_verdict


class Pipeline:
    def __init__(self):
        settings = get_settings()
        self.gemini = GeminiService(api_key=settings.gemini_api_key)
        self.embeddings = EmbeddingsService(
            account_id=settings.cf_account_id,
            api_token=settings.cf_api_token,
        )
        self.github_token = settings.github_token

        self.resume_chunks: list[str] = []
        self.resume_embeddings: list[np.ndarray] = []
        self.resume_loaded: bool = False
        self.resume_last_updated: str | None = None

    async def load_resume(self, text: str) -> ResumeStatus:
        self.resume_chunks = chunk_text(text)
        raw_embeddings = await self.embeddings.embed(self.resume_chunks)
        self.resume_embeddings = [np.array(e) for e in raw_embeddings]
        self.resume_loaded = True
        self.resume_last_updated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        return self.get_resume_status()

    def get_resume_status(self) -> ResumeStatus:
        return ResumeStatus(
            resume_loaded=self.resume_loaded,
            chunks=len(self.resume_chunks),
            last_updated=self.resume_last_updated,
        )

    async def analyze(self, job_url: str) -> AnalyzeResponse:
        start = time.time()
        self.gemini.total_input_tokens = 0
        self.gemini.total_output_tokens = 0
        self.gemini.call_count = 0

        # Step 1: Fetch & Parse JD
        raw_text = await fetch_job_page(job_url)
        jd = await parse_job_description(self.gemini, raw_text)

        # Step 2: Company Research
        company = await research_company(self.gemini, jd.company)

        # Step 3: GitHub Scan
        org_slug = re.sub(r"[^a-z0-9-]", "", jd.company.lower().replace(" ", "-"))
        github = await scan_github_org(org_slug, self.github_token)

        # Step 4: Resume Comparison
        if self.resume_loaded:
            resume_match = await compare_resume(
                self.embeddings,
                jd.requirements,
                self.resume_chunks,
                self.resume_embeddings,
            )
        else:
            resume_match = ResumeMatch(overall_similarity=0.0, top_matches=[])

        # Step 5: Verdict
        verdict = await generate_verdict(
            self.gemini, jd, company, github, resume_match
        )

        elapsed = time.time() - start
        usage = self.gemini.get_usage()

        return AnalyzeResponse(
            status="completed",
            verdict=verdict,
            metadata=AnalysisMetadata(
                analysis_time_seconds=round(elapsed, 2),
                llm_calls=usage["calls"],
                tokens_used={"input": usage["input"], "output": usage["output"]},
                estimated_cost_usd=self.gemini.estimated_cost(),
            ),
        )
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_pipeline.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline orchestrator composing all 5 steps"
```

---

## Task 10: API Endpoints

**Files:**
- Modify: `src/job_researcher/main.py`
- Modify: `tests/test_api.py`

**Step 1: Write failing tests for API endpoints**

Replace `tests/test_api.py`:
```python
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import numpy as np

from job_researcher.models import (
    AnalysisMetadata,
    AnalyzeResponse,
    MatchTier,
    Recommendation,
    ResumeStatus,
    Verdict,
    CompanySnapshot,
)


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_resume_no_resume(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = MagicMock()
        mock_pipeline.get_resume_status.return_value = ResumeStatus(
            resume_loaded=False, chunks=0, last_updated=None
        )
        mock_get.return_value = mock_pipeline

        response = await client.get("/resume")
        assert response.status_code == 200
        data = response.json()
        assert data["resume_loaded"] is False


@pytest.mark.asyncio
async def test_analyze_no_resume_returns_error(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = MagicMock()
        mock_pipeline.resume_loaded = False
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/analyze", json={"job_url": "https://example.com/jobs/1"}
        )
        assert response.status_code == 400
        assert "resume" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_analyze_success(client):
    sample_verdict = Verdict(
        job_title="SWE",
        company="Co",
        match_score=70,
        match_tier=MatchTier.STRONG_MATCH,
        strengths=["Python"],
        gaps=[],
        company_snapshot=CompanySnapshot(
            stage="A", size="50", tech_stack=[], culture_signals="",
            glassdoor_sentiment="", recent_news=[],
        ),
        recommendation=Recommendation.APPLY,
        reasoning="Good fit.",
        application_tips=[],
    )
    sample_response = AnalyzeResponse(
        status="completed",
        verdict=sample_verdict,
        metadata=AnalysisMetadata(
            analysis_time_seconds=5.0,
            llm_calls=4,
            tokens_used={"input": 5000, "output": 1500},
            estimated_cost_usd=0.005,
        ),
    )

    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = AsyncMock()
        mock_pipeline.resume_loaded = True
        mock_pipeline.analyze.return_value = sample_response
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/analyze", json={"job_url": "https://example.com/jobs/1"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["verdict"]["match_score"] == 70
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_api.py -v
```

Expected: FAIL — `cannot import name 'get_pipeline'`

**Step 3: Implement API endpoints**

`src/job_researcher/main.py`:
```python
from fastapi import FastAPI, HTTPException, UploadFile
from pypdf import PdfReader
import io

from job_researcher.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ResumeStatus,
)
from job_researcher.pipeline import Pipeline

app = FastAPI(title="Job Researcher", version="0.1.0")

_pipeline: Pipeline | None = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/resume")
async def get_resume() -> ResumeStatus:
    pipeline = get_pipeline()
    return pipeline.get_resume_status()


@app.post("/resume/upload")
async def upload_resume(file: UploadFile) -> ResumeStatus:
    pipeline = get_pipeline()
    content = await file.read()

    if file.filename and file.filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Resume file is empty")

    return await pipeline.load_resume(text)


@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    pipeline = get_pipeline()

    if not pipeline.resume_loaded:
        raise HTTPException(
            status_code=400,
            detail="No resume uploaded. POST /resume/upload first.",
        )

    return await pipeline.analyze(str(request.job_url))
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add src/job_researcher/main.py tests/test_api.py
git commit -m "feat: add API endpoints for analyze, resume upload, and resume status"
```

---

## Task 11: Context Caching & Final Integration

**Files:**
- Modify: `src/job_researcher/services/gemini.py`
- Modify: `src/job_researcher/pipeline.py`
- Create: `tests/test_integration.py`

**Step 1: Add context caching to Gemini service**

Add to `src/job_researcher/services/gemini.py` (after existing methods):
```python
    async def create_cache(
        self, contents: list[str], display_name: str, ttl: str = "3600s"
    ) -> str:
        cache = self.client.caches.create(
            model=self.model,
            contents=contents,
            config=types.CreateCachedContentConfig(
                display_name=display_name,
                ttl=ttl,
            ),
        )
        return cache.name
```

**Step 2: Update pipeline to cache resume context**

Add to `Pipeline.load_resume` in `src/job_researcher/pipeline.py`, after embedding:
```python
        # Cache resume text for Gemini (saves tokens on repeated analyses)
        try:
            self._resume_cache = await self.gemini.create_cache(
                contents=[f"Candidate Resume:\n\n{text}"],
                display_name="resume-cache",
            )
        except Exception:
            # Caching is optional optimization — continue without it
            self._resume_cache = None
```

And in `Pipeline.__init__`, add:
```python
        self._resume_cache: str | None = None
```

And in `Pipeline.analyze`, before Step 5, pass the cache:
```python
        # Step 5: Verdict (with resume cache if available)
        # The generate_verdict function can use cached_content for the resume
```

**Step 3: Write integration smoke test**

`tests/test_integration.py`:
```python
"""
Integration smoke test — runs the full pipeline against mocked external services.
Verifies all steps connect properly end-to-end.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch

import httpx
import numpy as np
import respx

from job_researcher.models import AnalyzeResponse


SAMPLE_JOB_HTML = """
<html><body>
<h1>Backend Engineer at TestCo</h1>
<p>We need a Python developer with 3 years experience.</p>
<h2>Requirements</h2>
<ul><li>Python</li><li>FastAPI</li></ul>
<h2>Nice to have</h2>
<ul><li>Kubernetes</li></ul>
</body></html>
"""

PARSED_JD = {
    "title": "Backend Engineer",
    "company": "TestCo",
    "location": "Remote",
    "requirements": ["Python", "FastAPI"],
    "nice_to_haves": ["Kubernetes"],
    "tech_stack": ["Python", "FastAPI"],
    "experience_level": "Mid",
}

COMPANY_RESEARCH = {
    "stage": "Series A",
    "size": "~50",
    "tech_stack": ["Python"],
    "culture_signals": "Remote-first",
    "glassdoor_sentiment": "4.0/5",
    "recent_news": [],
}

VERDICT = {
    "job_title": "Backend Engineer",
    "company": "TestCo",
    "match_score": 75,
    "match_tier": "STRONG_MATCH",
    "strengths": ["Python experience"],
    "gaps": ["No K8s"],
    "company_snapshot": COMPANY_RESEARCH,
    "recommendation": "APPLY",
    "reasoning": "Good fit overall.",
    "application_tips": ["Highlight FastAPI experience"],
}

EMBEDDING = [0.1] * 768


@pytest.mark.asyncio
@respx.mock
async def test_full_pipeline_integration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-acct")
    monkeypatch.setenv("CF_API_TOKEN", "test-token")

    from job_researcher.config import get_settings
    get_settings.cache_clear()

    from job_researcher.pipeline import Pipeline

    pipeline = Pipeline()

    # Mock Gemini calls (returns different responses per call)
    gemini_responses = [
        json.dumps(PARSED_JD),       # Step 1: parse JD
        json.dumps(COMPANY_RESEARCH), # Step 2: company research
        json.dumps(VERDICT),          # Step 5: verdict
    ]
    call_index = {"i": 0}

    async def mock_generate(*args, **kwargs):
        idx = call_index["i"]
        call_index["i"] += 1
        return gemini_responses[idx]

    pipeline.gemini.generate = mock_generate

    # Mock job page fetch
    respx.get("https://example.com/jobs/be").mock(
        return_value=httpx.Response(200, html=SAMPLE_JOB_HTML)
    )

    # Mock GitHub API
    respx.get("https://api.github.com/orgs/testco/repos").mock(
        return_value=httpx.Response(200, json=[])
    )

    # Mock embeddings API
    respx.post(url__regex=r".*cloudflare.*bge-base.*").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "result": {"data": [EMBEDDING, EMBEDDING]},
        })
    )

    # Load resume
    await pipeline.load_resume("I have 5 years of Python and FastAPI experience.")

    # Run analysis
    result = await pipeline.analyze("https://example.com/jobs/be")

    assert isinstance(result, AnalyzeResponse)
    assert result.status == "completed"
    assert result.verdict.match_score == 75
    assert result.verdict.recommendation.value == "APPLY"
    assert result.metadata.llm_calls == 3
```

**Step 4: Run integration test**

```bash
uv run pytest tests/test_integration.py -v
```

Expected: PASS

**Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: add context caching and integration test"
```

---

## Task 12: Final Cleanup & Run

**Step 1: Create data directory with .gitkeep**

```bash
mkdir -p data
touch data/.gitkeep
```

**Step 2: Verify the server starts**

```bash
uv run uvicorn job_researcher.main:app --reload --port 8000 &
sleep 2
curl http://localhost:8000/health
curl http://localhost:8000/docs  # Swagger UI should load
kill %1
```

Expected: `{"status":"ok"}` from health endpoint

**Step 3: Run full test suite one final time**

```bash
uv run pytest -v --tb=short
```

Expected: ALL PASS

**Step 4: Final commit**

```bash
git add data/.gitkeep
git commit -m "chore: add data directory and verify server startup"
```

---

## Summary

| Task | Description | Key Files |
|------|-------------|-----------|
| 1 | Project bootstrap | pyproject.toml, main.py, conftest.py |
| 2 | Config & data models | config.py, models.py |
| 3 | Gemini client service | services/gemini.py |
| 4 | JD fetcher & parser | steps/jd_fetcher.py, steps/jd_parser.py |
| 5 | Company researcher | steps/company_researcher.py |
| 6 | GitHub scanner | steps/github_scanner.py |
| 7 | Embeddings & resume comparator | services/embeddings.py, steps/resume_comparator.py |
| 8 | Verdict generator | steps/verdict_generator.py |
| 9 | Pipeline orchestrator | pipeline.py |
| 10 | API endpoints | main.py (full) |
| 11 | Context caching & integration test | gemini.py update, test_integration.py |
| 12 | Final cleanup & verification | data dir, full test run |
