# DTCScout

A **pre-vetted database of fast-scaling DTC brands** — the free-tier version of
the "internal software" pitched in ad-spy membership tools. No Calvin Klein, no
random apps: every brand must keep meeting inclusion criteria, and brands that
fall off get flagged `removed` automatically on the next run.

```
              ┌────────────── DISCOVER ───────────────┐
niche terms ─►│ Meta Ad Library keyword search (EU     │─► candidate brands
              │ transparency: ALL ads + reach data)    │   (grouped by page)
              └────────────────────────────────────────┘        │
                                                                ▼
              ┌────────────── ENRICH ─────────────────┐  full ad account,
 each brand ─►│ Shopify probe · subscription-app       │  storefront signals,
              │ fingerprints · Tranco traffic tier     │  traffic tier
              └────────────────────────────────────────┘        │
                                                                ▼
              ┌────────────── VET ────────────────────┐  listed / rejected /
              │ criteria engine (active ads, launch    │  removed — with the
              │ velocity, brand age, no big brands)    │  failing reasons stored
              └────────────────────────────────────────┘        │
                                                                ▼
              ┌────────────── CLASSIFY ───────────────┐  awareness level ·
   top ads  ─►│ Claude API (or free keyword fallback)  │  authority figure ·
              └────────────────────────────────────────┘  subs vs one-time
                                                                ▼
                    SQLite DB + CSVs + filterable HTML dashboard
```

## What maps to the original spec

| Spec feature | v1 implementation |
|---|---|
| Pre-vetted, auto-removed brands | `vetting.py` criteria engine, re-run every execution |
| "Launched in last 6–12 months" | earliest ad in the Ad Library within `max_brand_age_months` |
| No Calvin Kleins | Tranco rank cutoff (`big_brand_rank_cutoff`) + domain blocklist |
| Awareness-level filter | LLM classification of ad copy (Schwartz stages) |
| Subs vs one-time filter | subscription-app fingerprints on the storefront **+** ad-copy classification |
| Authority-figure filter | LLM/keyword classification (doctor, dermatologist, …) |
| Monthly-traffic filter | Tranco rank → high/medium/low tier (free proxy) |
| Sort ads by impressions | `eu_total_reach` from EU ad transparency |
| Ad launch frequency / growth | `new_ads_30d`, per-run `snapshots` table |
| Best sellers / product data | `/products.json` probe (catalogue; sales rank not public) |
| Daily-updated database | run on a cron (GitHub Actions), same as TrendScout |

**Deliberately deferred** (v2+): visual treatment from actual video/images
(needs a vision pass over ad snapshots), landing-page type classification
(quiz/advertorial/listicle), video/audio download, transcripts, swipe files,
following, and the MCP server (trivial to add once the SQLite DB has data).

## Quick start

```bash
pip install -r requirements.txt
export META_ACCESS_TOKEN=...        # required (free) — see below
export ANTHROPIC_API_KEY=...        # optional — enables LLM classification

python scripts/run_dtc_scout.py --preflight   # network + env check
python scripts/run_dtc_scout.py --dry-run --verbose
python scripts/run_dtc_scout.py --verbose     # full run
```

Outputs:

- `data/dtc_scout.db` — SQLite source of truth (brands, ads, growth snapshots)
- `output/dtc_dashboard.html` — double-click to browse; filters for niche,
  awareness level, subs vs one-time, authority figure, traffic tier
- `output/dtc_brands.csv`, `output/dtc_ads.csv`

## Getting a Meta token

1. Create a (free) app at <https://developers.facebook.com/apps> and complete
   ID verification once at <https://www.facebook.com/ID> (required for Ad
   Library API access).
2. Grab a token from the Graph API Explorer, or generate an app token
   (`app_id|app_secret`). No special permissions needed for `ads_archive`.
3. `export META_ACCESS_TOKEN=...`

Why the EU country trick: since the DSA, ads delivered to any EU country are
fully queryable — every niche, not just political ads — including
`eu_total_reach`, the closest free thing to an impressions/spend signal. Any
brand scaling hard on Meta almost always delivers to the EU too.

## Configuration

Everything lives in [`dtc_config.yaml`](dtc_config.yaml):

- `meta.niches` — niche → Ad Library search terms (the discovery surface)
- `vetting.*` — the inclusion criteria (active ads, launch velocity, brand
  age, Shopify requirement, big-brand cutoff, blocklist)
- `classify.*` — model + how many top ads per brand get classified
- `traffic.*` — Tranco rank cutoffs for the traffic tiers

## Network allowlist (managed sandboxes)

Same gotcha as TrendScout: sandboxes with a **Trusted** egress policy block
the data sources. Run `--preflight` to check; allow:

```
graph.facebook.com
tranco-list.eu
api.anthropic.com     # only if using LLM classification
```

plus the storefront domains being probed (or run locally / with **Full**
network access, which is much more practical for the Shopify probing stage).

## Tests

```bash
pytest tests/test_dtc_*.py -q
```

Vetting rules, Ad Library parsing, metric aggregation, Shopify/subscription
fingerprints, and classifier parsing are pure functions tested offline.

## Costs

- Meta Ad Library API: free (rate-limited per token)
- Tranco: free
- Classification: $0 with the keyword fallback; with Claude Haiku, roughly
  ~$0.01 per 25 ads classified — a few dollars/month at daily cadence
