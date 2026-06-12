"""Tests for the egress preflight reporting (no network)."""
from trend_scout.preflight import HostStatus, report


def test_all_ok():
    statuses = [
        HostStatus("trends.google.com", True, "reachable (HTTP 200)"),
        HostStatus("www.reddit.com", True, "reachable (HTTP 200)"),
    ]
    ok, text = report(statuses)
    assert ok is True
    assert "BLOCKED" not in text


def test_allowlist_block_gives_actionable_guidance():
    statuses = [
        HostStatus("trends.google.com", False, "host_not_allowed (HTTP 403): ..."),
        HostStatus("www.reddit.com", True, "reachable (HTTP 200)"),
    ]
    ok, text = report(statuses)
    assert ok is False
    # Names the blocked host and the concrete fix.
    assert "trends.google.com" in text
    assert "Custom" in text
    assert "Network access" in text


def test_blocked_by_allowlist_flag():
    assert HostStatus("h", False, "host_not_allowed (HTTP 403)").blocked_by_allowlist
    assert not HostStatus("h", False, "network error: timeout").blocked_by_allowlist
