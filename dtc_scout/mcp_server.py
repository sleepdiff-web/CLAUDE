"""DTCScout MCP server — query the brand database from Claude (or any MCP client).

Read-only tools over the SQLite DB, mirroring the commercial tools' connector:
list/search brands, search ads by classification, per-brand breakdowns, and a
research brief that pulls hooks for a concept.

Run (stdio):        python -m dtc_scout.mcp_server
Add to Claude Code: claude mcp add dtcscout -- python -m dtc_scout.mcp_server

Requires: pip install "mcp[cli]"
"""
from __future__ import annotations

from datetime import date

from mcp.server.fastmcp import FastMCP

from .analytics import avg_ad_life_days, catalog_freshness, median_price, mix
from .config import load_config
from .db import Database

mcp = FastMCP("dtcscout")


def _db() -> Database:
    return Database(load_config().db_path)


def _find_brand(db: Database, query: str) -> dict | None:
    q = f"%{query.lower()}%"
    row = db.conn.execute(
        "SELECT * FROM brands WHERE lower(page_name) LIKE ? OR lower(domain) LIKE ? "
        "ORDER BY total_eu_reach DESC LIMIT 1",
        (q, q),
    ).fetchone()
    return dict(row) if row else None


@mcp.tool()
def list_brands(niche: str = "", sort: str = "reach", limit: int = 20) -> list[dict]:
    """List pre-vetted (listed) brands. sort: 'reach' | 'new_ads' | 'active_ads'."""
    order = {"reach": "total_eu_reach", "new_ads": "new_ads_30d", "active_ads": "active_ads"}
    col = order.get(sort, "total_eu_reach")
    db = _db()
    q = "SELECT * FROM brands WHERE status='listed'"
    args: list = []
    if niche:
        q += " AND niche=?"
        args.append(niche)
    rows = db.conn.execute(f"{q} ORDER BY {col} DESC LIMIT ?", (*args, int(limit))).fetchall()
    out = [dict(r) for r in rows]
    db.close()
    return out


@mcp.tool()
def search_ads(
    awareness_level: str = "",
    offer_type: str = "",
    authority_figure: str = "",
    niche: str = "",
    active_only: bool = True,
    limit: int = 20,
) -> list[dict]:
    """Search classified ads from listed brands, sorted by EU reach (spend proxy).
    awareness_level: unaware|problem_aware|solution_aware|product_aware|most_aware."""
    db = _db()
    q = (
        "SELECT a.*, b.page_name AS brand, b.domain FROM ads a "
        "JOIN brands b ON b.page_id=a.page_id AND b.status='listed' WHERE 1=1"
    )
    args: list = []
    for col, val in [
        ("a.awareness_level", awareness_level),
        ("a.offer_type", offer_type),
        ("a.authority_figure", authority_figure),
        ("a.niche", niche),
    ]:
        if val:
            q += f" AND {col}=?"
            args.append(val)
    if active_only:
        q += " AND (a.stop_date IS NULL OR a.stop_date='')"
    rows = db.conn.execute(f"{q} ORDER BY a.eu_reach DESC LIMIT ?", (*args, int(limit))).fetchall()
    out = [dict(r) for r in rows]
    db.close()
    return out


@mcp.tool()
def analyze_brand(query: str) -> dict:
    """Full breakdown of one brand (match by name or domain): store signals,
    creative pattern mix, awareness mix, catalog freshness, bestsellers, top ads."""
    db = _db()
    brand = _find_brand(db, query)
    if not brand:
        db.close()
        return {"error": f"no brand matching {query!r}"}
    ads = db.ads_for_brand(brand["page_id"])
    products = db.products_for_brand(brand["page_id"])
    result = {
        "brand": brand,
        "awareness_mix": mix(ads, "awareness_level"),
        "visual_mix": mix(ads, "visual_treatment"),
        "offer_mix": mix(ads, "offer_type"),
        "avg_ad_life_days": avg_ad_life_days(ads, date.today()),
        "median_price": median_price(products),
        "catalog_freshness": catalog_freshness(products),
        "bestsellers": products[:10],
        "top_ads": ads[:10],
        "ad_activity": db.snapshots_for_brand(brand["page_id"]),
    }
    db.close()
    return result


@mcp.tool()
def research_brief(niche: str, awareness_level: str = "", limit: int = 12) -> dict:
    """Pull the highest-reach hooks in a niche (optionally one awareness level)
    as raw material for new concepts — the 'best unaware ads from growing
    brands' workflow."""
    ads = search_ads(awareness_level=awareness_level, niche=niche, limit=limit)
    return {
        "niche": niche,
        "awareness_level": awareness_level or "all",
        "hooks": [
            {
                "brand": a["brand"],
                "hook": (a["link_title"] or a["body"] or "").split("\n")[0][:160],
                "body": (a["body"] or "")[:400],
                "eu_reach": a["eu_reach"],
                "offer_type": a["offer_type"],
            }
            for a in ads
        ],
    }


if __name__ == "__main__":
    mcp.run()
