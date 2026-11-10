import asyncio
import os
import re
import html
import json
import time
from typing import List, Dict, Any, Optional, Tuple

# Sanitize NO_PROXY for httpx compatibility with IPv6 brackets like [::1]
for var in ("no_proxy", "NO_PROXY"):
    if var in os.environ and "[::1]" in os.environ[var]:
        os.environ[var] = os.environ[var].replace(",[::1]", "").replace("[::1]", "")

import httpx
from ..models import IdentityFinding


# Curated high-value catalog of target platforms across key domains
PLATFORM_CATALOG: List[Dict[str, Any]] = [
    # --- Developer & Engineering ---
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
        "name": "Bitbucket",
        "category": "developer",
        "url_template": "https://bitbucket.org/{}/",
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
        "name": "DockerHub",
        "category": "developer",
        "url_template": "https://hub.docker.com/v2/users/{}/",
        "profile_url": "https://hub.docker.com/u/{}",
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
        "name": "NPM",
        "category": "developer",
        "url_template": "https://www.npmjs.com/~{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Kaggle",
        "category": "developer",
        "url_template": "https://www.kaggle.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Replit",
        "category": "developer",
        "url_template": "https://replit.com/@{}",
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
    {
        "name": "LeetCode",
        "category": "developer",
        "url_template": "https://leetcode.com/{}/",
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
        "name": "Hashnode",
        "category": "developer",
        "url_template": "https://hashnode.com/@{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },

    # --- Social & Publishing ---
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
        "name": "Telegram",
        "category": "messaging",
        "url_template": "https://t.me/{}",
        "check_type": "content_missing",
        "missing_string": '<meta property="twitter:title" content="Telegram: Contact @',
        "valid_status": [200],
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
        "name": "Medium",
        "category": "publishing",
        "url_template": "https://medium.com/@{}",
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
        "name": "Linktree",
        "category": "social",
        "url_template": "https://linktr.ee/{}",
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
        "name": "Gravatar",
        "category": "social",
        "url_template": "https://en.gravatar.com/{}.json",
        "profile_url": "https://en.gravatar.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Pastebin",
        "category": "tech",
        "url_template": "https://pastebin.com/u/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Disqus",
        "category": "social",
        "url_template": "https://disqus.com/by/{}/",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "ProductHunt",
        "category": "tech",
        "url_template": "https://www.producthunt.com/@{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "BuyMeACoffee",
        "category": "social",
        "url_template": "https://www.buymeacoffee.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Mastodon",
        "category": "social",
        "url_template": "https://mastodon.social/@{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },

    # --- Gaming, Creative & Streaming ---
    {
        "name": "Steam",
        "category": "gaming",
        "url_template": "https://steamcommunity.com/id/{}",
        "check_type": "content_missing",
        "missing_string": "The specified profile could not be found.",
        "valid_status": [200],
    },
    {
        "name": "Chess.com",
        "category": "gaming",
        "url_template": "https://api.chess.com/pub/player/{}",
        "profile_url": "https://www.chess.com/member/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "itch.io",
        "category": "gaming",
        "url_template": "https://{}.itch.io",
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
        "name": "TradingView",
        "category": "finance",
        "url_template": "https://www.tradingview.com/u/{}/",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Behance",
        "category": "creative",
        "url_template": "https://www.behance.net/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
    {
        "name": "Dribbble",
        "category": "creative",
        "url_template": "https://dribbble.com/{}",
        "check_type": "status_code",
        "valid_status": [200],
        "invalid_status": [404],
    },
]


def _clean_text(s: Optional[str]) -> Optional[str]:
    """Strip HTML entities, newlines, and trailing noise."""
    if not s:
        return None
    cleaned = html.unescape(s)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip() or None


def _extract_profile_metadata(platform: str, response_text: str, content_type: str, username: str) -> Dict[str, Any]:
    """Maigret-style deep parsing: extract display name, bio, avatar, and cross-referenced handles."""
    metadata: Dict[str, Any] = {}
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    extracted_links: List[str] = []
    extracted_handles: List[str] = []

    # 1. JSON parsing for API endpoints
    if "application/json" in content_type or response_text.startswith("{"):
        try:
            data = json.loads(response_text)
            if platform == "Reddit":
                user_data = data.get("data", {})
                display_name = user_data.get("name")
                subreddit = user_data.get("subreddit", {})
                bio = subreddit.get("public_description") or subreddit.get("title")
                avatar_url = user_data.get("icon_img") or subreddit.get("icon_img")
                metadata["karma"] = user_data.get("total_karma")
            elif platform == "Chess.com":
                display_name = data.get("name") or data.get("username")
                avatar_url = data.get("avatar")
                location = data.get("location")
                metadata["followers"] = data.get("followers")
            elif platform == "Gravatar":
                entries = data.get("entry", [])
                if entries:
                    e = entries[0]
                    display_name = e.get("displayName")
                    bio = e.get("aboutMe")
                    avatar_url = e.get("thumbnailUrl")
                    location = e.get("currentLocation")
            elif platform == "DockerHub":
                display_name = data.get("full_name") or data.get("username")
                bio = data.get("company")
        except Exception:
            pass

    # 2. HTML Meta / OpenGraph parsing
    if not display_name or not bio or not avatar_url:
        # Title / Open Graph Title
        og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', response_text, re.I)
        if not og_title:
            og_title = re.search(r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']', response_text, re.I)
        if not og_title:
            og_title = re.search(r'<title>([^<]+)</title>', response_text, re.I)
        if og_title and not display_name:
            t = _clean_text(og_title.group(1))
            if t and len(t) < 80:
                display_name = t

        # Description / Bio
        og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', response_text, re.I)
        if not og_desc:
            og_desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', response_text, re.I)
        if og_desc and not bio:
            b = _clean_text(og_desc.group(1))
            if b and len(b) > 3:
                bio = b

        # Avatar / Image
        og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', response_text, re.I)
        if not og_img:
            og_img = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', response_text, re.I)
        if og_img and not avatar_url:
            candidate_img = og_img.group(1).strip()
            if candidate_img.startswith("http") and not any(bad in candidate_img for bad in ("blank", "default-avatar", "placeholder")):
                avatar_url = candidate_img

    # 3. Recursive extraction of cross-referenced social handles and URLs
    search_corpus = f"{bio or ''} {display_name or ''}"
    # Handles: @handle
    found_handles = re.findall(r'@([a-zA-Z0-9_]{3,25})', search_corpus)
    for h in set(found_handles):
        if h.lower() != username.lower() and h.lower() not in ("gmail", "yahoo", "hotmail", "outlook", "everyone"):
            extracted_handles.append(f"@{h}")

    # Outbound links (Twitter, LinkedIn, YouTube, Personal site)
    raw_links = re.findall(r'https?://[a-zA-Z0-9.\-_]+(?:\/[a-zA-Z0-9._\-%/?=&]*)?', search_corpus)
    for l in set(raw_links):
        clean_l = l.rstrip(".,;:)")
        if len(clean_l) < 120 and not clean_l.endswith(('.png', '.jpg', '.jpeg', '.css', '.js')):
            extracted_links.append(clean_l)

    return {
        "display_name": display_name,
        "bio": bio,
        "avatar_url": avatar_url,
        "location": location,
        "extracted_handles": extracted_handles[:5],
        "extracted_links": extracted_links[:5],
    }


class IdentityHunter:
    """Asynchronous multi-platform username profiler & recursive metadata extractor (Maigret architecture)."""

    def __init__(self, concurrency_limit: int = 25, timeout: float = 6.0):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
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

                parsed_meta: Dict[str, Any] = {}
                name = None
                bio = None
                avatar_url = None
                location = None
                extracted_links: List[str] = []
                extracted_handles: List[str] = []

                if exists:
                    content_type = resp.headers.get("content-type", "")
                    parsed_meta = _extract_profile_metadata(site["name"], resp.text, content_type, target_user)
                    name = parsed_meta.get("display_name")
                    bio = parsed_meta.get("bio")
                    avatar_url = parsed_meta.get("avatar_url")
                    location = parsed_meta.get("location")
                    extracted_links = parsed_meta.get("extracted_links", [])
                    extracted_handles = parsed_meta.get("extracted_handles", [])

                return IdentityFinding(
                    platform=site["name"],
                    url=public_url,
                    exists=exists,
                    status_code=resp.status_code,
                    response_time_ms=duration,
                    category=site.get("category", "general"),
                    name=name,
                    bio=bio,
                    avatar_url=avatar_url,
                    location=location,
                    extracted_links=extracted_links,
                    extracted_handles=extracted_handles,
                    metadata=parsed_meta,
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

        # Sort: found profiles first, then alphabetically
        results.sort(key=lambda x: (not x.exists, x.platform))
        return results
