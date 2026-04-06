import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from job_researcher.models import (
    TailorQuestion,
    TailorStartResponse,
)


@pytest.mark.asyncio
async def test_tailor_start_no_resume(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = MagicMock()
        mock_pipeline.resume_loaded = False
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/resume/tailor",
            json={"job_url": "https://example.com/jobs/1"},
        )
        assert response.status_code == 400
        assert "resume" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tailor_start_success(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = AsyncMock()
        mock_pipeline.resume_loaded = True
        mock_pipeline.tailor_start.return_value = TailorStartResponse(
            session_id="test-session",
            questions=[
                TailorQuestion(id="q1", question="K8s exp?", context="Gap"),
            ],
            job_summary="Backend Engineer at Acme",
        )
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/resume/tailor",
            json={"job_url": "https://example.com/jobs/1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert len(data["questions"]) == 1


@pytest.mark.asyncio
async def test_tailor_generate_invalid_session(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = AsyncMock()
        mock_pipeline.tailor_generate.side_effect = KeyError("bad-session")
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/resume/tailor/generate",
            json={"session_id": "bad-session", "answers": {}},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_tailor_generate_success(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = AsyncMock()
        mock_pipeline.tailor_generate.return_value = b"%PDF-1.4 fake pdf content"
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/resume/tailor/generate",
            json={"session_id": "test-session", "answers": {"q1": "Yes"}},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


@pytest.mark.asyncio
async def test_tailor_generate_latex_failure(client):
    with patch("job_researcher.main.get_pipeline") as mock_get:
        mock_pipeline = AsyncMock()
        mock_pipeline.tailor_generate.return_value = None
        mock_get.return_value = mock_pipeline

        response = await client.post(
            "/resume/tailor/generate",
            json={"session_id": "test-session", "answers": {"q1": "Yes"}},
        )
        assert response.status_code == 500
        assert "pdf" in response.json()["detail"].lower()
