"""Write the ranked ingredient sheet to CSV (always) and, optionally, Google Sheets."""
from __future__ import annotations

import csv
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("trend_scout.output.sheet")

COLUMNS = [
    "rank", "ingredient", "score", "is_breakout", "is_new", "growth_pct",
    "mean_recent", "acceleration", "sustained", "source", "discovered_context",
    "kalodata_url", "google_trends_url",
]


def write_csv(rows: list[dict[str, Any]], path: str | os.PathLike) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    log.info("wrote %d rows -> %s", len(rows), path)
    return path


def push_to_gsheet(rows: list[dict[str, Any]], worksheet_title: str = "TrendScout") -> bool:
    """Push rows to a Google Sheet if credentials are configured.

    Requires env vars:
      GOOGLE_SERVICE_ACCOUNT_JSON  – path to a service-account key file
      GSHEET_ID                    – the target spreadsheet id (shared with the
                                     service account's email)
    Returns True if it pushed, False if skipped (no creds) — never raises.
    """
    sa_path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.environ.get("GSHEET_ID")
    if not sa_path or not sheet_id:
        log.info("Google Sheets not configured (set GOOGLE_SERVICE_ACCOUNT_JSON + GSHEET_ID) — skipping")
        return False
    try:
        import gspread  # type: ignore
        from google.oauth2.service_account import Credentials  # type: ignore

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(sa_path, scopes=scopes)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(sheet_id)
        try:
            ws = sh.worksheet(worksheet_title)
            ws.clear()
        except Exception:
            ws = sh.add_worksheet(title=worksheet_title, rows=len(rows) + 10, cols=len(COLUMNS))
        ws.update([COLUMNS] + [[r.get(c, "") for c in COLUMNS] for r in rows])
        log.info("pushed %d rows to Google Sheet %s", len(rows), sheet_id)
        return True
    except Exception as exc:  # never let an optional integration break the run
        log.error("Google Sheets push failed: %s", exc)
        return False
