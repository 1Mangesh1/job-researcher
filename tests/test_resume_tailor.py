import json
import pytest
from unittest.mock import AsyncMock

from job_researcher.models import (
    EducationEntry,
    Experience,
    JobDescription,
    Resume,
)
from job_researcher.steps.resume_tailor import tailor_resume


@pytest.fixture
def sample_jd():
    return JobDescription(
        title="Backend Engineer",
        company="Acme Corp",
        location="Remote",
        requirements=["Python", "Kubernetes", "GraphQL"],
        nice_to_haves=["Terraform"],
        tech_stack=["Python", "K8s", "GraphQL", "PostgreSQL"],
        experience_level="Mid-Senior",
        raw_text="...",
    )


SAMPLE_RESUME_TEXT = """
John Doe - Software Engineer
Email: john@example.com | Phone: 555-0100
5 years Python, Django, FastAPI experience.
Built REST APIs serving 10k req/s at TechCo (2021-present).
PostgreSQL, Redis, Docker.
BS Computer Science, MIT 2019.
"""

SAMPLE_ANSWERS = {
    "q1": "I deployed a side project on GKE with Helm charts",
    "q2": "I built a GraphQL wrapper around a REST API for a hackathon",
    "q3": "I used Ansible for server provisioning at my first job",
}


@pytest.mark.asyncio
async def test_tailor_resume(sample_jd):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-0100",
        "linkedin": "linkedin.com/in/johndoe",
        "github": "github.com/johndoe",
        "summary": "Backend engineer with 5 years Python experience and hands-on Kubernetes and GraphQL exposure.",
        "skills": {
            "Languages": "Python, SQL",
            "Frameworks": "FastAPI, Django, GraphQL",
            "Infrastructure": "Kubernetes, Docker, Ansible",
            "Databases": "PostgreSQL, Redis",
        },
        "experience": [
            {
                "title": "Software Engineer",
                "company": "TechCo",
                "location": "Remote",
                "start_date": "2021",
                "end_date": "Present",
                "bullets": [
                    "Built and maintained REST APIs serving 10,000+ requests/second using Python and FastAPI",
                    "Deployed microservices to Google Kubernetes Engine (GKE) using Helm charts",
                    "Developed a GraphQL API layer wrapping existing REST endpoints",
                    "Managed PostgreSQL databases with Redis caching layer",
                ],
            }
        ],
        "education": [
            {
                "degree": "BS Computer Science",
                "institution": "MIT",
                "dates": "2015-2019",
            }
        ],
        "projects": [],
    })

    result = await tailor_resume(
        mock_gemini, sample_jd, SAMPLE_RESUME_TEXT, SAMPLE_ANSWERS
    )

    assert isinstance(result, Resume)
    assert result.name == "John Doe"
    assert "Kubernetes" in result.skills.get("Infrastructure", "")
    assert len(result.experience) >= 1
    mock_gemini.generate.assert_called_once()

    call_kwargs = mock_gemini.generate.call_args.kwargs
    assert call_kwargs.get("thinking_budget", 0) >= 8192


@pytest.mark.asyncio
async def test_tailor_resume_includes_answers_in_prompt(sample_jd):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps({
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "",
        "linkedin": "",
        "github": "",
        "summary": "Engineer.",
        "skills": {"Languages": "Python"},
        "experience": [
            {
                "title": "SWE",
                "company": "Co",
                "location": "Remote",
                "start_date": "2021",
                "end_date": "Present",
                "bullets": ["Built APIs"],
            }
        ],
        "education": [
            {"degree": "BS", "institution": "MIT", "dates": "2019"},
        ],
        "projects": [],
    })

    await tailor_resume(mock_gemini, sample_jd, SAMPLE_RESUME_TEXT, SAMPLE_ANSWERS)

    prompt = mock_gemini.generate.call_args.args[0]
    assert "GKE" in prompt
    assert "Helm" in prompt
