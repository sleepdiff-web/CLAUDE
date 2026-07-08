# Manus Script-Writing Workflow — Setup Pack

This is a distilled, execute-from-top-to-bottom build of the "Phase 1" system from
the training: moving ad-script writing **out of static Claude projects** and into an
**agentic Manus workflow** where context refreshes itself, the prompt chain becomes
saved skills, and your winners train the next batch automatically.

> Same workflow you already run (the WAP concept-extraction chain) — better operating
> system. The goal isn't just more volume; it's more volume **without** the quality drop,
> because the research and the winner-memory feed each other.

## The one-paragraph mental model

Three tools, one loop:

- **Manus = the creative engine.** Holds the project brain (context files in its sandbox),
  runs the skills, one-shots the scripts.
- **Notion = the production database.** Every approved script lands here, tagged with
  everything (angle, mechanism, awareness, format), assigned to an editor, given a deadline.
- **Hermes (or Manus again) = the business OS layer.** Pulls performance from Meta + Notion,
  labels each ad win / high-potential / graveyard, and feeds winners back into Manus.

```
                    ┌─────────────────────── THE LOOP ───────────────────────┐
                    │                                                         │
   Connections ─►  MANUS project brain  ─►  /concept-extraction  ─►  draft    │
  (ZigPoll, Loox,   (sandbox context      /concept-extraction-optimized       │
   Reddit, Vantage,  files, auto-          (beat-by-beat) ─► you edit 5–15min  │
   Meta, Notion,     refreshed by crons)                        │             │
   Shopify)                                                     ▼             │
                                                       /notion-push  ─► NOTION │
                                                       (tagged, assigned)      │
                                                                │             │
   Meta performance ◄──────── media buyer launches (copies naming convention) │
        │                                                                     │
        ▼                                                                     │
   after 7 days: Hermes/Manus scores it ─► winning / high-potential / graveyard│
        │                                                                     │
        └─► winners pushed into "winning scripts" context file ───────────────┘
                (and /winning-script-iteration spins new formats off winners)
```

## What you'll have when this is done

1. **One managed project per core buyer problem** (not per angle, not one giant catch-all).
2. **Living context files** in the Manus sandbox, refreshed by scheduled cron jobs — not
   static uploads that go stale.
3. **Two script skills** — `concept-extraction` and `concept-extraction-optimized` (beat-by-beat).
4. **A Notion-push skill** that files the approved script with all tags + naming convention.
5. **A winning-script-iteration skill** (add this last) that spins winners into new formats.
6. **A learning loop** where Meta performance labels your winners and they train the next batch.

## Build order (do it in this sequence)

| Phase | What | File | Time |
|---|---|---|---|
| 0 | Decide your project boundary (one buyer problem) | [`01-project-structure.md`](01-project-structure.md) | 10 min |
| 1 | Wire up all data connections | [`02-connections.md`](02-connections.md) | 30–45 min |
| 2 | Build the 6 sandbox context files (the "brain") | [`03-context-files.md`](03-context-files.md) + [`context-file-templates/`](context-file-templates/) | 1–2 hrs (mostly Manus running research) |
| 3 | Set up the cron jobs so the brain refreshes itself | [`04-cron-jobs.md`](04-cron-jobs.md) | 20 min |
| 4 | Turn the WAP prompt chain into 2 skills | [`05-skills.md`](05-skills.md) + [`skills/`](skills/) | 15 min |
| 5 | Set up Notion tags + naming convention + push skill | [`06-notion-schema.md`](06-notion-schema.md) | 30 min |
| 6 | Add the winning-script-iteration skill (later) | [`05-skills.md`](05-skills.md) | when you have winners |

**Start with phases 0–4.** The Notion + iteration layers can come once scripts are flowing.

## The single most important operating principle

**Don't chase a master prompt.** Everything here is built by *talking* to Manus (use
Whisperflow), back and forth, refining. The context files, the skills, all of it — you
describe the vision out loud, review what it gives back, and correct it. There is no magic
one-shot prompt, and building around one is the #1 way people go wrong.

The copy-paste kickoff prompts in [`07-kickoff-prompts.md`](07-kickoff-prompts.md) are
*starting points for a conversation*, not fire-and-forget commands.

## A warning that will save you a week: avoid winner bias

When you build the winning-scripts context file, tell Manus to store **only the raw winning
script — no breakdowns, no "winning hook" analysis, no "winning mechanism" call-outs.** Early
on this system fixates on whatever you emphasize and every new script clings to it. Keep the
winner bank as a plain bank. After you've built everything, tell Manus:

> "Do a full audit of this project and make sure nothing in the context files will create
> bias in the scripts — no over-weighted patterns, no fixation on specific hooks or mechanisms."
