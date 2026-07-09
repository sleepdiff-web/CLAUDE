#!/usr/bin/env python3
"""Run the DTCScout pipeline.

  python scripts/run_dtc_scout.py --preflight   # check network + env vars
  python scripts/run_dtc_scout.py --dry-run     # discovery only, no writes
  python scripts/run_dtc_scout.py --verbose     # full run
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_dotenv(path: Path) -> None:
    """Minimal .env loader (no dependency): KEY=VALUE lines, # comments.

    Keeps secrets like META_ACCESS_TOKEN out of your shell history. Existing
    environment variables win, so an explicit `export` still overrides the file.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


load_dotenv(PROJECT_ROOT / ".env")

from dtc_scout.config import load_config  # noqa: E402
from dtc_scout.preflight import run_preflight  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="path to dtc_config.yaml")
    parser.add_argument("--preflight", action="store_true", help="check connectivity and exit")
    parser.add_argument("--dry-run", action="store_true", help="discovery only; no enrichment/writes")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.preflight:
        return 0 if run_preflight() else 1

    from dtc_scout.pipeline import run  # deferred: importing pulls in requests etc.

    cfg = load_config(args.config)
    summary = run(cfg, today=date.today(), dry_run=args.dry_run)
    print("DTCScout run complete:", summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
