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
