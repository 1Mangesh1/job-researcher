# Job Researcher

LLM-powered pipeline that analyzes a job posting against your resume and returns a verdict (APPLY / CONSIDER / SKIP) with evidence. Ships with both a fixed **DAG** flow and an **agentic** flow (planner → tool executor → synthesizer) over the same step library.

For a deep architecture walkthrough + interview prep, see [`docs/INTERVIEW_DEEP_DIVE.md`](docs/INTERVIEW_DEEP_DIVE.md).

## Features

- **JD fetch + parse** — scrape URL, extract structured fields via Gemini
- **Company research** — Gemini + Google Search grounding
- **GitHub org scan** — languages, notable repos, activity
- **Resume-vs-JD similarity** — Cloudflare BGE embeddings + cosine
- **Verdict** — high-thinking synthesis (match_score, strengths, gaps, recommendation)
- **Resume tailor** — AI rewrites resume for a specific JD, returns PDF (ReportLab)
- **Two analyze modes:**
  - `POST /analyze` — deterministic DAG (5 sequential steps)
  - `POST /analyze/agent` — planner LLM decides tool order; returns verdict + plan + per-step trace

## Tech Stack

**Backend:** FastAPI · Python 3.12 · google-genai SDK · BeautifulSoup4 · ReportLab · pypdf · numpy

**Frontend:** Vanilla HTML/JS static site in `frontend/docs/` (no build step). Calls the backend directly.

**External services:** Google Gemini (LLM + search grounding + context cache) · Cloudflare Workers AI (`@cf/baai/bge-base-en-v1.5` embeddings) · GitHub public API

**Infra:** Docker · docker-compose · GitHub Actions CI

## Quick Start

### Prerequisites
- Python 3.12+
- `uv` (recommended) or pip
- Gemini API key — https://aistudio.google.com/
- Cloudflare account ID + API token — account ID from `wrangler whoami`; API token from https://dash.cloudflare.com/profile/api-tokens (template: "Workers AI")
- GitHub token (optional — without it, scanner is rate-limited to 60 req/hr)

### Setup

```bash
cd "job researcher"
uv sync --all-extras        # or: pip install -e ".[dev]"
cp .env.example .env        # fill in keys (see below)
pytest                      # should pass 58 tests
make run                    # backend on :8000
```

### Run the UI

```bash
cd frontend/docs
python3 -m http.server 3000
# open http://localhost:3000
```

- Click **Profile** → upload resume PDF → **Parse with AI** → Save
- Paste job URL in top bar
- Click the paper-plane icon for the legacy `/api/analyze` flow
- Click the blue **Agent** button for the agentic `/analyze/agent` flow — shows verdict + planner output + execution trace

### Docker

```bash
docker-compose up
```

## Environment (`.env`)

```
GEMINI_API_KEY=...
CF_ACCOUNT_ID=...          # wrangler whoami
CF_API_TOKEN=...           # Cloudflare dashboard, Workers AI template
GITHUB_TOKEN=              # optional
```

## API Endpoints

### Core
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/docs` | Swagger UI |
| GET | `/resume` | Resume status |
| POST | `/resume/upload` | Upload PDF/text resume (populates backend state + embeddings) |
| POST | `/analyze` | DAG flow — 5 sequential steps, returns `Verdict` |
| POST | `/analyze/agent` | **Agent flow** — planner + executor + synthesizer, returns `Verdict + AgentTrace` |
| POST | `/resume/tailor` | Start tailor session, get clarifying questions |
| POST | `/resume/tailor/generate` | Submit answers, receive PDF bytes |

### Legacy UI endpoints (for `frontend/docs/` static site)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/parse-resume` | Parse resume text → structured profile JSON |
| POST | `/api/analyze` | Analyze JD against profile, return gap questions |
| POST | `/api/tailor` | Tailor resume JSON for a JD |

### Request example — agentic

```bash
curl -F "file=@resume.pdf" http://localhost:8000/resume/upload
curl -X POST http://localhost:8000/analyze/agent \
  -H "Content-Type: application/json" \
  -d '{"job_url":"https://..."}' | jq
```

Response includes:
- `verdict` — same shape as `/analyze`
- `trace.plan` — planner output (ordered list of `PlannedStep(tool, reason)`)
- `trace.executed` — per-step `{tool, status, elapsed_s, summary}`
- `metadata` — tokens, LLM calls, estimated cost

## Project Structure

```
job researcher/
├── src/job_researcher/
│   ├── main.py                 # FastAPI app + routes
│   ├── pipeline.py             # Orchestrator (DAG + tailor + analyze_agent wrapper)
│   ├── agent.py                # AnalyzeAgent — planner/executor/synthesizer
│   ├── models.py               # Pydantic schemas (JobDescription, Verdict, AgentPlan, …)
│   ├── config.py               # Pydantic Settings
│   ├── steps/                  # Pure step functions (reused by DAG + agent)
│   │   ├── jd_fetcher.py       # httpx + BeautifulSoup scrape
│   │   ├── jd_parser.py        # Gemini extraction
│   │   ├── company_researcher.py   # Gemini + Google Search grounding
│   │   ├── github_scanner.py   # GitHub REST API
│   │   ├── resume_comparator.py    # chunk + embed + cosine
│   │   ├── ats_scorer.py       # Gemini ATS score
│   │   ├── question_generator.py   # Gemini clarifying questions
│   │   ├── resume_tailor.py    # Gemini rewrite
│   │   └── verdict_generator.py    # Gemini thinking=10240
│   ├── services/
│   │   ├── gemini.py           # GeminiService (single LLM choke-point)
│   │   └── embeddings.py       # Cloudflare Workers AI BGE
│   └── templates/              # ReportLab PDF templates
├── frontend/
│   └── docs/                   # Static vanilla-JS UI (index.html + app.js)
├── tests/                      # 58 pytest-asyncio tests with respx mocks
├── docs/
│   └── INTERVIEW_DEEP_DIVE.md  # Architecture deep dive + interview Q&A
├── Makefile
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Agent vs DAG — at a glance

|  | `/analyze` (DAG) | `/analyze/agent` |
|--|------------------|------------------|
| Step order | Hardcoded in Python | Chosen by planner LLM |
| Extra LLM cost | 0 | +1 planner call (~512 think tokens) |
| Tool skipping | No | Planner may skip irrelevant tools (e.g. GitHub) |
| Failure handling | Raises → 500 | Per-step try/except → captured in trace |
| Response shape | `verdict + metadata` | `verdict + trace + metadata` |
| Determinism | High | Lower (planner decides) |

The agent is intentionally shallow — plan is made once, then executed. True ReAct (re-plan after each observation) is a TODO. See `docs/INTERVIEW_DEEP_DIVE.md` section 7.

## Development

```bash
make dev              # install with dev extras
make run              # backend on :8000
make test             # pytest
make format           # ruff format
make lint             # ruff check
make docker-up        # docker-compose
```

## Coding Standards

Karpathy guidelines: think before coding, simplest-thing-that-works, surgical changes, goal-driven. See `CLAUDE.md`.

## License

MIT
