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
