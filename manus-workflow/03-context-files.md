# Phase 2 — The project brain (sandbox context files)

This is the big conceptual shift from Claude. In a Claude project you **upload files**. In
this Manus workflow you **don't upload anything** — all context lives in the project's
**sandbox**, and the cron jobs keep it fresh.

Each project has its own sandbox. Inside it, the "brain" is a small set of files.

## The 6 core files

```
sandbox/
├── product-context.md        # product, offer, mechanism, proof, objections, compliance
├── customer-voc.md           # raw customer language (Reddit + ZigPoll + Loox)
├── master-research.md        # the AI deep-research doc (the WAP deep-research output)
├── ad-references.md          # swipe file / reference ads (Vantage or Atria)
├── winning-scripts.md        # your own winning scripts — RAW, no breakdowns
└── (optional) iteration-swipe.md  # saved "iteration inspiration" from Vantage
```

Templates for each are in [`context-file-templates/`](context-file-templates/). Fill the
scaffolding; let Manus populate the research-heavy parts.

### 1. `product-context.md`
Product, offer, mechanism(s), proof, objections, and **what you can and can't say**
(compliance / claims restrictions). This is the one file you mostly write by hand — it's
your ground truth.

### 2. `customer-voc.md`
Raw voice-of-customer language. Auto-fed from **Reddit** (cron), **ZigPoll** (live), and
**Loox** (live). This is what makes ads *land* — you're speaking the customer's actual words.

### 3. `master-research.md`
The deep-research document — the equivalent of the WAP deep-research workflow, but automated.
Pain points, failed solutions, current beliefs, **beliefs you need to break**, competitor
brands, mechanisms. Manus is genuinely excellent at this; a first Reddit deep-research run
can take 60–70 minutes and produce 80–100+ pages. That's fine — it's a one-time deep build,
then crons top it up.

> **Still do manual research too.** Even with this automated, going on Reddit yourself when
> you first launch a product is a must — not because the AI can't gather it, but because
> **you** need to train your own brain on the avatar/mechanism so your end-of-process review
> is any good. The AI isn't good enough to one-shot ads unreviewed; the review step is where
> your manual training pays off.

### 4. `ad-references.md`
Your swipe file — the reference ads you reverse-engineer. Connect Vantage (or Atria) so Manus
can pull structures from real winning ads. Reference ads give the **structure**; they don't
train the model on *your* voice.

### 5. `winning-scripts.md` — the file that actually trains Manus
Your own winning scripts. Manus uses its **Meta** connection to find ads above your win
threshold (e.g. ≥ 1.0 ROAS on a subscription brand pushing scale), then uses its **Notion**
connection to pull that ad's script, and files it here.

**Store the raw script and nothing else.** No "winning hook" extraction, no mechanism
call-outs, no directions, no emphasis. Just a growing bank of full scripts. The bigger this
bank gets, the more often Manus one-shots correctly and the fewer edits you make — especially
on short (sub-1-min) ads. (Long 5–6 min VSLs still need more hand-work.)

### 6. `iteration-swipe.md` (optional, for later)
When scanning Vantage you save iteration ideas into a Vantage swipe file called
"iteration inspiration." The winning-script-iteration skill checks this first before the
wider database. Only relevant once you're running the iteration skill.

## How the files stay alive

| File | Refreshed by |
|---|---|
| `product-context.md` | you, manually (rarely changes) |
| `customer-voc.md` | Reddit cron (weekly) + ZigPoll/Loox (live on read) |
| `master-research.md` | deep-research cron (periodic) |
| `ad-references.md` | Vantage (live) + your manual saves |
| `winning-scripts.md` | Meta→Notion winner cron (daily) |

## Build it by talking, not by prompting

Build these in a back-and-forth with Manus (Whisperflow). Typical flow: give it a first
instruction ("build the VOC doc, start with these subreddits, 80+ pages, find pain points /
failed solutions / beliefs to break / competitor brands"), review what comes back, then
push: "not deep enough, go find more X, add Y." Iterate file by file. The kickoff prompts in
[`07-kickoff-prompts.md`](07-kickoff-prompts.md) get you started.

After all 6 exist, run the **bias audit** (see README) so no file over-weights a pattern.

Next: [`04-cron-jobs.md`](04-cron-jobs.md).
