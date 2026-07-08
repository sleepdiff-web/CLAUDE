# Skill spec: `/notion-push`

**Trigger:** `/notion-push` (after you approve the final script)
**Input:** the approved script + your tag choices (Manus can infer most, confirm the rest)
**Uses connection:** Notion

## What it must do
1. Create a Notion page containing the **full approved script**.
2. Apply **all** tags: product, angle, mechanism(s), awareness level, format, concept type, avatar.
3. Write the **ad naming convention**: `{buyerproblem}_{angle}_{format}_{version}`
   (e.g. `sleep_racingmind_aisong_v012`) — this is the join key to Meta.
4. Assign **editor / reviewer / strategist** and set the **deadline**.
5. Move the page to the correct **status** (e.g. `ready-to-launch`).

## Output contract
- Confirms the Notion page URL + the exact naming convention string (the media buyer copies
  this verbatim into Meta).

## Why the naming convention is non-negotiable
It's the only link between "this ad spent $X @ Y ROAS" (Meta) and "here's the script" (Notion).
Break it and the winner-harvest loop can't find scripts.
