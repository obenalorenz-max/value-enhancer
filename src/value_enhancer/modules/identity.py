import asyncio
import os
import time
from typing import List, Dict, Any, Optional

# Sanitize NO_PROXY for httpx compatibility with IPv6 brackets like [::1]
for var in ("no_proxy", "NO_PROXY"):
    if var in os.environ and "[::1]" in os.environ[var]:
        os.environ[var] = os.environ[var].replace(",[::1]", "").replace("[::1]", "")

import httpx
from ..models import IdentityFinding


# Curated catalog of target platforms with URL formats, categories, and error signals
PLATFORM_CATALOG: List[Dict[str, Any]] = [
    {
        "name": "GitHub",
        "category": "developer",
        "url_template": "https://github.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "GitLab",
        "category": "developer",
        "url_template": "https://gitlab.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Reddit",
        "category": "social",
        "url_template": "https://www.reddit.com/user/{}/about.json",
        "profile_url": "https://www.reddit.com/user/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Dev.to",
        "category": "developer",
        "url_template": "https://dev.to/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Pinterest",
        "category": "social",
        "url_template": "https://www.pinterest.com/{}/",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Telegram",
        "category": "messaging",
        "url_template": "https://t.me/{}",
        "check_type": "content_missing",
        "missing_string": '<meta property="twitter:title" content="Telegram: Contact @',
        "valid_status": [200],
    },
    {
        "name": "Medium",
        "category": "publishing",
        "url_template": "https://medium.com/@{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "HackerNews",
        "category": "tech",
        "url_template": "https://news.ycombinator.com/user?id={}",
        "check_type": "content_missing",
        "missing_string": "No such user.",
        "valid_status": [200],
    },
    {
        "name": "DockerHub",
        "category": "developer",
        "url_template": "https://hub.docker.com/v2/users/{}/",
        "profile_url": "https://hub.docker.com/u/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Linktree",
        "category": "social",
        "url_template": "https://linktr.ee/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Substack",
        "category": "publishing",
        "url_template": "https://{}.substack.com",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "PyPI",
        "category": "developer",
        "url_template": "https://pypi.org/user/{}/",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Keybase",
        "category": "security",
        "url_template": "https://keybase.io/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Kaggle",
        "category": "datascience",
        "url_template": "https://www.kaggle.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "SoundCloud",
        "category": "media",
        "url_template": "https://soundcloud.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Codeforces",
        "category": "developer",
        "url_template": "https://codeforces.com/profile/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
]


class IdentityHunter:
    """Asynchronous multi-platform username scanner (Maigret / Sherlock architecture)."""

    def __init__(self, concurrency_limit: int = 20, timeout: float = 6.0):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    async def _probe_single(
        self, client: httpx.AsyncClient, target_user: str, site: Dict[str, Any]
    ) -> IdentityFinding:
        query_url = site["url_template"].format(target_user)
        public_url = site.get("profile_url", query_url).format(target_user)
        start_time = time.monotonic()

        async with self.semaphore:
            try:
                resp = await client.get(
                    query_url,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True,
                )
                duration = round((time.monotonic() - start_time) * 1000, 2)
                exists = False

                if site.get("check_type") == "content_missing":
                    missing_str = site.get("missing_string", "")
                    if resp.status_code == 200 and missing_str not in resp.text:
                        exists = True
                else:
                    if resp.status_code in site.get("valid_status", [200]):
                        exists = True

                return IdentityFinding(
                    platform=site["name"],
                    url=public_url,
                    exists=exists,
                    status_code=resp.status_code,
                    response_time_ms=duration,
                    category=site.get("category", "general"),
                )

            except Exception as e:
                duration = round((time.monotonic() - start_time) * 1000, 2)
                return IdentityFinding(
                    platform=site["name"],
                    url=public_url,
                    exists=False,
                    status_code=0,
                    response_time_ms=duration,
                    category=site.get("category", "general"),
                    metadata={"error": str(e)},
                )

    async def scan(
        self, username: str, platforms: Optional[List[str]] = None
    ) -> List[IdentityFinding]:
        target_sites = PLATFORM_CATALOG
        if platforms:
            names = set(p.lower() for p in platforms)
            target_sites = [s for s in target_sites if s["name"].lower() in names]

        async with httpx.AsyncClient(verify=False) as client:
            tasks = [
                self._probe_single(client, username, site) for site in target_sites
            ]
            results = await asyncio.gather(*tasks)

        # Sort with found profiles first, then by platform name
        results.sort(key=lambda x: (not x.exists, x.platform))
        return results
