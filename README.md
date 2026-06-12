# TrendScout

Weekly discovery of **in-demand supplement ingredients** — so you can take the
trending ingredient (turmeric, berberine, sea moss, …) straight to
[Kalodata](https://www.kalodata.com) and find the supplements selling on TikTok
Shop.

The hard part of this problem is that **Google Trends can't tell you about an
ingredient you don't already know to search for** — you have to give it a term.
TrendScout solves that with a *discovery layer* that surfaces ingredient names
you've never heard of, then a *scoring layer* that ranks them by momentum.

```
                 ┌──────────────── DISCOVERY ────────────────┐
   seed terms ─► Google Trends "rising related queries"       │
 ("supplement",                                               ├─► candidate
  "gut health") Reddit top posts (r/Supplements, r/Nootropics)│    ingredients
                 └───────────────────────────────────────────┘        │
                                                                       ▼
                 ┌──────────────── SCORING ──────────────────┐  filter to
   each term ─► Google Trends interest-over-time (90 days) ──┤  plausible
                 growth % · acceleration · sustained-not-spike│  ingredients
                 └───────────────────────────────────────────┘        │
                                                                       ▼
                 ranked CSV + breakout alerts (Slack/file) with Kalodata links
```

## Design choices (from the initial spec)

| Decision | Choice |
|---|---|
| Discovery sources | Google Trends rising queries **+** Reddit (free, no key) |
| "In demand" means | Fast growth / breakout **and** sustained + accelerating (not a one-week spike) |
| Trends access | Free `pytrends` (0–100 interest index; swappable later) |
| Market | Worldwide (`geo: ""` in `config.yaml`) |
| Cadence | Weekly (GitHub Actions cron) |
| Output | Ranked CSV sheet **+** breakout alerts, each with a Kalodata search link |
| Cost | $0 — no paid APIs |

## Quick start

```bash
pip install -r requirements.txt

# 0. Confirm the network can actually reach the data sources (see gotcha below):
python scripts/run_weekly.py --preflight

# Discover candidates without hitting the Trends scoring API (fast, offline-ish):
python scripts/run_weekly.py --dry-run --verbose

# Full run (discovery + momentum scoring + outputs):
python scripts/run_weekly.py --verbose
```

Outputs land in `output/`:

- `trending_ingredients.csv` — ranked sheet (open in Excel/Google Sheets)
- `breakout_alerts.md` / `.json` — this week's breakouts
- `data/history.json` — remembers seen ingredients so new ones get a 🆕 flag

## Configuration

Everything lives in [`config.yaml`](config.yaml): seed categories, subreddits,
scoring thresholds, and output settings. Key knobs:

- `discovery.trends_seeds` — broad categories to harvest rising queries from.
- `discovery.reddit_subreddits` — communities to mine for ingredient mentions.
- `scoring.breakout_growth_pct` — growth % that flags a breakout (default 80).
- `scoring.max_recent_volatility` — spike filter; lower = stricter.
- `market.geo` — `""` for worldwide, or `"US"`, `"GB"`, etc. to narrow.

## How discovery works

1. **Trends rising queries** — for each seed (`"supplement"`, `"gut health"`…),
   `pytrends` returns queries rising in popularity. A query like
   `"berberine benefits weight loss"` is reduced to its core ingredient
   (`berberine`) by stripping modifier words. Terms not in the seed lexicon but
   shaped like ingredients (e.g. `kanna extract`) are surfaced as **NEW**
   candidates.
2. **Reddit** — top posts of the week from supplement subreddits are scanned and
   matched against the ingredient lexicon (`data/ingredient_lexicon.txt`),
   ranked by how often each ingredient is mentioned.

Both feeds merge into one candidate pool (capped by `max_candidates` to respect
Trends rate limits). Terms found in **both** sources are a stronger signal.

## How scoring works

For each candidate we pull 90 days of worldwide interest and compute:

- **growth %** — mean of the last 4 weeks vs the prior 8 weeks
- **acceleration** — recent trend-line slope minus the prior slope
- **sustained** — recent demand is above a noise floor across multiple weeks and
  isn't a single spike (volatility cap)
- **breakout** — sustained **and** growth ≥ threshold
- **score (0–100)** — weighted blend of growth, current level, and acceleration,
  penalised for spikiness

See `tests/test_momentum.py` for worked examples.

## Optional integrations

All optional — the tool runs fully without them. Enable via environment vars /
GitHub secrets:

| Integration | Env vars |
|---|---|
| Slack breakout alerts | `SLACK_WEBHOOK_URL` |
| Push sheet to Google Sheets | `GOOGLE_SERVICE_ACCOUNT_JSON` (key file path) + `GSHEET_ID` |

## Weekly automation

[`.github/workflows/weekly.yml`](.github/workflows/weekly.yml) runs the pipeline
every Monday 07:00 UTC, commits the refreshed `output/` artifacts, and (if
secrets are set) posts Slack alerts. Trigger it manually any time from the
Actions tab (**Run workflow**).

## Tests

```bash
pytest -q
```

The scoring and ingredient-extraction cores are pure Python and tested without
any network access.

## Roadmap / where to spend next

These were deliberately left out to keep it free; easy to add later:

- **TikTok signal** (where supplement trends actually start) via a paid scraper
  (Apify) or Kalodata's own trend feed — the strongest upgrade for your use case.
- **Real search volumes** via Glimpse/SerpApi (pytrends only gives a 0–100 index).
- **Per-region scoring** (US/UK separately) by running the pipeline per `geo`.

## The #1 gotcha: network egress allowlist (read this first)

If a run returns **no data** and you see `HTTP 403` with
`x-deny-reason: host_not_allowed`, the data sources are being blocked by your
environment's **network egress allowlist** — *not* by Google or Reddit. Managed
sandboxes (Claude Code on the web, many CI setups) default to a **Trusted**
network policy that only permits package registries and a few cloud hosts.
`trends.google.com` and `reddit.com` aren't on that list, so the proxy denies
them before the request ever leaves the box.

**Check it in one command:**

```bash
python scripts/run_weekly.py --preflight
```

This probes every required host and, if any are blocked, prints the exact
domains to allow and how.

**The fix** — in the environment's settings, set **Network access → Custom**,
keep *"Also include default list of common package managers"* checked, and add:

```
trends.google.com
www.google.com        # pytrends fetches a consent cookie here
www.reddit.com
old.reddit.com
oauth.reddit.com      # only if you use the PRAW (official API) path
```

(Or set Network access to **Full**.) Docs:
<https://code.claude.com/docs/en/claude-code-on-the-web#network-access>

Running **locally on your own machine** has no such allowlist — Trends + Reddit
just work, no config needed.

## Other limitations

- `pytrends` is an unofficial scraper: free but rate-limited and can break if
  Google changes Trends. It's isolated behind `trends_client.py` so it can be
  swapped for a paid API (Glimpse/SerpApi) without touching the rest. If Google
  itself (not the allowlist) rate-limits a cloud IP, supply residential proxies
  via `market.proxies` in `config.yaml` or the `TRENDS_PROXIES` env var.
- **Reddit**: the fetcher uses a browser-like UA and falls back across
  `www`/`old` hosts. If Reddit blocks the unauthenticated path, set
  `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` to use the official API (PRAW).
- The Trends 0–100 interest index is *relative*, not absolute search volume.
- The Kalodata link is best-effort; adjust `kalodata.search_url_template` in
  `config.yaml` if their URL scheme changes.

### Recommended ways to run

1. **Locally** (simplest, free): `python scripts/run_weekly.py` — no allowlist,
   Trends + Reddit both work out of the box.
2. **Cloud / GitHub Actions**: allowlist the domains above (the workflow assumes
   they're reachable). Add a `TRENDS_PROXIES` secret only if Google additionally
   rate-limits the runner IP; optionally `REDDIT_CLIENT_ID`/`SECRET` for Reddit.
