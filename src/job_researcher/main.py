from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
import io
import logging
import traceback

logger = logging.getLogger("job_researcher")

from job_researcher.models import (
    AgentAnalyzeResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    InterviewPrepReport,
    InterviewPrepRequest,
    ResumeStatus,
    TailorStartRequest,
    TailorStartResponse,
    TailorGenerateRequest,
)
from job_researcher.pipeline import Pipeline

app = FastAPI(title="Job Researcher", version="0.1.0")

import os

_default_origins = "http://localhost:3000,http://localhost:8000,https://job-researcher.onrender.com,https://fieldnotes.mangeshbide.tech"
_allow_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", _default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {exc}",
            "path": request.url.path,
        },
        headers={"Access-Control-Allow-Origin": "*"},
    )

_pipeline: Pipeline | None = None


def get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/resume")
async def get_resume() -> ResumeStatus:
    pipeline = get_pipeline()
    return pipeline.get_resume_status()


@app.post("/resume/upload")
async def upload_resume(file: UploadFile) -> ResumeStatus:
    pipeline = get_pipeline()
    content = await file.read()

    if file.filename and file.filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = content.decode("utf-8")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Resume file is empty")

    return await pipeline.load_resume(text)


@app.post("/analyze")
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    pipeline = get_pipeline()

    if not pipeline.resume_loaded:
        raise HTTPException(
            status_code=400,
            detail="No resume uploaded. POST /resume/upload first.",
        )

    return await pipeline.analyze(str(request.job_url))


@app.post("/analyze/agent")
async def analyze_agent(request: AnalyzeRequest) -> AgentAnalyzeResponse:
    pipeline = get_pipeline()

    if not pipeline.resume_loaded:
        raise HTTPException(
            status_code=400,
            detail="No resume uploaded. POST /resume/upload first.",
        )

    return await pipeline.analyze_agent(str(request.job_url))


@app.post("/interview-prep")
async def interview_prep(request: InterviewPrepRequest) -> InterviewPrepReport:
    pipeline = get_pipeline()
    return await pipeline.interview_prep(str(request.job_url))


@app.post("/resume/tailor")
async def tailor_start(request: TailorStartRequest) -> TailorStartResponse:
    pipeline = get_pipeline()

    if not pipeline.resume_loaded:
        raise HTTPException(
            status_code=400,
            detail="No resume uploaded. POST /resume/upload first.",
        )

    return await pipeline.tailor_start(str(request.job_url))


@app.post("/resume/tailor/generate")
async def tailor_generate(request: TailorGenerateRequest) -> Response:
    pipeline = get_pipeline()

    try:
        pdf_bytes = await pipeline.tailor_generate(request.session_id, request.answers)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=tailored_resume.pdf"},
    )


# --- Frontend-compatible endpoints ---
# These match the API contract of the jd-based-resume-maker frontend (frontend/docs/app.js)

import json
import re


def _extract_json(raw: str) -> dict | list:
    """Extract JSON from a response that may contain markdown fences or extra text."""
    if not raw or not raw.strip():
        raise ValueError("Empty response from AI")
    s = raw.strip()
    # Try direct parse
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    # Try extracting from markdown fences
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", s)
    if fenced:
        return json.loads(fenced.group(1).strip())
    # Try finding first { ... } or [ ... ]
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", s)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"Could not extract JSON from response: {s[:200]}")


@app.post("/api/parse-resume")
async def api_parse_resume(body: dict):
    """Parse resume text into structured profile using Gemini."""
    pipeline = get_pipeline()
    text = body.get("text", "")

    # Frontend fallback: when browser PDF.js fails, it sends pdf_base64 instead.
    if not text and body.get("pdf_base64"):
        import base64
        try:
            pdf_bytes = base64.b64decode(body["pdf_base64"])
            reader = PdfReader(io.BytesIO(pdf_bytes))
            text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PDF decode failed: {e}")

    if not text or len(text) < 20:
        raise HTTPException(status_code=400, detail="Resume text too short or missing.")

    response = await pipeline.gemini.generate(
        f"""Parse this resume into structured JSON.

RESUME:
{text[:8000]}

Return JSON:
{{
  "name": "", "title": "", "email": "", "phone": "", "location": "",
  "summary": "",
  "skills": ["every skill mentioned"],
  "skillsText": "Categorized skills preserving original format",
  "experience": [{{"company": "", "role": "", "startDate": "", "endDate": "", "bullets": []}}],
  "projects": [{{"name": "", "tech": "", "bullets": [], "link": ""}}],
  "education": [{{"institution": "", "degree": "", "year": "", "score": ""}}],
  "certifications": [],
  "links": [{{"label": "", "url": ""}}]
}}

Extract EVERY detail. Copy bullets VERBATIM. Return JSON only.""",
        system_instruction="You are a resume parser. Respond ONLY with valid JSON, no markdown fences.",
    )

    try:
        data = _extract_json(response)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {e}")
    return {"profile": data}


