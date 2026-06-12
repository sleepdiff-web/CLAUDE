"""Discover candidate ingredients from Google Trends rising related queries.

For each broad seed (e.g. "supplement", "gut health") Trends returns the
queries rising in popularity alongside it. Those rising queries are where new
ingredient names surface before we'd otherwise know to look for them.
"""
from __future__ import annotations

import logging

from ..ingredients import Candidate, candidate_from_query
from ..trends_client import TrendsClient

log = logging.getLogger("trend_scout.discovery.trends")


def discover_from_trends(client: TrendsClient, seeds: list[str]) -> list[Candidate]:
    found: dict[str, Candidate] = {}
    for seed in seeds:
        queries = client.rising_related_queries(seed)
        log.info("seed %r -> %d rising/top queries", seed, len(queries))
        for q in queries:
            cand = candidate_from_query(q, source="trends")
            if cand and cand.term not in found:
                found[cand.term] = cand
    log.info("trends discovery -> %d unique candidates", len(found))
    return list(found.values())
