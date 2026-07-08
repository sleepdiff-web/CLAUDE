# Skill spec: `/concept-extraction-optimized`

> SPEC for the second skill — pour your WAP beat-by-beat / optimization prompts into it.

**Trigger:** `/concept-extraction-optimized`
**Input:** the first-draft script from `/concept-extraction` (uses the last draft in context)
**Runs:** the WAP beat-by-beat optimization pass
**Runtime:** ~60 seconds

## What it must do
1. **Optimize the hook** — strongest opening for scroll-stop + belief-shift.
2. **Beat-by-beat pass** — tighten every beat: pacing, clarity, that each beat earns the next,
   mechanism lands, proof is placed right.
3. **Final refinements** — cut fat, sharpen CTA, ensure compliance (`product-context` rules).

## Output contract
- The optimized, near-final script (ready for your 5–15 min human edit).

## Build note
Same conversational build. This runs *after* `/concept-extraction` in the same session, so it
should reference the existing draft rather than ask for a re-paste.
