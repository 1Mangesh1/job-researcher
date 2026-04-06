import pytest
from job_researcher.config import Settings
from job_researcher.models import (
    AnalyzeRequest,
    CompanySnapshot,
    JobDescription,
    MatchTier,
    Recommendation,
    Verdict,
)


def test_settings_loads_from_env(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("CF_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("CF_API_TOKEN", "test-token")
    settings = Settings()
    assert settings.gemini_api_key == "test-key"
    assert settings.cf_account_id == "test-account"
    assert settings.cf_api_token == "test-token"
    assert settings.github_token is None


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
