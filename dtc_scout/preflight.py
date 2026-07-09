"""Preflight: confirm the network can reach every data source.

Managed sandboxes (Claude Code on the web, CI) often run behind an egress
allowlist — same gotcha as TrendScout. This prints exactly which hosts to
allow instead of failing mysteriously mid-run.
"""
from __future__ import annotations

import os

import requests

CHECKS = [
    ("Meta Ad Library API", "https://graph.facebook.com/v21.0/ads_archive", "graph.facebook.com"),
    ("Tranco rank API", "https://tranco-list.eu/api/ranks/domain/example.com", "tranco-list.eu"),
    ("Claude API (optional)", "https://api.anthropic.com/v1/messages", "api.anthropic.com"),
]


def run_preflight() -> bool:
    ok = True
    print("DTCScout preflight\n" + "=" * 40)
    for name, url, host in CHECKS:
        try:
            resp = requests.get(url, timeout=15)
            blocked = resp.status_code == 403 and "host_not_allowed" in resp.headers.get(
                "x-deny-reason", ""
            )
            if blocked:
                print(f"✗ {name}: blocked by egress allowlist — allow '{host}'")
                ok = False
            else:
                # Any HTTP response (even 400: missing token) means reachable.
                print(f"✓ {name}: reachable (HTTP {resp.status_code})")
        except requests.RequestException as exc:
            print(f"✗ {name}: {type(exc).__name__} — allow '{host}' or check connectivity")
            ok = False

    print("-" * 40)
    print(f"{'✓' if os.environ.get('META_ACCESS_TOKEN') else '✗'} META_ACCESS_TOKEN "
          f"{'set' if os.environ.get('META_ACCESS_TOKEN') else 'NOT set (required)'}")
    print(f"{'✓' if os.environ.get('ANTHROPIC_API_KEY') else '·'} ANTHROPIC_API_KEY "
          f"{'set' if os.environ.get('ANTHROPIC_API_KEY') else 'not set (optional: keyword fallback used)'}")
    if not ok:
        print("\nFix: environment settings -> Network access -> Custom, add the hosts above.")
        print("Docs: https://code.claude.com/docs/en/claude-code-on-the-web#network-access")
    return ok
