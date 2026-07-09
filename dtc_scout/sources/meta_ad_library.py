"""Meta Ad Library client (Graph API `ads_archive` endpoint).

Since the EU Digital Services Act, ads delivered to any EU country are fully
queryable — not just political ads — including `eu_total_reach`, which we use
as the impressions/spend proxy. A free Meta developer access token is required
(META_ACCESS_TOKEN); see DTC_SCOUT.md for how to create one.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Iterator
from urllib.parse import urlparse

import requests

from ..models import Ad

log = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/{version}/ads_archive"

FIELDS = ",".join(
    [
        "id",
        "page_id",
        "page_name",
        "ad_creative_bodies",
        "ad_creative_link_titles",
        "ad_creative_link_captions",
        "ad_delivery_start_time",
        "ad_delivery_stop_time",
        "eu_total_reach",
        "ad_snapshot_url",
        "publisher_platforms",
    ]
)

# Link captions that are ad-network noise, not the brand's storefront.
_NON_STORE_HOSTS = {
    "fb.me", "facebook.com", "instagram.com", "linktr.ee", "bit.ly",
    "apps.apple.com", "play.google.com", "youtube.com", "amazon.com",
}


def extract_domain(caption_or_url: str) -> str:
    """Reduce an ad's link caption/URL to a bare storefront domain.

    Captions come in many shapes: "EXAMPLE.COM", "https://example.com/pages/x",
    "www.example.com | Free shipping". Returns "" when no plausible store
    domain is present.
    """
    if not caption_or_url:
        return ""
    text = caption_or_url.strip().lower()
    # Take the first token that looks like a domain or URL.
    match = re.search(r"(?:https?://)?(?:www\.)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})", text)
    if not match:
        return ""
    host = match.group(1)
    # If a full URL was given, urlparse is more reliable for the host part.
    if "://" in text:
        parsed_host = urlparse(text.split()[0]).netloc.lower()
        if parsed_host:
            host = parsed_host.removeprefix("www.")
    host = host.strip(".").split("/")[0]
    if host in _NON_STORE_HOSTS or host.endswith(".facebook.com"):
        return ""
    return host


def parse_ad(raw: dict, niche: str = "") -> Ad:
    """Normalise one raw ads_archive record into an Ad."""
    bodies = raw.get("ad_creative_bodies") or []
    titles = raw.get("ad_creative_link_titles") or []
    captions = raw.get("ad_creative_link_captions") or []
    return Ad(
        archive_id=str(raw.get("id", "")),
        page_id=str(raw.get("page_id", "")),
        page_name=raw.get("page_name", "") or "",
        body=(bodies[0] if bodies else "")[:2000],
        link_title=titles[0] if titles else "",
        link_caption=captions[0] if captions else "",
        start_date=(raw.get("ad_delivery_start_time") or "")[:10],
        stop_date=(raw.get("ad_delivery_stop_time") or "")[:10],
        eu_reach=int(raw.get("eu_total_reach") or 0),
        snapshot_url=raw.get("ad_snapshot_url", "") or "",
        platforms=",".join(raw.get("publisher_platforms") or []),
        niche=niche,
    )


class MetaAdLibraryClient:
    """Thin paginated wrapper over the ads_archive endpoint."""

    def __init__(
        self,
        access_token: str | None = None,
        api_version: str = "v21.0",
        countries: list[str] | None = None,
        session: requests.Session | None = None,
        timeout: int = 30,
    ) -> None:
        self.token = access_token or os.environ.get("META_ACCESS_TOKEN", "")
        if not self.token:
            raise RuntimeError(
                "META_ACCESS_TOKEN is not set. Create a (free) Meta developer "
                "app token — see DTC_SCOUT.md 'Getting a Meta token'."
            )
        self.url = GRAPH_URL.format(version=api_version)
        self.countries = countries or ["NL"]
        self.session = session or requests.Session()
        self.timeout = timeout

    def _paginate(self, params: dict, limit: int) -> Iterator[dict]:
        params = {
            **params,
            "access_token": self.token,
            "ad_reached_countries": str(self.countries).replace("'", '"'),
            "ad_type": "ALL",
            "ad_active_status": "ALL",
            "fields": FIELDS,
            "limit": min(limit, 100),
        }
        url, fetched = self.url, 0
        while url and fetched < limit:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                log.warning("ads_archive HTTP %s: %s", resp.status_code, resp.text[:300])
                return
            data = resp.json()
            for item in data.get("data", []):
                yield item
                fetched += 1
                if fetched >= limit:
                    return
            url = data.get("paging", {}).get("next")
            params = {}  # `next` URL already carries all params

    def search_ads(self, term: str, limit: int, niche: str = "") -> list[Ad]:
        """Keyword search across the library — the discovery entry point."""
        raws = self._paginate({"search_terms": term}, limit)
        return [parse_ad(r, niche) for r in raws]

    def page_ads(self, page_id: str, limit: int, niche: str = "") -> list[Ad]:
        """All ads for one advertiser page — the enrichment pull per brand."""
        raws = self._paginate({"search_page_ids": f'["{page_id}"]'}, limit)
        return [parse_ad(r, niche) for r in raws]
