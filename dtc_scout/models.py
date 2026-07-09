"""Core data shapes passed between pipeline stages."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class Ad:
    """One creative from the Meta Ad Library, normalised."""

    archive_id: str
    page_id: str
    page_name: str
    body: str = ""
    link_title: str = ""
    link_caption: str = ""          # usually the destination domain
    start_date: str = ""            # ISO date the ad started delivering
    stop_date: str = ""             # empty = still active
    eu_reach: int = 0               # eu_total_reach: our impressions proxy
    snapshot_url: str = ""
    platforms: str = ""             # "facebook,instagram"
    niche: str = ""
    # Classification (filled by classify stage; "unknown" until then)
    awareness_level: str = "unknown"
    visual_treatment: str = "unknown"
    authority_figure: str = "unknown"
    offer_type: str = "unknown"

    @property
    def active(self) -> bool:
        return not self.stop_date

    def to_dict(self) -> dict:
        d = asdict(self)
        d["active"] = self.active
        return d


@dataclass
class BrandMetrics:
    """Aggregated signals used by the vetting criteria."""

    page_id: str
    page_name: str
    domain: str = ""
    niche: str = ""
    active_ads: int = 0
    total_ads: int = 0
    new_ads_30d: int = 0
    first_ad_date: str = ""         # earliest delivery start = launch proxy
    total_eu_reach: int = 0
    is_shopify: bool | None = None  # None = not checked / unreachable
    is_subscription: bool | None = None
    traffic_rank: int | None = None
    traffic_tier: str = "unknown"


@dataclass
class VetResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)
