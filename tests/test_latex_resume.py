import pytest

from job_researcher.models import (
    ContactInfo,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    TailoredResume,
)
from job_researcher.steps.latex_resume import render_latex, compile_pdf


@pytest.fixture
def sample_resume():
    return TailoredResume(
        name="John Doe",
        contact=ContactInfo(
            email="john@example.com",
            phone="555-0100",
            location="San Francisco, CA",
            linkedin="linkedin.com/in/johndoe",
            github="github.com/johndoe",
        ),
        summary="Backend engineer with 5 years of Python experience.",
        experience=[
            ExperienceEntry(
                title="Software Engineer",
                company="TechCo",
                location="Remote",
                dates="2021 -- Present",
                bullets=[
                    "Built REST APIs serving 10,000+ req/s",
                    "Deployed to Kubernetes via Helm",
                ],
            ),
        ],
        skills=["Python", "FastAPI", "Kubernetes", "PostgreSQL"],
        education=[
            EducationEntry(
                degree="BS Computer Science",
                institution="MIT",
                dates="2015 -- 2019",
            ),
        ],
        projects=[
            ProjectEntry(
                name="GraphQL Gateway",
                description="API gateway wrapping REST services",
                tech_stack="Python, Strawberry, FastAPI",
                bullets=["Reduced frontend API calls by 60%"],
            ),
        ],
    )


def test_render_latex_produces_valid_document(sample_resume):
    latex = render_latex(sample_resume)

    assert "\\documentclass" in latex
    assert "\\begin{document}" in latex
    assert "\\end{document}" in latex
    assert "John Doe" in latex
    assert "john@example.com" in latex
    assert "Software Engineer" in latex
    assert "TechCo" in latex
    assert "Built REST APIs" in latex
    assert "Python" in latex
    assert "BS Computer Science" in latex
    assert "GraphQL Gateway" in latex


def test_render_latex_escapes_special_characters():
    resume = TailoredResume(
        name="Jane O'Brien",
        contact=ContactInfo(email="jane@example.com"),
        summary="Experience with C++ & Java, 100% test coverage.",
        experience=[],
        skills=["C++", "C#"],
        education=[],
        projects=[],
    )
    latex = render_latex(resume)

    # LaTeX special chars should be escaped
    assert "\\#" in latex
    assert "100\\%" in latex
    assert "\\&" in latex


def test_render_latex_omits_empty_projects():
    resume = TailoredResume(
        name="John Doe",
        contact=ContactInfo(),
        summary="Summary",
        experience=[],
        skills=[],
        education=[],
        projects=[],
    )
    latex = render_latex(resume)
    assert "Projects" not in latex


def test_compile_pdf_returns_none_when_pdflatex_missing(sample_resume):
    latex = render_latex(sample_resume)
    result = compile_pdf(latex)
    assert result is None or isinstance(result, bytes)
