"""Track ingredients seen in previous runs so we can flag NEW entrants."""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path

log = logging.getLogger("trend_scout.history")


def load_history(path: str | Path) -> dict[str, str]:
    """Return {ingredient: first_seen_iso_date}."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        log.warning("could not read history %s: %s", p, exc)
        return {}


def update_history(path: str | Path, terms: list[str]) -> dict[str, str]:
    """Record any unseen terms with today's date; persist and return history."""
    p = Path(path)
    history = load_history(p)
    today = date.today().isoformat()
    for term in terms:
        history.setdefault(term, today)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(history, indent=2, sort_keys=True), encoding="utf-8")
    return history
