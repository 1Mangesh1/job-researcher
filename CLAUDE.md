# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Commands

All commands available in Makefile. Most common:

```bash
make dev              # Install with dev dependencies (required for local work)
make run              # Start FastAPI server on :8000
make test             # Run full pytest suite
pytest tests/test_foo.py -v  # Run single test file with verbose output
make docker-up        # Start with docker-compose
```

## Architecture

**High-level flow:**

1. **Pipeline (orchestrator)** — Single stateful class in `src/job_researcher/pipeline.py`
   - Manages resume state (text, chunks, embeddings)
   - Manages tailor sessions (dict of uuid → TailorSession)
   - Initializes services: GeminiService, EmbeddingsService

2. **Analysis pipeline** (`pipeline.analyze()`) — 5 sequential steps:
   - Fetch & parse job description (URL → JobDescription object)
   - Research company (Gemini + web search)
   - Scan GitHub org (GitHub API via token)
   - Compare resume (embeddings + cosine similarity)
   - Generate verdict (Gemini with high thinking budget)

3. **Resume tailor pipeline** (`pipeline.tailor_start/generate()`) — Session-based:
   - Create session with job context + AI questions
   - User submits answers
   - Tailor resume text with Gemini
   - Render PDF with ReportLab (LaTeX templates in `templates/`)

4. **Services:**
   - `GeminiService` — Google Generative AI, context caching for resume
   - `EmbeddingsService` — Cloudflare Workers AI for resume embeddings

5. **Steps** (`src/job_researcher/steps/`) — Individual analysis functions:
   - `jd_fetcher.py` — Scrape + parse HTML
   - `jd_parser.py` — Extract requirements with Gemini
   - `resume_comparator.py` — Chunk & embed resume, compute similarity
   - `ats_scorer.py` — ATS compatibility check
   - `company_researcher.py` — Company context gathering
   - `question_generator.py` — Interview prep questions
   - `resume_tailor.py` — AI-powered resume rewriting
   - `github_scanner.py` — Org tech stack discovery
   - `verdict_generator.py` — High-thinking final assessment

**State management:**
- Pipeline is singleton (`_pipeline` global in main.py)
- Resume state cached in memory (text, chunks, embeddings)
- Tailor sessions stored in dict keyed by uuid
- Gemini context caching is optional (wrapped in try/except)

## Key Implementation Details

**Resume caching:** When resume uploaded, Gemini context cache created to save tokens on repeated analyses. If caching fails, analysis continues without it.

**Embeddings:** Resume text chunked → embedded via Cloudflare → stored as numpy arrays. Used for similarity scoring against JD.

**Async throughout:** All I/O (API calls, HTTP) is async. Use `async def` / `await`.

**PDF generation:** ReportLab-based templates in `templates/`. Minimal template is default. LaTeX integration via Dockerfile (texlive installed).

**Testing:** pytest-asyncio for async tests, respx for HTTP mocking. Configuration in pyproject.toml.

## Common Patterns

- **Error handling:** Gemini API calls wrapped in try/except when optional (e.g., caching). Required steps propagate exceptions.
- **Configuration:** Environment variables via Pydantic Settings in `config.py`. See `.env.example`.
- **Models:** Pydantic models in `models.py` (JobDescription, Resume, AnalyzeResponse, etc.)
- **Type hints:** Full Python 3.12+ typing throughout.

## Coding Standards

Follow Karpathy Guidelines:
- Think before coding — surface assumptions & tradeoffs
- Simplicity first — no speculative features/abstractions
- Surgical changes — only touch what you must
- Goal-driven execution — define success criteria

User handles git operations themselves. Avoid force-pushing or rewriting history.

## Frontend

React TypeScript app in `frontend/`. Separate concern from backend (FastAPI handles all logic). State management via useState + useContext (no Redux).
