import json

from job_researcher.models import JobDescription, Resume
from job_researcher.services.gemini import GeminiService

SYSTEM_PROMPT = """You are an expert resume writer. Given a candidate's original resume, a target job description,
and the candidate's answers to clarifying questions, produce a tailored resume optimized for this specific role.

Rules:
- NEVER fabricate experience. Only use information from the original resume and the candidate's answers.
- Reframe existing experience to highlight relevance to the target role.
- Incorporate new information from the candidate's answers naturally.
- Front-load the most relevant skills and experience.
- Use strong action verbs and quantify achievements where possible.
- Keep bullet points concise (1-2 lines each), max 7 per role.
- Tailor the summary to speak directly to this role's requirements (max 500 chars).
- Order skills by relevance to the JD (most relevant first).
- Group skills by category (e.g. Languages, Frameworks, Cloud).

Return valid JSON matching the requested schema."""

USER_PROMPT_TEMPLATE = """## Target Job
Title: {title}
Company: {company}
Requirements: {requirements}
Nice to haves: {nice_to_haves}
Tech stack: {tech_stack}

## Candidate's Original Resume
{resume_text}

## Candidate's Answers to Clarifying Questions
{answers_text}

## Instructions
Rewrite this resume tailored for the target job. Incorporate the candidate's answers as additional experience/context.
Return JSON with fields:
- name, email, phone, linkedin, github, website (optional)
- summary (max 500 chars)
- skills: object mapping category to comma-separated skills (e.g. {{"Languages": "Python, Go", "Cloud": "AWS, GCP"}})
- experience: list of {{title, company, location, start_date, end_date, bullets}} (1-7 bullets each)
- projects: list of {{name, tech_stack, bullets, link (optional)}}
- education: list of {{degree, institution, dates, details (optional)}}

Return JSON only."""


async def tailor_resume(
    gemini: GeminiService,
    jd: JobDescription,
    resume_text: str,
    answers: dict[str, str],
) -> Resume:
    answers_text = "\n".join(
        f"Q: {qid}\nA: {answer}" for qid, answer in answers.items()
    )

    prompt = USER_PROMPT_TEMPLATE.format(
        title=jd.title,
        company=jd.company,
        requirements=", ".join(jd.requirements),
        nice_to_haves=", ".join(jd.nice_to_haves),
        tech_stack=", ".join(jd.tech_stack),
        resume_text=resume_text,
        answers_text=answers_text,
    )

    response = await gemini.generate(
        prompt,
        system_instruction=SYSTEM_PROMPT,
        response_schema=Resume,
        thinking_budget=10240,
    )

    data = json.loads(response)
    return Resume(**data)
