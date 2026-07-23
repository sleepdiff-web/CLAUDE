# Drip Writer — desktop app (Windows)

The version that types your text into **any program** on your computer — Google
Docs in a browser, Word, Notepad, a chat window, anything — using real keyboard
input. This is the one to use when the browser tool and extension can't reach
your app (e.g. Google Docs).

## Download & run (no install)

1. Go to the **Releases** page and download **`DripWriter.exe`**:
   <https://github.com/sleepdiff-web/CLAUDE/releases/tag/drip-writer-desktop>
2. Double-click `DripWriter.exe`.
   - The first time, Windows may show **"Windows protected your PC"** (because
     the app isn't code-signed). Click **More info → Run anyway**. It's the file
     built from the source in this folder.
3. The Drip Writer window opens.

## How to use

1. Paste your text into the box.
2. Set the sliders if you like — **Speed** (words per minute), **Typo rate**,
   **Rhythm variance**, and **Start delay** (how many seconds you get to switch
   windows).
3. Press **Start typing**.
4. **Click into the document/app you want it typed into** before the countdown
   reaches zero.
5. It types there like a human — variable speed, the odd typo backspaced and
   corrected, pauses at punctuation. Use **Pause** or **Stop** any time.

Because it sends real keystrokes to whatever window is focused, the countdown is
how it "hands off" to your target app — just click into that app while it counts
down.

## Run from source instead (optional, for developers)

```bash
cd drip-writer/desktop
pip install -r requirements.txt
python drip_writer.py
```

## How the build works

`.github/workflows/build-drip-writer.yml` compiles `drip_writer.py` into a
standalone `DripWriter.exe` on a Windows runner (via PyInstaller) every time the
app changes, and publishes it to the `drip-writer-desktop` release. Trigger it
by hand any time from the repo's **Actions** tab → *Build Drip Writer desktop
app* → **Run workflow**.

## Notes & limits

- **Windows** build is provided here. The Python source also runs on macOS/Linux
  (`python drip_writer.py`), but macOS needs Accessibility permission and Linux
  works best on X11.
- It types into whatever is focused — it doesn't target a specific field, so
  don't click away to another window mid-type.
- Everything runs locally. No text leaves your computer.
