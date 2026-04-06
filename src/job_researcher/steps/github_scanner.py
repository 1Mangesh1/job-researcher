from collections import Counter

import httpx

from job_researcher.models import GitHubSummary

GITHUB_API = "https://api.github.com"
NOTABLE_STAR_THRESHOLD = 100


async def scan_github_org(
    org_name: str, token: str | None = None
) -> GitHubSummary:
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        response = await client.get(
            f"{GITHUB_API}/orgs/{org_name}/repos",
            params={"per_page": 100, "sort": "pushed", "type": "sources"},
        )

    if response.status_code == 404:
        return GitHubSummary(activity_level="not found")

    response.raise_for_status()
    repos = response.json()

    if not repos:
        return GitHubSummary(
            org_url=f"https://github.com/{org_name}",
            activity_level="inactive",
        )

    # Count languages
    lang_counter = Counter(
        r["language"] for r in repos if r.get("language") and not r.get("fork")
    )

    # Find notable repos (by stars)
    notable = [r["name"] for r in repos if r.get("stargazers_count", 0) >= NOTABLE_STAR_THRESHOLD]

    # Activity level based on most recent push
    activity_level = "active" if repos else "inactive"

    return GitHubSummary(
        org_url=f"https://github.com/{org_name}",
        total_public_repos=len(repos),
        primary_languages=[lang for lang, _ in lang_counter.most_common(5)],
        notable_repos=notable,
        activity_level=activity_level,
        open_source_signals=f"{len(notable)} repos with {NOTABLE_STAR_THRESHOLD}+ stars",
    )
