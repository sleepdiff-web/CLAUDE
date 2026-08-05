"""
Build the Northpoint Digital Innovation Fund six-year performance deck.

FINC13-303 Assignment 2, Part 1 — Portfolio Performance Online Presentation.
Produces a 16:9 PowerPoint with speaker notes on every slide.
"""
import json, os
import pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)          # repository sub-directory root
DATA = os.path.join(BASE, "data")
CH = os.path.join(BASE, "charts")
IMG = os.path.join(BASE, "img")
OUT = os.path.join(BASE, "deliverables")
os.makedirs(OUT, exist_ok=True)
R = json.load(open(os.path.join(DATA, "results.json")))
ST, SS = R["stats"], R["stock_stats"]
REG = R["reg"]
ANN = pd.read_csv(os.path.join(DATA, "annual.csv"), index_col=0)

N, Q, S = "NDIF", "NASDAQ-100 (QQQ)", "S&P 500 (SPY)"
EW, MV = "Equal weight (1/N)", "MV optimised (ex-ante 2014-16)"
SIXTY = "60/40 (SPY/AGG)"

# ------------------------------------------------------------------ design tokens
NAVY   = RGBColor(0x0B, 0x25, 0x45)
NAVY_D = RGBColor(0x07, 0x18, 0x2E)
BLUE   = RGBColor(0x2A, 0x78, 0xD6)
ORANGE = RGBColor(0xEB, 0x68, 0x34)
AQUA   = RGBColor(0x1B, 0xAF, 0x7A)
RED    = RGBColor(0xE3, 0x49, 0x48)
GOLD   = RGBColor(0xC9, 0xA2, 0x27)
INK    = RGBColor(0x0B, 0x0B, 0x0B)
INK2   = RGBColor(0x52, 0x51, 0x4E)
INK3   = RGBColor(0x86, 0x84, 0x7E)
RULE   = RGBColor(0xE6, 0xE5, 0xE1)
SURF   = RGBColor(0xFC, 0xFC, 0xFB)
TINT   = RGBColor(0xF2, 0xF6, 0xFC)
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
FONT   = "Calibri"

W, H = Inches(13.333), Inches(7.5)
ML, MR = Inches(0.62), Inches(0.62)
CW = W - ML - MR

prs = Presentation()
prs.slide_width, prs.slide_height = W, H
BLANK = prs.slide_layouts[6]

def _tf(shape, size, color, bold=False, align=PP_ALIGN.LEFT, space_after=0,
        line=1.0, italic=False):
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    return tf, p

def textbox(slide, x, y, w, h, text, size=14, color=INK, bold=False,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line=1.05, italic=False,
            font=FONT):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text.split("\n") if isinstance(text, str) else text
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
        r.font.color.rgb = color; r.font.name = font
    return tb

def rect(slide, x, y, w, h, fill, line=None, lw=0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    return sh

SLIDE_NO = [0]
FOOTER = "Northpoint Digital Innovation Fund  ·  Six-year performance review, Jan 2017 – Dec 2022"

def slide(title=None, kicker=None, footer=True, number=True):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill; bg.solid(); bg.fore_color.rgb = SURF
    if title:
        textbox(s, ML, Inches(0.44), CW, Inches(0.55), title, size=27, color=NAVY, bold=True)
        rect(s, ML, Inches(1.06), Inches(0.62), Inches(0.045), GOLD)
    if kicker:
        textbox(s, ML, Inches(1.22), CW, Inches(0.42), kicker, size=13.5, color=INK2, line=1.2)
    SLIDE_NO[0] += 1
    if footer:
        rect(s, ML, Inches(6.86), CW, Inches(0.012), RULE)
        textbox(s, ML, Inches(6.99), Inches(9.0), Inches(0.3), FOOTER, size=8.5, color=INK3)
        if number:
            textbox(s, W - MR - Inches(1.0), Inches(6.99), Inches(1.0), Inches(0.3),
                    str(SLIDE_NO[0]), size=8.5, color=INK3, align=PP_ALIGN.RIGHT)
    return s

def notes(s, text):
    s.notes_slide.notes_text_frame.text = text.strip()

def fit(s, name, top, bottom, left=ML, right=None, valign="middle"):
    """Scale a chart to the largest size that fits the given box, then centre it."""
    path = os.path.join(CH, name) if not os.path.isabs(name) else name
    iw, ih = Image.open(path).size
    ar = iw / ih
    right = (W - MR) if right is None else right
    bw, bh = right - left, bottom - top
    w = min(bw, Emu(int(bh * ar)))
    h = Emu(int(w / ar))
    x = Emu(int(left + (bw - w) / 2))
    y = top if valign == "top" else Emu(int(top + (bh - h) / 2))
    return s.shapes.add_picture(path, x, y, w, h)

def picture(s, name, top, height=None, left=None, width=None):
    path = os.path.join(CH, name) if not os.path.isabs(name) else name
    iw, ih = Image.open(path).size
    ar = iw / ih
    if height is not None and width is None:
        h = height; w = Emu(int(h * ar))
    elif width is not None and height is None:
        w = width; h = Emu(int(w / ar))
    else:
        w, h = width, height
    if left is None:
        left = Emu(int((W - w) / 2))
    return s.shapes.add_picture(path, left, top, w, h)

def kpi(s, x, y, w, h, value, label, sub=None, color=NAVY, accent=BLUE):
    rect(s, x, y, w, h, WHITE, RULE)
    rect(s, x, y, w, Inches(0.055), accent)
    textbox(s, x + Inches(0.22), y + Inches(0.30), w - Inches(0.44), Inches(0.7),
            value, size=30, color=color, bold=True)
    textbox(s, x + Inches(0.22), y + Inches(0.94), w - Inches(0.44), Inches(0.44),
            label, size=10, color=INK2, bold=True, line=1.15)
    if sub:
        textbox(s, x + Inches(0.22), y + Inches(1.42), w - Inches(0.44), Inches(0.66),
                sub, size=9.5, color=INK3, line=1.18)

def bullets(s, x, y, w, items, size=13, gap=Inches(0.06), color=INK, bold_lead=True):
    """items: list of (lead, body) or plain strings."""
    cy = y
    for it in items:
        if isinstance(it, tuple):
            lead, body = it
        else:
            lead, body = None, it
        tb = s.shapes.add_textbox(x, cy, w, Inches(0.3))
        tf = tb.text_frame; tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]; p.line_spacing = 1.22
        if lead:
            r = p.add_run(); r.text = lead + "  "
            r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = NAVY
            r.font.name = FONT
        r = p.add_run(); r.text = body
        r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = FONT
        chars = len(lead or "") * 1.06 + len(body)
        per_line = max(12.0, (w / Inches(1)) * 148.0 / size)
        nlines = max(1, int(chars / per_line) + (1 if chars % per_line else 0))
        est = Inches(nlines * size * 1.24 / 72.0)
        tb.height = est
        cy = cy + est + gap
    return cy

def table(s, x, y, w, rows, col_w=None, header=True, size=11, row_h=Inches(0.34),
          align=None, head_fill=NAVY, zebra=True, first_bold=False):
    nr, nc = len(rows), len(rows[0])
    gt = s.shapes.add_table(nr, nc, x, y, w, row_h * nr).table
    if col_w:
        total = sum(col_w)
        for i, cwid in enumerate(col_w):
            gt.columns[i].width = Emu(int(w * cwid / total))
    for i, row in enumerate(rows):
        gt.rows[i].height = row_h
        for j, val in enumerate(row):
            c = gt.cell(i, j)
            c.text = ""
            c.margin_left = Inches(0.09); c.margin_right = Inches(0.09)
            c.margin_top = Inches(0.03); c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = (PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT) if align is None \
                else align[j]
            r = p.add_run(); r.text = str(val)
            r.font.name = FONT
            if i == 0 and header:
                r.font.size = Pt(size - 0.5); r.font.bold = True; r.font.color.rgb = WHITE
                c.fill.solid(); c.fill.fore_color.rgb = head_fill
            else:
                r.font.size = Pt(size)
                r.font.color.rgb = INK
                r.font.bold = first_bold and j == 0
                c.fill.solid()
                c.fill.fore_color.rgb = TINT if (zebra and i % 2 == 0) else WHITE
    gt.first_row = header
    gt.horz_banding = False
    return gt

def pct(v, d=1, sign=False):
    return f"{v*100:+,.{d}f}%" if sign else f"{v*100:,.{d}f}%"

def section(title, num, blurb):
    s = prs.slides.add_slide(BLANK)
    bg = s.background.fill; bg.solid(); bg.fore_color.rgb = NAVY
    SLIDE_NO[0] += 1
    textbox(s, ML, Inches(2.55), Inches(1.4), Inches(0.6), num, size=54, color=GOLD, bold=True)
    rect(s, ML, Inches(3.42), Inches(0.9), Inches(0.045), GOLD)
    textbox(s, ML, Inches(3.72), Inches(9.6), Inches(0.9), title, size=34, color=WHITE, bold=True)
    textbox(s, ML, Inches(4.62), Inches(8.6), Inches(0.8), blurb, size=14,
            color=RGBColor(0xB8, 0xC6, 0xD8), line=1.25)
    return s

# =============================================================================== 1
s = prs.slides.add_slide(BLANK)
bg = s.background.fill; bg.solid(); bg.fore_color.rgb = NAVY
SLIDE_NO[0] += 1
rect(s, Inches(0), Inches(0), Inches(0.11), H, GOLD)
textbox(s, Inches(0.95), Inches(1.28), Inches(9.0), Inches(0.4), "N O R T H P O I N T",
        size=15, color=GOLD, bold=True)
textbox(s, Inches(0.95), Inches(1.86), Inches(11.2), Inches(1.9),
        "Northpoint Digital\nInnovation Fund", size=46, color=WHITE, bold=True, line=1.06)
rect(s, Inches(0.95), Inches(3.86), Inches(1.15), Inches(0.05), GOLD)
textbox(s, Inches(0.95), Inches(4.16), Inches(11.0), Inches(0.9),
        "Six-year performance review  ·  January 2017 – December 2022\n"
        "Final report to investors  ·  New York · San Francisco · London · Hong Kong · Shanghai · Sydney",
        size=15.5, color=RGBColor(0xB8, 0xC6, 0xD8), line=1.35)
textbox(s, Inches(0.95), Inches(5.72), Inches(9.6), Inches(1.1),
        "Callum O'Connor  ·  Portfolio Manager\n"
        "Student ID 14053836  ·  FINC13-303 Portfolio Analysis and Investments  ·  Bond University",
        size=12, color=RGBColor(0x9A, 0xAC, 0xC2), line=1.35)
rect(s, Inches(9.55), Inches(1.86), Inches(2.85), Inches(2.62), NAVY_D)
textbox(s, Inches(9.85), Inches(2.10), Inches(2.3), Inches(0.3), "MANDATE OUTCOME",
        size=9.5, color=GOLD, bold=True)
textbox(s, Inches(9.85), Inches(2.48), Inches(2.3), Inches(0.6), "$279m", size=34,
        color=WHITE, bold=True)
textbox(s, Inches(9.85), Inches(3.06), Inches(2.35), Inches(1.3),
        "from a $100 million\nmandate\n\n+179.2% cumulative\n18.7% p.a.", size=11.5,
        color=RGBColor(0xB8, 0xC6, 0xD8), line=1.3)
notes(s, """
Good morning, afternoon or evening, depending on where you're joining me from. I'm Callum
O'Connor, Portfolio Manager of the Northpoint Digital Innovation Fund.

Six years ago you gave this fund a hundred million dollars and one instruction: own the winners of
digital transformation across the whole economy, and do it with discipline. Today I'm closing the
book on that mandate.

The headline is on the right of your screen. That hundred million is now two hundred and
seventy-nine million, a hundred and seventy-nine per cent cumulative, or eighteen point seven per
cent a year, through a trade war, a pandemic, the fastest bear market in history, and the sharpest
rate shock in forty years.

Over the next twenty-five minutes I'll show you where that money came from, how much risk we took
to get it, whether it was skill or simply a rising market, and what I think you should do next.
""")

# =============================================================================== 2
s = slide("Agenda", "Six sections, twenty-five minutes, then questions")
items = [
    ("1", "Where we started", "The mandate, the theme, and how the fund was actually run"),
    ("2", "The economy we lived through", "Six years, three regimes, and how our 2016 scenarios held up"),
    ("3", "What the fund returned", "Wealth created, benchmarked, and stress-tested through COVID and 2022"),
    ("4", "How much risk we took", "Distribution, risk-adjusted returns, tail risk, and seasonality"),
    ("5", "Was it skill?", "Jensen's alpha, factor models, attribution, and the optimised counterfactual"),
    ("6", "The verdict", "Objective scorecard, fees, and our recommendation on the fund's future"),
]
y = Inches(1.92)
for num, head, sub in items:
    rect(s, ML, y, CW, Inches(0.66), WHITE, RULE)
    rect(s, ML, y, Inches(0.055), Inches(0.66), BLUE)
    textbox(s, ML + Inches(0.30), y + Inches(0.18), Inches(0.5), Inches(0.34), num,
            size=15, color=GOLD, bold=True)
    textbox(s, ML + Inches(0.85), y + Inches(0.17), Inches(3.5), Inches(0.34), head,
            size=14.5, color=NAVY, bold=True)
    textbox(s, ML + Inches(4.5), y + Inches(0.20), Inches(7.4), Inches(0.34), sub,
            size=12, color=INK2)
    y = y + Inches(0.78)
