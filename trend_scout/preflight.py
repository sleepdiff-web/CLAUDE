"""Preflight: verify the network egress allowlist permits our data sources.

The biggest gotcha running TrendScout in a managed/cloud sandbox (Claude Code
on the web, CI, etc.) is the *network egress allowlist*. By default these
environments use a "Trusted" policy that only permits package registries and a
few cloud hosts — so Google Trends and Reddit are denied at the proxy with an
HTTP 403 carrying `x-deny-reason: host_not_allowed`. That looks identical to a
rate-limit unless you check the header, which previously sent us chasing the
wrong fix.

This module probes each required host and returns an actionable report so the
run fails loud with "add these domains to your allowlist" instead of silently
collecting no data.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import requests

log = logging.getLogger("trend_scout.preflight")

# Hosts each data source needs reachable.
TRENDS_HOSTS = ["trends.google.com", "www.google.com"]   # pytrends fetches a cookie from www.google.com
REDDIT_HOSTS = ["www.reddit.com", "old.reddit.com"]      # public JSON
REDDIT_OAUTH_HOSTS = ["oauth.reddit.com", "www.reddit.com"]  # PRAW


@dataclass
class HostStatus:
    host: str
    ok: bool
    detail: str

    @property
    def blocked_by_allowlist(self) -> bool:
        return "host_not_allowed" in self.detail


def check_host(host: str, *, timeout: float = 10.0) -> HostStatus:
    """Probe a host and classify the result.

    We only care whether the proxy lets us reach it, so any HTTP response that
    is NOT an egress denial counts as reachable (the data source's own
    auth/rate-limit handling is the client's job, not preflight's).
    """
    url = f"https://{host}/"
    try:
        resp = requests.get(url, headers={"User-Agent": "TrendScout-preflight/1.0"}, timeout=timeout)
        deny = resp.headers.get("x-deny-reason", "")
        if resp.status_code == 403 and "host_not_allowed" in (deny or resp.text[:200]):
            return HostStatus(host, False, f"host_not_allowed (HTTP 403): {resp.text[:120].strip()}")
        return HostStatus(host, True, f"reachable (HTTP {resp.status_code})")
    except requests.RequestException as exc:
        return HostStatus(host, False, f"network error: {exc}")


def check_egress(hosts: list[str]) -> list[HostStatus]:
    return [check_host(h) for h in dict.fromkeys(hosts)]  # de-dupe, keep order


def report(statuses: list[HostStatus]) -> tuple[bool, str]:
    """Return (all_ok, human_readable_report)."""
    blocked = [s for s in statuses if not s.ok]
    lines = []
    for s in statuses:
        mark = "OK " if s.ok else "BLOCKED"
        lines.append(f"  [{mark}] {s.host} — {s.detail}")

    allowlist_blocked = [s for s in blocked if s.blocked_by_allowlist]
    if allowlist_blocked:
        domains = "\n".join(f"    {s.host}" for s in allowlist_blocked)
        lines.append(
            "\nThese hosts are blocked by your environment's network egress allowlist.\n"
            "Fix: open the environment for editing, set Network access to \"Custom\",\n"
            "keep \"Also include default list of common package managers\" checked, and add:\n"
            f"{domains}\n"
            "(or set Network access to \"Full\"). Docs:\n"
            "  https://code.claude.com/docs/en/claude-code-on-the-web#network-access"
        )
    return (len(blocked) == 0, "\n".join(lines))
