import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

from job_researcher.models import Resume
from job_researcher.templates.base import get_styles


def _section(title: str, styles: dict) -> list:
    return [
        Paragraph(title.upper(), styles["section_heading"]),
        HRFlowable(width="100%", thickness=0.5, color="#222222", spaceAfter=4),
    ]


def render_minimal(resume: Resume) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    styles = get_styles()
    story: list = []

    # Name
    story.append(Paragraph(resume.name, styles["name"]))

    # Contact line
    parts = [resume.email, resume.phone]
    if resume.linkedin:
        parts.append(resume.linkedin)
    if resume.github:
        parts.append(resume.github)
    if resume.website:
        parts.append(resume.website)
    contact_line = " · ".join(p for p in parts if p)
    story.append(Paragraph(contact_line, styles["contact"]))

    # Summary
    if resume.summary:
        story.extend(_section("Summary", styles))
        story.append(Paragraph(resume.summary, styles["body"]))

    # Skills
    if resume.skills:
        story.extend(_section("Skills", styles))
        for category, items in resume.skills.items():
            story.append(
                Paragraph(
                    f"<b>{category}:</b> {items}",
                    styles["skill_category"],
                )
            )
        story.append(Spacer(1, 4))

    # Experience
    if resume.experience:
        story.extend(_section("Experience", styles))
        for exp in resume.experience:
            story.append(
                Paragraph(
                    f"<b>{exp.title}</b> — {exp.company}",
                    styles["job_title"],
                )
            )
            story.append(
                Paragraph(
                    f"{exp.location} | {exp.start_date} – {exp.end_date}",
                    styles["job_meta"],
                )
            )
            for bullet in exp.bullets:
                story.append(
                    Paragraph(f"• {bullet}", styles["bullet"])
                )
            story.append(Spacer(1, 4))

    # Projects
    if resume.projects:
        story.extend(_section("Projects", styles))
        for proj in resume.projects:
            title_text = f"<b>{proj.name}</b>"
            if proj.tech_stack:
                title_text += f" — {proj.tech_stack}"
            story.append(Paragraph(title_text, styles["job_title"]))
            for bullet in proj.bullets:
                story.append(Paragraph(f"• {bullet}", styles["bullet"]))
            if proj.link:
                story.append(
                    Paragraph(proj.link, styles["job_meta"])
                )
            story.append(Spacer(1, 4))

    # Education
    if resume.education:
        story.extend(_section("Education", styles))
        for edu in resume.education:
            line = f"<b>{edu.degree}</b> — {edu.institution}"
            if edu.dates:
                line += f" ({edu.dates})"
            story.append(Paragraph(line, styles["edu_line"]))
            if edu.details:
                story.append(Paragraph(edu.details, styles["body"]))

    doc.build(story)
    return buf.getvalue()
