"""
Drip Writer — desktop app.

A small window: paste your text, press Start, and it types the text into
whatever program is focused (Google Docs in a browser, Word, Notepad, a chat
box — anything) using real operating-system keystrokes. It types like a human:
variable speed, the occasional typo that backspaces and corrects itself, and
natural pauses at punctuation.

Because it sends real keystrokes, after you press Start there is a short
countdown — click into the document you want it typed into before it hits zero.

Requires: pynput  (pip install pynput).  Standard library: tkinter, threading.
"""

import random
import threading
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

try:
    from pynput.keyboard import Controller, Key
except Exception:  # pragma: no cover - only hit if dependency missing
    Controller = None
    Key = None


# QWERTY neighbours, for realistic "fat finger" typos.
NEIGH = {
    "q": "wa", "w": "qeas", "e": "wrsd", "r": "etdf", "t": "ryfg", "y": "tugh",
    "u": "yihj", "i": "uojk", "o": "ipkl", "p": "ol",
    "a": "qwsz", "s": "awedxz", "d": "serfcx", "f": "drtgvc", "g": "ftyhbv",
    "h": "gyujnb", "j": "huikmn", "k": "jiolm", "l": "kop",
    "z": "asx", "x": "zsdc", "c": "xdfv", "v": "cfgb", "b": "vghn",
    "n": "bhjm", "m": "njk",
    "1": "2", "2": "13", "3": "24", "4": "35", "5": "46", "6": "57",
    "7": "68", "8": "79", "9": "80", "0": "9",
}


def wrong_char(ch):
    lo = ch.lower()
    opts = NEIGH.get(lo)
    if not opts:
        return None
    w = random.choice(opts)
    return w.upper() if ch != lo else w


def randn():
    """Rough normal-ish value in about -1..1."""
    return (sum(random.random() for _ in range(3)) / 3 - 0.5) * 2


