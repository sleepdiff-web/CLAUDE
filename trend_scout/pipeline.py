"""End-to-end weekly run: discover -> score -> rank -> output."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from .config import Config
from .discovery import discover_from_reddit, discover_from_trends
from .history import load_history, update_history
from .ingredients import Candidate
from .output import (
    google_trends_url,
    kalodata_url,
    push_to_gsheet,
    send_slack,
    write_alerts,
    write_csv,
)
from .scoring import score_series
from .trends_client import TrendsClient

log = logging.getLogger("trend_scout.pipeline")


@dataclass
class RunResult:
    rows: list[dict[str, Any]]
    breakouts: list[dict[str, Any]]
    csv_path: str
    alerts_md: str


def _gather_candidates(cfg: Config, client: TrendsClient) -> dict[str, Candidate]:
    """Run both discovery sources and merge into a unique term -> Candidate map."""
    merged: dict[str, Candidate] = {}

    trends_cands = discover_from_trends(client, cfg.trends_seeds)
    reddit_cands = discover_from_reddit(
        cfg.reddit_subreddits,
        listing=cfg.discovery.get("reddit_listing", "top"),
        time_filter=cfg.discovery.get("reddit_time", "week"),
        limit=cfg.discovery.get("reddit_limit", 75),
    )

    # Trends candidates take priority for the 'source' label; if a term shows
    # up in both, mark it as discovered by both (stronger signal).
    for cand in reddit_cands:
        merged[cand.term] = cand
    for cand in trends_cands:
        if cand.term in merged:
            existing = merged[cand.term]
            merged[cand.term] = Candidate(
                term=cand.term, source="trends+reddit",
                known=existing.known or cand.known, context=cand.context,
            )
        else:
            merged[cand.term] = cand

    cap = cfg.discovery.get("max_candidates", 120)
    if len(merged) > cap:
        # Keep known ingredients + the first `cap` to bound rate-limited calls.
        items = sorted(merged.values(), key=lambda c: (not c.known))
        merged = {c.term: c for c in items[:cap]}
    log.info("merged candidate pool: %d (capped at %d)", len(merged), cap)
    return merged


def run(cfg: Config, *, dry_run: bool = False) -> RunResult:
    sc = cfg.scoring
    client = TrendsClient(geo=cfg.geo, timeframe=cfg.timeframe, proxies=cfg.proxies)

    candidates = _gather_candidates(cfg, client)
    terms = list(candidates.keys())

    # Score momentum from Trends interest-over-time (batched, backed off).
    series = {} if dry_run else client.interest_over_time(terms)

    history = load_history(cfg.history_path)
    scored: list[dict[str, Any]] = []
    for term, cand in candidates.items():
        values = series.get(term, [])
        result = score_series(
            values,
            recent_weeks=sc["recent_weeks"],
            prior_weeks=sc["prior_weeks"],
            min_interest=sc["min_interest"],
            breakout_growth_pct=sc["breakout_growth_pct"],
            min_sustained_weeks=sc["min_sustained_weeks"],
            max_recent_volatility=sc["max_recent_volatility"],
            weights=sc["weights"],
        )
        row = result.to_row()
        row.update(
            ingredient=term,
            is_new=term not in history,
            source=cand.source,
            discovered_context=cand.context,
            kalodata_url=kalodata_url(term, cfg.kalodata_template()),
            google_trends_url=google_trends_url(term, cfg.geo),
        )
        scored.append(row)

    scored.sort(key=lambda r: r["score"], reverse=True)
    for i, row in enumerate(scored, start=1):
        row["rank"] = i

    top_n = cfg.output.get("top_n", 60)
    top_rows = scored[:top_n]
    breakouts = [r for r in scored if r["is_breakout"]]

    # Outputs
    out_dir = cfg.output_dir
    csv_path = out_dir / cfg.output["csv_name"]
    alerts_base = out_dir / cfg.output["alerts_name"]

    write_csv(top_rows, csv_path)
    _, alerts_md = write_alerts(breakouts, alerts_base)
    push_to_gsheet(top_rows)
    send_slack(breakouts)

    # Persist history (only terms that actually scored above the noise floor,
    # so a one-off junk candidate doesn't suppress a future genuine NEW flag).
    update_history(cfg.history_path, [r["ingredient"] for r in scored if r["mean_recent"] >= sc["min_interest"]])

    log.info("run complete: %d scored, %d breakouts", len(scored), len(breakouts))
    return RunResult(
        rows=top_rows,
        breakouts=breakouts,
        csv_path=str(csv_path),
        alerts_md=str(alerts_md),
    )
