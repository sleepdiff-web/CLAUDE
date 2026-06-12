"""Momentum scoring for a Google Trends interest series.

Pure Python (no numpy/pandas) so it is trivially unit-testable. Input is the
list of interest values (0-100 index) over the configured window, oldest
first. We score for the two things you asked for:

  * fast growth / breakout  -> recent window mean vs prior window mean
  * sustained + accelerating -> not a one-week spike, and the recent trend
    line is sloping up faster than the prior trend line.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class MomentumResult:
    score: float            # 0-100 composite momentum score
    growth_pct: float       # % change, recent mean vs prior mean
    mean_recent: float
    mean_prior: float
    slope_recent: float     # linear slope over recent window
    acceleration: float     # slope_recent - slope_prior
    volatility: float       # coeff. of variation of recent window
    sustained: bool         # recent demand is real, not a single spike
    is_breakout: bool       # growth + sustained + above floor
    n_points: int

    def to_row(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("score", "growth_pct", "mean_recent", "mean_prior",
                  "slope_recent", "acceleration", "volatility"):
            d[k] = round(d[k], 2)
        return d


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _slope(xs: list[float]) -> float:
    """Least-squares slope of xs against index 0..n-1."""
    n = len(xs)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2.0
    mean_y = _mean(xs)
    num = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(xs))
    den = sum((i - mean_x) ** 2 for i in range(n))
    return num / den if den else 0.0


def _cv(xs: list[float]) -> float:
    """Coefficient of variation (std / mean); high => spiky."""
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    if m <= 0:
        return float("inf")
    var = sum((x - m) ** 2 for x in xs) / len(xs)
    return math.sqrt(var) / m


def score_series(
    values: list[float],
    *,
    recent_weeks: int = 4,
    prior_weeks: int = 8,
    min_interest: float = 8.0,
    breakout_growth_pct: float = 80.0,
    min_sustained_weeks: int = 2,
    max_recent_volatility: float = 1.1,
    weights: dict[str, float] | None = None,
) -> MomentumResult:
    """Compute a MomentumResult from an oldest-first interest series."""
    weights = weights or {"growth": 0.5, "level": 0.25, "acceleration": 0.25}
    values = [float(v) for v in values if v is not None]
    n = len(values)

    if n == 0:
        return MomentumResult(0, 0, 0, 0, 0, 0, 0, False, False, 0)

    # Carve windows from the tail. If the series is short, scale down windows.
    rw = min(recent_weeks, max(1, n // 2))
    pw = min(prior_weeks, n - rw)
    recent = values[-rw:]
    prior = values[-(rw + pw):-rw] if pw > 0 else values[:-rw] or recent

    mean_recent = _mean(recent)
    mean_prior = _mean(prior)
    growth_pct = ((mean_recent - mean_prior) / mean_prior * 100.0) if mean_prior > 0 else (
        100.0 if mean_recent > 0 else 0.0
    )

    slope_recent = _slope(recent)
    slope_prior = _slope(prior)
    acceleration = slope_recent - slope_prior
    volatility = _cv(recent)

    weeks_above = sum(1 for v in recent if v >= min_interest)
    sustained = (
        mean_recent >= min_interest
        and weeks_above >= min_sustained_weeks
        and volatility <= max_recent_volatility
    )

    is_breakout = bool(sustained and growth_pct >= breakout_growth_pct)

    score = _composite_score(
        growth_pct=growth_pct,
        mean_recent=mean_recent,
        acceleration=acceleration,
        volatility=volatility,
        sustained=sustained,
        weights=weights,
    )

    return MomentumResult(
        score=score,
        growth_pct=growth_pct,
        mean_recent=mean_recent,
        mean_prior=mean_prior,
        slope_recent=slope_recent,
        acceleration=acceleration,
        volatility=volatility,
        sustained=sustained,
        is_breakout=is_breakout,
        n_points=n,
    )


def _composite_score(
    *,
    growth_pct: float,
    mean_recent: float,
    acceleration: float,
    volatility: float,
    sustained: bool,
    weights: dict[str, float],
) -> float:
    """Blend growth, current level, and acceleration into 0-100."""
    # Normalise each component to ~0-100.
    growth_norm = max(0.0, min(growth_pct, 300.0)) / 3.0          # 0-100 (cap at +300%)
    level_norm = max(0.0, min(mean_recent, 100.0))               # already 0-100
    accel_norm = max(0.0, min((acceleration + 5.0) * 10.0, 100.0))  # center ~0 -> 50

    raw = (
        weights.get("growth", 0.5) * growth_norm
        + weights.get("level", 0.25) * level_norm
        + weights.get("acceleration", 0.25) * accel_norm
    )

    # Penalise spiky series and reward genuinely sustained demand.
    if not sustained:
        raw *= 0.5
    if volatility > 1.0:
        raw *= max(0.4, 1.0 - (volatility - 1.0))

    return round(max(0.0, min(raw, 100.0)), 2)
