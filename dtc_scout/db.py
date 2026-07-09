"""SQLite persistence: brands, ads, and per-run snapshots (growth over time)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Ad, BrandMetrics

SCHEMA = """
CREATE TABLE IF NOT EXISTS brands (
    page_id         TEXT PRIMARY KEY,
    page_name       TEXT,
    domain          TEXT,
    niche           TEXT,
    status          TEXT,            -- listed | removed | rejected
    vet_reasons     TEXT,
    active_ads      INTEGER,
    total_ads       INTEGER,
    new_ads_30d     INTEGER,
    first_ad_date   TEXT,
    total_eu_reach  INTEGER,
    is_shopify      INTEGER,
    is_subscription INTEGER,
    traffic_rank    INTEGER,
    traffic_tier    TEXT,
    first_seen      TEXT,
    last_seen       TEXT
);
CREATE TABLE IF NOT EXISTS ads (
    archive_id       TEXT PRIMARY KEY,
    page_id          TEXT,
    body             TEXT,
    link_title       TEXT,
    link_caption     TEXT,
    start_date       TEXT,
    stop_date        TEXT,
    eu_reach         INTEGER,
    snapshot_url     TEXT,
    platforms        TEXT,
    niche            TEXT,
    awareness_level  TEXT,
    visual_treatment TEXT,
    authority_figure TEXT,
    offer_type       TEXT
);
CREATE TABLE IF NOT EXISTS snapshots (
    page_id    TEXT,
    run_date   TEXT,
    active_ads INTEGER,
    eu_reach   INTEGER,
    PRIMARY KEY (page_id, run_date)
);
CREATE TABLE IF NOT EXISTS products (
    page_id    TEXT,
    handle     TEXT,
    title      TEXT,
    price      REAL,
    image      TEXT,
    created_at TEXT,
    position   INTEGER,
    PRIMARY KEY (page_id, handle)
);
"""


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # --- brands -------------------------------------------------------------
    def upsert_brand(self, m: BrandMetrics, status: str, vet_reasons: list[str], run_date: str) -> None:
        self.conn.execute(
            """
            INSERT INTO brands (page_id, page_name, domain, niche, status, vet_reasons,
                                active_ads, total_ads, new_ads_30d, first_ad_date,
                                total_eu_reach, is_shopify, is_subscription,
                                traffic_rank, traffic_tier, first_seen, last_seen)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(page_id) DO UPDATE SET
                page_name=excluded.page_name, domain=excluded.domain,
                niche=excluded.niche, status=excluded.status,
                vet_reasons=excluded.vet_reasons, active_ads=excluded.active_ads,
                total_ads=excluded.total_ads, new_ads_30d=excluded.new_ads_30d,
                first_ad_date=excluded.first_ad_date,
                total_eu_reach=excluded.total_eu_reach,
                is_shopify=excluded.is_shopify,
                is_subscription=excluded.is_subscription,
                traffic_rank=excluded.traffic_rank,
                traffic_tier=excluded.traffic_tier,
                last_seen=excluded.last_seen
            """,
            (
                m.page_id, m.page_name, m.domain, m.niche, status, "; ".join(vet_reasons),
                m.active_ads, m.total_ads, m.new_ads_30d, m.first_ad_date,
                m.total_eu_reach,
                None if m.is_shopify is None else int(m.is_shopify),
                None if m.is_subscription is None else int(m.is_subscription),
                m.traffic_rank, m.traffic_tier, run_date, run_date,
            ),
        )
        self.conn.execute(
            "INSERT OR REPLACE INTO snapshots (page_id, run_date, active_ads, eu_reach) VALUES (?,?,?,?)",
            (m.page_id, run_date, m.active_ads, m.total_eu_reach),
        )
        self.conn.commit()

    def listed_page_ids(self) -> list[str]:
        rows = self.conn.execute("SELECT page_id FROM brands WHERE status='listed'").fetchall()
        return [r["page_id"] for r in rows]

    def brands(self, status: str | None = None) -> list[dict]:
        q = "SELECT * FROM brands"
        args: tuple = ()
        if status:
            q += " WHERE status=?"
            args = (status,)
        return [dict(r) for r in self.conn.execute(q + " ORDER BY total_eu_reach DESC", args)]

    # --- ads ----------------------------------------------------------------
    def upsert_ad(self, ad: Ad) -> None:
        self.conn.execute(
            """
            INSERT INTO ads (archive_id, page_id, body, link_title, link_caption,
                             start_date, stop_date, eu_reach, snapshot_url, platforms,
                             niche, awareness_level, visual_treatment, authority_figure, offer_type)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(archive_id) DO UPDATE SET
                stop_date=excluded.stop_date, eu_reach=excluded.eu_reach,
                awareness_level=CASE WHEN excluded.awareness_level!='unknown'
                    THEN excluded.awareness_level ELSE ads.awareness_level END,
                visual_treatment=CASE WHEN excluded.visual_treatment!='unknown'
                    THEN excluded.visual_treatment ELSE ads.visual_treatment END,
                authority_figure=CASE WHEN excluded.authority_figure!='unknown'
                    THEN excluded.authority_figure ELSE ads.authority_figure END,
                offer_type=CASE WHEN excluded.offer_type!='unknown'
                    THEN excluded.offer_type ELSE ads.offer_type END
            """,
            (
                ad.archive_id, ad.page_id, ad.body, ad.link_title, ad.link_caption,
                ad.start_date, ad.stop_date, ad.eu_reach, ad.snapshot_url, ad.platforms,
                ad.niche, ad.awareness_level, ad.visual_treatment,
                ad.authority_figure, ad.offer_type,
            ),
        )
        self.conn.commit()

    def ads_for_brand(self, page_id: str, top_n: int | None = None) -> list[dict]:
        q = "SELECT * FROM ads WHERE page_id=? ORDER BY eu_reach DESC"
        if top_n:
            q += f" LIMIT {int(top_n)}"
        return [dict(r) for r in self.conn.execute(q, (page_id,))]

    def snapshots_for_brand(self, page_id: str) -> list[dict]:
        return [
            dict(r)
            for r in self.conn.execute(
                "SELECT * FROM snapshots WHERE page_id=? ORDER BY run_date", (page_id,)
            )
        ]

    # --- products -------------------------------------------------------------
    def replace_products(self, page_id: str, products: list[dict]) -> None:
        self.conn.execute("DELETE FROM products WHERE page_id=?", (page_id,))
        self.conn.executemany(
            "INSERT OR REPLACE INTO products (page_id, handle, title, price, image, created_at, position)"
            " VALUES (?,?,?,?,?,?,?)",
            [
                (page_id, p["handle"], p["title"], p["price"], p["image"], p["created_at"], i)
                for i, p in enumerate(products)
            ],
        )
        self.conn.commit()

    def products_for_brand(self, page_id: str, top_n: int | None = None) -> list[dict]:
        q = "SELECT * FROM products WHERE page_id=? ORDER BY position"
        if top_n:
            q += f" LIMIT {int(top_n)}"
        return [dict(r) for r in self.conn.execute(q, (page_id,))]