@app.post("/api/analyze")
async def api_analyze_jd(body: dict):
    """Analyze a JD against candidate profile, return gaps."""
    pipeline = get_pipeline()

    jd_text = body.get("text", "")
    url = body.get("url", "")
    profile = body.get("profile", {})

    if url:
        from job_researcher.steps.jd_fetcher import fetch_job_page
        jd_text = await fetch_job_page(url)

    if not jd_text or len(jd_text) < 30:
        raise HTTPException(status_code=400, detail="Provide a URL or paste the JD text.")

    profile_str = json.dumps(profile)

    response = await pipeline.gemini.generate(
        f"""Analyze this job description against the candidate profile.

JOB DESCRIPTION:
{jd_text}

CANDIDATE PROFILE:
{profile_str}

Return JSON:
{{
  "jobTitle": "extracted job title",
  "company": "extracted company name",
  "keyRequirements": ["top 5-8 requirements"],
  "gaps": [
    {{
      "id": "gap_1",
      "skill": "skill name",
      "question": "Friendly question asking if they have this experience"
    }}
  ]
}}

Rules:
- Identify 3-5 skills/requirements NOT clearly in the profile
- Skip requirements the profile clearly covers
- Be specific and conversational in questions
- If no gaps, return empty gaps array""",
        system_instruction="You are a career analyst. Respond ONLY with valid JSON, no markdown fences.",
    )

    try:
        analysis = _extract_json(response)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {e}")
    return {
        "jdText": jd_text,
        "jobTitle": analysis.get("jobTitle", "Position"),
        "company": analysis.get("company", "Company"),
        "keyRequirements": analysis.get("keyRequirements", []),
        "gaps": analysis.get("gaps", []),
    }


@app.post("/api/tailor")
async def api_tailor_resume(body: dict):
    """Tailor resume for a JD using Gemini."""
    pipeline = get_pipeline()

    profile = body.get("profile")
    jd_text = body.get("jdText", "")
    answers = body.get("answers", {})
    intensity = min(5, max(1, body.get("intensity", 3)))

    if not profile or not jd_text:
        raise HTTPException(status_code=400, detail="profile and jdText are required.")

    intensity_guide = {
        1: "MINIMAL changes: only reorder sections and skills.",
        2: "CONSERVATIVE: reorder + tweak 1-2 words per bullet for JD keywords.",
        3: "BALANCED: reorder, rewrite bullets to naturally include JD keywords.",
        4: "AGGRESSIVE: significantly rewrite bullets to maximize JD keyword matches.",
        5: "FULL REWRITE: completely rewrite everything optimized for this JD.",
    }

    answers_str = "\n".join(
        f"- {skill}: {answer}" for skill, answer in answers.items()
    ) or "No additional answers."

    response = await pipeline.gemini.generate(
        f"""Tailor this resume for the job description.

INTENSITY LEVEL: {intensity}/5 — {intensity_guide[intensity]}

JOB DESCRIPTION:
{jd_text}

FULL ORIGINAL PROFILE:
{json.dumps(profile)}

GAP ANSWERS FROM CANDIDATE:
{answers_str}

Return the COMPLETE resume as JSON with ALL fields preserved.
Include: name, title, email, phone, location, links, summary, experience, projects, skills, skillsText, education, certifications.
Keep ALL entries. Reword based on intensity level. Do NOT fabricate.""",
        system_instruction="You are an expert resume writer. Respond ONLY with valid JSON, no markdown fences.",
    )

    try:
        resume = _extract_json(response)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=500, detail=f"AI parsing failed: {e}")
    return {"resume": resume}


_frontend_dir = Path(__file__).resolve().parents[2] / "frontend" / "docs"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
