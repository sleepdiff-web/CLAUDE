# Phase 3 — Cron jobs (scheduled tasks that keep the brain alive)

Cron jobs are scheduled tasks in Manus (or Hermes). They're what makes your context files
*living* instead of static. Set each one up once by describing it to Manus in plain language
— you're telling it what to do, when, and where to write the result.

## The cron jobs to set up

| Cron | Cadence | What it does | Writes to |
|---|---|---|---|
| **Reddit threads** | Weekly (e.g. Mon 07:00) | Scan your subreddits, pull top-upvoted threads, extract new VOC / pain points / beliefs / failed solutions / angle ideas | `customer-voc.md`, `master-research.md` |
| **Post-purchase surveys** | Daily | Read new ZigPoll responses, add fresh buyer language | `customer-voc.md` |
| **Customer reviews** | Daily/weekly | Pull new Loox reviews | `customer-voc.md` |
| **Deep research** | Periodic (e.g. monthly) | Refresh the master research doc — new competitors, mechanisms, market beliefs | `master-research.md` |
| **Creative performance** | Daily | Read Meta ad account + Notion, identify ads over win threshold | `winning-scripts.md` |
| **Winning-script harvest** | Daily | For each new winner: pull its script from Notion (matched by naming convention) and file the raw script | `winning-scripts.md` |
| **Concepts to reverse-engineer** | Weekly | Scan Vantage for strong new reference concepts in your niche | `ad-references.md` |
| **(optional) Clean-out** | Monthly | Remove context that's no longer relevant so the brain stays tight | all files |

## The one that matters most: the Reddit cron

This is the highest-leverage scheduled task. Example instruction to give Manus:

> "Every Monday at 7am, go through these subreddits: [list]. Pull the most-upvoted threads
> from the past week. For each, extract: new voice-of-customer phrases, new pain points, new
> beliefs the market holds, failed solutions they've tried, and any potential new angle ideas.
> Append the findings to `customer-voc.md` and `master-research.md`. Flag anything that could
> be a brand-new concept to run."

Why it's worth it: a single Reddit thread — "after a walk my dog gets so stiff he lies down
for the rest of the day" — is a ready-made angle you'd miss unless you were reading Reddit
manually every day. The cron surfaces those for you continuously.

## The winner-harvest cron (the learning loop)

This is the daily job that makes winners train the next batch:

> "Every day, scan the Meta ad account. For any ad that has spent over [$X] at [≥ Y ROAS],
> classify it as a winner. Take the ad's naming convention, find the matching page in Notion,
> open the brief, copy the **raw script**, and append it to `winning-scripts.md`. Do not add
> any analysis or breakdown — just the script."

## Your action

Set up the top block first (Reddit, ZigPoll, Loox, creative performance, winner harvest).
Add deep-research and reverse-engineer crons once the basics run clean. Add the clean-out
cron last.

Next: [`05-skills.md`](05-skills.md).
