from fastapi import FastAPI, HTTPException, UploadFile
from pypdf import PdfReader
import io

from job_researcher.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    ResumeStatus,
)
from job_researcher.pipeline import Pipeline

app = FastAPI(title="Job Researcher", version="0.1.0")

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
