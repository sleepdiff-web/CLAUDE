# Kickoff prompts — copy, paste, then *talk*

These are conversation starters for Whisperflow, **not** master prompts. Say them out loud,
review what Manus returns, then push back and refine. The refinement loop is the actual work.

---

## 0. Orientation (paste a screenshot of the connections list too)

> "I run an e-commerce brand and I want to use you as my agentic workflow for writing ad
> scripts. Here's a screenshot of the connections I want to set up. Walk me through connecting
> each one step by step. Let's start with ZigPoll — tell me where to find the API key."

Then go connection by connection: ZigPoll → Loox → Vantage → Meta Ads → Notion → Shopify.
Reddit has no API key, so it becomes a scheduled task, not a connection.

---

## 1. Build the VOC / research brain

> "Now build the context for this project. The project is my brand [X], and this project
> covers one core buyer problem: [buyer problem]. First build the voice-of-customer document.
> Start with Reddit — here are the main subreddits: [list]. Use these as a baseline but go
> find other relevant subreddits yourself. Make it 80+ pages. Find all the pain points, the
> failed solutions, the beliefs the market holds, the beliefs we need to break, and other
> brands mentioned. Pull in ZigPoll and Loox language too. As much depth as you can."

Then review and push:

> "This isn't deep enough. Go find more on [X]. Add [Y]. Expand the failed-solutions section."

Repeat per file: `product-context` (mostly you), `customer-voc`, `master-research`,
`ad-references`, `winning-scripts`.

---

## 2. Set up the Reddit cron

> "Set up a scheduled task: every Monday 7am, go through these subreddits, pull the
> most-upvoted threads of the past week, extract new VOC / pain points / beliefs / failed
> solutions / angle ideas, append to my customer-voc and master-research files, and flag
> anything that could be a brand-new concept."

---

## 3. Set up the winner-harvest cron

> "Set up a daily task: scan my Meta ad account; any ad that's spent over [$X] at [≥ Y ROAS]
> is a winner. Take its ad name, find the matching page in Notion, open the brief, copy the
> raw script, and append it to my winning-scripts file. No breakdowns — just the script."

---

## 4. Build the two script skills

> "Here's my current script workflow [paste the WAP prompt doc]. I run these prompts manually
> inside a project with my context files. Turn it into a skill so I get the same output
> faster. Split it into two skills. Skill one, `concept-extraction`: run prompts 1–2 — break
> down the reference ad, define the structure and flow, write the first draft. Skill two,
> `concept-extraction-optimized`: run the beat-by-beat optimization on that draft — hooks,
> each beat, final refinements."

Test skill 1:

> "/concept-extraction [paste a reference-ad transcript]"

If it's wrong:

> "No, this is wrong because [X]. Learn from this and adjust the skill so it doesn't repeat
> this mistake."

---

## 5. Build the Notion-push skill

> "Build a skill called `notion-push`. When I approve a script, create a Notion page with the
> full script, tag it with product / angle / mechanism / awareness level / format / concept
> type / avatar, write the ad naming convention `{buyerproblem}_{angle}_{format}_{version}`,
> assign the editor / reviewer / strategist, set the deadline, and move it to the right status."

---

## 6. Bias audit (run after everything's built)

> "Do a full audit of this project's context files and make sure nothing will create bias in
> the scripts — no over-weighted patterns, no fixation on specific hooks or mechanisms. The
> winning-scripts file should be a plain bank of raw scripts with no analysis."

---

## Daily driver, once it's all live

```
/concept-extraction            → paste reference transcript → review draft
/concept-extraction-optimized  → beat-by-beat (~60s)
edit 5–15 min (Whisperflow the weak sections)
/notion-push
```
