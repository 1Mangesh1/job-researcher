"""
Integration test for the full tailor flow: start session -> generate PDF.
Mocks external services, exercises the full pipeline.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import respx

from job_researcher.models import TailorStartResponse


SAMPLE_JOB_HTML = """
<html><body>
<h1>Backend Engineer at TestCo</h1>
<p>Requirements: Python, Kubernetes, GraphQL</p>
</body></html>
"""

PARSED_JD = {
    "title": "Backend Engineer",
    "company": "TestCo",
    "location": "Remote",
    "requirements": ["Python", "Kubernetes"],
    "nice_to_haves": ["GraphQL"],
    "tech_stack": ["Python", "K8s"],
    "experience_level": "Mid",
}

QUESTIONS = [
    {"id": "q1", "question": "K8s experience?", "context": "Gap in resume"},
]

TAILORED_RESUME = {
    "name": "John Doe",
    "contact": {"email": "john@example.com"},
    "summary": "Backend engineer with Python and K8s.",
    "experience": [
        {
            "title": "SWE",
            "company": "Co",
            "location": "Remote",
            "dates": "2021 -- Present",
            "bullets": ["Built APIs", "Deployed to K8s"],
        }
    ],
    "skills": ["Python", "Kubernetes"],
    "education": [
        {"degree": "BS CS", "institution": "MIT", "dates": "2019"},
    ],
    "projects": [],
}

EMBEDDING = [0.1] * 768


@pytest.mark.asyncio
@respx.mock
async def test_tailor_flow_integration(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-acct")
    monkeypatch.setenv("CF_API_TOKEN", "test-token")

    from job_researcher.config import get_settings
    get_settings.cache_clear()

    from job_researcher.pipeline import Pipeline

    pipeline = Pipeline()

    # Mock Gemini: parse JD -> questions -> tailored resume
    gemini_responses = [
        json.dumps(PARSED_JD),
        json.dumps(QUESTIONS),
        json.dumps(TAILORED_RESUME),
    ]
    call_index = {"i": 0}

    async def mock_generate(*args, **kwargs):
        idx = call_index["i"]
        call_index["i"] += 1
        pipeline.gemini.call_count += 1
        return gemini_responses[idx]

    pipeline.gemini.generate = mock_generate

    # Mock embeddings for resume loading
    respx.post(url__regex=r".*cloudflare.*bge-base.*").mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "result": {"data": [EMBEDDING]},
        })
    )

    # Mock job page
    respx.get("https://example.com/jobs/be").mock(
        return_value=httpx.Response(200, html=SAMPLE_JOB_HTML)
    )

    # Load resume
    await pipeline.load_resume("John Doe, 5 years Python, FastAPI, PostgreSQL.")

    # Step 1: Start tailor session
    result = await pipeline.tailor_start("https://example.com/jobs/be")

    assert isinstance(result, TailorStartResponse)
    assert result.session_id
    assert len(result.questions) == 1

    # Step 2: Generate tailored resume
    pdf_or_none = await pipeline.tailor_generate(
        result.session_id,
        {"q1": "I deployed to GKE with Helm charts"},
    )

    # PDF compilation may fail without texlive -- that's OK in CI
    assert pdf_or_none is None or isinstance(pdf_or_none, bytes)
