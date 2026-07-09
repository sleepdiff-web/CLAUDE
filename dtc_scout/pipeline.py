"""End-to-end pipeline: discover -> enrich -> vet -> classify -> publish.

Stages
  1. DISCOVER  Ad Library keyword search per niche; group hits by advertiser
               page to surface candidate brands.
  2. ENRICH    Pull each candidate's full ad account; probe the storefront
               (Shopify? subscriptions?); look up the Tranco traffic tier.
  3. VET       Apply the criteria engine. Passing brands are "listed";
               previously listed brands that fail are flipped to "removed".
  4. CLASSIFY  Top ads (by EU reach) of listed brands get awareness level /
               visual treatment / authority figure / offer type.
  5. PUBLISH   SQLite is the source of truth; CSVs + self-contained HTML
               dashboard land in output/.
"""
from __future__ import annotations

import csv
import logging
from collections import defaultdict
from datetime import date, timedelta

from .classify.classifier import classify_ads
from .config import Config
from .dashboard import render_dashboard
from .db import Database
from .models import Ad, BrandMetrics
from .sources.meta_ad_library import MetaAdLibraryClient, extract_domain
from .sources.shopify import ShopifyProbe
from .sources.traffic import TrafficClient
from .vetting import Criteria, evaluate

log = logging.getLogger(__name__)


def build_metrics(page_id: str, page_name: str, ads: list[Ad], today: date, niche: str) -> BrandMetrics:
    """Pure aggregation of one brand's ads into vetting signals."""
    cutoff_30d = (today - timedelta(days=30)).isoformat()
    domains: dict[str, int] = defaultdict(int)
    for ad in ads:
        domain = extract_domain(ad.link_caption)
        if domain:
            domains[domain] += 1
    starts = sorted(a.start_date for a in ads if a.start_date)
    return BrandMetrics(
        page_id=page_id,
        page_name=page_name,
        domain=max(domains, key=domains.get) if domains else "",
        niche=niche,
        active_ads=sum(1 for a in ads if a.active),
        total_ads=len(ads),
        new_ads_30d=sum(1 for a in ads if a.start_date >= cutoff_30d),
        first_ad_date=starts[0] if starts else "",
        total_eu_reach=sum(a.eu_reach for a in ads),
    )


def run(cfg: Config, today: date, dry_run: bool = False) -> dict:
    run_date = today.isoformat()
    criteria = Criteria.from_config(cfg.vetting)
    db = Database(cfg.db_path)
    meta = MetaAdLibraryClient(api_version=cfg.api_version, countries=cfg.countries)

    # 1. DISCOVER ------------------------------------------------------------
    candidates: dict[str, tuple[str, str]] = {}  # page_id -> (page_name, niche)
    for niche, terms in cfg.niches.items():
        for term in terms:
            hits = meta.search_ads(term, limit=cfg.ads_per_term, niche=niche)
            for ad in hits:
                if ad.page_id and ad.page_id not in candidates:
                    candidates[ad.page_id] = (ad.page_name, niche)
            log.info("discover: %-12s %-28r -> %d ads", niche, term, len(hits))
    # Re-check everything already listed so falling brands get removed.
    for page_id in db.listed_page_ids():
        candidates.setdefault(page_id, ("", ""))
    log.info("discover: %d candidate brands", len(candidates))

    if dry_run:
        db.close()
        return {"candidates": len(candidates), "dry_run": True}

    # 2-3. ENRICH + VET --------------------------------------------------------
    shopify = ShopifyProbe()
    traffic = TrafficClient(
        high_cutoff=int(cfg.traffic.get("high_cutoff", 60000)),
        medium_cutoff=int(cfg.traffic.get("medium_cutoff", 250000)),
    )
    listed, removed, rejected = 0, 0, 0
    for page_id, (page_name, niche) in candidates.items():
        ads = meta.page_ads(page_id, limit=cfg.max_ads_per_brand, niche=niche)
        if not ads:
            continue
        m = build_metrics(page_id, page_name or ads[0].page_name, ads, today, niche or ads[0].niche)
        products: list[dict] = []
        if m.domain:
            probe = shopify.probe(m.domain)
            m.is_shopify = probe["is_shopify"]
            m.is_subscription = probe["is_subscription"]
            products = probe["products"]
            m.traffic_rank, m.traffic_tier = traffic.lookup(m.domain)

        verdict = evaluate(m, criteria, today)
        was_listed = page_id in db.listed_page_ids()
        if verdict.passed:
            status, listed = "listed", listed + 1
        elif was_listed:
            status, removed = "removed", removed + 1  # fell off the criteria
        else:
            status, rejected = "rejected", rejected + 1
        db.upsert_brand(m, status, verdict.reasons, run_date)
        if verdict.passed:
            for ad in ads:
                db.upsert_ad(ad)
            if products:
                db.replace_products(page_id, products[:40])
        log.info("vet: %-30s %s %s", m.page_name[:30], status, "; ".join(verdict.reasons))

    # 4. CLASSIFY ----------------------------------------------------------------
    model = cfg.classify.get("model", "claude-haiku-4-5-20251001")
    per_brand = int(cfg.classify.get("max_ads_per_brand", 8))
    batch = int(cfg.classify.get("batch_size", 8))
    for brand in db.brands(status="listed"):
        top_ads = [
            a for a in db.ads_for_brand(brand["page_id"], top_n=per_brand)
            if a["awareness_level"] == "unknown"
        ]
        for archive_id, result in classify_ads(top_ads, model, batch).items():
            row = next(a for a in top_ads if a["archive_id"] == archive_id)
            db.upsert_ad(Ad(**{
                k: row[k] for k in (
                    "archive_id", "page_id", "body", "link_title", "link_caption",
                    "start_date", "stop_date", "eu_reach", "snapshot_url",
                    "platforms", "niche",
                )
            } | {k: result[k] for k in (
                "awareness_level", "visual_treatment", "authority_figure", "offer_type",
            )}, page_name=brand["page_name"]))

    # 5. PUBLISH -----------------------------------------------------------------
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    _write_csvs(cfg, db)
    dashboard_path = cfg.output_dir / cfg.output["dashboard_name"]
    dashboard_path.write_text(render_dashboard(db, run_date), encoding="utf-8")
    summary = {"listed": listed, "removed": removed, "rejected": rejected,
               "dashboard": str(dashboard_path)}
    db.close()
    return summary


def _write_csvs(cfg: Config, db: Database) -> None:
    brands = db.brands()
    with (cfg.output_dir / cfg.output["brands_csv"]).open("w", newline="", encoding="utf-8") as fh:
        if brands:
            writer = csv.DictWriter(fh, fieldnames=brands[0].keys())
            writer.writeheader()
            writer.writerows(brands)
    with (cfg.output_dir / cfg.output["ads_csv"]).open("w", newline="", encoding="utf-8") as fh:
        writer = None
        for brand in db.brands(status="listed"):
            for ad in db.ads_for_brand(brand["page_id"]):
                if writer is None:
                    writer = csv.DictWriter(fh, fieldnames=ad.keys())
                    writer.writeheader()
                writer.writerow(ad)
