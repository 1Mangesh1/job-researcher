# Job Researcher

Agentic pipeline that researches job postings and evaluates fit against your resume. Powered by FastAPI, Google Gemini AI, and sophisticated data processing pipelines.

## Features

- **Job Fetching**: Scrape and parse job descriptions from URLs
- **Resume Analysis**: Upload and parse your resume (PDF/text)
- **JD Parsing**: Intelligent extraction of requirements from job descriptions
- **ATS Scoring**: Semantic similarity scoring between resume and JD
- **Resume Tailoring**: AI-powered resume customization for specific job postings
- **PDF Generation**: Generate tailored resumes with LaTeX templates
- **Company Research**: Gather company context via GitHub scanning
- **Question Generation**: Generate interview prep questions based on job fit
- **Verdict Generation**: High-thinking AI analysis for comprehensive job fit assessment

## Tech Stack

**Backend:**
- FastAPI 0.115+
- Python 3.12+
- Google Generative AI SDK
- BeautifulSoup4 (web scraping)
- ReportLab (PDF generation)
- pypdf (resume parsing)

**Frontend:**
- TypeScript/React
- Modern UI for resume uploads and job analysis

**Infrastructure:**
- Docker & Docker Compose
- GitHub Actions CI/CD
- LaTeX for resume PDF compilation

## Quick Start

### Prerequisites
- Python 3.12+
- Docker (optional)
- Google API key for Gemini

### Local Setup

1. Clone and install dependencies:
```bash
cd "job researcher"
uv sync  # or pip install -e .
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your Google API key
```

3. Run tests:
```bash
pytest
```

4. Start the server:
```bash
python -m uvicorn src.job_researcher.main:app --reload
```

Server runs on `http://localhost:8000`

### Docker

```bash
docker-compose up
```

## API Endpoints

### Job Analysis
- `POST /api/analyze` - Analyze job posting against resume
- `POST /api/verdict` - Generate comprehensive fit assessment

### Resume Management
- `POST /api/resume/upload` - Upload resume PDF
- `GET /api/resume/status` - Get parsed resume info

### Resume Tailoring
- `POST /api/tailor/start` - Start tailoring session
- `POST /api/tailor/step` - Execute tailoring step
- `POST /api/tailor/generate` - Generate tailored resume PDF
- `GET /api/tailor/session/{session_id}` - Get session status

### Support
- `GET /health` - Health check
- `GET /docs` - Swagger UI

## Project Structure

```
job researcher/
├── src/job_researcher/
│   ├── main.py                 # FastAPI app
│   ├── pipeline.py             # Orchestrator
│   ├── models.py               # Data models
│   ├── config.py               # Configuration
│   ├── steps/                  # Analysis pipeline
│   │   ├── jd_fetcher.py       # Fetch job descriptions
│   │   ├── jd_parser.py        # Parse JD content
│   │   ├── resume_comparator.py # Similarity scoring
│   │   ├── ats_scorer.py       # ATS compatibility
│   │   ├── company_researcher.py # Company data
│   │   ├── question_generator.py # Interview prep
│   │   ├── resume_tailor.py    # Resume customization
│   │   ├── github_scanner.py   # GitHub insights
│   │   └── verdict_generator.py # Final assessment
│   ├── services/
│   │   └── gemini.py           # Google AI integration
│   └── templates/              # LaTeX resume templates
├── frontend/                   # React UI
├── tests/                      # Comprehensive test suite
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

## Development

### Running Tests
```bash
pytest                    # All tests
pytest tests/test_api.py  # Specific test file
pytest -v                 # Verbose
```

### Code Quality
The project uses pytest with async support and respx for HTTP mocking.

### Environment Variables
See `.env.example` for all available configuration options.

## Features in Development

- Resume version history
- LinkedIn integration
- Job tracking dashboard
- Email notifications
- Bulk job analysis

## Contributing

1. Write tests first (TDD approach encouraged)
2. Ensure tests pass
3. Update docs if needed

## License

MIT
