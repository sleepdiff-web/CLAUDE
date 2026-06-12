"""Tests for the momentum scoring core (no network)."""
from trend_scout.scoring.momentum import score_series

# 12 weekly points = ~3 months, matching "today 3-m".
DEFAULTS = dict(recent_weeks=4, prior_weeks=8, min_interest=8,
                breakout_growth_pct=80, min_sustained_weeks=2,
                max_recent_volatility=1.1)


def test_clear_breakout_is_flagged():
    # Flat-ish low baseline, then a sustained climb in the recent window.
    values = [10, 12, 11, 13, 12, 14, 13, 15, 40, 55, 70, 80]
    r = score_series(values, **DEFAULTS)
    assert r.is_breakout is True
    assert r.growth_pct > 80
    assert r.sustained is True
    assert r.score > 50


def test_single_spike_is_not_sustained():
    # One isolated spike at the very end -> high volatility, not a breakout.
    values = [10, 11, 10, 12, 11, 10, 11, 12, 0, 0, 0, 95]
    r = score_series(values, **DEFAULTS)
    assert r.sustained is False
    assert r.is_breakout is False


def test_flat_series_low_score():
    values = [50] * 12
    r = score_series(values, **DEFAULTS)
    assert r.growth_pct == 0
    assert r.is_breakout is False


def test_declining_series_no_breakout():
    values = [80, 75, 70, 65, 60, 55, 50, 45, 30, 25, 20, 15]
    r = score_series(values, **DEFAULTS)
    assert r.growth_pct < 0
    assert r.is_breakout is False


def test_below_noise_floor_not_breakout():
    # Big % growth but tiny absolute interest -> rejected by min_interest.
    values = [0, 0, 1, 0, 1, 0, 1, 0, 2, 3, 4, 5]
    r = score_series(values, **DEFAULTS)
    assert r.is_breakout is False


def test_empty_series_is_safe():
    r = score_series([], **DEFAULTS)
    assert r.score == 0
    assert r.is_breakout is False
    assert r.n_points == 0


def test_short_series_scales_windows():
    # Fewer points than recent+prior should not crash.
    r = score_series([10, 20, 30, 40], **DEFAULTS)
    assert r.n_points == 4
    assert r.growth_pct > 0
