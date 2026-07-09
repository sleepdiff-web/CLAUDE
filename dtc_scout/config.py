"""Configuration loading and typed access for DTCScout."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "dtc_config.yaml"


@dataclass
class Config:
    """Parsed dtc_config.yaml plus a few resolved helpers."""

    raw: dict[str, Any]
    path: Path

    # --- meta ad library ---------------------------------------------------
    @property
    def api_version(self) -> str:
        return self.raw["meta"].get("api_version", "v21.0")

    @property
    def countries(self) -> list[str]:
        return list(self.raw["meta"]["countries"])

    @property
    def niches(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in self.raw["meta"]["niches"].items()}

    @property
    def ads_per_term(self) -> int:
        return int(self.raw["meta"].get("ads_per_term", 200))

    @property
    def max_ads_per_brand(self) -> int:
        return int(self.raw["meta"].get("max_ads_per_brand", 400))

    # --- vetting -------------------------------------------------------------
    @property
    def vetting(self) -> dict[str, Any]:
        return self.raw["vetting"]

    # --- classification ------------------------------------------------------
    @property
    def classify(self) -> dict[str, Any]:
        return self.raw.get("classify", {})

    # --- media -----------------------------------------------------------------
    @property
    def media(self) -> dict[str, Any]:
        return self.raw.get("media", {})

    # --- traffic ---------------------------------------------------------------
    @property
    def traffic(self) -> dict[str, Any]:
        return self.raw.get("traffic", {})

    # --- output ----------------------------------------------------------------
    @property
    def output(self) -> dict[str, Any]:
        return self.raw["output"]

    @property
    def output_dir(self) -> Path:
        return (PROJECT_ROOT / self.raw["output"]["dir"]).resolve()

    @property
    def db_path(self) -> Path:
        return (PROJECT_ROOT / self.raw["output"]["db_path"]).resolve()


def load_config(path: str | os.PathLike | None = None) -> Config:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config not found: {cfg_path}")
    with cfg_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    return Config(raw=raw, path=cfg_path)
