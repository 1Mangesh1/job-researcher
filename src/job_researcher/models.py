from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


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
    top_matches: list[dict[str, str | float]]


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


class AgentToolName(StrEnum):
    FETCH_AND_PARSE_JD = "fetch_and_parse_jd"
    RESEARCH_COMPANY = "research_company"
    SCAN_GITHUB = "scan_github"
    COMPARE_RESUME = "compare_resume"


class PlannedStep(BaseModel):
    tool: AgentToolName
    reason: str
    depends_on: list[str] = []


class AgentPlan(BaseModel):
    goal: str
    steps: list[PlannedStep]


class AgentTrace(BaseModel):
    plan: AgentPlan
    executed: list[dict]
    reflections: list[str] = []


class AgentAnalyzeResponse(BaseModel):
    status: str
    verdict: Verdict
    trace: AgentTrace
    metadata: AnalysisMetadata


class ResumeStatus(BaseModel):
    resume_loaded: bool
    chunks: int
    last_updated: str | None


class EducationEntry(BaseModel):
    degree: str
    institution: str
    dates: str
    details: str = ""


class Experience(BaseModel):
    title: str
    company: str
    location: str
    start_date: str
    end_date: str
    bullets: list[str] = Field(min_length=1, max_length=7)


class Project(BaseModel):
    name: str
    tech_stack: str
    bullets: list[str]
    link: str | None = None


class Resume(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: str
    github: str
    website: str | None = None
    summary: str = Field(max_length=500)
    skills: dict[str, str]
    experience: list[Experience]
    projects: list[Project]
    education: list[EducationEntry]


class ATSReport(BaseModel):
    score: int
    matched_keywords: list[str]
    missing_keywords: list[str]
    suggestions: list[str]


class GenerateRequest(BaseModel):
    raw_text: str | None = None
    job_url: HttpUrl | None = None
    template_id: str = "minimal"


class GenerateResponse(BaseModel):
    resume_data: Resume
    ats_report: ATSReport | None = None
    pdf_base64: str
    template_id: str


class RenderRequest(BaseModel):
    resume_data: Resume
    template_id: str = "minimal"


class RenderResponse(BaseModel):
    pdf_base64: str


class TailorQuestion(BaseModel):
    id: str
    question: str
    context: str


class TailorStartRequest(BaseModel):
    job_url: HttpUrl


class TailorStartResponse(BaseModel):
    session_id: str
    questions: list[TailorQuestion]
    job_summary: str


class TailorGenerateRequest(BaseModel):
    session_id: str
    answers: dict[str, str]
    template_id: str = "minimal"
