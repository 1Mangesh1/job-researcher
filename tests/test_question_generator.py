import json
import pytest
from unittest.mock import AsyncMock

from job_researcher.models import JobDescription, TailorQuestion
from job_researcher.steps.question_generator import generate_questions


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
        raw_text="We need a backend engineer...",
    )


SAMPLE_RESUME_TEXT = """
John Doe - Software Engineer
5 years Python, Django, FastAPI experience.
Built REST APIs serving 10k req/s.
PostgreSQL, Redis, Docker.
BS Computer Science, MIT 2019.
"""


@pytest.mark.asyncio
async def test_generate_questions(sample_jd):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps([
        {
            "id": "q1",
            "question": "Do you have any Kubernetes experience, even from personal projects or learning?",
            "context": "JD requires Kubernetes but resume doesn't mention it",
        },
        {
            "id": "q2",
            "question": "Have you worked with GraphQL in any capacity?",
            "context": "JD requires GraphQL, resume only mentions REST APIs",
        },
        {
            "id": "q3",
            "question": "Can you describe a project where you handled infrastructure or deployment?",
            "context": "Terraform is nice-to-have; any IaC experience strengthens the application",
        },
    ])

    result = await generate_questions(mock_gemini, sample_jd, SAMPLE_RESUME_TEXT)

    assert len(result) == 3
    assert all(isinstance(q, TailorQuestion) for q in result)
    assert result[0].id == "q1"
    mock_gemini.generate.assert_called_once()

    call_args = mock_gemini.generate.call_args
    prompt = call_args.args[0]
    assert "Kubernetes" in prompt


@pytest.mark.asyncio
async def test_generate_questions_uses_low_thinking(sample_jd):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = json.dumps([
        {"id": "q1", "question": "Q?", "context": "C"},
    ])

    await generate_questions(mock_gemini, sample_jd, SAMPLE_RESUME_TEXT)

    call_kwargs = mock_gemini.generate.call_args.kwargs
    assert call_kwargs.get("thinking_budget", 0) <= 2048
