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
        pipeline.gemini.call_count += 1
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

    # Mock embeddings API (for both resume loading and JD comparison)
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
