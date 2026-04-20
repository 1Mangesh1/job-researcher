import numpy as np
import pytest
import respx
import httpx

from job_researcher.services.embeddings import EmbeddingsService
from job_researcher.steps.resume_comparator import (
    chunk_text,
    compare_resume,
)

SAMPLE_EMBEDDING = [0.1] * 768  # bge-base-en-v1.5 outputs 768-dim vectors


@pytest.mark.asyncio
@respx.mock
async def test_embeddings_service_embed():
    respx.post(
        "https://api.cloudflare.com/client/v4/accounts/test-account/ai/run/@cf/baai/bge-base-en-v1.5"
    ).mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "result": {"data": [SAMPLE_EMBEDDING, SAMPLE_EMBEDDING]},
        })
    )

    service = EmbeddingsService(account_id="test-account", api_token="test-token")
    result = await service.embed(["text one", "text two"])

    assert len(result) == 2
    assert len(result[0]) == 768


def test_chunk_text_splits_by_paragraphs():
    text = "Paragraph one about Python.\n\nParagraph two about FastAPI.\n\nParagraph three about Docker."
    chunks = chunk_text(text, max_chunk_size=50)
    assert len(chunks) >= 2
    assert all(len(c) <= 50 or "\n\n" not in c for c in chunks)


def test_chunk_text_handles_single_block():
    text = "Short resume"
    chunks = chunk_text(text, max_chunk_size=500)
    assert len(chunks) == 1
    assert chunks[0] == "Short resume"


@pytest.mark.asyncio
@respx.mock
async def test_compare_resume():
    respx.post(
        "https://api.cloudflare.com/client/v4/accounts/test-account/ai/run/@cf/baai/bge-base-en-v1.5"
    ).mock(
        return_value=httpx.Response(200, json={
            "success": True,
            "result": {"data": [SAMPLE_EMBEDDING]},
        })
    )

    service = EmbeddingsService(account_id="test-account", api_token="test-token")

    resume_chunks = ["3 years Python and FastAPI experience"]
    resume_embeddings = [np.array(SAMPLE_EMBEDDING)]

    jd_requirements = ["Python experience required"]

    result = await compare_resume(
        service, jd_requirements, resume_chunks, resume_embeddings
    )

    assert 0.0 <= result.overall_similarity <= 1.0
    assert len(result.top_matches) > 0