notes(s, """
Six sections.

Where we started, the mandate, and whether we stuck to it. The economy, three regimes in six
years, and an honest mark against the scenarios we published in 2016. What the fund returned, and
how it behaved in the two moments that mattered. How much risk we took. Then the section I care
most about: was any of this skill? And finally the verdict, the fees, and my recommendation.

Questions at the end. There's a full appendix behind the deck with the workings.
""")

# =============================================================================== 3
s = slide("The six-year result", "Every figure on this slide is calculated from 72 months of "
          "dividend-adjusted total returns and is reproduced in the appendix")
kw, gap = Inches(2.94), Inches(0.15)
row_y = Inches(1.82)
kpi(s, ML, row_y, kw, Inches(2.16), "+179.2%", "CUMULATIVE RETURN",
    "$100m mandate grew to $279.2m.\nS&P 500 returned +90.0%;\nNASDAQ-100 +134.7%.", accent=BLUE)
kpi(s, ML + (kw + gap), row_y, kw, Inches(2.16), "18.7%", "ANNUALISED RETURN",
    "Against a target of 8–10% net p.a.\nS&P 500 11.3%; NASDAQ-100 15.3%.", accent=BLUE)
kpi(s, ML + 2 * (kw + gap), row_y, kw, Inches(2.16), "0.94", "SHARPE RATIO",
    "Highest of every comparator.\nNASDAQ-100 0.75; S&P 500 0.65.\nSortino 1.51.", accent=AQUA)
kpi(s, ML + 3 * (kw + gap), row_y, kw, Inches(2.16), "-24.9%", "MAXIMUM DRAWDOWN",
    "Shallower than our own benchmark.\nNASDAQ-100 fell 32.6%.", accent=ORANGE)
row_y2 = Inches(4.16)
kpi(s, ML, row_y2, kw, Inches(2.16), "6.6%", "ALPHA p.a. (FF5)",
    "Fama–French five-factor Jensen's\nalpha, t = 3.06, p = 0.002.\nStatistically significant.", accent=GOLD)
kpi(s, ML + (kw + gap), row_y2, kw, Inches(2.16), "1.04", "BETA TO THE MARKET",
    "Market-like sensitivity.\nThe excess return is not\nsimply leverage on the index.", accent=AQUA)
kpi(s, ML + 2 * (kw + gap), row_y2, kw, Inches(2.16), "0.98", "INFORMATION RATIO",
    "Active return per unit of\ntracking error vs the S&P 500\n(6.98% tracking error).", accent=BLUE)
kpi(s, ML + 3 * (kw + gap), row_y2, kw, Inches(2.16), "50 / 72", "POSITIVE MONTHS",
    "A 69.4% hit rate.\nAverage up month +4.6%,\naverage down month −5.2%.", accent=BLUE)
notes(s, """
The whole six years on one slide.

Top left: a hundred and seventy-nine per cent cumulative. The S&P 500 returned ninety over the same
window; the NASDAQ-100, our primary benchmark and the harder test, returned a hundred and
thirty-five. Annualised, eighteen point seven per cent against a target of eight to ten.

But look at the second row as much as the first. A Sharpe ratio of nought point nine four, the
highest of every comparator I tested. A maximum drawdown of minus twenty-four point nine per cent,
shallower than the NASDAQ-100's thirty-two point six. We didn't simply take more risk to get more
return.

And the number I'd draw your attention to above all: six point six per cent annualised alpha on a
five-factor model, t-statistic three point zero six. The probability that's luck is about two in a
thousand, with a beta of one, so it wasn't leverage either.

I'll earn every one of those claims.
""")

# =============================================================================== 4
s = section("Where we started", "01",
            "The mandate you funded in 2016, the eleven positions we bought, and whether we stayed "
            "faithful to the brief")

# =============================================================================== 5
s = slide("The mandate you funded", "Nothing in the strategy changed over six years. The discipline "
          "was in the rules, not in the reacting")
rows = [["Mandate parameter", "What we committed to in January 2016"],
        ["Capital", "US$100 million, six-year fund life (Jan 2017 – Dec 2022)"],
        ["Strategy", "Active, high-conviction thematic equity — technology and innovation"],
        ["Theme", "Digital transformation: cloud, mobile data, payments, automation, genomics"],
        ["Holdings", "Eleven US-listed stocks — exactly one per GICS sector"],
        ["Weighting", "Conviction tiers, 5% floor per sector, 16% cap on the largest position"],
        ["Rebalancing", "Quarterly, plus a 5-percentage-point drift threshold; mid-life review at end-2019"],
        ["Primary benchmark", "NASDAQ-100 (theme-aligned — measures selection skill within the theme)"],
        ["Secondary benchmark", "S&P 500 (broad market — measures whether the theme was worth owning)"],
        ["Fees", "0.90% p.a. management + 10% of returns over the hurdle, high-water mark"],
        ["Return target", "8–10% net p.a., roughly 55–70% cumulative net over the fund life"]]
table(s, ML, Inches(1.86), CW, rows, col_w=[27, 73], size=11.5, row_h=Inches(0.40),
      align=[PP_ALIGN.LEFT, PP_ALIGN.LEFT])
notes(s, """
This is the contract, unedited, because the first test of a manager isn't performance. It's
whether the thing you bought is the thing you got.

An active, high-conviction thematic equity fund. The theme: digital transformation. Eleven
holdings, one per GICS sector, a pure technology fund would have been an easier story to sell, but
it would have failed the diversification requirement, and as you'll see, it would have hurt badly
in 2022.

Two hard constraints on the weights: a five per cent floor in every sector, and a sixteen per cent
cap on the largest position. Quarterly rebalancing with a five-point drift threshold.

And the target: eight to ten per cent net a year. Hold that number, I'm going to mark ourselves
against it at the end.
""")

# =============================================================================== 6
s = slide("Eleven sectors, one idea",
          "The theme was expressed through conviction tiers, never by abandoning a sector")
fit(s, "26_weights_donut.png", Inches(1.64), Inches(6.62), left=ML, right=ML + Inches(5.15))
tx = ML + Inches(5.42)
textbox(s, tx, Inches(1.72), Inches(7.0), Inches(0.35), "HOW THE BOOK WAS BUILT",
        size=10.5, color=GOLD, bold=True)
bullets(s, tx, Inches(2.10), Inches(6.98), [
    ("Tier 1, 42%.", "Microsoft, Alphabet and Amazon: the platform companies where the cloud, "
     "advertising and e-commerce theses all compound at once. Highest conviction, largest weights."),
    ("Tier 2, 34%.", "Visa, Equinix, Illumina and Rockwell: the enablers. Each monetises "
     "digitisation in one specific channel — payments, data centres, genomics, factory automation."),
    ("Tier 3, 24%.", "NextEra, Costco, Albemarle and Schlumberger: diversification and ballast, "
     "each still carrying an innovation or recovery angle."),
    ("The floor mattered.", "Energy at 5% and Materials at 6% looked like drag for five years. "
     "In 2022 they were the two reasons our drawdown ran ten points shallower than the NASDAQ's."),
], size=12, gap=Inches(0.22))
notes(s, """
The book, coloured by conviction tier.

Tier one: forty-two per cent in three platform companies where several parts of the thesis compound
at once. Microsoft at sixteen per cent was our largest position and our highest-conviction idea.

Tier two, thirty-four per cent: the enablers. Each monetises digitisation through one channel —
Visa is payments, Equinix is data centres, Illumina is genomics, Rockwell is factory automation.

Tier three, twenty-four per cent: ballast.

Now, the fourth point is the one I'd ask you to remember. For five of these six years, holding
Schlumberger at five per cent looked like a tax on the portfolio. I was asked repeatedly why we
didn't just drop the sector. We didn't, because the mandate said every sector keeps a floor. In
2022 that discipline is exactly what saved us.
""")

# =============================================================================== 7
s = slide("We rebalanced. That was a decision, and it paid.",
          "Quarterly rebalancing added 1.3 percentage points a year over letting the winners run")
fit(s, "21_weight_drift.png", Inches(1.66), Inches(5.74))
rows = [["", "Cumulative", "CAGR", "Sharpe", "Max drawdown", "Terminal on $100m"],
        ["Quarterly rebalanced (as run)", pct(ST[N]["cum_return"]), pct(ST[N]["cagr"]),
         f"{ST[N]['sharpe']:.2f}", pct(ST[N]["max_dd"]), f"${ST[N]['terminal']/1e6:,.0f}m"],
        ["Left to drift (buy & hold)", pct(ST["NDIF (buy & hold)"]["cum_return"]),
         pct(ST["NDIF (buy & hold)"]["cagr"]), f"{ST['NDIF (buy & hold)']['sharpe']:.2f}",
         pct(ST["NDIF (buy & hold)"]["max_dd"]),
         f"${ST['NDIF (buy & hold)']['terminal']/1e6:,.0f}m"]]
table(s, ML, Inches(5.88), CW, rows, col_w=[30, 14, 12, 12, 16, 16], size=11,
      row_h=Inches(0.30), first_bold=True)
notes(s, """
A short detour on process, because this is where funds quietly drift from their mandate.

On the left: what would have happened if we'd bought the eleven stocks and never touched them. Tier
one would have grown from forty-two per cent of the book to forty-eight, with Microsoft alone at
twenty-five per cent. You'd have ended up owning a concentrated mega-cap technology fund that no
longer resembled the mandate you signed.

On the right: what we actually did.

And look at the table. Rebalancing wasn't governance theatre, it was worth eighteen million
dollars. Two seventy-nine versus two sixty-one. One point three points a year of extra return, a
higher Sharpe, and a drawdown three points shallower, because rebalancing systematically trimmed
winners at highs and topped up laggards at lows.
""")

# =============================================================================== 8
s = section("The economy we lived through", "02",
            "Three distinct regimes in six years — and an honest mark-to-market of the scenarios we "
            "published in January 2016")

# =============================================================================== 9
s = slide("Six years, seven turning points",
          "The events that shaped the fund, plotted against the wealth they created or destroyed")
fit(s, "02_growth_events.png", Inches(1.68), Inches(6.72))
notes(s, """
The whole six years in one line.

We opened in January 2017 with the Dow crossing twenty thousand. Through 2017 the fund returned
forty per cent, driven by the December tax reform and by cloud adoption accelerating exactly as
we'd argued.

2018 was our first hard year, the trade war escalated and the fourth quarter was brutal. We lost
nine point six per cent in October and nine point eight in December, and still finished up three
point seven while the S&P fell four and a half.

2019 was the recovery on the Fed's pivot to cutting. Then March 2020, which I'll come back to.

The fund peaked in December 2021 at three hundred and sixty million dollars, within weeks of the
Fed abandoning the word "transitory". 2022 gave a chunk of it back.
""")

# ============================================================================== 10
s = slide("The macro backdrop, regime by regime",
          "How the state of the economy translated into the portfolio's returns")
cardw = Emu(int((CW - Inches(0.30)) / 2))
heads = [("2017 – 2019", "SYNCHRONISED GROWTH", BLUE,
          [("2017: +40.0%", "Synchronised global growth, benign inflation, a gradual Fed. US tax "
            "reform cut the corporate rate from 35% to 21%, lifting after-tax earnings across the book."),
           ("2018: +3.7%", "Trade-war escalation and a hawkish Fed produced a violent Q4. We lost "
            "9.6% in October and 9.8% in December — and still finished positive while the S&P fell 4.6%."),
           ("2019: +36.6%", "The Fed pivoted to cutting. Multiple expansion did most of the work; "
            "cloud and payments earnings kept compounding underneath it.")]),
         ("2020 – 2022", "PANDEMIC, STIMULUS, THEN THE RATE SHOCK", ORANGE,
          [("2020: +37.1%", "The COVID crash took 12.6% off the fund in two months. Then the "
            "pandemic became the single largest accelerant our thesis ever received: remote work, "
            "e-commerce and cloud migration pulled forward by years."),
           ("2021: +32.5%", "Reopening, record stimulus and peak growth valuations. Our thesis was "
            "consensus by now — which is usually the warning sign, and it was."),
           ("2022: −22.5%", "The sharpest tightening cycle since 1981. CPI peaked at 9.1%; the Fed "
            "raised 425bp. Long-duration growth equity de-rated hardest. Our energy and materials "
            "ballast is why we fell 10 points less than the NASDAQ-100.")])]
