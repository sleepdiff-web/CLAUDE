"""Breakout alerts: write a markdown + JSON digest and optionally ping Slack."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

log = logging.getLogger("trend_scout.output.alerts")


def write_alerts(breakouts: list[dict[str, Any]], base_path: str | os.PathLike) -> tuple[Path, Path]:
    """Write breakouts to <base>.json and <base>.md. Returns both paths."""
    base = Path(base_path)
    base.parent.mkdir(parents=True, exist_ok=True)
    json_path = base.with_suffix(".json")
    md_path = base.with_suffix(".md")

    json_path.write_text(json.dumps(breakouts, indent=2), encoding="utf-8")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# Breakout ingredients — {stamp}", ""]
    if not breakouts:
        lines.append("_No breakouts this week._")
    for b in breakouts:
        new_tag = " 🆕" if b.get("is_new") else ""
        lines.append(
            f"- **{b['ingredient']}**{new_tag} — score {b['score']}, "
            f"+{b['growth_pct']}% growth · [Kalodata]({b['kalodata_url']}) · "
            f"[Trends]({b['google_trends_url']})"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("wrote %d breakout alerts -> %s", len(breakouts), md_path)
    return json_path, md_path


def send_slack(breakouts: list[dict[str, Any]], top_n: int = 10) -> bool:
    """Post a breakout summary to Slack if SLACK_WEBHOOK_URL is set.

    Returns True if a message was sent, False if skipped — never raises.
    """
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        log.info("SLACK_WEBHOOK_URL not set — skipping Slack alert")
        return False
    if not breakouts:
        log.info("no breakouts — skipping Slack alert")
        return False

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f":mag: *TrendScout breakouts — {stamp}*"]
    for b in breakouts[:top_n]:
        new_tag = " :new:" if b.get("is_new") else ""
        lines.append(
            f"• *{b['ingredient']}*{new_tag} — score {b['score']}, "
            f"+{b['growth_pct']}% · <{b['kalodata_url']}|Kalodata>"
        )
    try:
        resp = requests.post(webhook, json={"text": "\n".join(lines)}, timeout=15)
        ok = resp.status_code // 100 == 2
        if not ok:
            log.error("Slack webhook returned HTTP %d", resp.status_code)
        return ok
    except requests.RequestException as exc:
        log.error("Slack webhook failed: %s", exc)
        return False
