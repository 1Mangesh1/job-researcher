from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.colors import HexColor


def get_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "name": ParagraphStyle(
            "ResumeName",
            parent=base["Title"],
            fontSize=18,
            leading=22,
            alignment=1,
            spaceAfter=2,
        ),
        "contact": ParagraphStyle(
            "ResumeContact",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            alignment=1,
            textColor=HexColor("#444444"),
            spaceAfter=8,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=10,
            spaceAfter=4,
            textColor=HexColor("#222222"),
        ),
        "body": ParagraphStyle(
            "ResumeBody",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
        ),
        "bullet": ParagraphStyle(
            "ResumeBullet",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            leftIndent=12,
            bulletIndent=0,
        ),
        "skill_category": ParagraphStyle(
            "SkillCategory",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
        ),
        "job_title": ParagraphStyle(
            "JobTitle",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            textColor=HexColor("#000000"),
        ),
        "job_meta": ParagraphStyle(
            "JobMeta",
            parent=base["Normal"],
            fontSize=9,
            leading=11,
            textColor=HexColor("#444444"),
        ),
        "edu_line": ParagraphStyle(
            "EduLine",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
        ),
    }
