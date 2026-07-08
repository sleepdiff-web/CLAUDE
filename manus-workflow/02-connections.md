# Phase 1 — Connections (wire the sources before you build the brain)

The best context already lives in tools you're using. Connect those first, then Manus can
keep the brain fresh forever instead of you re-uploading stale PDFs.

Each source connects via **MCP** or an **API token/key**. In Manus you connect it once, then
reference it from any project.

## The connection list

| Source | What it feeds | How to connect | Priority |
|---|---|---|---|
| **ZigPoll** | Post-purchase survey answers (real buyer language, "golden unlocks") | API key | ⭐ Must |
| **Loox** (or Judge.me) | Customer reviews / VOC | API / connection | ⭐ Must |
| **Reddit** | Pain points, failed solutions, beliefs, new angle ideas | *Scheduled task* (no API key — see crons) | ⭐ Must |
| **Meta Ads** | Ad performance → identifies winners | API | ⭐ Must |
| **Notion** | Production DB + winning-script retrieval | API | ⭐ Must |
| **Vantage** | Swipe files / reverse-engineer concepts / iteration inspiration | MCP | Nice |
| **Shopify** | Product / order context | API | Nice |
| **Google Analytics** | Traffic / behavior context | connection | Optional |

The ones that actually matter for *writing scripts* are the top block. Don't over-connect —
just wire what's genuinely valuable context for producing a script.

## Why ZigPoll matters more than a PDF

A static Claude context file is a screenshot of survey data frozen in time. ZigPoll connected
via API means Manus checks **new responses every day**. On a brand with 200k+ survey responses,
one golden line from a customer can be the unlock that takes you to the next scale — and you'd
never see it in a one-time PDF export.

## Setup, step by step (do this by *talking* to Manus)

You don't need a special prompt. Open Manus and walk it through one connection at a time:

1. **ZigPoll first.** Get your API key from ZigPoll → give it to Manus → confirm the endpoint
   connects → confirm it can read responses.
2. **Loox** — same: find the connection/API, connect, confirm it can pull reviews.
3. **Vantage** — connect the MCP, confirm it can see your ad database + swipe files.
4. **Meta Ads** — connect, confirm it can read ad-level spend/ROAS.
5. **Notion** — connect, confirm it can read/write your production database.
6. **Shopify** — connect if you want product/order context.
7. **Reddit** — no API key; this is a *scheduled task*, set it up in [`04-cron-jobs.md`](04-cron-jobs.md).

See [`07-kickoff-prompts.md`](07-kickoff-prompts.md) for the exact conversational script.

## Critical: consistent naming so sources can be joined

The learning loop only works if **the ad name in Meta is identical to the ad name in Notion.**
That shared naming convention is what lets Manus join "this ad spent $1.5k at 1.5 ROAS" (Meta)
to "here's the actual script" (Notion). Lock the naming convention now — it's defined in
[`06-notion-schema.md`](06-notion-schema.md) — and make your media buyer copy it verbatim
into Meta at launch.

Once sources are connected, Manus turns the useful data into project files and keeps
refreshing them via the crons. Next: [`03-context-files.md`](03-context-files.md).
