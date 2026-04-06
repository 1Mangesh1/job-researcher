import pytest
import respx
import httpx

from job_researcher.steps.jd_fetcher import fetch_job_page


SAMPLE_HTML = """
<html>
<head><title>Backend Engineer - Acme Corp</title></head>
<body>
  <nav>Home | Jobs | About</nav>
  <div class="job-description">
    <h1>Backend Engineer</h1>
    <p>We're looking for a Backend Engineer to join our team.</p>
    <h2>Requirements</h2>
    <ul>
      <li>3+ years Python experience</li>
      <li>Experience with FastAPI or Django</li>
    </ul>
    <h2>Nice to have</h2>
    <ul>
      <li>Kubernetes experience</li>
    </ul>
  </div>
  <footer>Copyright 2026</footer>
</body>
</html>
"""


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_returns_text():
    respx.get("https://example.com/jobs/123").mock(
        return_value=httpx.Response(200, html=SAMPLE_HTML)
    )
    text = await fetch_job_page("https://example.com/jobs/123")
    assert "Backend Engineer" in text
    assert "3+ years Python experience" in text


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_strips_nav_and_footer():
    respx.get("https://example.com/jobs/123").mock(
        return_value=httpx.Response(200, html=SAMPLE_HTML)
    )
    text = await fetch_job_page("https://example.com/jobs/123")
    # Nav and footer should be stripped or minimized
    assert len(text) < len(SAMPLE_HTML)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_raises_on_error():
    respx.get("https://example.com/jobs/404").mock(
        return_value=httpx.Response(404)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_job_page("https://example.com/jobs/404")
