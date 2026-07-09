"""Pure per-brand analytics: the numbers on the detail page and the ledger.

Everything here is derived from data already in the DB — no network, fully
unit-testable.
"""
from __future__ import annotations

import statistics
from datetime import date


def median_price(products: list[dict]) -> float | None:
    prices = [p["price"] for p in products if p.get("price") is not None]
    return round(statistics.median(prices), 2) if prices else None


def avg_ad_life_days(ads: list[dict], today: date) -> int | None:
    """Mean days an ad stays live. Stopped ads use their real lifespan;
    active ads count their age so far (a lower bound, same as spy tools)."""
    spans = []
    for a in ads:
        if not a.get("start_date"):
            continue
        try:
            start = date.fromisoformat(a["start_date"][:10])
            end = date.fromisoformat(a["stop_date"][:10]) if a.get("stop_date") else today
        except ValueError:
            continue
        if end >= start:
            spans.append((end - start).days)
    return round(statistics.mean(spans)) if spans else None


def catalog_freshness(products: list[dict]) -> dict:
    """Newest/oldest product publish dates + active span — 'is this store
    still shipping new SKUs?'"""
    dates = sorted(p["created_at"] for p in products if p.get("created_at"))
    if not dates:
        return {"newest": None, "oldest": None, "span_days": None}
    try:
        span = (date.fromisoformat(dates[-1]) - date.fromisoformat(dates[0])).days
    except ValueError:
        span = None
    return {"newest": dates[-1], "oldest": dates[0], "span_days": span}


def mix(ads: list[dict], field: str) -> list[dict]:
    """Distribution of a classification field over labeled ads, descending —
    the 'creative pattern mix' bars. Unlabeled ads are excluded from the base."""
    counts: dict[str, int] = {}
    for a in ads:
        value = a.get(field) or "unknown"
        if value in ("unknown", "none"):
            continue
        counts[value] = counts.get(value, 0) + 1
    total = sum(counts.values())
    return [
        {"label": k, "count": v, "pct": round(100 * v / total)}
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    ]
