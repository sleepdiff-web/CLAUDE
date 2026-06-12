"""Configuration loading and typed access."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@dataclass
class Config:
    """Parsed config.yaml plus a few resolved helpers."""

    raw: dict[str, Any]
    path: Path

    # --- convenience accessors -------------------------------------------
    @property
    def geo(self) -> str:
        return self.raw["market"].get("geo", "") or ""

    @property
    def timeframe(self) -> str:
        return self.raw["market"].get("timeframe", "today 3-m")

    @property
    def proxies(self) -> list[str] | None:
        """Optional residential proxies for running Trends from a cloud IP.

        Prefer config 'market.proxies'; if absent, TrendsClient reads the
        TRENDS_PROXIES env var so you don't have to commit proxy URLs.
        """
        proxies = self.raw["market"].get("proxies") or []
        return list(proxies) or None

    @property
    def trends_seeds(self) -> list[str]:
        return list(self.raw["discovery"]["trends_seeds"])

    @property
    def reddit_subreddits(self) -> list[str]:
        return list(self.raw["discovery"]["reddit_subreddits"])

    @property
    def discovery(self) -> dict[str, Any]:
        return self.raw["discovery"]

    @property
    def scoring(self) -> dict[str, Any]:
        return self.raw["scoring"]

    @property
    def output(self) -> dict[str, Any]:
        return self.raw["output"]

    @property
    def output_dir(self) -> Path:
        return (PROJECT_ROOT / self.raw["output"]["dir"]).resolve()

    @property
    def history_path(self) -> Path:
        return (PROJECT_ROOT / self.raw["output"]["history_path"]).resolve()

    def kalodata_template(self) -> str:
        return self.raw["kalodata"]["search_url_template"]


def load_config(path: str | os.PathLike | None = None) -> Config:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return Config(raw=raw, path=cfg_path)
