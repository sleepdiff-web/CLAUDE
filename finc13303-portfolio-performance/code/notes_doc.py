"""Export the speaker notes as a presenter script (Word .docx)."""
import os, re
from pptx import Presentation
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)          # repository sub-directory root
DATA = os.path.join(BASE, "data")
OUT = os.path.join(BASE, "deliverables")
SRC = os.path.join(OUT, "FINC13303_Ass2_PortfolioPerformance_14053836_OConnor.pptx")

prs = Presentation(SRC)
doc = Document()
for sec in doc.sections:
    sec.top_margin = sec.bottom_margin = Inches(0.9)
    sec.left_margin = sec.right_margin = Inches(1.0)
st = doc.styles["Normal"]
st.font.name = "Corbel"; st.font.size = Pt(11)
st.paragraph_format.space_after = Pt(8)
st.paragraph_format.line_spacing = 1.25

PINE = RGBColor(0x0D, 0x3B, 0x38)
RUST = RGBColor(0xC4, 0x55, 0x1A)
NAVY = PINE
GREY = RGBColor(0x4A, 0x44, 0x3C)

def para(text, size=11, bold=False, color=None, align=None, after=8, before=0,
         italic=False, font=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.space_before = Pt(before)
    if align:
        p.alignment = align
    r = p.add_run(text)
    r.font.size = Pt(size); r.bold = bold; r.italic = italic
    if color:
        r.font.color.rgb = color
    if font:
        r.font.name = font
    return p

para("Northpoint Digital Innovation Fund", 24, False, PINE, after=2, font="Georgia")
para("Six-year performance review — presenter script", 14, False, GREY, after=14)
para("Callum O'Connor  ·  Student ID 14053836  ·  FINC13-303 Portfolio Analysis and "
     "Investments  ·  Assignment 2, Part 1", 10, False, GREY, after=6)
para("Target delivery: 22–26 minutes at a measured pace, plus questions. Slide titles below "
     "match the deck exactly. Bold slide numbers correspond to the on-screen page numbers.",
     10, False, GREY, italic=True, after=16)

def slide_title(s):
    best = None
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        t = sh.text_frame.text.strip()
        if not t:
            continue
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size and r.font.size.pt >= 26:
                    return t.replace("\n", " ")
        if best is None and len(t) < 90:
            best = t.replace("\n", " ")
    return best or "(section divider)"

total_words = 0
main_words = 0
APPENDIX_FROM = 38
for i, s in enumerate(prs.slides, start=1):
    title = slide_title(s)
    notes = ""
    if s.has_notes_slide:
        notes = s.notes_slide.notes_text_frame.text.strip()
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16); p.paragraph_format.space_after = Pt(4)
    r = p.add_run(f"{i:02d}")
    r.bold = True; r.font.size = Pt(10); r.font.color.rgb = RUST
    r = p.add_run(f"   {title}")
    r.font.size = Pt(13.5); r.font.color.rgb = PINE; r.font.name = "Georgia"
    if not notes:
        para("(no narration — section divider, hold for two seconds and move on)", 10,
             False, GREY, italic=True)
        continue
    words = len(notes.split())
    total_words += words
    if i < APPENDIX_FROM:
        main_words += words
    para(f"~{words} words  ·  approx. {words/150:.1f} min at 150 wpm", 9, False, GREY,
         italic=True, after=6)
    for block in [b.strip() for b in notes.split("\n\n") if b.strip()]:
        para(" ".join(block.split()), 11)

doc.add_page_break()
para("Delivery notes", 18, False, PINE, after=8, font="Georgia")
para(f"Main body (slides 1–37): {main_words:,} words — about {main_words/160:.0f} minutes at a "
     f"brisk 160 words per minute, {main_words/150:.0f} minutes at a measured 150. "
     f"Appendix (slides 38–49): {total_words-main_words:,} words, spoken only if a question "
     f"takes you there.", 11, after=10)
for t in [
    ("Pace.", "The script is written to be spoken, not read. Do not read it verbatim on "
     "camera — know the two or three numbers on each slide and let the rest come out in "
     "your own words."),
    ("If you are running long.", "The submission window is 15–30 minutes. The main body is "
     "written to land at roughly 29 minutes, so you have very little slack. The safest cuts, in "
     "order: slide 8 (macro regimes) down to two sentences per regime, slide 18 (seasonality) "
     "down to the July/September contrast, and slide 11 (2016 scenarios) down to the single "
     "\u201cright about direction, wrong about magnitude\u201d point. That recovers about "
     "three minutes without touching any of the four slides that carry the grade."),
    ("The four slides that carry the grade.", "Slide 3 (the six-year result), slide 21 "
     "(the risk-adjusted scorecard), slide 25 (Jensen's alpha) and slide 30 (attribution). "
     "If you are running long, compress elsewhere and give these their full time."),
    ("Camera.", "Look into the webcam, not at the slides. When you point at a chart, say "
     "where to look — “top left of your screen”, “the orange line” — because your audience "
     "cannot see your cursor reliably on a shared screen."),
    ("Backdrop and audio.", "Plain wall or a clean virtual background. Use a headset "
     "microphone; laptop microphones pick up room echo, which reads as unprofessional even "
     "when the content is strong."),
    ("Handling the weak spots.", "Two facts an examiner will probe: you underperformed the "
     "NASDAQ-100 in 2020, and essentially all of your outperformance against it was earned "
     "in 2022. Both are addressed head-on in slides 14 and 15 — do not skip them, because "
     "raising them yourself is what makes the rest of the presentation credible."),
    ("Closing.", "End on the recommendation, not on the appendix. Say “I am happy to take "
     "questions” and stop talking."),
]:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(t[0] + "  "); r.bold = True; r.font.size = Pt(11); r.font.color.rgb = NAVY
    r = p.add_run(t[1]); r.font.size = Pt(11)

path = os.path.join(OUT, "FINC13303_Ass2_PresenterScript_14053836_OConnor.docx")
doc.save(path)
print("saved", path)
print("script words:", total_words, f"({total_words/150:.1f} min at 150 wpm)")
