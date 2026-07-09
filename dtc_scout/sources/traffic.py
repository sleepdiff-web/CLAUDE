"""Free traffic estimation via the Tranco domain-rank API.

Tranco (https://tranco-list.eu) is a research-grade popularity ranking. It's a
*rank*, not absolute visitors, so we bucket it into tiers that stand in for
the "monthly traffic" filter: a rank inside `high_cutoff` roughly corresponds
to the 100K+ uniques/month stores the spec cares about. Swappable for a
SimilarWeb-class API later without touching the rest of the pipeline.
"""
from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)

TRANCO_API = "https://tranco-list.eu/api/ranks/domain/{domain}"


def rank_to_tier(rank: int | None, high_cutoff: int, medium_cutoff: int) -> str:
    if rank is None:
        return "unknown"
    if rank <= high_cutoff:
        return "high"
    if rank <= medium_cutoff:
        return "medium"
    return "low"


class TrafficClient:
    def __init__(
        self,
        high_cutoff: int = 60000,
        medium_cutoff: int = 250000,
        session: requests.Session | None = None,
        timeout: int = 15,
    ) -> None:
        self.high_cutoff = high_cutoff
        self.medium_cutoff = medium_cutoff
        self.session = session or requests.Session()
        self.timeout = timeout

    def lookup(self, domain: str) -> tuple[int | None, str]:
        """Returns (latest_rank_or_None, tier)."""
        rank: int | None = None
        try:
            resp = self.session.get(TRANCO_API.format(domain=domain), timeout=self.timeout)
            if resp.ok:
                ranks = resp.json().get("ranks") or []
                if ranks:
                    rank = int(ranks[-1]["rank"])
        except (requests.RequestException, ValueError, KeyError) as exc:
            log.debug("tranco lookup failed for %s: %s", domain, exc)
        return rank, rank_to_tier(rank, self.high_cutoff, self.medium_cutoff)
