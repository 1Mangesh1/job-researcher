import pytest

from job_researcher.models import EducationEntry, Experience, Project, Resume
from job_researcher.templates.minimal import render_minimal


@pytest.fixture
def sample_resume():
    return Resume(
        name="John Doe",
        email="john@example.com",
        phone="555-0100",
        linkedin="linkedin.com/in/johndoe",
        github="github.com/johndoe",
        summary="Backend engineer with 5 years of Python experience.",
        skills={
            "Languages": "Python, Go, SQL",
            "Infrastructure": "Docker, Kubernetes, Terraform",
        },
        experience=[
            Experience(
                title="Senior Backend Engineer",
                company="Acme Corp",
                location="San Francisco, CA",
                start_date="Jan 2022",
                end_date="Present",
                bullets=[
                    "Led migration of monolith to microservices",
                    "Reduced API latency by 40%",
                ],
            ),
        ],
        projects=[
            Project(
                name="GraphQL Gateway",
                tech_stack="Python, Strawberry, FastAPI",
                bullets=["Reduced frontend API calls by 60%"],
                link="https://github.com/johndoe/gql-gateway",
            ),
        ],
        education=[
            EducationEntry(
                degree="BS Computer Science",
                institution="MIT",
                dates="2015-2019",
            ),
        ],
    )


def test_render_minimal_returns_pdf_bytes(sample_resume):
    pdf_bytes = render_minimal(sample_resume)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:5] == b"%PDF-"


def test_render_minimal_produces_valid_pdf(sample_resume):
    pdf_bytes = render_minimal(sample_resume)
    # PDF is compressed, so check structure not raw text
    assert len(pdf_bytes) > 500  # non-trivial content
    assert b"%%EOF" in pdf_bytes


def test_render_minimal_handles_empty_projects():
    resume = Resume(
        name="Jane Doe",
        email="jane@example.com",
        phone="555-0200",
        linkedin="",
        github="",
        summary="Engineer.",
        skills={"Languages": "Python"},
        experience=[
            Experience(
                title="Engineer",
                company="Corp",
                location="NYC",
                start_date="2020",
                end_date="Present",
                bullets=["Did things"],
            ),
        ],
        projects=[],
        education=[
            EducationEntry(degree="BS", institution="State U", dates="2020"),
        ],
    )
    pdf_bytes = render_minimal(resume)
    assert pdf_bytes[:5] == b"%PDF-"


def test_render_minimal_multi_skill_categories(sample_resume):
    # Verify it generates without error for multi-category skills
    pdf_bytes = render_minimal(sample_resume)
    assert pdf_bytes[:5] == b"%PDF-"
    assert len(pdf_bytes) > 500


def test_render_minimal_optional_website():
    resume = Resume(
        name="Test User",
        email="test@test.com",
        phone="555-0300",
        linkedin="linkedin.com/in/test",
        github="github.com/test",
        website="https://test.dev",
        summary="Full-stack dev.",
        skills={"Languages": "Python"},
        experience=[
            Experience(
                title="Dev",
                company="Startup",
                location="Remote",
                start_date="2021",
                end_date="Present",
                bullets=["Built stuff"],
            ),
        ],
        projects=[],
        education=[
            EducationEntry(degree="BS", institution="Uni", dates="2021"),
        ],
    )
    pdf_bytes = render_minimal(resume)
    assert pdf_bytes[:5] == b"%PDF-"
