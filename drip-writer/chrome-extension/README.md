# Drip Writer — Chrome extension

Types your text into a real text field on **any website** (a comment box, a
form, a chat, a message) like a human would — variable speed, the occasional
typo that backspaces and corrects itself, natural pauses. This is the version
that types into *other tabs*, unlike the standalone `index.html` which only
types into its own box.

## Install (about 1 minute, one time)

1. Download the `chrome-extension` folder to your computer (unzip it if it came
   as a `.zip`, and remember where it is).
2. Open Chrome and go to **`chrome://extensions`** (type it in the address bar).
3. Turn on **Developer mode** — the toggle in the top-right corner.
4. Click **Load unpacked** (top-left) and select the `chrome-extension` folder.
5. Done. You'll see **Drip Writer** in your extensions list. Click the puzzle-piece
   icon in the toolbar and pin it so it's always visible.

## Use it

1. Go to the page you want to type into and **click into the text box** so the
   cursor is blinking in it.
2. Click the **Drip Writer** toolbar icon — a small panel appears in the corner.
3. Paste your text into the panel, set the speed/typo sliders if you like, and
   press **Start typing**.
4. Watch it type into the page field. Use **Pause** or **Stop** any time.

Tip: if it says *"Click into a text box first"*, just click the field on the
page again, then press Start. The panel remembers the last field you clicked.

## Controls

- **Speed** — words per minute (40–70 is typical human range).
- **Typos** — chance of a mistake per keystroke (then fixed).
- **Rhythm variance** — how uneven the timing feels.
- **Punctuation pauses / Thinking pauses / Fix typos** — toggles.

## What it works on (and what it doesn't)

Works on the vast majority of fields: standard text boxes, search bars, form
inputs, comment boxes, and most rich-text editors (the "contenteditable" kind
used by many chat and note apps).

Known limitations:
- **Google Docs** and a few apps with their own custom editing engines ignore
  scripted typing — the extension can't drive those. (Making Docs work needs a
  heavier tool that uses Chrome's debugger API.)
- Fields inside a different-site embedded frame (cross-origin iframe) can't be
  reached, for browser security reasons.
- Chrome's own pages (`chrome://…`), the Web Store, and the PDF viewer block all
  extensions, including this one.

Everything runs locally in your browser. The extension asks only for
`activeTab` — it can touch a page **only** at the moment you click its icon, and
never reads or sends your data anywhere.
