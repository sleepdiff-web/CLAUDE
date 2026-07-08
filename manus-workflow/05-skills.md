# Phase 4 — Skills (kill the manual prompt chain)

This is the part that ends the beat-by-beat, copy-from-Google-Doc grind. Your existing WAP
concept-extraction workflow (the ~5 prompts) becomes **saved Manus skills** you trigger with
a forward slash.

## Why two skills, not one

The full WAP chain can't run as a single skill — it's too much for one pass. Split it exactly
where the training does:

- **`/concept-extraction`** — runs roughly the **first two** WAP prompts: break down the
  reference ad, define the structure/positioning/flow, and write the **first script draft**.
- **`/concept-extraction-optimized`** — runs the **beat-by-beat**: optimizes hooks, tightens
  each beat, does final refinements on the draft the first skill produced. ~60 seconds.

Two more skills come later:

- **`/notion-push`** — files the approved script into Notion with all tags + naming
  convention, assigns editor/reviewer/deadline.
- **`/winning-script-iteration`** — spins a winner into new formats (add this once you have winners).

## How to build the two script skills (≈5 min each)

You do **not** write these from scratch. You hand Manus your existing WAP Google Doc and have
it convert the prompts into a skill. Conversationally:

1. Open Manus, paste (or link) the WAP prompt doc.
2. Say: *"This is my current script workflow — I run these prompts manually inside a project
   with my context files. Turn it into a skill so I get the same output, faster. Let's split
   it into two: the first skill, `concept-extraction`, runs prompts 1–2 — break down the
   reference ad, define the structure, and write the first draft. The second skill,
   `concept-extraction-optimized`, runs the beat-by-beat optimization on that draft."*
3. Manus builds skill 1. Test it (below), correct it, let it update the skill.
4. Repeat for skill 2 using the same doc.

The skill scaffolds in [`skills/`](skills/) describe what each skill must do, its inputs, and
its output contract — use them as the spec when you tell Manus what to build. **They are not
the WAP prompts** (those are your IP from the course); they're the structure to pour your
prompts into.

## Using the skills (the daily driver)

```
1. Pick the project (buyer problem).
2. Grab your reference ad transcript.
3. /concept-extraction   → paste transcript   → review structure + first draft
4. /concept-extraction-optimized               → beat-by-beat, ~60s
5. Edit the final script (5–15 min; VSLs longer). Whisperflow: paste a weak
   section, say "I don't like this, it should be X/Y/Z," let it adjust.
6. Approve → /notion-push
```

Start-to-finish: ~10–20 min for a concept, ~40 min for a 5-min VSL. That's the volume unlock.

## Skills get better over time — this is the whole point

When a skill produces something wrong, don't just fix the output — tell Manus:

> *"No, this is wrong because X. Learn from this and adjust the skill so it doesn't make this
> mistake again."*

Manus updates the skill itself. The more you use them, the more context they carry and the
better they get. Combined with a growing `winning-scripts.md`, you drift toward clean
one-shots on short ads.

Next: [`06-notion-schema.md`](06-notion-schema.md).