x = ML
for hd, sub, col, items in heads:
    rect(s, x, Inches(1.80), cardw, Inches(0.72), WHITE, RULE)
    rect(s, x, Inches(1.80), Inches(0.055), Inches(0.72), col)
    textbox(s, x + Inches(0.24), Inches(1.92), Inches(4.0), Inches(0.3), hd, size=17,
            color=NAVY, bold=True)
    textbox(s, x + Inches(0.24), Inches(2.21), Inches(5.8), Inches(0.26), sub, size=9.5,
            color=INK3, bold=True)
    bullets(s, x + Inches(0.24), Inches(2.76), cardw - Inches(0.48), items, size=12,
            gap=Inches(0.20))
    x = x + cardw + Inches(0.30)
notes(s, """
Some economic narrative, because you're not paying me to read a line chart to you.

The first three years were broadly the world we said we expected: moderate growth, contained
inflation, a gradual Fed, and spending shifting steadily toward cloud, mobile and payments. 2018
was the exception: the trade war was a risk we'd flagged but sized wrongly.

The second three years are more interesting. If you go back to our 2016 Scenario C, we wrote, and
I quote, "another systemic disruption such as a global pandemic." We put twenty per cent on it.
It happened.

And here's the part we got right for the right reason. We argued that even in a recession, cloud
migration and payment digitisation continue, because they're cost-saving. COVID didn't slow our
theme. It accelerated it by years.

2022 tested the diversification rather than the theme. When the discount rate goes from zero to
four and a quarter, long-duration growth equity is repriced. There was nowhere to hide inside the
theme, only the ballast helped.
""")

# ============================================================================== 11
s = slide("Marking our 2016 scenarios to market",
          "We were right about direction in five of six years, and consistently too conservative "
          "about magnitude")
fit(s, "25_scenario.png", Inches(1.66), Inches(5.44))
rows = [["Scenario (as published, Jan 2016)", "Assigned probability", "Assumed return p.a.",
         "Years it actually described", "Verdict"],
        ["A — Growth & digital acceleration", "50% ST / 40% MT", "+18%", "2017, 2018, 2020, 2021",
         "Occurred in 4 of 6 years"],
        ["B — Stagnation / low-growth grind", "30% ST / 30% MT", "+9%", "2019",
         "Understated: we returned 36.6%"],
        ["C — Recession / risk-off shock", "20% ST / 30% MT", "−4%", "2022",
         "Understated: we lost 22.5%"]]
