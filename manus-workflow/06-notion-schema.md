# Phase 5 — Notion schema, tags & naming convention

Notion turns a script into trackable production work **and** is the join point between Meta
performance data and the winning-script memory. It doesn't have to be Notion — anything with
API access works (ClickUp, etc.) — but you need the **tagging**, because the tags are what let
you track everything on the back end.

## Tag every concept with all of these

| Tag | Example values | Why |
|---|---|---|
| **Ad name** | `sleep_racingmind_aisong_v012` | the join key to Meta (see naming convention) |
| **Product** | which SKU | track by product |
| **Angle** | racing-mind, 3am-wakeups, wired-but-tired | win rate per angle |
| **Mechanism** | you run >1 per concept — tag each | which mechanism converts |
| **Awareness level** | unaware → most-aware | where spend/wins concentrate |
| **Format** | UGC, text-led, product demo, AI animation, AI authority, AI song, before/after, testimonial, VSL | which formats win |
| **Concept type** | e.g. VSL, AI animation ad, AI song ad | pairs with format for "winning combinations" |
| **Avatar** | sub-persona | which avatar responds |

With these, your business-OS dashboard (built via Hermes/Claude Code) can show: win rate per
angle, most-spending awareness level, and **winning combinations** — e.g. "joint-pain angle +
AI song ad + this concept type" is your top performer, so double down on it.

## Production fields (standard)

Status pipeline (`in-progress → approved → ready-to-launch`), assigned editor, reviewer,
strategist, deadline, plus a **core-metrics** block that gets filled in after launch.

## The naming convention (most important thing in the whole system)

The ad name **must be identical in Notion and in Meta.** That identity is the only thing that
lets Manus join performance ↔ script. Pick a convention and never break it. Suggested shape:

```
{buyerproblem}_{angle}_{format}_{version}
        e.g.  sleep_racingmind_aisong_v012
```

- `/notion-push` writes this naming convention onto the Notion concept at approval.
- The **media buyer copies it verbatim into Meta** at launch — they invent nothing.
- Now: Meta reports "`sleep_racingmind_aisong_v012` spent $1.5k @ 1.5 ROAS" → Manus finds the
  same name in Notion → opens the brief → pulls the script → files it as a winner.

## The `/notion-push` skill

Train a skill (same conversational build as the script skills) that, on an approved script:

1. Creates the Notion page with the full script.
2. Applies **all** tags above.
3. Writes the **ad naming convention**.
4. Assigns editor / reviewer / strategist and sets the deadline.
5. Moves it to the right status.

## The 7-day feedback loop (Hermes or Manus)

Seven days after launch, a scheduled task (Hermes in the training, but Manus can do it):

1. Scans the Meta account, matches ads by naming convention.
2. Fills the core-metrics block back into each Notion concept.
3. Sorts each ad into **winning** / **high-potential** / **graveyard** (losers, no iterations).

Then the Manus winner-harvest cron reads the winning + high-potential set and (a) files their
raw scripts into `winning-scripts.md`, and (b) feeds `/winning-script-iteration`.

## The `/winning-script-iteration` skill (add last)

Once you have winners, this automates format-iteration. For a winning script it pulls: the
script + concept tags from Notion, the Meta ad name + performance summary, the project brain,
the Vantage ad database, and your Vantage "iteration inspiration" swipe file (checked first).
It then picks the strongest *different* next format (an AI-song winner → AI animation VSL / AI
authority / text-slideshow) and runs a full rewrite into that format. This is how one winner
becomes many, fast.

That's the whole system. See [`07-kickoff-prompts.md`](07-kickoff-prompts.md) to start.
