import pytest
import respx
import httpx

from job_researcher.models import GitHubSummary
from job_researcher.steps.github_scanner import scan_github_org


SAMPLE_ORG_REPOS = [
    {
        "name": "api-server",
        "language": "Python",
        "stargazers_count": 230,
        "description": "Main API server",
        "pushed_at": "2026-04-01T10:00:00Z",
        "fork": False,
    },
    {
        "name": "frontend",
        "language": "TypeScript",
        "stargazers_count": 45,
        "description": "Web frontend",
        "pushed_at": "2026-03-28T10:00:00Z",
        "fork": False,
    },
    {
        "name": "go-sdk",
        "language": "Go",
        "stargazers_count": 800,
        "description": "Official Go SDK",
        "pushed_at": "2026-04-05T10:00:00Z",
        "fork": False,
    },
]


@pytest.mark.asyncio
@respx.mock
async def test_scan_github_org():
    respx.get("https://api.github.com/orgs/acmecorp/repos").mock(
        return_value=httpx.Response(200, json=SAMPLE_ORG_REPOS)
    )

    result = await scan_github_org("acmecorp")

    assert isinstance(result, GitHubSummary)
    assert result.total_public_repos == 3
    assert "Python" in result.primary_languages
    assert result.org_url == "https://github.com/acmecorp"


@pytest.mark.asyncio
@respx.mock
async def test_scan_github_org_not_found():
    respx.get("https://api.github.com/orgs/nonexistent/repos").mock(
        return_value=httpx.Response(404)
    )

    result = await scan_github_org("nonexistent")

    assert isinstance(result, GitHubSummary)
    assert result.total_public_repos == 0
    assert result.activity_level == "not found"


@pytest.mark.asyncio
@respx.mock
async def test_scan_github_org_identifies_notable_repos():
    respx.get("https://api.github.com/orgs/acmecorp/repos").mock(
        return_value=httpx.Response(200, json=SAMPLE_ORG_REPOS)
    )

    result = await scan_github_org("acmecorp")

    # go-sdk has 800 stars, should be notable
    assert "go-sdk" in result.notable_repos
