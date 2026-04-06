import pytest

from job_researcher.models import (
    ContactInfo,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    TailorGenerateRequest,
    TailorQuestion,
    TailorStartRequest,
    TailorStartResponse,
    TailoredResume,
)


def test_tailor_question_schema():
    q = TailorQuestion(
        id="q1",
        question="Do you have any Kubernetes experience?",
        context="JD requires K8s but resume doesn't mention it",
    )
    assert q.id == "q1"


def test_tailor_start_request():
    req = TailorStartRequest(job_url="https://example.com/jobs/1")
    assert str(req.job_url) == "https://example.com/jobs/1"


def test_tailor_start_response():
    resp = TailorStartResponse(
        session_id="abc-123",
        questions=[
            TailorQuestion(id="q1", question="Q?", context="Why"),
        ],
        job_summary="Backend Engineer at Acme Corp",
    )
    assert resp.session_id == "abc-123"
    assert len(resp.questions) == 1


def test_tailor_generate_request():
    req = TailorGenerateRequest(
        session_id="abc-123",
        answers={"q1": "Yes, I used K8s in a side project"},
    )
    assert req.answers["q1"].startswith("Yes")


def test_experience_entry():
    entry = ExperienceEntry(
        title="Backend Engineer",
        company="Acme Corp",
        location="Remote",
        dates="Jan 2024 -- Present",
        bullets=["Built REST APIs", "Deployed to K8s"],
    )
    assert len(entry.bullets) == 2


def test_tailored_resume():
    resume = TailoredResume(
        name="John Doe",
        contact=ContactInfo(email="john@example.com", phone="555-0100"),
        summary="Experienced backend engineer...",
        experience=[
            ExperienceEntry(
                title="SWE",
                company="Co",
                location="NYC",
                dates="2023 -- 2024",
                bullets=["Did stuff"],
            )
        ],
        skills=["Python", "FastAPI"],
        education=[
            EducationEntry(
                degree="BS CS",
                institution="MIT",
                dates="2019 -- 2023",
            )
        ],
        projects=[],
    )
    assert resume.name == "John Doe"
    assert len(resume.experience) == 1
