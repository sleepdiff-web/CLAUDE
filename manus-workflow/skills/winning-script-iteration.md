# Skill spec: `/winning-script-iteration`  (add LAST)

> Only build this once you have winners and a populated `winning-scripts.md`. It automates
> spinning one winner into new formats.

**Trigger:** `/winning-script-iteration`
**Input:** a winning ad (from the winner set the feedback loop produced)
**Uses connections:** Notion, Meta, Vantage

## What it pulls
- The winning script + concept tags (Notion)
- The Meta ad name + performance summary (Meta)
- The project brain (all context files)
- The Vantage ad database
- Your Vantage **"iteration inspiration"** swipe file — **checked FIRST**, before the wider DB

## What it must do
1. Given a winning script, decide the strongest **different** next format to push it into
   (an AI-song winner → AI animation VSL, AI authority, text-slideshow — never the same format).
2. Scan the iteration swipe file first, then the wider Vantage DB, for the best structure to
   fit this winning script into.
3. Run a **full rewrite** of the script into that chosen format.

## Output contract
- A new full script in the new format, ready to run through `/concept-extraction-optimized`
  and your edit pass, then `/notion-push` as a new tagged concept (new version).

## Why it works
One proven winner becomes many format variants fast — the highest-ROI kind of new creative,
because the underlying concept is already validated.
