# Drip Writer

A self-contained web tool that "types out" any text like a human would —
variable keystroke speed, the occasional fat-finger typo that gets backspaced
and corrected, and natural pauses at punctuation.

## Use it

Open [`index.html`](index.html) in any browser (double-click the file, or host
it anywhere). No build step, no dependencies, no network calls — everything
runs locally in the page.

1. Paste your text into the box.
2. Adjust the controls (optional):
   - **Speed** — words per minute (40–70 is typical human range).
   - **Typo rate** — how often a mistake is made (then fixed).
   - **Rhythm variance** — how uneven the keystroke timing feels.
   - Toggles for punctuation pauses, thinking pauses, and whether typos get
     corrected (turn off to leave mistakes in).
3. Press **Start**. Use **Pause/Resume** any time.
4. Press **Copy result** when it finishes.

## How the "human" typing works

- **Timing** — base delay comes from the WPM setting (5 chars/word convention),
  then each keystroke gets Gaussian jitter. Spaces are a touch slower; sentence
  endings (`. ! ?`) get a long pause, commas a shorter one; occasionally it
  "thinks" mid-sentence.
- **Typos** — on letters/digits, with the chosen probability it makes one of a
  few realistic mistakes: an adjacent-key substitution (QWERTY neighbours), a
  doubled letter, or an extra inserted key. If correction is on it pauses,
  backspaces, and retypes — so the finished text always matches your input
  exactly.

## Note

This types into its **own** output box (which you then copy from). It does not
type into other apps or websites — that would need a browser extension or a
desktop automation script.