class DripWriter:
    def __init__(self, root):
        self.root = root
        self.kb = Controller() if Controller else None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.worker = None

        root.title("Drip Writer")
        root.geometry("520x620")
        root.minsize(460, 560)

        pad = dict(padx=14, pady=(0, 10))

        tk.Label(root, text="Drip Writer", font=("Segoe UI", 16, "bold")).pack(
            anchor="w", padx=14, pady=(14, 0))
        tk.Label(
            root,
            text="Paste your text, press Start, then click into the app you want "
                 "it typed into before the countdown ends.",
            font=("Segoe UI", 9), fg="#555", wraplength=490, justify="left",
        ).pack(anchor="w", padx=14, pady=(2, 12))

        self.text = scrolledtext.ScrolledText(root, height=8, wrap="word",
                                              font=("Segoe UI", 10))
        self.text.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        # sliders
        self.wpm = tk.IntVar(value=55)
        self.err = tk.IntVar(value=4)
        self.vary = tk.IntVar(value=35)
        self.delay = tk.IntVar(value=5)
        self._slider("Speed (words per minute)", self.wpm, 15, 140, **pad)
        self._slider("Typo rate (%)", self.err, 0, 20, **pad)
        self._slider("Rhythm variance (%)", self.vary, 0, 80, **pad)
        self._slider("Start delay — seconds to switch windows", self.delay, 2, 15, **pad)

        # toggles
        self.punct = tk.BooleanVar(value=True)
        self.think = tk.BooleanVar(value=True)
        self.fix = tk.BooleanVar(value=True)
        togs = tk.Frame(root)
        togs.pack(anchor="w", padx=12, pady=(0, 8))
        tk.Checkbutton(togs, text="Pause at punctuation", variable=self.punct).grid(row=0, column=0, sticky="w")
        tk.Checkbutton(togs, text="Thinking pauses", variable=self.think).grid(row=0, column=1, sticky="w", padx=8)
        tk.Checkbutton(togs, text="Fix typos", variable=self.fix).grid(row=0, column=2, sticky="w")

        # buttons
        btns = tk.Frame(root)
        btns.pack(fill="x", padx=12, pady=(2, 6))
        self.start_btn = tk.Button(btns, text="Start typing", command=self.start,
                                   bg="#2f6bff", fg="white", font=("Segoe UI", 10, "bold"),
                                   activebackground="#2559d8", relief="flat", padx=12, pady=6)
        self.start_btn.pack(side="left")
        self.pause_btn = tk.Button(btns, text="Pause", command=self.toggle_pause,
                                   state="disabled", relief="flat", padx=12, pady=6)
        self.pause_btn.pack(side="left", padx=6)
        self.stop_btn = tk.Button(btns, text="Stop", command=self.stop,
                                  state="disabled", relief="flat", padx=12, pady=6)
        self.stop_btn.pack(side="left")

        self.status = tk.StringVar(value="Ready.")
        self.status_lbl = tk.Label(root, textvariable=self.status, anchor="w",
                                   fg="#2f7d3a", font=("Segoe UI", 9))
        self.status_lbl.pack(fill="x", padx=14, pady=(2, 12))

        if self.kb is None:
            messagebox.showerror(
                "Missing dependency",
                "This app needs the 'pynput' library to send keystrokes.\n\n"
                "Install it with:  pip install pynput")

    def _slider(self, label, var, lo, hi, **pad):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", **pad)
        top = tk.Frame(frame)
        top.pack(fill="x")
        tk.Label(top, text=label, font=("Segoe UI", 9)).pack(side="left")
        val = tk.Label(top, textvariable=var, font=("Segoe UI", 9, "bold"))
        val.pack(side="right")
        ttk.Scale(frame, from_=lo, to=hi, variable=var,
                  command=lambda e, v=var: v.set(int(float(e)))).pack(fill="x")

    # ---- control ----------------------------------------------------------
    def set_status(self, msg, color="#2f7d3a"):
        self.root.after(0, lambda: (self.status.set(msg),
                                    self.status_lbl.config(fg=color)))

    def start(self):
        if self.kb is None:
            return
        if self.worker and self.worker.is_alive():
            return
        text = self.text.get("1.0", "end-1c")
        if not text.strip():
            self.set_status("Paste some text first.", "#b00")
            return
        self.stop_event.clear()
        self.pause_event.clear()
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="Pause")
        self.stop_btn.config(state="normal")
        self.worker = threading.Thread(target=self._run, args=(text,), daemon=True)
        self.worker.start()

    def toggle_pause(self):
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_btn.config(text="Pause")
            self.set_status("Typing…")
        else:
            self.pause_event.set()
            self.pause_btn.config(text="Resume")
            self.set_status("Paused.", "#996b00")

    def stop(self):
        self.stop_event.set()
        self.pause_event.clear()

    def _finish(self, msg, color="#2f7d3a"):
        self.set_status(msg, color)
        self.root.after(0, lambda: (
            self.start_btn.config(state="normal"),
            self.pause_btn.config(state="disabled", text="Pause"),
            self.stop_btn.config(state="disabled")))

    # ---- typing engine ----------------------------------------------------
    def _interruptible_sleep(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            if self.stop_event.is_set():
                return False
            while self.pause_event.is_set():
                if self.stop_event.is_set():
                    return False
                time.sleep(0.05)
                end += 0.05  # don't count paused time
            time.sleep(min(0.02, max(0, end - time.time())))
        return not self.stop_event.is_set()

    def _base_delay(self):
        return 60.0 / (max(5, self.wpm.get()) * 5)  # seconds per char

    def _jitter(self, secs):
        v = self.vary.get() / 100.0
        return max(0.008, secs * (1 + randn() * v))

    def _emit(self, ch):
        self.kb.type(ch)

    def _backspace(self):
        self.kb.press(Key.backspace)
        self.kb.release(Key.backspace)

    def _type_error(self, correct):
        style = random.random()
        bd = self._base_delay()
        fix = self.fix.get()
        if style < 0.6:
            w = wrong_char(correct)
            if w is None:
                return False
            self._emit(w)
            if not fix:
                return True
            if not self._interruptible_sleep(self._jitter(bd * (1.6 + random.random() * 2))):
                return True
            self._backspace()
            self._interruptible_sleep(self._jitter(bd * 0.7))
            self._emit(correct)
            return True
        if style < 0.8:
            self._emit(correct)
            self._emit(correct)
            if not fix:
                self._backspace()
                return True
            if not self._interruptible_sleep(self._jitter(bd * (1.4 + random.random() * 1.5))):
                return True
            self._backspace()
            return True
        w = wrong_char(correct)
        if w is None:
            return False
        self._emit(w)
        if not fix:
            self._emit(correct)
            return True
        if not self._interruptible_sleep(self._jitter(bd * (1.5 + random.random() * 1.6))):
            return True
        self._backspace()
        self._interruptible_sleep(self._jitter(bd * 0.7))
        self._emit(correct)
        return True

    def _run(self, text):
        # countdown so the user can click into the target window
        for s in range(self.delay.get(), 0, -1):
            if self.stop_event.is_set():
                self._finish("Stopped.", "#996b00")
                return
            self.set_status(f"Click into your document… typing in {s}", "#2f6bff")
            time.sleep(1)
        if self.stop_event.is_set():
            self._finish("Stopped.", "#996b00")
            return

        self.set_status("Typing…")
        err_rate = self.err.get() / 100.0
        total = len(text)
        try:
            for i, ch in enumerate(text):
                if self.stop_event.is_set():
                    self._finish("Stopped.", "#996b00")
                    return
                while self.pause_event.is_set():
                    if self.stop_event.is_set():
                        self._finish("Stopped.", "#996b00")
                        return
                    time.sleep(0.05)

                is_ld = ch.isalnum() and ch.isascii()
                if is_ld and random.random() < err_rate:
                    if self._type_error(ch):
                        self._interruptible_sleep(self._jitter(self._base_delay()))
                        if i % 8 == 0:
                            self.set_status(f"Typing… {round(i / total * 100)}%")
                        continue

                self._emit(ch)
                d = self._base_delay()
                if ch == " ":
                    d *= 1.15
                if self.punct.get():
                    if ch in ".!?":
                        d *= 6 + random.random() * 6
                    elif ch in ",;:":
                        d *= 2.5 + random.random() * 2
                    elif ch == "\n":
                        d *= 4
                if not self._interruptible_sleep(self._jitter(d)):
                    self._finish("Stopped.", "#996b00")
                    return
                if self.think.get() and ch == " " and random.random() < 0.03:
                    self._interruptible_sleep(self._jitter(self._base_delay() * (6 + random.random() * 10)))
                if i % 8 == 0:
                    self.set_status(f"Typing… {round(i / total * 100)}%")
            self._finish("Done ✓")
        except Exception as exc:  # pragma: no cover
            self._finish(f"Error: {exc}", "#b00")


def main():
    root = tk.Tk()
    DripWriter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
