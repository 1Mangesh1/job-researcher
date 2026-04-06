import os
import subprocess
import tempfile

from job_researcher.models import TailoredResume

_LATEX_ESCAPES = {
    "&": "\\&",
    "%": "\\%",
    "$": "\\$",
    "#": "\\#",
    "_": "\\_",
    "{": "\\{",
    "}": "\\}",
    "~": "\\textasciitilde{}",
    "^": "\\textasciicircle{}",
}


def _escape(text: str) -> str:
    for char, replacement in _LATEX_ESCAPES.items():
        text = text.replace(char, replacement)
    return text


def _build_contact_line(contact) -> str:
    parts = []
    if contact.email:
        parts.append(f"\\href{{mailto:{contact.email}}}{{{_escape(contact.email)}}}")
    if contact.phone:
        parts.append(_escape(contact.phone))
    if contact.location:
        parts.append(_escape(contact.location))
    if contact.linkedin:
        parts.append(f"\\href{{https://{contact.linkedin}}}{{{_escape(contact.linkedin)}}}")
    if contact.github:
        parts.append(f"\\href{{https://{contact.github}}}{{{_escape(contact.github)}}}")
    if contact.website:
        parts.append(f"\\href{{https://{contact.website}}}{{{_escape(contact.website)}}}")
    return " \\textbar\\ ".join(parts)


def render_latex(resume: TailoredResume) -> str:
    sections = []

    sections.append(f"""\\documentclass[11pt,letterpaper]{{article}}
\\usepackage[top=0.5in,bottom=0.5in,left=0.6in,right=0.6in]{{geometry}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{lmodern}}
\\usepackage{{titlesec}}
\\usepackage{{enumitem}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{xcolor}}

\\pagestyle{{empty}}
\\setlength{{\\parindent}}{{0pt}}
\\setlength{{\\parskip}}{{0pt}}

\\titleformat{{\\section}}{{\\large\\bfseries\\color{{black}}}}{{}}{{0em}}{{}}[\\vspace{{-0.5em}}\\rule{{\\textwidth}}{{0.5pt}}]
\\titlespacing{{\\section}}{{0pt}}{{0.8em}}{{0.4em}}

\\setlist[itemize]{{nosep,leftmargin=1.5em,topsep=2pt}}

\\begin{{document}}

\\begin{{center}}
{{\\LARGE\\bfseries {_escape(resume.name)}}}\\\\[0.3em]
{_build_contact_line(resume.contact)}
\\end{{center}}""")

    sections.append(f"""
\\section{{Summary}}
{_escape(resume.summary)}""")

    if resume.experience:
        exp_entries = []
        for exp in resume.experience:
            bullets = "\n".join(f"  \\item {_escape(b)}" for b in exp.bullets)
            exp_entries.append(f"""\\textbf{{{_escape(exp.title)}}} \\hfill {_escape(exp.dates)}\\\\
\\textit{{{_escape(exp.company)}}} \\hfill {_escape(exp.location)}
\\begin{{itemize}}
{bullets}
\\end{{itemize}}""")
        sections.append(f"""
\\section{{Experience}}
{"\\n\\n".join(exp_entries)}""")

    if resume.projects:
        proj_entries = []
        for proj in resume.projects:
            bullets = "\n".join(f"  \\item {_escape(b)}" for b in proj.bullets)
            proj_entries.append(f"""\\textbf{{{_escape(proj.name)}}} --- \\textit{{{_escape(proj.tech_stack)}}}\\\\
{_escape(proj.description)}
\\begin{{itemize}}
{bullets}
\\end{{itemize}}""")
        sections.append(f"""
\\section{{Projects}}
{"\\n\\n".join(proj_entries)}""")

    if resume.skills:
        sections.append(f"""
\\section{{Technical Skills}}
{", ".join(_escape(s) for s in resume.skills)}""")

    if resume.education:
        edu_entries = []
        for edu in resume.education:
            entry = f"\\textbf{{{_escape(edu.degree)}}} \\hfill {_escape(edu.dates)}\\\\\\textit{{{_escape(edu.institution)}}}"
            if edu.details:
                entry += f"\\\\\n{_escape(edu.details)}"
            edu_entries.append(entry)
        sections.append(f"""
\\section{{Education}}
{"\\n\\n".join(edu_entries)}""")

    sections.append("""
\\end{document}""")

    return "\n".join(sections)


def compile_pdf(latex_content: str) -> bytes | None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")

        with open(tex_path, "w") as f:
            f.write(latex_content)

        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "resume.tex"],
                cwd=tmpdir,
                capture_output=True,
                timeout=30,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return None

        if not os.path.exists(pdf_path):
            return None

        with open(pdf_path, "rb") as f:
            return f.read()
