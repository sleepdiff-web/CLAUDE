#!/usr/bin/env python3
"""TrendScout CLI entry point — run the weekly discovery pipeline.

Examples:
    python scripts/run_weekly.py                 # full run with config.yaml
    python scripts/run_weekly.py --dry-run       # discover only, skip Trends scoring
    python scripts/run_weekly.py --config my.yaml --verbose
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make the package importable when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trend_scout.config import load_config  # noqa: E402
from trend_scout.pipeline import run  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TrendScout weekly ingredient discovery")
    parser.add_argument("--config", default=None, help="path to config.yaml")
    parser.add_argument("--dry-run", action="store_true",
                        help="discover candidates but skip Trends scoring / API calls")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config(args.config)
    result = run(cfg, dry_run=args.dry_run)

    print(f"\nScored ingredients written to: {result.csv_path}")
    print(f"Breakout alerts written to:    {result.alerts_md}")
    print(f"Breakouts this run: {len(result.breakouts)}")
    for r in result.rows[:15]:
        flag = "🔥" if r["is_breakout"] else ("🆕" if r["is_new"] else "  ")
        print(f"  {r['rank']:>2}. {flag} {r['ingredient']:<28} "
              f"score={r['score']:<6} growth={r['growth_pct']}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
