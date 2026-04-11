import pytest
from pydantic import ValidationError

from job_researcher.models import (
    ATSReport,
    EducationEntry,
    Experience,
    Project,
    Resume,
    TailorGenerateRequest,
    TailorQuestion,
    TailorStartRequest,
    TailorStartResponse,
)


def test_experience_requires_at_least_one_bullet():
    with pytest.raises(ValidationError):
        Experience(
            title="SWE",
            company="Co",
            location="Remote",
            start_date="Jan 2024",
            end_date="Present",
            bullets=[],
        )


def test_experience_valid():
    exp = Experience(
        title="Backend Engineer",
        company="Acme Corp",
        location="Remote",
        start_date="Jan 2024",
        end_date="Present",
        bullets=["Built REST APIs", "Deployed to K8s"],
    )
    assert exp.start_date == "Jan 2024"
    assert len(exp.bullets) == 2


def test_project_with_link():
    proj = Project(
        name="MyApp",
        tech_stack="Python, FastAPI",
        bullets=["Built a thing"],
        link="https://github.com/user/myapp",
    )
    assert proj.link == "https://github.com/user/myapp"


def test_project_without_link():
    proj = Project(
        name="MyApp",
        tech_stack="Python, FastAPI",
        bullets=["Built a thing"],
    )
    assert proj.link is None


def test_resume_with_categorized_skills():
    resume = Resume(
        name="John Doe",
        email="john@example.com",
        phone="555-0100",
        linkedin="https://linkedin.com/in/johndoe",
        github="https://github.com/johndoe",
        summary="Experienced backend engineer.",
        skills={
            "Languages": "Python, Go, TypeScript",
            "Frameworks": "FastAPI, React",
            "Cloud": "AWS, GCP",
        },
        experience=[
            Experience(
                title="SWE",
                company="Co",
                location="NYC",
                start_date="2023",
                end_date="2024",
                bullets=["Did stuff"],
            )
        ],
        projects=[
            Project(
                name="MyApp",
                tech_stack="Python",
                bullets=["Built it"],
            )
        ],
        education=[
            EducationEntry(
                degree="BS CS",
                institution="MIT",
                dates="2019 -- 2023",
            )
        ],
    )
    assert resume.name == "John Doe"
    assert "Languages" in resume.skills
    assert resume.website is None


def test_resume_optional_website():
    resume = Resume(
        name="Jane Doe",
        email="jane@example.com",
        phone="555-0200",
        linkedin="https://linkedin.com/in/janedoe",
        github="https://github.com/janedoe",
        website="https://janedoe.dev",
        summary="Full-stack engineer.",
        skills={"Languages": "Python"},
        experience=[
            Experience(
                title="SWE",
                company="Co",
                location="Remote",
                start_date="2022",
                end_date="Present",
                bullets=["Built APIs"],
            )
        ],
        projects=[],
        education=[
            EducationEntry(
                degree="BS CS",
                institution="Stanford",
                dates="2018 -- 2022",
            )
        ],
    )
    assert resume.website == "https://janedoe.dev"


def test_ats_report_schema():
    report = ATSReport(
        score=85,
        matched_keywords=["Python", "FastAPI", "Docker"],
        missing_keywords=["Kubernetes"],
        suggestions=["Add K8s experience to resume"],
    )
    assert report.score == 85
    assert len(report.matched_keywords) == 3
    assert "Kubernetes" in report.missing_keywords


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
    assert req.template_id == "minimal"


def test_tailor_generate_request_custom_template():
    req = TailorGenerateRequest(
        session_id="abc-123",
        answers={"q1": "Answer"},
        template_id="professional",
    )
    assert req.template_id == "professional"
