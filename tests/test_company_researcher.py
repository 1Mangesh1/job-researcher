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
