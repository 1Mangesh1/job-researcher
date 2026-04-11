import json

import pytest
from unittest.mock import AsyncMock

from job_researcher.models import (
    ATSReport,
    EducationEntry,
    Experience,
    Resume,
)
from job_researcher.steps.ats_scorer import score_resume


@pytest.fixture
def sample_resume():
    return Resume(
        name="John Doe",
        email="john@example.com",
        phone="555-0100",
        linkedin="linkedin.com/in/johndoe",
        github="github.com/johndoe",
        summary="Backend engineer with Python and FastAPI experience.",
        skills={"Languages": "Python, SQL", "Frameworks": "Django, FastAPI"},
        experience=[
            Experience(
                title="Backend Engineer",
                company="Acme Corp",
                location="SF",
                start_date="2020",
                end_date="Present",
                bullets=["Built REST APIs with FastAPI"],
            )
        ],
        projects=[],
        education=[
            EducationEntry(degree="BS CS", institution="MIT", dates="2019"),
        ],
    )


SAMPLE_JD_TEXT = "We need a backend engineer with Python, Kubernetes, and GraphQL experience."


@pytest.mark.asyncio
async def test_score_resume_returns_ats_report(sample_resume):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "score": 65,
        "matched_keywords": ["Python", "backend engineer"],
        "missing_keywords": ["Kubernetes", "GraphQL"],
        "suggestions": [
            "Add Kubernetes experience to skills section",
        ],
    })

    report = await score_resume(mock_gemini, sample_resume, SAMPLE_JD_TEXT)

    assert isinstance(report, ATSReport)
    assert report.score == 65
    assert "Python" in report.matched_keywords
    assert "Kubernetes" in report.missing_keywords
    assert len(report.suggestions) >= 1
    mock_gemini.generate.assert_called_once()


@pytest.mark.asyncio
async def test_score_resume_prompt_includes_resume_and_jd(sample_resume):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "score": 50,
        "matched_keywords": [],
        "missing_keywords": [],
        "suggestions": [],
    })

    await score_resume(mock_gemini, sample_resume, SAMPLE_JD_TEXT)

    call_args = mock_gemini.generate.call_args
    prompt = call_args.args[0]
    assert "John Doe" in prompt
    assert "Kubernetes" in prompt
