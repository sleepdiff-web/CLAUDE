"""The vetting criteria engine — the "pre-vetted" in pre-vetted database.

Pure functions over BrandMetrics so every rule is unit-testable without any
network. The same criteria run on every pipeline execution: brands that stop
meeting them are automatically flagged "removed" (mirroring the spec's
"if they start falling off, they get removed off the software").
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .models import BrandMetrics, VetResult


@dataclass
class Criteria:
    min_active_ads: int = 12
    min_new_ads_30d: int = 4
    max_brand_age_months: int = 12
    require_shopify: bool = True
    big_brand_rank_cutoff: int = 5000
    exclude_domains: tuple[str, ...] = ()

    @classmethod
    def from_config(cls, vetting_cfg: dict) -> "Criteria":
        return cls(
            min_active_ads=int(vetting_cfg.get("min_active_ads", 12)),
            min_new_ads_30d=int(vetting_cfg.get("min_new_ads_30d", 4)),
            max_brand_age_months=int(vetting_cfg.get("max_brand_age_months", 12)),
            require_shopify=bool(vetting_cfg.get("require_shopify", True)),
            big_brand_rank_cutoff=int(vetting_cfg.get("big_brand_rank_cutoff", 5000)),
            exclude_domains=tuple(d.lower() for d in vetting_cfg.get("exclude_domains", [])),
        )


def brand_age_ok(first_ad_date: str, today: date, max_months: int) -> bool:
    """Launch-recency proxy: earliest ad in the library within N months.

    An empty/unparseable date passes (we can't prove the brand is old).
    """
    if not first_ad_date:
        return True
    try:
        first = date.fromisoformat(first_ad_date[:10])
    except ValueError:
        return True
    return first >= today - timedelta(days=max_months * 30)


def evaluate(m: BrandMetrics, criteria: Criteria, today: date) -> VetResult:
    """Apply every rule; collect all failures so the DB explains itself."""
    reasons: list[str] = []

    if m.domain and m.domain.lower() in criteria.exclude_domains:
        reasons.append(f"domain '{m.domain}' is on the exclude list")
    if not m.domain:
        reasons.append("no storefront domain found in ad links")
    if m.active_ads < criteria.min_active_ads:
        reasons.append(f"active ads {m.active_ads} < {criteria.min_active_ads}")
    if m.new_ads_30d < criteria.min_new_ads_30d:
        reasons.append(f"new ads (30d) {m.new_ads_30d} < {criteria.min_new_ads_30d}")
    if not brand_age_ok(m.first_ad_date, today, criteria.max_brand_age_months):
        reasons.append(
            f"first ad {m.first_ad_date} older than {criteria.max_brand_age_months} months"
        )
    if criteria.require_shopify and m.is_shopify is False:
        reasons.append("store is not on Shopify")
    if m.traffic_rank is not None and m.traffic_rank <= criteria.big_brand_rank_cutoff:
        reasons.append(
            f"traffic rank {m.traffic_rank} <= {criteria.big_brand_rank_cutoff}: "
            "household-name brand, not a fast-scaling DTC store"
        )

    return VetResult(passed=not reasons, reasons=reasons)
