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
