import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from job_researcher.services.gemini import GeminiService


@pytest.fixture
def gemini_service():
    return GeminiService(api_key="test-key")


def test_gemini_service_init(gemini_service):
    assert gemini_service.api_key == "test-key"
    assert gemini_service.model == "gemini-2.5-flash"


def test_gemini_service_tracks_usage(gemini_service):
    assert gemini_service.usage_by_model == {}
    assert gemini_service.call_count == 0
    assert gemini_service.get_usage() == {
        "input": 0,
        "output": 0,
        "calls": 0,
        "by_model": {},
    }
