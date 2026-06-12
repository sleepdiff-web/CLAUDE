"""Discover candidate ingredients from Reddit (free, no API key).

By default this reads each subreddit's public listing JSON endpoint
(https://www.reddit.com/r/<sub>/<listing>.json) — the unauthenticated read
path Reddit exposes for listings. Reddit increasingly blocks datacenter IPs /
generic user-agents with HTTP 403, so we send a browser-like User-Agent and
fall back across host variants (www / old / json.reddit) before giving up.

If the public endpoint is blocked in your environment, set Reddit API
credentials and the pipeline will use the official API via PRAW instead:
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
No credentials are required to start; discovery just falls back to Trends-only.
"""
from __future__ import annotations

import logging
import os
import time

import requests

from ..ingredients import Candidate, extract_candidates_from_text

log = logging.getLogger("trend_scout.discovery.reddit")

# A descriptive but browser-shaped UA. Reddit 403s terse/datacenter UAs.
_UA = (
    "Mozilla/5.0 (compatible; TrendScout/0.1; +https://github.com/sleepdiff-web/claude) "
    "AppleWebKit/537.36"
)
_HOSTS = ("https://www.reddit.com", "https://old.reddit.com")


def _fetch_listing(
    subreddit: str,
    listing: str,
    time_filter: str,
    limit: int,
    session: requests.Session,
    max_retries: int = 4,
) -> list[dict]:
    params = {"limit": limit, "raw_json": 1}
    if listing == "top":
        params["t"] = time_filter
    headers = {"User-Agent": _UA, "Accept": "application/json"}

    for host in _HOSTS:
        url = f"{host}/r/{subreddit}/{listing}.json"
        for attempt in range(max_retries):
            try:
                resp = session.get(url, params=params, headers=headers, timeout=20)
                if resp.status_code == 200:
                    children = resp.json().get("data", {}).get("children", [])
                    return [c.get("data", {}) for c in children]
                # Egress allowlist denial — not transient, don't retry/host-hop blindly.
                if resp.headers.get("x-deny-reason") == "host_not_allowed":
                    log.error(
                        "r/%s blocked by network egress allowlist (%s). Add '%s' to your "
                        "environment's Allowed domains (Network access -> Custom).",
                        subreddit, host, host.split("//")[-1],
                    )
                    break
                if resp.status_code in (429, 500, 502, 503):
                    wait = 2 * (2 ** attempt)
                    log.warning("r/%s HTTP %d via %s — backing off %ds",
                                subreddit, resp.status_code, host, wait)
                    time.sleep(wait)
                    continue
                # 403/404 etc: don't retry this host, try the next one.
                log.warning("r/%s HTTP %d via %s — trying next host",
                            subreddit, resp.status_code, host)
                break
            except requests.RequestException as exc:
                wait = 2 * (2 ** attempt)
                log.warning("r/%s request error via %s: %s — backing off %ds",
                            subreddit, host, exc, wait)
                time.sleep(wait)
    log.error("r/%s unreachable via public JSON — skipping (set REDDIT_CLIENT_ID to use the API)",
              subreddit)
    return []


def _fetch_listing_praw(
    subreddit: str, listing: str, time_filter: str, limit: int
) -> list[dict] | None:
    """Use the official Reddit API via PRAW if credentials are present.

    Returns a list of post dicts, or None if PRAW/credentials are unavailable
    (so the caller falls back to the public JSON path).
    """
    cid = os.environ.get("REDDIT_CLIENT_ID")
    secret = os.environ.get("REDDIT_CLIENT_SECRET")
    if not (cid and secret):
        return None
    try:
        import praw  # type: ignore

        reddit = praw.Reddit(
            client_id=cid,
            client_secret=secret,
            user_agent=os.environ.get("REDDIT_USER_AGENT", _UA),
        )
        sub = reddit.subreddit(subreddit)
        listing_fn = sub.top(time_filter=time_filter, limit=limit) if listing == "top" \
            else sub.hot(limit=limit)
        return [
            {"title": p.title, "selftext": p.selftext or "",
             "link_flair_text": p.link_flair_text or ""}
            for p in listing_fn
        ]
    except Exception as exc:  # praw missing or auth failed -> fall back
        log.warning("PRAW path unavailable (%s) — using public JSON", exc)
        return None


def discover_from_reddit(
    subreddits: list[str],
    *,
    listing: str = "top",
    time_filter: str = "week",
    limit: int = 75,
    request_pause: float = 1.5,
) -> list[Candidate]:
    """Return candidate ingredients mentioned in recent top/hot posts.

    Frequency matters: a term mentioned across many posts is a stronger
    signal, so we keep the highest-frequency context for each term.
    """
    session = requests.Session()
    counts: dict[str, int] = {}
    best: dict[str, Candidate] = {}

    for sub in subreddits:
        posts = _fetch_listing_praw(sub, listing, time_filter, limit)
        if posts is None:
            posts = _fetch_listing(sub, listing, time_filter, limit, session)
        log.info("r/%s -> %d posts", sub, len(posts))
        for post in posts:
            text = " ".join(
                str(post.get(k, "")) for k in ("title", "selftext", "link_flair_text")
            )
            for cand in extract_candidates_from_text(text, source="reddit"):
                counts[cand.term] = counts.get(cand.term, 0) + 1
                best.setdefault(cand.term, cand)
        time.sleep(request_pause)

    # Order by mention frequency (most-discussed first).
    ordered = sorted(best.values(), key=lambda c: counts[c.term], reverse=True)
    log.info("reddit discovery -> %d unique candidates", len(ordered))
    return ordered
