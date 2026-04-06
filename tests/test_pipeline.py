import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

import numpy as np

from job_researcher.config import get_settings
from job_researcher.models import AnalyzeResponse, Verdict
from job_researcher.pipeline import Pipeline


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("CF_API_TOKEN", "test-token")
    get_settings.cache_clear()


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
        pipeline.resume_loaded = True

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
