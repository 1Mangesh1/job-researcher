import json
import pytest
from unittest.mock import AsyncMock

from job_researcher.models import JobDescription
from job_researcher.steps.jd_parser import parse_job_description


SAMPLE_JD_TEXT = """
Backend Engineer
Acme Corp - San Francisco, CA (Remote OK)

About the role:
We're looking for a Backend Engineer to build our API platform.

Requirements:
- 3+ years of Python experience
- Experience with FastAPI or Django
- PostgreSQL knowledge

Nice to have:
- Kubernetes experience
- GraphQL

Tech stack: Python, FastAPI, PostgreSQL, Docker, AWS
"""


@pytest.mark.asyncio
async def test_parse_job_description():
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "title": "Backend Engineer",
        "company": "Acme Corp",
        "location": "San Francisco, CA (Remote OK)",
        "requirements": [
            "3+ years of Python experience",
            "Experience with FastAPI or Django",
            "PostgreSQL knowledge",
        ],
        "nice_to_haves": ["Kubernetes experience", "GraphQL"],
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "experience_level": "Mid-Senior",
        "raw_text": SAMPLE_JD_TEXT,
    })

    result = await parse_job_description(mock_gemini, SAMPLE_JD_TEXT)

    assert isinstance(result, JobDescription)
    assert result.title == "Backend Engineer"
    assert result.company == "Acme Corp"
    assert len(result.requirements) == 3
    assert "Python" in result.tech_stack
    mock_gemini.generate.assert_called_once()


@pytest.mark.asyncio
async def test_parse_job_description_passes_raw_text():
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "title": "SWE",
        "company": "Co",
        "location": "Remote",
        "requirements": [],
        "nice_to_haves": [],
        "tech_stack": [],
        "experience_level": "Unknown",
        "raw_text": SAMPLE_JD_TEXT,
    })

    result = await parse_job_description(mock_gemini, SAMPLE_JD_TEXT)
    assert result.raw_text == SAMPLE_JD_TEXT