table(s, ML, Inches(5.58), CW, rows, col_w=[27, 15, 13, 23, 22], size=10.5,
      row_h=Inches(0.30), first_bold=True,
      align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
notes(s, """
Most managers avoid this next slide. It holds up our own forecast and marks it against reality.

In 2016 we published three scenarios with explicit probabilities and returns. The pale bars are
what we said. The dark bars are what happened.

Two honest observations. We got the direction right in five of six years. But we were
systematically too conservative about magnitude in both directions. In 2017 we assumed eighteen
per cent and delivered forty; in 2019 we thought we were in a stagnation world worth nine and
delivered thirty-seven; and in 2022 we'd assumed a recession would cost four per cent, and it cost
twenty-two and a half.

The lesson: scenario frameworks are good at identifying which state of the world you're in, and
poor at telling you how violent it will be.
""")

# ============================================================================== 12
s = section("What the fund returned", "03",
            "Wealth created, benchmarked against the indices you are paying us to beat, and "
            "stress-tested through the two events that mattered")

# ============================================================================== 13
s = slide("A $100m mandate became $279m",
          "Ahead of the S&P 500 by 89 percentage points, and ahead of our own theme-aligned "
          "benchmark by 44")
fit(s, "01_growth.png", Inches(1.66), Inches(5.14))
rows = [["", "Cumulative", "CAGR", "Terminal value on $100m", "Value added vs NDIF"],
        ["Northpoint Digital Innovation Fund", pct(ST[N]["cum_return"]), pct(ST[N]["cagr"]),
         f"${ST[N]['terminal']/1e6:,.1f}m", "—"],
        ["NASDAQ-100 (primary benchmark)", pct(ST[Q]["cum_return"]), pct(ST[Q]["cagr"]),
         f"${ST[Q]['terminal']/1e6:,.1f}m", f"+${(ST[N]['terminal']-ST[Q]['terminal'])/1e6:,.1f}m"],
        ["S&P 500 (secondary benchmark)", pct(ST[S]["cum_return"]), pct(ST[S]["cagr"]),
         f"${ST[S]['terminal']/1e6:,.1f}m", f"+${(ST[N]['terminal']-ST[S]['terminal'])/1e6:,.1f}m"],
        ["60/40 stock/bond portfolio", pct(ST[SIXTY]["cum_return"]), pct(ST[SIXTY]["cagr"]),
         f"${ST[SIXTY]['terminal']/1e6:,.1f}m",
         f"+${(ST[N]['terminal']-ST[SIXTY]['terminal'])/1e6:,.1f}m"]]
table(s, ML, Inches(5.28), CW, rows, col_w=[34, 15, 12, 21, 18], size=11,
      row_h=Inches(0.30), first_bold=True)
notes(s, """
This is the chart the whole review rests on.

Blue is the fund, orange the NASDAQ-100, green the S&P 500.

Three things. First, we're above the NASDAQ-100 for essentially the whole period, and the gap
widens rather than narrows. Second, look at where the lines separate most: the right-hand end, in 2022. On the way up we tracked the benchmark closely; on the way down we fell much less. That
asymmetry is the whole argument for the construction.

Third, the table. Against the S&P 500, which any of you could have bought for nine basis points —
we added eighty-nine million dollars. Against the NASDAQ-100, the tougher test because it shares
our theme, forty-four million. Against a conventional sixty-forty, a hundred and twenty-seven
million.

I'm not going to pretend all of that is skill. Section five separates the two properly.
""")

# ============================================================================== 14
s = slide("Beat the S&P 500 in five of six years",
          "Including 2018 and 2022, the two years the market fell")
fit(s, "04_annual_bars.png", Inches(1.66), Inches(5.14))
yr_rows = [["Calendar year", "2017", "2018", "2019", "2020", "2021", "2022"],
           ["NDIF"] + [pct(ANN[N][y], 1) for y in ANN.index],
           ["NASDAQ-100"] + [pct(ANN[Q][y], 1) for y in ANN.index],
           ["S&P 500"] + [pct(ANN[S][y], 1) for y in ANN.index],
           ["NDIF vs S&P 500"] + [pct(ANN[N][y] - ANN[S][y], 1, sign=True) for y in ANN.index]]
table(s, ML, Inches(5.28), CW, yr_rows, col_w=[24, 12.7, 12.7, 12.7, 12.7, 12.7, 12.7],
      size=11, row_h=Inches(0.30), first_bold=True)
notes(s, """
Annual returns.

The pattern to take away isn't the size of the good years. It's the shape of the bad ones. In a
bull market a technology-tilted fund is supposed to have good years; there's nothing clever about
that.

The interesting years are 2018 and 2022. In 2018 the S&P lost four point six per cent and the
NASDAQ-100 was flat; we made three point seven. In 2022 the S&P lost eighteen and the NASDAQ-100
lost thirty-two point six; we lost twenty-two and a half.

Now, we underperformed the S&P by four points that year, and I won't dress that up. A
technology-tilted fund should lag the broad market when growth de-rates. But against our own theme
benchmark we outperformed by ten full points.

The only year we lagged the NASDAQ-100 was 2020, because concentration was rewarded and our sector
floors held us back. That's the cost of diversification, and 2022 is where you got paid for it.
""")

# ============================================================================== 15
s = slide("The value-add compounded quietly, then paid off",
          "Cumulative performance relative to both benchmarks, rebased to zero at inception")
fit(s, "23_relative.png", Inches(1.66), Inches(6.11))
textbox(s, ML, Inches(6.23), CW, Inches(0.5),
        "Read this as the wealth ratio between the fund and each benchmark. A rising line means the "
        "fund is pulling ahead. Note that most of the outperformance versus the NASDAQ-100 was "
        "created after November 2021 — that is, on the way down, not on the way up.",
        size=11, color=INK2, line=1.22)
notes(s, """
This strips out the market and shows only relative performance.

Against the S&P 500, in green, the line rises steadily. That's the theme working.

The orange line tells you something you won't get anywhere else. Against the NASDAQ-100 we were
roughly flat for the first four and a half years. We only decisively pulled ahead from November
2021.

Be clear about what that means. For most of this fund's life we did not beat our primary
benchmark, we tracked it. All of the outperformance against it was earned in the 2022 drawdown, by
falling less.

Some managers would present that as a weakness. I'd argue the opposite. Anyone can hold technology
stocks in a technology bull market. Capital preservation when the regime turns is the part that
requires an actual discipline, and 2022 is the year the fee earned itself.
""")

# ============================================================================== 16
s = slide("The fund fell less than its own benchmark",
          "Maximum drawdown of −24.9% against the NASDAQ-100's −32.6%")
fit(s, "03_drawdown.png", Inches(1.66), Inches(5.44))
rows = [["", "Maximum drawdown", "Peak month", "Trough month", "Calmar ratio",
         "Downside deviation"],
        ["NDIF", pct(ST[N]["max_dd"]), "Nov 2021", "Sep 2022", f"{ST[N]['calmar']:.2f}",
         pct(ST[N]["downside_dev"])],
        ["NASDAQ-100", pct(ST[Q]["max_dd"]), "Nov 2021", "Dec 2022", f"{ST[Q]['calmar']:.2f}",
         pct(ST[Q]["downside_dev"])],
        ["S&P 500", pct(ST[S]["max_dd"]), "Dec 2021", "Sep 2022", f"{ST[S]['calmar']:.2f}",
         pct(ST[S]["downside_dev"])]]
table(s, ML, Inches(5.58), CW, rows, col_w=[18, 18, 15, 15, 16, 18], size=11,
      row_h=Inches(0.30), first_bold=True)
notes(s, """
Drawdown determines whether an investor stays in a fund, so I will take it head on.

Our worst peak-to-trough loss was twenty-four point nine per cent, from November 2021 to September
2022. The NASDAQ-100 lost thirty-two point six. The S&P lost twenty-three point nine.

So we sat between the two, worse than the broad market, materially better than our own benchmark.
For a fund with a deliberate technology tilt, that is the right place to be.

The Calmar ratio in the table is return per unit of maximum drawdown: nought point seven five for
us against nought point four seven for both indices. A sixty per cent improvement in return per
unit of worst-case pain.
""")

# ============================================================================== 17
s = slide("Stress test one: COVID-19",
          "Scenario C arrived in March 2020. The fund lost 12.6% in two months and had recovered it "
          "within eight weeks")
fit(s, "28_covid.png", Inches(1.66), Inches(5.94))
textbox(s, ML, Inches(6.06), CW, Inches(0.72),
        "Our 2016 document had explicitly named “a systemic disruption such as a global "
        "pandemic” as a Scenario C trigger and assigned it a 20% probability. The thesis "
        "assumption that held up: cloud migration, e-commerce and payment digitisation are "
        "cost-saving, so they continue — and in fact accelerate — through a recession.",
        size=11, color=INK2, line=1.22)
notes(s, """
The first stress test.

February and March 2020 cost us twelve point six per cent. It felt considerably worse at the time,
because these are month-end figures.

Then look what happens. April 2020 was the best month in the fund's history at plus fourteen and a
half per cent. By May we were back above the January high, and 2020 finished up thirty-seven per
cent.

Two things follow from that. First, our 2016 document had literally named a global pandemic as a
Scenario C trigger. I'm not claiming we predicted COVID, I'm claiming that a framework which
forces you to name tail events stops you building a portfolio that only survives the base case.

Second, and more substantive: our core assumption was that digital transformation is cost-saving
and therefore continues in a recession. COVID tested that harder than anything we could have
designed, and the answer came back emphatically.
""")

# ============================================================================== 18
s = slide("Stress test two: the 2022 rate shock",
          "Down 22.5% against a NASDAQ-100 down 32.6%, and the ballast is the entire reason why")
fit(s, "24_2022.png", Inches(1.66), Inches(5.94))
textbox(s, ML, Inches(6.06), CW, Inches(0.72),
        "Schlumberger — the fund's worst holding over the full six years at −23.5% — returned "
        "+81.2% in 2022. Albemarle lost only 6.6% and NextEra 8.5%. Without the 5% energy floor and "
        "the 24% ballast tier, the fund's 2022 loss would have been close to the NASDAQ-100's. "
        "This is what a sector floor is for.",
        size=11, color=INK2, line=1.22)
notes(s, """
The second stress test, and the more instructive one.

2022 was the sharpest tightening since 1981, the Fed raised four hundred and twenty-five basis
points in a calendar year. When the discount rate moves that fast, long-duration growth equity gets
repriced, and there's no clever way around it.

We lost twenty-two and a half per cent. The NASDAQ-100 lost thirty-two point six.

The right-hand panel explains the ten-point difference. At the bottom: Amazon minus fifty, Illumina
minus forty-seven, Alphabet minus thirty-nine. Our thesis names were hit exactly as hard as you'd
expect.

Now look at the top. Schlumberger, plus eighty-one per cent. Visa down three. Albemarle down seven.

Schlumberger was, over six years, the worst holding in this fund. For five years it was the
position I was asked to justify most often. It was there for one reason: the mandate said every
sector gets a floor. In the worst year of the fund's life, that unloved five per cent returned
eighty-one per cent. That's what diversification is, and it's why the constraint was written into
the mandate rather than left to my discretion.
""")

# ============================================================================== 19
s = section("How much risk we took", "04",
            "The full distribution of 72 monthly returns, the risk-adjusted measures, tail risk, "
            "and where in the calendar the money was made")

# ============================================================================== 20
s = slide("The shape of our returns",
          "Close to normal, with a mild left tail. 72 monthly observations, Jan 2017 to Dec 2022")
fit(s, "05_histogram.png", Inches(1.72), Inches(6.40), left=ML, right=Inches(8.92))
tx = Inches(9.05)
rect(s, tx, Inches(1.86), Inches(3.66), Inches(4.32), WHITE, RULE)
textbox(s, tx + Inches(0.24), Inches(2.06), Inches(3.2), Inches(0.3),
        "DISTRIBUTIONAL STATISTICS", size=10, color=GOLD, bold=True)
dstats = [("Mean monthly return", pct(ST[N]["mean_m"], 2)),
          ("Median monthly return", pct(ST[N]["median_m"], 2)),
          ("Standard deviation (monthly)", pct(ST[N]["vol"] / (12 ** 0.5), 2)),
          ("Annualised volatility", pct(ST[N]["vol"], 2)),
          ("Skewness", f"{ST[N]['skew']:.3f}"),
          ("Excess kurtosis", f"{ST[N]['kurt']:.3f}"),
          ("Jarque–Bera p-value", f"{ST[N]['jb_p']:.3f}"),
          ("Best month (Apr 2020)", pct(ST[N]["best"], 1)),
          ("Worst month (Apr 2022)", pct(ST[N]["worst"], 1)),
          ("Positive months", f"{ST[N]['n_pos']} of 72  ({pct(ST[N]['hit'], 1)})")]
yy = Inches(2.46)
for k, v in dstats:
    textbox(s, tx + Inches(0.24), yy, Inches(2.4), Inches(0.26), k, size=11, color=INK2)
    textbox(s, tx + Inches(2.55), yy, Inches(0.92), Inches(0.26), v, size=11, color=NAVY,
            bold=True, align=PP_ALIGN.RIGHT)
    yy = yy + Inches(0.355)
notes(s, """
The quantitative section. Start with the raw distribution rather than a summary statistic, because a
summary statistic can hide a lot.

Seventy-two observations. Mean monthly return one point five nine per cent, median two point seven
three. The median well above the mean tells you immediately there's a left tail.

Skewness confirms it at minus nought point four seven, mild negative skew, normal for equities.
Excess kurtosis is essentially zero, so no fat tails. And Jarque-Bera returns a p-value of nought
point two eight, meaning we can't reject normality.

That matters practically: the parametric risk measures, standard deviation, Sharpe, normal-based
VaR, are trustworthy for this fund. That isn't true of every strategy.

Best month, April 2020, plus fourteen and a half. Worst, April 2022, minus twelve point one. Fifty
of seventy-two months positive.
""")

# ============================================================================== 21
s = slide("Risk-adjusted, we beat every comparator",
          "Highest Sharpe, Sortino, Calmar and Treynor, and the highest information ratio")
rows = [["Measure", "NDIF", "NASDAQ-100", "S&P 500", "Equal weight", "60/40",
         "What it tells you"],
        ["Annualised return", pct(ST[N]["cagr"]), pct(ST[Q]["cagr"]), pct(ST[S]["cagr"]),
         pct(ST[EW]["cagr"]), pct(ST[SIXTY]["cagr"]), "Geometric growth rate"],
        ["Annualised volatility", pct(ST[N]["vol"]), pct(ST[Q]["vol"]), pct(ST[S]["vol"]),
         pct(ST[EW]["vol"]), pct(ST[SIXTY]["vol"]), "Total risk"],
        ["Sharpe ratio", f"{ST[N]['sharpe']:.2f}", f"{ST[Q]['sharpe']:.2f}",
         f"{ST[S]['sharpe']:.2f}", f"{ST[EW]['sharpe']:.2f}", f"{ST[SIXTY]['sharpe']:.2f}",
         "Excess return per unit of total risk"],
        ["Sortino ratio", f"{ST[N]['sortino']:.2f}", f"{ST[Q]['sortino']:.2f}",
         f"{ST[S]['sortino']:.2f}", f"{ST[EW]['sortino']:.2f}", f"{ST[SIXTY]['sortino']:.2f}",
         "Excess return per unit of downside risk"],
        ["Treynor ratio", f"{ST[N]['treynor']:.3f}", f"{ST[Q]['treynor']:.3f}",
         f"{ST[S]['treynor']:.3f}", f"{ST[EW]['treynor']:.3f}", f"{ST[SIXTY]['treynor']:.3f}",
         "Excess return per unit of market beta"],
        ["Calmar ratio", f"{ST[N]['calmar']:.2f}", f"{ST[Q]['calmar']:.2f}",
         f"{ST[S]['calmar']:.2f}", f"{ST[EW]['calmar']:.2f}", f"{ST[SIXTY]['calmar']:.2f}",
         "Return per unit of maximum drawdown"],
        ["Information ratio (vs S&P)", f"{ST[N]['info_ratio']:.2f}", f"{ST[Q]['info_ratio']:.2f}",
         "—", f"{ST[EW]['info_ratio']:.2f}", f"{ST[SIXTY]['info_ratio']:.2f}",
         "Active return per unit of tracking error"],
        ["Beta (vs S&P 500)", f"{ST[N]['beta']:.2f}", f"{ST[Q]['beta']:.2f}", "1.00",
         f"{ST[EW]['beta']:.2f}", f"{ST[SIXTY]['beta']:.2f}", "Market sensitivity"],
        ["M² (risk-matched return)", pct(ST[N]["m2"]), pct(ST[Q]["m2"]), pct(ST[S]["m2"]),
         pct(ST[EW]["m2"]), pct(ST[SIXTY]["m2"]), "Return at benchmark risk"]]
table(s, ML, Inches(1.86), CW, rows, col_w=[19, 9, 11, 9, 11, 8, 33], size=10.5,
      row_h=Inches(0.42), first_bold=True,
      align=[PP_ALIGN.LEFT] + [PP_ALIGN.RIGHT] * 5 + [PP_ALIGN.LEFT])
textbox(s, ML, Inches(6.26), CW, Inches(0.5),
        "Risk-free rate is the Fama–French one-month Treasury bill series (mean 1.25% p.a. over the "
        "period). All ratios are computed on the same 72 monthly observations and annualised by √12.",
        size=10.5, color=INK3, line=1.2)
notes(s, """
If you keep one slide from today, keep this one.

Read down the NDIF column against the benchmarks.

Sharpe: nought point nine four against nought point seven five and nought point six five. Sortino,
which penalises only downside volatility: one point five one against one point one eight, a bigger
improvement than on Sharpe, which tells you our volatility was disproportionately upside
volatility. Treynor highest. Calmar sixty per cent better than both indices.

Information ratio against the S&P is nought point nine eight. As a rule of thumb, above nought
point five over a multi-year period is good and above one is excellent.

And the last row, M-squared: if you levered this fund to exactly the S&P's volatility it would have
returned seventeen point two per cent a year against the index's eleven point three. A like-for-like
comparison, and a six-point gap.

Note also that we beat the naive equal-weight portfolio of the same eleven stocks on every one of
these. That's a famously hard benchmark to beat.
""")

# ============================================================================== 22
s = slide("Tail risk sits below the NASDAQ-100 on every measure",
          "One-month value-at-risk and expected shortfall from the empirical distribution")
fit(s, "22_var.png", Inches(1.72), Inches(6.40), left=ML, right=Inches(8.92))
tx = Inches(9.05)
rect(s, tx, Inches(1.86), Inches(3.66), Inches(4.24), WHITE, RULE)
textbox(s, tx + Inches(0.24), Inches(2.06), Inches(3.2), Inches(0.3),
        "NDIF TAIL MEASURES", size=10, color=GOLD, bold=True)
tail = [("VaR 95% (historical)", pct(ST[N]["var95_hist"], 2)),
        ("VaR 95% (parametric normal)", pct(ST[N]["var95_param"], 2)),
        ("VaR 95% (Cornish–Fisher)", pct(ST[N]["var95_cf"], 2)),
        ("CVaR 95% (expected shortfall)", pct(ST[N]["cvar95_hist"], 2)),
        ("VaR 99% (historical)", pct(ST[N]["var99_hist"], 2)),
        ("CVaR 99% (expected shortfall)", pct(ST[N]["cvar99_hist"], 2)),
        ("On $279m, a 95% VaR month is", f"−${abs(ST[N]['var95_hist'])*279.2:,.1f}m")]
yy = Inches(2.52)
for k, v in tail:
    textbox(s, tx + Inches(0.24), yy, Inches(2.35), Inches(0.32), k, size=10.5, color=INK2)
    textbox(s, tx + Inches(2.5), yy, Inches(0.97), Inches(0.32), v, size=11, color=NAVY,
            bold=True, align=PP_ALIGN.RIGHT)
    yy = yy + Inches(0.50)
notes(s, """
Value-at-risk and expected shortfall, what your risk committees will ask for.

Our ninety-five per cent one-month VaR is minus eight point eight two per cent. In the worst month
in twenty we'd expect to lose at least that. On two hundred and seventy-nine million, a
twenty-four point six million dollar month.

Note the historical, parametric and Cornish-Fisher estimates all cluster between seven and nine per
cent, another confirmation the distribution is close to normal.

The number I'd actually watch is CVaR, because VaR only tells you the threshold, not how bad it
gets beyond it. Ours is minus ten point two per cent.

Compare the NASDAQ-100: essentially the same VaR threshold, but a worse CVaR and a worse
ninety-nine per cent VaR. Same threshold risk, thinner tail beyond it. Again, that's
diversification rather than anything clever in timing.
""")

# ============================================================================== 23
s = slide("Where in the calendar the money was made",
          "Seasonality across 72 months. Six observations per calendar month, so read this as "
          "description rather than a tradeable signal")
fit(s, "10_seasonality.png", Inches(1.66), Inches(4.98))
tx1, tw = ML, Inches(3.94)
cards = [("July  +5.8%", "The strongest month, on the back of six positive Julys out of six — "
          "including +13.1% in July 2022 during the bear-market rally.", AQUA),
         ("September  −2.8%", "The weakest month. Negative in three of six years, but heavily so: "
          "September 2022 alone cost 9.3%.", RED),
         ("2020 and 2022 were the extremes", "April 2020 was the best month on record at +14.5%; "
          "April 2022 the worst at −12.1%. Both sit inside the same two-year window.", BLUE)]
x = ML
for hd, body, col in cards:
    rect(s, x, Inches(5.10), tw, Inches(1.48), WHITE, RULE)
    rect(s, x, Inches(5.10), tw, Inches(0.05), col)
    textbox(s, x + Inches(0.22), Inches(5.30), tw - Inches(0.44), Inches(0.3), hd,
            size=13.5, color=NAVY, bold=True)
    textbox(s, x + Inches(0.22), Inches(5.68), tw - Inches(0.44), Inches(0.8), body,
            size=11, color=INK2, line=1.2)
    x = x + tw + Inches(0.26)
notes(s, """
Seasonality, and I will frame this carefully, because seasonality is easy to over-read.

Blue is positive, red negative, intensity is magnitude.

July was our strongest month at plus five point eight per cent average, positive in all six years.
September was weakest at minus two point eight, dragged there by three heavy losses in 2020,
2021 and 2022.

But here's why I wouldn't build a strategy on it. Six observations per calendar month is nowhere
near enough to separate a real seasonal effect from noise, the standard error on any monthly mean
is over two per cent. Almost none of these differences would survive a significance test.

What the grid does show usefully is the concentration of extremes. Look at the 2020 and 2022
rows. The best month in the fund's history and the worst sit within twenty-four months of each
other. That's the volatility regime we were managing through.
""")

# ============================================================================== 24
s = section("Was it skill?", "05",
            "Jensen's alpha, factor models, performance attribution, and what a mean-variance "
            "optimiser would have done with the same eleven stocks")

# ============================================================================== 25
s = slide("Jensen's alpha: significant on every model we ran",
          "Excess return regressed on risk factors. 72 monthly observations, Newey–West standard "
          "errors with four lags")
rows = [["Model", "Annualised alpha", "Alpha t-stat", "p-value", "Market beta", "Adjusted R²",
         "Interpretation"],
        ["CAPM (single factor)", pct(REG["CAPM"]["alpha_a"]), f"{REG['CAPM']['alpha_t']:.2f}",
         f"{REG['CAPM']['alpha_p']:.3f}", f"{REG['CAPM']['Mkt-RF']:.3f}",
         f"{REG['CAPM']['r2adj']:.3f}", "Significant at the 5% level"],
        ["Fama–French 3-factor", pct(REG["FF3"]["alpha_a"]), f"{REG['FF3']['alpha_t']:.2f}",
         f"{REG['FF3']['alpha_p']:.3f}", f"{REG['FF3']['Mkt-RF']:.3f}",
         f"{REG['FF3']['r2adj']:.3f}", "Significant at the 1% level"],
        ["Fama–French 5-factor", pct(REG["FF5"]["alpha_a"]), f"{REG['FF5']['alpha_t']:.2f}",
         f"{REG['FF5']['alpha_p']:.3f}", f"{REG['FF5']['Mkt-RF']:.3f}",
         f"{REG['FF5']['r2adj']:.3f}", "Significant at the 1% level"],
        ["FF5 + momentum (Carhart)", pct(REG["FF6"]["alpha_a"]), f"{REG['FF6']['alpha_t']:.2f}",
         f"{REG['FF6']['alpha_p']:.3f}", f"{REG['FF6']['Mkt-RF']:.3f}",
         f"{REG['FF6']['r2adj']:.3f}", "Significant at the 1% level"],
        ["NASDAQ-100, same FF5 test", pct(R["reg_qqq"]["FF5"]["alpha_a"]),
         f"{R['reg_qqq']['FF5']['alpha_t']:.2f}", f"{R['reg_qqq']['FF5']['alpha_p']:.3f}",
         f"{R['reg_qqq']['FF5']['Mkt-RF']:.3f}", f"{R['reg_qqq']['FF5']['r2adj']:.3f}",
         "Not statistically significant"]]
table(s, ML, Inches(1.90), CW, rows, col_w=[21, 13, 10, 9, 10, 10, 27], size=11,
      row_h=Inches(0.48), first_bold=True,
      align=[PP_ALIGN.LEFT] + [PP_ALIGN.RIGHT] * 5 + [PP_ALIGN.LEFT])
textbox(s, ML, Inches(5.10), CW, Inches(1.4),
        "The test that matters. After controlling for the market, size, value, profitability, "
        "investment and momentum factors, the fund still delivered 6.6% a year that those factors "
        "cannot explain, with a t-statistic of 3.06 (p = 0.002). The same test applied to the "
        "NASDAQ-100 returns an alpha of 2.4% that is statistically indistinguishable from zero. "
        "The benchmark's excess return is explained by its factor exposures. Ours is not.", size=13, color=INK, line=1.3)
notes(s, """
Now the question you should be asking: was this skill, or did we simply own high-beta growth
stocks in a decade that rewarded them?

You answer that with a factor regression. Take the fund's excess return, regress it on known risk
factors, and see what's left over. That leftover is Jensen's alpha.

Start with the CAPM: alpha of seven point two per cent, t of two point one nine. But the CAPM only
controls for market risk, so a sceptic would say a growth tilt is doing the work.

Add size and value: five point nine per cent, t of two point eight three. Add profitability and
investment: six point six per cent, t of three point zero six, p-value nought point zero zero two.
With momentum, unchanged.

Ninety-two per cent of our variance is explained by the factors. The remaining six point six per
cent a year is not.

Now the bottom row, the one I'd spend most time on. I ran the same test on the NASDAQ-100 itself.
Its alpha is two point four per cent with a t of one point four one: statistically
indistinguishable from zero.

The benchmark's strong decade is fully explained by its factor exposures. Ours is not. That
difference is what you paid a management fee for.
""")

# ============================================================================== 26
s = slide("What the factor loadings say about us",
          "A large-cap growth fund with market-like beta, which is the profile the mandate described")
fit(s, "18_factors.png", Inches(1.72), Inches(6.40), left=ML, right=Inches(8.92))
tx = Inches(9.05)
textbox(s, tx, Inches(1.90), Inches(3.7), Inches(0.3), "READING THE COEFFICIENTS",
        size=10, color=GOLD, bold=True)
ey = bullets(s, tx, Inches(2.26), Inches(3.66), [
    ("Market +1.05.", "Essentially one-for-one with the market. We were not levered."),
    ("Size −0.22.", "Significantly negative: a large-cap fund, as intended."),
    ("Value −0.19.", "Significantly negative: a growth fund, as intended."),
    ("Profitability −0.11, Investment −0.05.", "Neither is significant, so no hidden quality tilt."),
    ("Momentum +0.02.", "Effectively zero. This was not a momentum-chasing strategy."),
], size=11, gap=Inches(0.15))
rect(s, tx, ey + Inches(0.16), Inches(3.66), Inches(0.02), RULE)
textbox(s, tx, ey + Inches(0.34), Inches(3.66), Inches(1.0),
        "Every loading sits where the January-2016 mandate said it would. There are no unexplained "
        "exposures hiding in this portfolio.", size=11, color=NAVY, bold=True,
        line=1.25)
notes(s, """
Those five coefficients describe the fund more honestly than any marketing document could.

Market loading, one point zero five, one-for-one with the market. Not levered.

Size, minus nought point two two and significant: large-cap. Value, minus nought point one nine and
significant: growth. Both correct and intended.

Profitability and investment are both small and insignificant. That matters, because a common criticism of
"technology alpha" is that it is really a quality tilt in disguise. Here it is not.

Momentum is effectively zero, this wasn't a momentum-chasing strategy that would blow up on the
first reversal.

So: a large-cap growth fund with market-like beta, no leverage, no hidden factor bets. Precisely
the description in the mandate I showed you at the start.
""")

# ============================================================================== 27
s = slide("Alpha was persistent, not a single lucky year",
          "Rolling 36-month Jensen's alpha stays positive across every window in the sample")
fit(s, "15_rolling_alpha.png", Inches(1.66), Inches(5.98))
textbox(s, ML, Inches(6.10), CW, Inches(0.7),
        "A single full-sample alpha can be produced by one exceptional year. This chart re-estimates "
        "the CAPM alpha on every rolling three-year window from Dec-2019 onward. It never turns "
        "negative — including the windows dominated by the 2022 drawdown, where the alpha comes from "
        "losing less rather than gaining more.",
        size=11.5, color=INK2, line=1.25)
notes(s, """
One more robustness check, because a full-sample alpha can always be produced by a single
extraordinary year buried in the middle.

I've re-estimated the CAPM alpha on every rolling thirty-six-month window. The line never goes
below zero.

Alpha was earned in the growth years of 2017 to 2019, and in the very different windows dominated
by 2020's crash-and-recovery and 2022's rate shock.

The shape of the line is worth a moment. It declines through the middle of the sample and recovers
at the right. The middle windows are 2020 and 2021, when the NASDAQ-100 was extremely hard to beat.
The recovery at the right is 2022.

So the source of alpha changed character, security selection early, downside protection late.
That's healthy rather than worrying: it means the fund wasn't dependent on one market regime.
""")

# ============================================================================== 28
s = slide("Nine of eleven picks beat their own sector",
          "Each holding measured against the GICS sector ETF it sits in, which is the fairest test "
          "of stock selection")
fit(s, "13_stock_vs_sector.png", Inches(1.66), Inches(6.06))
textbox(s, ML, Inches(6.20), CW, Inches(0.6),
        "Only two picks lagged: Illumina, 60 points behind XLV, and Schlumberger, 77 points behind "
        "XLE. The standouts were Costco at 152 points ahead of XLP, NextEra 146 ahead of XLU and "
        "Microsoft 142 ahead of XLK. XLC did not exist until June 2018, so the Communication "
        "Services sleeve is spliced with XLK before that date.",
        size=11, color=INK2, line=1.22)
notes(s, """
Let's get underneath the portfolio number, because ultimately you hired me to pick eleven stocks.

The fairest test isn't whether a pick went up. It's whether it beat the sector it sits in, because
if I pick a technology stock in a decade when all technology stocks rose, I've demonstrated
nothing.

Blue is the stock, orange is its sector ETF. Eight of eleven picks beat their sector.

The standouts: Costco beat consumer staples by a hundred and fifty-two points, NextEra beat
utilities by a hundred and forty-six, and Microsoft beat the technology sector by a hundred and
forty-two. That last one matters most, because it happened in our largest position.

Two misses. Illumina, where the thesis was right but the GRAIL acquisition and the regulatory
fight around it destroyed value. And Schlumberger, which lost money against an energy sector that
gained fifty-four per cent.

I own both. But nine of eleven, weighted toward our largest positions, is why the portfolio
worked.
""")

# ============================================================================== 29
s = slide("Where the 179% came from",
          "Compounded contribution to cumulative return by holding. Microsoft alone delivered "
          "nearly a quarter of it")
fit(s, "12_contribution.png", Inches(1.72), Inches(6.50), left=ML, right=Inches(9.02))
tx = Inches(9.15)
textbox(s, tx, Inches(1.90), Inches(3.6), Inches(0.3), "TOP 3 AND BOTTOM 3",
        size=10, color=GOLD, bold=True)
rowsx = [["", "Contribution", "Total return"],
         ["MSFT", "41.9 pts", pct(R["stock_total"]["MSFT"], 0)],
         ["GOOGL", "22.1 pts", pct(R["stock_total"]["GOOGL"], 0)],
         ["ALB", "20.8 pts", pct(R["stock_total"]["ALB"], 0)],
         ["EQIX", "10.5 pts", pct(R["stock_total"]["EQIX"], 0)],
         ["AMZN", "10.3 pts", pct(R["stock_total"]["AMZN"], 0)],
         ["ILMN", "1.8 pts", pct(R["stock_total"]["ILMN"], 0)]]
table(s, tx, Inches(2.28), Inches(3.56), rowsx, col_w=[32, 36, 32], size=11,
      row_h=Inches(0.32), first_bold=True)
textbox(s, tx, Inches(4.68), Inches(3.56), Inches(1.6),
        "Schlumberger is the instructive case. It lost 23.5% over six years, yet contributed a "
        "positive 13.2 points — because quarterly rebalancing kept buying it back to its 5% floor "
        "at successively lower prices, and it then returned +81% in 2022.",
        size=11.5, color=INK2, line=1.28)
notes(s, """
How each holding's weight and return compounded into the total.

Microsoft contributed forty-one point nine points of the fund's hundred and seventy-nine. That's
twenty-three per cent of everything the fund made, from a sixteen per cent position. Sizing your
highest-conviction idea largest is the most consequential decision a manager makes, and this is
what it looks like when it goes right.

Alphabet twenty-two points, Albemarle twenty-one, the surprise, a six per cent materials position
riding the lithium and EV supply chain. Illumina is the clear disappointment: eight per cent of the
book delivered under two points.

But the panel on the right contains the most interesting finding in this review. Schlumberger lost
twenty-three and a half per cent over six years, and yet contributed a positive thirteen points.

How? Every quarter it fell, the rebalancing rule bought more at a lower price. Then in 2022 it
returned eighty-one per cent, and by then we owned considerably more shares. A losing stock made
money for this fund because of a mechanical process rule.
""")

# ============================================================================== 30
s = slide("94% of the value-add came from stock picking",
          "Brinson–Fachler attribution against an equal-weight benchmark of the eleven GICS sector "
          "ETFs")
fit(s, "31_attribution.png", Inches(1.72), Inches(6.40), left=ML, right=Inches(8.92))
tx = Inches(9.05)
textbox(s, tx, Inches(1.92), Inches(3.66), Inches(0.3), "DECOMPOSITION", size=10,
        color=GOLD, bold=True)
ey = bullets(s, tx, Inches(2.26), Inches(3.66), [
    ("Allocation +1.8 pts.", "The sector tilts, overweight technology and underweight energy, "
     "contributed very little."),
    ("Selection +41.4 pts.", "Almost all of the active return came from picking better stocks "
     "than the sector average."),
    ("Interaction +1.0 pt.", "The residual from being overweight where we also picked well."),
], size=11, gap=Inches(0.16))
rect(s, tx, ey + Inches(0.16), Inches(3.66), Inches(0.02), RULE)
textbox(s, tx, ey + Inches(0.34), Inches(3.66), Inches(2.0),
        "Why this matters for your decision: allocation skill is a macro call and is hard to "
        "repeat. Selection skill is a research process. That 94% of our value-add came from "
        "selection is the strongest argument that the result is repeatable.",
        size=11, color=NAVY, line=1.3)
notes(s, """
Brinson attribution answers a specific question: how much came from being in the right sectors, and
how much from picking the right stocks within them?

To isolate that, I built a benchmark with exactly our sector coverage at neutral weights and no
stock selection, an equal-weight portfolio of the eleven sector ETFs. It returned eighty-five per
cent against our hundred and seventy-nine.

Allocation, our sector tilts, contributed one point eight points. Almost nothing. Selection
contributed forty-one point four. Interaction, one.

So ninety-four per cent of our active return came from security selection.

Why that matters for your decision: allocation skill is a macro forecasting call, and the evidence
that anyone repeats macro calls is weak. Selection skill is the output of a research process. You
can describe it, staff it, and repeat it. If our outperformance had come from sector timing, I'd be
much less confident recommending this fund continue.
""")

# ============================================================================== 31
s = slide("Would an optimiser have done better?",
          "A mean-variance model given three years of pre-launch data would have added 1.1% a year, "
          "by taking concentration risk we were not permitted to take")
fit(s, "27_variants.png", Inches(1.72), Inches(6.50), left=ML, right=Inches(8.92))
tx = Inches(9.05)
rows = [["Construction rule", "CAGR", "Sharpe"],
        ["NDIF as run", pct(ST[N]["cagr"]), f"{ST[N]['sharpe']:.2f}"],
        ["Mean–variance (2014–16 inputs)", pct(ST[MV]["cagr"]), f"{ST[MV]['sharpe']:.2f}"],
        ["Equal weight (1/N)", pct(ST[EW]["cagr"]), f"{ST[EW]['sharpe']:.2f}"],
        ["Buy & hold", pct(ST["NDIF (buy & hold)"]["cagr"]),
         f"{ST['NDIF (buy & hold)']['sharpe']:.2f}"],
        ["Perfect-foresight optimum",
         pct(ST["MV optimised (perfect foresight)"]["cagr"]),
         f"{ST['MV optimised (perfect foresight)']['sharpe']:.2f}"]]
table(s, tx, Inches(1.92), Inches(3.66), rows, col_w=[52, 24, 24], size=10.5,
      row_h=Inches(0.34), first_bold=True)
textbox(s, tx, Inches(4.16), Inches(3.66), Inches(2.4),
        "The optimiser's solution put 25% in Equinix and 25% in NextEra — breaching our 16% position "
        "cap — and zero in Alphabet, Visa, Albemarle and Schlumberger, breaching the 5% sector floor "
        "four times over. It bought a better backtest by discarding the mandate.\n\n"
        "Even with perfect foresight, the best achievable was 22.9% a year. We captured 82% of a "
        "result nobody could have known in advance.",
        size=10.5, color=INK2, line=1.26)
notes(s, """
The obvious challenge to everything I've said is: fine, but a model could have done better. So I
tested it.

I took three years of data ending December 2016, which is the information a manager actually had
at launch. I fed it to a mean-variance optimiser and ran the weights forward on the same
rebalancing rule.

The result: nineteen point seven per cent a year against our eighteen point seven. So yes, it wins,
by a point a year.

But look at what it had to do. Twenty-five per cent in Equinix and twenty-five in NextEra, both
breaching our sixteen per cent cap. And zero in Alphabet, Visa, Albemarle and Schlumberger,
breaching the sector floor four times over.

The optimiser didn't beat our strategy. It declined to run it, it bought a better backtest by
discarding the constraints that, as we saw in 2022, protected you. And there's a known reason to
distrust it anyway: DeMiguel, Garlappi and Uppal showed in 2009 that naive equal weighting
frequently beats optimisation out of sample, because small input errors produce wildly concentrated
portfolios.

The last row is the humbling one. With perfect hindsight the best achievable was twenty-two point
nine per cent. We captured eighty-two per cent of a number nobody could have known.
""")

# ============================================================================== 32
s = slide("120% of the upside, 97% of the downside",
          "The asymmetry that produced the result: most of the market's gains, without most of "
          "its losses")
fit(s, "19_capture.png", Inches(1.72), Inches(6.40), left=ML, right=Inches(8.92))
tx = Inches(9.05)
textbox(s, tx, Inches(1.92), Inches(3.66), Inches(0.3), "THE ASYMMETRY", size=10,
        color=GOLD, bold=True)
ey = bullets(s, tx, Inches(2.26), Inches(3.66), [
    ("Upside capture 120%.", "In months the S&P 500 rose, we rose 20% more than it did."),
    ("Downside capture 97%.", "In months it fell, we fell slightly less."),
    ("The NASDAQ-100, by contrast,", "captured 118% of the upside but 108% of the downside: "
     "more of the gains, and more of the losses."),
    ("50 positive months of 72.", "A 69.4% hit rate against 65.3% for the NASDAQ-100."),
], size=11, gap=Inches(0.16))
rect(s, tx, ey + Inches(0.16), Inches(3.66), Inches(0.02), RULE)
textbox(s, tx, ey + Inches(0.34), Inches(3.66), Inches(1.6),
        "Those two numbers, 120 up and 97 down, are the compact statement of what the fund did. "
        "Everything else in this deck elaborates on them.",
        size=11, color=NAVY, bold=True, line=1.3)
notes(s, """
If I had to reduce this whole presentation to two numbers, it would be these.

Upside capture of a hundred and twenty per cent: in months the S&P rose, we rose twenty per cent
more. Downside capture of ninety-seven: in months it fell, we fell slightly less.

That asymmetry is the engine of the result. You don't need to be right about market direction to
compound at eighteen per cent a year if you participate disproportionately in the good months and
proportionately in the bad ones.

Contrast the NASDAQ-100: a hundred and eighteen per cent of the upside, very similar, but a
hundred and eight per cent of the downside. More of the gains and more of the losses. That
eleven-point difference, compounded over seventy-two months, is essentially the entire gap between
our two seventy-nine and its two thirty-five.
""")

# ============================================================================== 33
s = section("The verdict", "06",
            "Marking the fund against the objective we set in 2016, the fees you paid, and our "
            "recommendation on what happens next")

# ============================================================================== 34
s = slide("Marking ourselves against the 2016 objective",
          "Every commitment we made when we asked you for the mandate, scored against what we "
          "actually delivered")
rows = [["What we committed to in January 2016", "Target", "Delivered", "Verdict"],
        ["Net annualised return", "8–10% p.a.", "17.5% p.a. net of all fees", "Exceeded"],
        ["Cumulative net return over the fund life", "55–70%", "163% net", "Exceeded"],
        ["Outperform the S&P 500", "~2% p.a. net", "+6.2% p.a. net", "Exceeded"],
        ["Outperform the NASDAQ-100 (primary benchmark)", "Beat it", "+3.4% p.a. gross", "Met"],
        ["Maintain all eleven GICS sectors, 5% floor", "No sector abandoned", "Held throughout, "
         "all 24 quarters", "Met"],
        ["Cap the largest position at 16%", "16% cap", "Held at every rebalance; MSFT drifted to a "
         "peak of 17.6% within a quarter", "Met"],
        ["Rebalance quarterly with a 5-point drift rule", "24 rebalances", "24 executed; drift "
         "never exceeded 2.9 pts, so the rule never fired", "Met"],
        ["Deliver a mid-life strategic review at end-2019", "Formal review", "Conducted; target "
         "weights reconfirmed", "Met"],
        ["Keep the drawdown below the theme benchmark's", "Beat NASDAQ-100", "−24.9% vs −32.6%",
         "Met"],
        ["Generate return the market cannot explain", "Positive alpha", "+6.6% p.a., t = 3.06, "
         "p = 0.002", "Exceeded"]]
table(s, ML, Inches(1.86), CW, rows, col_w=[38, 14, 32, 16], size=10.5, row_h=Inches(0.42),
      first_bold=True,
      align=[PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.LEFT, PP_ALIGN.LEFT])
notes(s, """
The accountability slide. Ten commitments, marked against what happened.

We said eight to ten per cent net a year; we delivered seventeen and a half net. We said fifty-five
to seventy per cent cumulative; we delivered a hundred and sixty-three.

I'll be careful how I present that, because doubling your target isn't automatically a compliment
to the manager. Part of it is that this was an unusually strong period for our theme. The honest
framing: our central estimate was reasonable and our distribution around it was too narrow.

Then the process commitments, which matter as much. All eleven sectors held through all twenty-four
quarters. Twenty-four rebalances executed on schedule. The largest drift we ever ran was two point
nine points, comfortably inside the five-point threshold, so the drift rule never had to fire. And
the mid-life review was delivered at the end of 2019.

Ten commitments. Four exceeded, six met, none missed.
""")

# ============================================================================== 35
s = slide("Gross to net: what you actually kept",
          "0.90% management fee plus 10% of the excess over the NASDAQ-100 hurdle, subject to the "
          "high-water mark")
fit(s, "33_fees.png", Inches(1.72), Inches(6.50), left=ML, right=Inches(8.92))
tx = Inches(9.05)
_net = 0.1751
rows = [["", "p.a.", "Over six years"],
        ["Gross return", pct(ST[N]["cagr"]), pct(ST[N]["cum_return"], 0)],
        ["Management fee", "−0.90%", "−5.3%"],
        ["Performance fee", "−0.25%", "−1.5%"],
        ["Net to investors", pct(_net, 2), pct((1 + _net) ** 6 - 1, 0)]]
table(s, tx, Inches(1.92), Inches(3.66), rows, col_w=[46, 27, 27], size=11,
      row_h=Inches(0.34), first_bold=True)
textbox(s, tx, Inches(3.80), Inches(3.66), Inches(2.7),
        "Total fee load was 1.15% a year — 0.90% base plus 0.25% of performance fee, because the "
        "hurdle is the NASDAQ-100 rather than zero and we only cleared it by 2.5 points a year.\n\n"
        "A passive NASDAQ-100 ETF at 0.20% would have cost $5.7m less over the six years and "
        "returned $235m. We returned $279m, so investors kept $38.7m after paying for active "
        "management.",
        size=11, color=INK2, line=1.28)
notes(s, """
Fees in full, because you're entitled to see the bridge.

Gross, the fund compounded at eighteen point seven per cent. The management fee is ninety basis
points, flat.

The performance fee is where the structure earns its keep. We charge ten per cent of returns above
the hurdle, and the hurdle is the NASDAQ-100, not zero. Because that benchmark itself returned fifteen point three per cent a year, we cleared it by
only two and a half points. So the performance fee is twenty-five basis points, against the one
point eight per cent a zero-hurdle fund would have charged.

Total load: one point one five per cent a year. Net to you, seventeen point five one per cent a
year, or a hundred and sixty-three per cent cumulative.

The honest alternative: a NASDAQ-100 ETF at twenty basis points would have returned two hundred and
thirty-five million and cost five point seven million less. After paying us every dollar of fee you
are thirty-eight point seven million ahead of the cheap passive option. That is the only fee test
that matters, and we pass it.
""")

# ============================================================================== 36
s = slide("Our recommendation: the fund should continue",
          "With three changes to the mandate, which we would want your agreement on before raising "
          "the successor vehicle")
left_w = Inches(6.05)
rect(s, ML, Inches(1.84), left_w, Inches(4.62), WHITE, RULE)
rect(s, ML, Inches(1.84), left_w, Inches(0.055), AQUA)
textbox(s, ML + Inches(0.28), Inches(2.06), left_w - Inches(0.56), Inches(0.34),
        "THE CASE FOR CONTINUING", size=10, color=GOLD, bold=True)
bullets(s, ML + Inches(0.28), Inches(2.48), left_w - Inches(0.56), [
    ("The alpha is real and it is repeatable.", "6.6% a year that five risk factors cannot "
     "explain, with 94% of it from security selection rather than sector timing."),
    ("The thesis is not exhausted.", "Cloud is still a minority of enterprise IT spend; "
     "electrification and genomics are earlier still. The 2022 de-rating repriced the multiple, "
     "not the demand."),
    ("The construction discipline was tested and held.", "Sector floors, the position cap and "
     "quarterly rebalancing were all worth measurable money — most visibly in 2022."),
], size=12, gap=Inches(0.22))
right_x = ML + left_w + Inches(0.28)
right_w = CW - left_w - Inches(0.28)
rect(s, right_x, Inches(1.84), right_w, Inches(4.62), WHITE, RULE)
rect(s, right_x, Inches(1.84), right_w, Inches(0.055), ORANGE)
textbox(s, right_x + Inches(0.28), Inches(2.06), right_w - Inches(0.56), Inches(0.34),
        "WHAT WE WOULD CHANGE", size=10, color=GOLD, bold=True)
bullets(s, right_x + Inches(0.28), Inches(2.48), right_w - Inches(0.56), [
    ("Widen the tail-scenario assumptions.", "Our Scenario C assumed a 4% loss. The real one cost "
     "22.5%. The framework identified the regime correctly and sized it badly."),
    ("Add a valuation discipline to the entry rule.", "Illumina, our worst selection decision, was "
     "a correct thesis bought without a price constraint."),
    ("Review the position cap upward, carefully.", "The 16% cap forced us to trim Microsoft, our "
     "single best decision, at 19 of the 24 rebalances. We would seek 20%, with the sector "
     "floors untouched."),
], size=12, gap=Inches(0.22))
notes(s, """
So: should this fund continue?

My recommendation is yes, for three specific reasons rather than a general expression of
confidence.

First, the alpha is real and repeatable, six point six per cent a year that five established
factors can't explain, and ninety-four per cent of it from selection rather than sector timing.
Selection skill is a process; macro timing is a guess.

Second, the thesis isn't exhausted. Cloud is still a minority of enterprise IT spend, six years
after we argued it was early. 2022 repriced the multiple, not the demand.

Third, the construction discipline was tested by the two hardest events in twenty years and held.

But I'd be doing you a disservice if I asked for renewal without saying what I'd change.

We need wider tail-scenario assumptions. We said a recession would cost four per cent; it cost
twenty-two and a half. We need a valuation discipline on entry: Illumina was a correct thesis
bought with no margin of safety. And I would ask you to consider raising the position cap from
sixteen to twenty per cent. That cap forced us to trim Microsoft, our single best decision, at
nineteen of the twenty-four rebalances. The sector floors I would leave untouched, because those
are what saved us.
""")

# ============================================================================== 37
s = prs.slides.add_slide(BLANK)
bg = s.background.fill; bg.solid(); bg.fore_color.rgb = NAVY
SLIDE_NO[0] += 1
rect(s, Inches(0), Inches(0), Inches(0.11), H, GOLD)
textbox(s, Inches(0.95), Inches(1.86), Inches(7.4), Inches(0.4), "N O R T H P O I N T",
        size=14, color=GOLD, bold=True)
textbox(s, Inches(0.95), Inches(2.42), Inches(9.0), Inches(1.0), "Thank you.", size=44,
        color=WHITE, bold=True)
textbox(s, Inches(0.95), Inches(3.42), Inches(9.4), Inches(1.4),
        "I am happy to take questions on any part of this review.\n"
        "An appendix follows with the full methodology, the complete metric tables, the per-holding "
        "statistics, and the full factor-model output.",
        size=15, color=RGBColor(0xB8, 0xC6, 0xD8), line=1.35)
rect(s, Inches(0.95), Inches(5.10), Inches(1.15), Inches(0.05), GOLD)
textbox(s, Inches(0.95), Inches(5.40), Inches(9.0), Inches(0.8),
        "Callum O'Connor  ·  Portfolio Manager  ·  Northpoint Capital Partners\n"
        "FINC13-303 Portfolio Analysis and Investments  ·  Student ID 14053836",
        size=12, color=RGBColor(0x9A, 0xAC, 0xC2), line=1.35)
notes(s, """
That's the review.

Three sentences: a hundred million became two hundred and seventy-nine million; we did it with less
drawdown than our own benchmark and a higher Sharpe than any comparator I could construct; and
after controlling for every standard risk factor, six point six per cent a year remains unexplained
by anything other than the decisions we made.

I recommend the fund continues, with the three mandate changes I've set out.

Happy to take questions, and there's a substantial appendix if you want to go deeper on the
methodology, the holdings or the regressions. Thank you for six years of patient capital.
""")

# =========================================================================== APPENDIX
s = section("Appendix", "A",
            "Methodology and data sources, full metric tables, per-holding statistics, complete "
            "factor-model output, and supporting exhibits")

# A1
s = slide("A1 · Methodology, data and assumptions",
          "Everything in this deck is reproducible from the accompanying Python analysis and Excel "
          "workbook")
rows = [["Item", "Treatment"],
        ["Return data", "Monthly total returns from dividend- and split-adjusted closing prices, "
         "Jan 2017 – Dec 2022 (72 observations per series)"],
        ["Portfolio construction", "Target weights per the January-2016 mandate; drift within the "
         "quarter, restored to target at each calendar quarter-end (24 rebalances)"],
        ["Primary benchmark", "NASDAQ-100 total return, proxied by the QQQ ETF so that dividends "
         "are included (the ^NDX index itself is price-only)"],
        ["Secondary benchmark", "S&P 500 total return, proxied by the SPY ETF on the same basis"],
        ["Sector benchmarks", "The eleven SPDR GICS sector ETFs. XLC launched Jun-2018, so XLK is "
         "used for the Communication Services sleeve before that date"],
        ["Risk-free rate", "Fama–French one-month Treasury bill series; mean 1.25% p.a. over the "
         "sample"],
        ["Risk factors", "Kenneth R. French Data Library: Mkt-RF, SMB, HML, RMW, CMA and the "
         "momentum factor, monthly, US research series"],
        ["Regressions", "OLS with Newey–West (HAC) standard errors, four lags, to correct for "
         "autocorrelation and heteroskedasticity in monthly returns"],
        ["Annualisation", "Returns compounded geometrically; volatility scaled by √12; ratios "
         "computed on monthly data then annualised"],
        ["Attribution", "Brinson–Fachler, summed arithmetically across 72 months against an "
         "equal-weight benchmark of the eleven sector ETFs"],
        ["Mean–variance optimisation", "SLSQP, long-only, maximum Sharpe, 25% position bound; "
         "in-sample window Jan 2014 – Dec 2016 for the ex-ante case"],
        ["Excluded", "Transaction costs, market impact, taxes and cash drag. All returns are "
         "gross of these unless a slide states otherwise"]]
table(s, ML, Inches(1.82), CW, rows, col_w=[23, 77], size=10, row_h=Inches(0.36),
      align=[PP_ALIGN.LEFT, PP_ALIGN.LEFT])
notes(s, """
This slide exists so anyone can reproduce every number in the deck.

Two points I'd flag. First, I've used QQQ and SPY rather than the raw index levels, because the raw
series are price-only. Comparing our dividend-inclusive return against a price-only index would
have flattered us by roughly two per cent a year. Using the ETFs makes it apples-to-apples, and
investable.

Second, these returns are gross of transaction costs and taxes. With twenty-four rebalances of
eleven liquid mega-caps, realistic round-trip costs are a few basis points a year, immaterial, but
I'd rather state it than have it discovered.
""")

# A2
s = slide("A2 · Full performance and risk metrics",
          "All strategies and benchmarks, 72 monthly observations, January 2017 – December 2022")
keys = [(N, "NDIF"), (EW, "Equal weight"), (MV, "Mean–variance"), (Q, "NASDAQ-100"),
        (S, "S&P 500"), (SIXTY, "60/40")]
metrics = [("Cumulative return", "cum_return", "pct0"), ("Annualised return", "cagr", "pct"),
           ("Annualised volatility", "vol", "pct"), ("Mean monthly return", "mean_m", "pct2"),
           ("Median monthly return", "median_m", "pct2"), ("Skewness", "skew", "num"),
           ("Excess kurtosis", "kurt", "num"), ("Best month", "best", "pct"),
           ("Worst month", "worst", "pct"), ("Sharpe ratio", "sharpe", "num"),
           ("Sortino ratio", "sortino", "num"), ("Treynor ratio", "treynor", "num3"),
           ("Calmar ratio", "calmar", "num"), ("Maximum drawdown", "max_dd", "pct"),
           ("Downside deviation", "downside_dev", "pct"), ("VaR 95% (monthly)", "var95_hist", "pct"),
           ("CVaR 95% (monthly)", "cvar95_hist", "pct"), ("Beta vs S&P 500", "beta", "num"),
           ("Tracking error vs S&P 500", "te", "pct"), ("Upside capture", "up_capture", "pct0"),
           ("Downside capture", "down_capture", "pct0"),
           ("Terminal value on $100m", "terminal", "usd")]
def fmt(v, kind):
    if v is None: return "—"
    return {"pct": pct(v, 1), "pct0": pct(v, 0), "pct2": pct(v, 2), "num": f"{v:.2f}",
            "num3": f"{v:.3f}", "usd": f"${v/1e6:,.0f}m"}[kind]
rows = [["Metric"] + [lbl for _, lbl in keys]]
for label, key, kind in metrics:
    rows.append([label] + [fmt(ST[k].get(key), kind) for k, _ in keys])
table(s, ML, Inches(1.80), CW, rows, col_w=[26] + [12.3] * 6, size=8.5,
      row_h=Inches(0.212), first_bold=True)
notes(s, """
The complete metric table.

The comparison I'd encourage you to make is NDIF against equal weight, in the first two data
columns, a hard benchmark to beat.

We beat it on cumulative return, annualised return, Sharpe, Sortino, Treynor and information ratio.
Equal weight beat us on maximum drawdown and Calmar, because it held less in the mega-caps that
fell hardest in 2022.

So conviction weighting added return and risk-adjusted return while costing a little on worst-case
drawdown. That's a fair characterisation of what active weighting bought you.
""")

# A3
s = slide("A3 · Per-holding statistics",
          "Every position measured over the full six years on the same basis as the portfolio")
tick_order = ["MSFT", "GOOGL", "AMZN", "V", "EQIX", "ILMN", "ROK", "NEE", "COST", "ALB", "SLB"]
GICS = {"MSFT": "Info Tech", "GOOGL": "Comm Svcs", "AMZN": "Cons Disc", "V": "Financials",
        "EQIX": "Real Estate", "ILMN": "Health Care", "ROK": "Industrials", "NEE": "Utilities",
        "COST": "Cons Staples", "ALB": "Materials", "SLB": "Energy"}
rows = [["Ticker", "GICS sector", "Weight", "Total return", "CAGR", "Volatility", "Sharpe",
         "Max DD", "Beta", "CAPM alpha", "t-stat", "Contribution"]]
for t in tick_order:
    rows.append([t, GICS[t], pct(R["weights_target"][t], 0), pct(R["stock_total"][t], 0),
                 pct(SS[t]["cagr"]), pct(SS[t]["vol"]), f"{SS[t]['sharpe']:.2f}",
                 pct(SS[t]["max_dd"]), f"{SS[t]['beta']:.2f}",
                 pct(R["reg_stock_capm"][t]["alpha_a"]),
                 f"{R['reg_stock_capm'][t]['alpha_t']:.2f}",
                 f"{R['contrib'][t]*100:,.1f} pts"])
rows.append(["NDIF", "All eleven", "100%", pct(ST[N]["cum_return"], 0), pct(ST[N]["cagr"]),
             pct(ST[N]["vol"]), f"{ST[N]['sharpe']:.2f}", pct(ST[N]["max_dd"]),
             f"{ST[N]['beta']:.2f}", pct(REG["CAPM"]["alpha_a"]),
             f"{REG['CAPM']['alpha_t']:.2f}", "179.2 pts"])
table(s, ML, Inches(1.84), CW, rows, col_w=[7, 12, 7, 9.5, 8, 9, 7, 8.5, 6.5, 9.5, 7, 9],
      size=9.5, row_h=Inches(0.335), first_bold=True)
textbox(s, ML, Inches(6.16), CW, Inches(0.5),
        "Only Microsoft (t = 2.76) and NextEra (t = 3.14) clear the 1.96 threshold on their own; "
        "Costco misses it by a whisker at 1.95. The portfolio's alpha is more significant than any "
        "constituent's, which is the diversification benefit doing real statistical work.",
        size=11, color=INK2, line=1.25)
notes(s, """
Every holding on the same basis as the portfolio.

The interesting part is in the last two columns and the bottom row.

Only two holdings, Microsoft and NextEra, produced a statistically significant CAPM alpha on their
own. Costco misses the threshold by a whisker at one point nine five. Everything else is below two.

But the portfolio's alpha has a t of two point one nine on the CAPM and three point zero six on the
five-factor. The portfolio is more significant than almost every stock in it.

That's not a paradox, it's diversification. Combining eleven imperfectly correlated positions
cancels idiosyncratic noise while retaining the common component of the selection skill. The signal
survives; much of the noise doesn't.
""")

# A4
s = slide("A4 · Complete factor-model output",
          "Coefficient, t-statistic and significance for every factor across all four models")
def cell(reg, f):
    if f not in reg: return "—"
    t = reg[f + "_t"]
    star = "***" if abs(t) > 2.58 else ("**" if abs(t) > 1.96 else ("*" if abs(t) > 1.65 else ""))
    return f"{reg[f]:+.3f}{star}\n(t = {t:.2f})"
facs = [("Alpha (annualised)", "alpha"), ("Market (Mkt-RF)", "Mkt-RF"), ("Size (SMB)", "SMB"),
        ("Value (HML)", "HML"), ("Profitability (RMW)", "RMW"), ("Investment (CMA)", "CMA"),
        ("Momentum (MOM)", "MOM")]
models = ["CAPM", "FF3", "FF5", "FF6"]
rows = [["Factor", "CAPM", "Fama–French 3", "Fama–French 5", "FF5 + momentum"]]
for label, f in facs:
    row = [label]
    for m in models:
        reg = REG[m]
        if f == "alpha":
            t = reg["alpha_t"]
            star = "***" if abs(t) > 2.58 else ("**" if abs(t) > 1.96 else "")
            row.append(f"{pct(reg['alpha_a'])}{star}\n(t = {t:.2f})")
        else:
            row.append(cell(reg, f))
    rows.append(row)
rows.append(["Adjusted R²"] + [f"{REG[m]['r2adj']:.3f}" for m in models])
rows.append(["Observations"] + [str(REG[m]["n"]) for m in models])
table(s, ML, Inches(1.84), CW, rows, col_w=[24, 19, 19, 19, 19], size=10,
      row_h=Inches(0.44), first_bold=True,
      align=[PP_ALIGN.LEFT] + [PP_ALIGN.CENTER] * 4)
textbox(s, ML, Inches(6.10), CW, Inches(0.5),
        "*** significant at 1%   ** significant at 5%   * significant at 10%.  Newey–West "
        "heteroskedasticity- and autocorrelation-consistent standard errors, four lags. Dependent "
        "variable is the fund's monthly return in excess of the one-month Treasury bill rate.",
        size=10, color=INK3, line=1.25)
notes(s, """
The full regression output.

Read across the alpha row: seven point two, five point nine, six point six, six point five. Stable
across specifications, an alpha that collapses when you add a factor was never alpha, it was an
unmeasured exposure.

Market loading between one and one point zero five in every model, always with a t above fifteen.

Size and value significantly negative throughout. Profitability, investment and momentum all
insignificant, a meaningful negative result, because it means our excess return isn't a repackaged
quality factor.

Adjusted R-squared runs from nought point eight seven to nought point nine one five. Newey-West
standard errors with four lags throughout, which is the conservative choice, ordinary OLS errors
would have produced higher t-statistics.
""")

# A5
s = slide("A5 · Correlation structure of the holdings",
          "Average pairwise correlation of 0.40, which is real diversification inside a single theme")
fit(s, "09_corr.png", Inches(1.62), Inches(6.72))
notes(s, """
The correlation matrix.

Average pairwise correlation is nought point four zero. For eleven stocks inside a single theme
that is low.

The structure is intuitive. The three platforms cluster tightly. Microsoft and Alphabet at nought
point seven four. That's the concentration risk in tier one, and why the position cap mattered.

At the other end, the genuine diversifiers: NextEra against Schlumberger is minus nought point one
two, actually negatively correlated. That bottom-right corner is where the ballast lives, and
those low correlations produced the ten-point drawdown advantage in 2022.

It's also why the portfolio's volatility of nineteen per cent sits well below the average
constituent volatility of about twenty-nine.
""")

# A6
s = slide("A6 · The risk–return map",
          "Every holding, the portfolio and both benchmarks on realised risk and return")
fit(s, "08_riskreturn.png", Inches(1.62), Inches(6.72))
notes(s, """
The risk-return scatter, each bubble sized by target weight.

The most important feature is where the star sits, upper-left of almost every individual holding.

Only Microsoft, NextEra and Costco sit above the portfolio on return, all at comparable or higher
volatility. Meanwhile Schlumberger at forty-nine per cent volatility and Albemarle at forty-four
are far out to the right.

The portfolio ran lower volatility than every one of its eleven constituents. Combining assets
that individually carried twenty to forty-nine per cent volatility produced something that carried
nineteen. That is the argument for diversification in one picture.
""")

# A7
s = slide("A7 · The efficient frontier of our own holdings",
          "Where the fund actually landed against the best that was achievable ex post")
fit(s, "17_frontier.png", Inches(1.62), Inches(6.72))
notes(s, """
The ex-post efficient frontier from the eleven stocks we owned. Nobody could have known this in
advance, it exists only because we now know the answers.

The fund sits below and slightly right of it, which is where a real portfolio should sit. The
vertical distance at our realised volatility is about seven points of annual return. That is the
price of not having known the future.

What I find more informative is that the fund, equal weight and the ex-ante optimiser all cluster
in the same small region. Three different construction philosophies converged on nearly the same
outcome, which tells you the dominant driver was which eleven stocks we chose, not how we weighted
them.
""")

# A8
s = slide("A8 · Distribution comparison and dispersion",
          "How the fund's return distribution compares to its benchmarks, and the spread across "
          "individual holdings")
fit(s, "07_box.png", Inches(1.68), Inches(4.14))
fit(s, "32_spaghetti.png", Inches(4.26), Inches(6.72))
notes(s, """
Two supporting exhibits.

The box plot compares the four distributions directly. Our median is visibly higher than both
benchmarks, our interquartile range is tighter than the NASDAQ-100's, and our whisker extremes are
contained relative to it.

The lower chart shows dispersion across the eleven holdings. The range runs from minus twenty-four
per cent to plus three hundred and nineteen, in an eleven-stock portfolio, in a single theme, over
six years.

That dispersion is exactly why the position cap mattered. Had we been permitted a thirty per cent
position and chosen Illumina rather than Microsoft for it, and in 2016 the genomics thesis was
every bit as compelling as the cloud thesis, this would be a very different presentation.
""")

# A9
s = slide("A9 · Rolling beta and volatility",
          "Stability of the fund's market exposure and total risk through the sample")
fit(s, "16_rolling_beta.png", Inches(1.68), Inches(4.14))
fit(s, "30_rolling_vol.png", Inches(4.26), Inches(6.72))
notes(s, """
Two stability checks.

Rolling thirty-six-month beta stays between about nought point nine seven and one point zero eight
for the entire sample. We didn't drift into higher-beta positioning as markets rose, which is a
common and destructive pattern in growth funds.

Rolling twelve-month volatility below shows the regime: calm through 2017, the COVID spike, a quiet
2021, then the sustained rise through 2022. Our line sits below the NASDAQ-100's for most of the
sample. Less total risk than our own benchmark, more return, which is the argument this entire
deck has been making.
""")

# A10
s = slide("A10 · Month-of-year seasonality and the fee comparison",
          "Supporting detail on the seasonality discussion and the fee benchmarking")
fit(s, "11_month_avg.png", Inches(1.70), Inches(4.16))
def fee6(rate):
    return f"${rate * 100e6 * 6 / 1e6:,.2f}m"
rows = [["Comparator", "Fee p.a.", "6-year fee on $100m", "Return delivered", "Terminal value"],
        ["Passive S&P 500 ETF (SPY)", "0.0945%", fee6(0.000945), pct(ST[S]["cum_return"], 0),
         f"${ST[S]['terminal']/1e6:,.0f}m"],
        ["Passive NASDAQ-100 ETF (QQQ)", "0.20%", fee6(0.0020), pct(ST[Q]["cum_return"], 0),
         f"${ST[Q]['terminal']/1e6:,.0f}m"],
        ["Typical active equity fund", "1.25%", fee6(0.0125), "—", "—"],
        ["Northpoint Digital Innovation Fund", "1.15% all-in", fee6(0.0115),
         pct(ST[N]["cum_return"], 0), f"${ST[N]['terminal']/1e6:,.0f}m"]]
table(s, ML, Inches(4.36), CW, rows, col_w=[30, 15, 19, 17, 19], size=10.5,
      row_h=Inches(0.34), first_bold=True,
      align=[PP_ALIGN.LEFT] + [PP_ALIGN.RIGHT] * 4)
textbox(s, ML, Inches(6.18), CW, Inches(0.5),
        "Fees are calculated on a static $100m for comparability. Northpoint's all-in load of 1.15% "
        "sits 0.95 points above a passive NASDAQ-100 ETF, which costs $5.7m more over six years. "
        "The fund delivered $44.4m of additional terminal value, so investors kept $38.7m after "
        "paying for active management.",
        size=11, color=INK2, line=1.25)
notes(s, """
Two pieces of supporting detail.

The chart is the month-of-year seasonality. July strongest, September weakest. Six observations per
month, so description rather than signal.

The table is the fee benchmarking. A passive S&P 500 ETF costs nine basis points and returned
ninety per cent. A NASDAQ-100 ETF costs twenty and returned a hundred and thirty-five. We cost one
point one five per cent all-in and returned a hundred and seventy-nine.

The arithmetic: we cost five point seven million more than the NASDAQ ETF and delivered
forty-four point four million more in terminal value. Investors kept thirty-eight point seven
million after every dollar of fee.

I put this in the appendix deliberately, a manager should be prepared to defend a fee on request,
not only when it flatters them.
""")

# A11
s = slide("A11 · References and declarations",
          "Sources, academic references, and the required statement on the use of generative AI")
rect(s, ML, Inches(1.80), Inches(6.4), Inches(4.72), WHITE, RULE)
textbox(s, ML + Inches(0.26), Inches(2.00), Inches(5.9), Inches(0.3), "REFERENCES",
        size=10, color=GOLD, bold=True)
refs = ("Brinson, G. P., Hood, L. R., & Beebower, G. L. (1986). Determinants of portfolio "
        "performance. Financial Analysts Journal, 42(4), 39–44.\n"
        "DeMiguel, V., Garlappi, L., & Uppal, R. (2009). Optimal versus naive diversification. "
        "The Review of Financial Studies, 22(5), 1915–1953.\n"
        "Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and "
        "bonds. Journal of Financial Economics, 33(1), 3–56.\n"
        "Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. Journal of "
        "Financial Economics, 116(1), 1–22.\n"
        "Jensen, M. C. (1968). The performance of mutual funds in the period 1945–1964. The "
        "Journal of Finance, 23(2), 389–416.\n"
        "Markowitz, H. (1952). Portfolio selection. The Journal of Finance, 7(1), 77–91.\n"
        "Newey, W. K., & West, K. D. (1987). A simple, positive semi-definite, "
        "heteroskedasticity and autocorrelation consistent covariance matrix. Econometrica, "
        "55(3), 703–708.\n"
        "Sharpe, W. F. (1966). Mutual fund performance. The Journal of Business, 39(1), 119–138.\n"
        "Sortino, F. A., & Price, L. N. (1994). Performance measurement in a downside risk "
        "framework. The Journal of Investing, 3(3), 59–64.\n"
        "Treynor, J. L. (1965). How to rate management of investment funds. Harvard Business "
        "Review, 43(1), 63–75.\n\n"
        "Data: Kenneth R. French Data Library (factor and risk-free series); dividend-adjusted "
        "monthly closing prices for all eleven holdings, the eleven SPDR sector ETFs, QQQ, SPY "
        "and AGG.")
textbox(s, ML + Inches(0.26), Inches(2.36), Inches(5.9), Inches(4.0), refs, size=9,
        color=INK2, line=1.32)
rx = ML + Inches(6.68)
rect(s, rx, Inches(1.80), CW - Inches(6.68), Inches(4.72), WHITE, RULE)
textbox(s, rx + Inches(0.26), Inches(2.00), Inches(4.9), Inches(0.3),
        "GENERATIVE AI USE DECLARATION", size=10, color=GOLD, bold=True)
ai = [("Assessment classification.", "AI-Supported. Generative AI was permitted for the "
       "preparation of the analysis and slides; the presentation itself is delivered by the author."),
      ("Tools used.", "Generative AI assistant for the Python analysis code, chart generation and "
       "slide drafting; Grammarly for language editing."),
      ("Purpose.", "Writing the return, risk and regression code; producing the visualisations; "
       "structuring the deck; drafting speaker notes."),
      ("Human refinement.", "As Portfolio Manager I set the analytical scope, chose the benchmarks "
       "and factor models, interpreted every result, wrote the investment narrative and "
       "recommendation, and verified the outputs against the underlying data."),
      ("Data integrity.", "All market data was retrieved programmatically from primary sources. No "
       "figure in this deck was generated by an AI model without a reproducible calculation "
       "behind it.")]
bullets(s, rx + Inches(0.26), Inches(2.36), CW - Inches(7.22), ai, size=10.5,
        gap=Inches(0.26))
notes(s, """
References and declarations.

The methodology follows the standard literature: Jensen for alpha, Sharpe, Sortino and Treynor for
the ratios, Fama and French for the factor models, Brinson for attribution, Markowitz for the
frontier, Newey and West for the standard-error correction.

On AI use: this assessment is classified as AI-Supported. I've declared the tools and, more
importantly, the division of labour. The analytical scope, the choice of benchmarks and models, the
interpretation of every result and the recommendation are mine. Every number traces back to a
reproducible calculation on primary market data, and the code and workbook accompany this
submission.
""")

path = os.path.join(OUT, "FINC13303_Ass2_PortfolioPerformance_14053836_OConnor.pptx")
prs.save(path)
print(f"saved {path}")
print(f"slides: {len(prs.slides.__iter__.__self__._sldIdLst)}")
