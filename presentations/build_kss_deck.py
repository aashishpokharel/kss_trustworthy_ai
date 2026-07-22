"""
Build KSS — Trustworthy AI slide deck.
Extends KSS_template.pptx using its existing layouts and visual language.
Follows KSS_Slide_Agent_Architecture.md spec (Section 1 rulebook, 8-step workflow).

Template visual conventions preserved:
  - Titles via placeholder (Arial, bold, theme-inherited sizing ~30pt)
  - Body text in Montserrat (matching template Slides 5-6 convention)
  - Theme colors: BLUE #2074B9, TEAL #2EBFCA, AMBER #FDBA4D, GREEN #8BB762, RED #E85B5B
  - No custom accent bars/stripes beyond what template defines
  - Content slides use standard layouts (TITLE_AND_BODY, TITLE_AND_TWO_COLUMNS, TITLE_ONLY)
"""

import copy
import os
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn, nsmap

# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════

TEMPLATE_PATH = "KSS_template.pptx"
OUTPUT_PATH = "presentations/KSS_output.pptx"
os.makedirs("presentations", exist_ok=True)

prs = Presentation(TEMPLATE_PATH)
SW = prs.slide_width   # 9144000 EMU = 10.00"
SH = prs.slide_height  # 5143500 EMU = 5.62"

# ── Template Theme Colors (from ppt/theme/theme1.xml "Simple Light") ──
BLUE   = RGBColor(0x20, 0x74, 0xB9)  # accent1
LTBLUE = RGBColor(0x58, 0xA4, 0xE2)  # accent2
TEAL   = RGBColor(0x2E, 0xBF, 0xCA)  # accent3
AMBER  = RGBColor(0xFD, 0xBA, 0x4D)  # accent4
GREEN  = RGBColor(0x8B, 0xB7, 0x62)  # accent5
RED    = RGBColor(0xE8, 0x5B, 0x5B)  # accent6
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)  # lt1
BLACK  = RGBColor(0x00, 0x00, 0x00)  # dk1
DARK   = RGBColor(0x3A, 0x3A, 0x3A)  # dk2
GRAY   = RGBColor(0x4E, 0x4F, 0x50)  # lt2

# ── Extended semantic colors (derived from theme) ──
PURPLE     = RGBColor(0x6B, 0x46, 0xC1)
NAVY_DARK  = RGBColor(0x1A, 0x5C, 0x8A)  # Darker blue, derived from accent1
TEAL_LIGHT = RGBColor(0xE0, 0xF7, 0xF9)  # Light teal, derived from accent3
AMBER_LIGHT = RGBColor(0xFF, 0xF5, 0xE0)  # Light amber
RED_LIGHT  = RGBColor(0xFD, 0xEC, 0xEC)   # Light red
BLUE_LIGHT = RGBColor(0xE3, 0xF0, 0xFA)   # Light blue
GRAY_LIGHT = RGBColor(0xF0, 0xF2, 0xF5)   # Light neutral

PRINCIPLE_COLORS = {
    "Fairness":       RED,
    "Transparency":   BLUE,
    "Accountability": GREEN,
    "Robustness":     AMBER,
    "Privacy":        PURPLE,
    "Reliability":    TEAL,
}

# Fonts (matching template convention: Arial=titles, Montserrat=body, Calibri=supplemental)
FONT_TITLE = "Arial"
FONT_BODY  = "Montserrat"
FONT_ALT   = "Calibri"

# ── Layout indices (from template) ──
LAYOUTS = {lay.name: i for i, lay in enumerate(prs.slide_layouts)}
# 0=TITLE, 1=SECTION_HEADER, 2=TITLE_AND_BODY, 3=TITLE_AND_TWO_COLUMNS,
# 4=TITLE_ONLY, 5=ONE_COLUMN_TEXT, 6=MAIN_POINT, 7=SECTION_TITLE_AND_DESCRIPTION,
# 8=CAPTION_ONLY, 9=BIG_NUMBER, 10=BLANK

# ══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════

def _emu(inches):
    return int(inches * 914400)

def _in(emu):
    return emu / 914400

def add_slide(layout_name):
    """Add a new slide using a template layout."""
    idx = LAYOUTS[layout_name]
    return prs.slides.add_slide(prs.slide_layouts[idx])

def set_title(slide, text):
    """Set the title placeholder text on a slide."""
    try:
        ph = slide.placeholders[0]
        ph.text = ""
        p = ph.text_frame.paragraphs[0]
        p.text = text
        # Title font is inherited from theme (Arial, bold) — keep defaults
        return ph
    except (IndexError, KeyError):
        return None

def set_subtitle(slide, text):
    """Set the subtitle placeholder text (for TITLE layout)."""
    try:
        ph = slide.placeholders[1]
        ph.text = ""
        p = ph.text_frame.paragraphs[0]
        p.text = text
        run = p.runs[0] if p.runs else p.add_run()
        run.font.name = FONT_BODY
        run.font.size = Pt(16)
        return ph
    except (IndexError, KeyError):
        return None

def add_body_text(slide, left, top, width, height, lines, font_size=14,
                  color=DARK, bold_first=False, line_spacing=1.35, font_name=FONT_BODY):
    """Add a multi-line text box in the content area."""
    txBox = slide.shapes.add_textbox(
        Inches(_in(left)), Inches(_in(top)),
        Inches(_in(width)), Inches(_in(height)))
    txBox.text_frame.word_wrap = True
    for i, line in enumerate(lines):
        p = txBox.text_frame.paragraphs[0] if i == 0 else txBox.text_frame.add_paragraph()
        p.text = line
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = font_name
        p.line_spacing = Pt(font_size * line_spacing)
        p.space_after = Pt(4)
        if bold_first and i == 0:
            p.font.bold = True
    return txBox

def add_single_text(slide, left, top, width, height, text, font_size=14,
                    bold=False, color=DARK, font_name=FONT_BODY, align=PP_ALIGN.LEFT,
                    line_spacing=None):
    """Add a single-line text box."""
    txBox = slide.shapes.add_textbox(
        Inches(_in(left)), Inches(_in(top)),
        Inches(_in(width)), Inches(_in(height)))
    txBox.text_frame.word_wrap = True
    p = txBox.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align
    if line_spacing:
        p.line_spacing = Pt(font_size * line_spacing)
    return txBox

def add_rect(slide, left, top, width, height, fill=None, border=None, radius=None):
    """Add a filled rectangle."""
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type, Inches(_in(left)), Inches(_in(top)),
        Inches(_in(width)), Inches(_in(height)))
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if border:
        shape.line.color.rgb = border
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def add_colored_badge(slide, left, top, width, height, label, fill_color):
    """A small rounded rectangle with white centered text."""
    shape = add_rect(slide, left, top, width, height, fill=fill_color, radius=0.1)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT_BODY
    p.alignment = PP_ALIGN.CENTER
    return shape

def add_speaker_notes(slide, text):
    """Set speaker notes on a slide."""
    try:
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = text
    except Exception:
        pass  # Notes slide might not exist yet

def remove_unused_placeholders(slide, keep_indices=(0,)):
    """Remove body/subtitle placeholders that won't be filled.
    Call this on slides where custom shapes replace the default body content."""
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx not in keep_indices:
            # Remove the placeholder shape from the slide XML
            sp = ph._element
            sp.getparent().remove(sp)

def update_placeholder_text(shape, new_text, font_name=None, font_size=None,
                            bold=None, color=None):
    """Update text in an existing shape, preserving formatting."""
    tf = shape.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    p.text = new_text
    if font_name or font_size or bold is not None or color:
        run = p.runs[0] if p.runs else p.add_run()
        if font_name:
            run.font.name = font_name
        if font_size:
            run.font.size = Pt(font_size)
        if bold is not None:
            run.font.bold = bold
        if color:
            run.font.color.rgb = color
    return p

def build_three_column_card(slide, x, y, col_w, card_h, title, title_color, lines, bg_color=None, border_color=None):
    """Build a single card in a three-column layout. Returns bottom y."""
    # Title bar
    add_rect(slide, x, y, col_w, 0.45, fill=title_color, radius=0.06)
    add_single_text(slide, x + 0.1, y + 0.05, col_w - 0.2, 0.35,
                    title, font_size=11, bold=True, color=WHITE)
    # Body
    body_bg = bg_color or WHITE
    body_border = border_color or GRAY_LIGHT
    add_rect(slide, x, y + 0.45, col_w, card_h, fill=body_bg, border=body_border, radius=0.06)
    add_body_text(slide, x + 0.12, y + 0.55, col_w - 0.24, card_h - 0.2,
                  lines, font_size=12, color=DARK, line_spacing=1.3, font_name=FONT_BODY)
    return y + 0.45 + card_h

# ══════════════════════════════════════════════════════════════════════════
# STEP 3: STRUCTURAL WORK — Edit existing template slides + add new ones
# ══════════════════════════════════════════════════════════════════════════

# We'll edit slides 0-6 (existing template) and append new slides.
# At the end, we'll reorder via sldIdLst manipulation.

# Track which existing slide indices map to which logical slides
existing = list(prs.slides)  # snapshot of 7 template slides

print("=== Repurposing existing template slides (1-7) ===")

# ── SLIDE 1: Title (existing slide 0, TITLE layout) ──
slide = existing[0]
# Keep the existing title text (it already says "KSS - Trustworthy AI")
# Add a subtitle
try:
    sub_ph = slide.placeholders[1]
    sub_ph.text = ""
    p = sub_ph.text_frame.paragraphs[0]
    p.text = "From Explainability to Verifiable Trust:\nA Framework for Building AI Systems People Can Rely On"
    for run in p.runs:
        run.font.name = FONT_BODY
        run.font.size = Pt(16)
        run.font.color.rgb = WHITE
except Exception:
    pass
add_speaker_notes(slide, (
    "Welcome everyone. Today's session is about Trustworthy AI — not as a buzzword, "
    "but as an engineering discipline with concrete properties we can measure, verify, "
    "and build against. We'll work through what trustworthy AI actually means under "
    "the NIST AI RMF definition, why explainability alone isn't enough, the six core "
    "principles, how they connect to causal reasoning, and then ground everything "
    "in what our codebase actually implements against each principle."
))
print("  Slide 1: Title — kept, added subtitle + speaker notes")

# ── SLIDE 2: Agenda (existing slide 1, Overview with 2 groups) ──
slide = existing[1]
agenda_topics_s2 = [
    ("1", "Why Trustworthy AI Matters", "The stakes have shifted — AI now makes consequential decisions"),
    ("2", "The Explainability Trap", "Why \"we can explain it\" does not mean \"we can trust it\""),
]
# Collect groups and sort by top position
groups_s2 = [s for s in slide.shapes if s.shape_type == 6]
groups_s2.sort(key=lambda g: g.top)
for gi, shape in enumerate(groups_s2):
    if gi >= len(agenda_topics_s2):
        break
    num, title, desc = agenda_topics_s2[gi]
    for child in shape.shapes:
        if child.has_text_frame:
            tf = child.text_frame
            text = tf.text.strip()
            # Identify by content: number overlay vs title text
            if text in ("1", "2"):
                # This is the number overlay — update it
                if tf.paragraphs[0].runs:
                    tf.paragraphs[0].runs[0].text = num
            elif text in ("Topic 1", "Topic 2"):
                # This is the topic title text — update with title + newline + description
                if tf.paragraphs[0].runs:
                    tf.paragraphs[0].runs[0].text = title
                # Add description as second paragraph
                # Clear any existing second paragraph
                for extra_p in list(tf.paragraphs)[1:]:
                    extra_p.getparent().remove(extra_p)
                p2 = tf.add_paragraph()
                p2.text = desc
                p2.font.name = FONT_BODY
                p2.font.size = Pt(11)
                p2.font.color.rgb = GRAY
            elif not text:
                # Empty text child — may be the title box in some group variants
                # Check if this is the wide text box (title area based on position)
                if child.width > 5000000:  # wide text box = title area
                    if tf.paragraphs[0].runs:
                        tf.paragraphs[0].runs[0].text = title
                    elif tf.paragraphs[0].text == "":
                        tf.paragraphs[0].text = title
                    # Add description
                    for extra_p in list(tf.paragraphs)[1:]:
                        extra_p.getparent().remove(extra_p)
                    p2b = tf.add_paragraph()
                    p2b.text = desc
                    p2b.font.name = FONT_BODY
                    p2b.font.size = Pt(11)
                    p2b.font.color.rgb = GRAY
            else:
                # Unknown text content - skip
                pass
add_speaker_notes(slide, (
    "Six sections today, each building on the last. We start with motivation — why "
    "this isn't optional anymore — then the conceptual hinge: why the industry's "
    "default answer ('just make it explainable') isn't sufficient. From there we "
    "build up the actual principles, map the vocabulary, connect to causal reasoning, "
    "and then ground everything in our implementation."
))
print("  Slide 2: Agenda — filled numbered groups")

# ── SLIDE 3: Agenda Continued (existing slide 2, 3 empty groups) ──
slide = existing[2]
agenda_continued = [
    ("3", "Core Principles", "Fairness, Transparency, Accountability, Robustness, Privacy, Reliability"),
    ("4", "XAI × Causal AI", "Why correlational explanations aren't enough for trust"),
    ("5", "Our Codebase, Mapped", "What we've built against each principle — and what we haven't"),
]

# Collect groups and sort by top position for visual order
groups = [s for s in slide.shapes if s.shape_type == 6]
groups.sort(key=lambda g: g.top)

for group_idx, shape in enumerate(groups):
    if group_idx >= len(agenda_continued):
        break
    num, title, desc = agenda_continued[group_idx]
    for child in shape.shapes:
        if child.has_text_frame:
            tf = child.text_frame
            text = tf.text.strip()
            # AUTO_SHAPE (blue square) with the number
            if child.shape_type == 1 and text in ("1", "2", "3", "4", "5"):
                if tf.paragraphs[0].runs:
                    tf.paragraphs[0].runs[0].text = num
            # TEXT_BOX number overlay (like Group 0 child "1")
            elif child.shape_type == 17 and text in ("1", "2", "3", "4", "5"):
                if tf.paragraphs[0].runs:
                    tf.paragraphs[0].runs[0].text = num
            # TEXT_BOX — wide title area (empty or tab in template)
            elif child.shape_type == 17 and (text in ("", "\t") or child.width > 5000000):
                # This is the topic title text box — fill it
                if tf.paragraphs[0].runs:
                    tf.paragraphs[0].runs[0].text = title
                elif tf.paragraphs[0].text in ("", "\t"):
                    tf.paragraphs[0].text = title
                # Add description paragraph
                for extra_p in list(tf.paragraphs)[1:]:
                    extra_p.getparent().remove(extra_p)
                p2 = tf.add_paragraph()
                p2.text = desc
                p2.font.name = FONT_BODY
                p2.font.size = Pt(11)
                p2.font.color.rgb = GRAY
add_speaker_notes(slide, (
    "Agenda continued: the Core Principles section covers all six NIST-aligned principles "
    "one slide per principle with definition, failure modes, and concrete techniques. "
    "XAI × Causal AI explores why production XAI methods explain correlation, not causation. "
    "The final section maps every concept back to our actual codebase implementation."
))
print("  Slide 3: Agenda Continued — filled 3 numbered groups")

# ── SLIDE 4: What Is Trustworthy AI (existing slide 3, TITLE_ONLY) ──
slide = existing[3]
set_title(slide, "What Is Trustworthy AI?")
# Replace <Text Here>
for shape in slide.shapes:
    if shape.has_text_frame and "<Text Here>" in shape.text_frame.text:
        update_placeholder_text(shape,
            "Trustworthy AI = an AI system whose behavior can be justifiably\n"
            "relied upon by the people affected by it.",
            font_name=FONT_BODY, font_size=16, bold=True, color=DARK)
    elif shape.has_text_frame and "<Notes>" in shape.text_frame.text:
        update_placeholder_text(shape,
            "Not \"AI that feels okay\" — AI with demonstrable, verifiable properties.\n\n"
            "NIST AI RMF defines trustworthy AI through seven characteristics.\n"
            "\"Explainable\" is one of seven — not the whole definition.",
            font_name=FONT_BODY, font_size=14, color=DARK)
    # Remove the existing image placeholder (ML infrastructure diagram — not relevant)
    elif shape.shape_type == 13:  # PICTURE
        sp = shape._element
        sp.getparent().remove(sp)

# Add seven NIST characteristic badges below the existing content
nist_chars = [
    ("Valid &\nReliable", TEAL),
    ("Safe", RED),
    ("Secure &\nResilient", PURPLE),
    ("Accountable &\nTransparent", GREEN),
    ("Explainable &\nInterpretable", AMBER),
    ("Privacy-\nEnhanced", GRAY),
    ("Fair — Harmful\nBias Managed", RED),
]
for i, (label, color) in enumerate(nist_chars):
    x = _emu(0.45) + i * _emu(1.28)
    y = _emu(4.1)
    shape = add_rect(slide, x, y, 1.15, 1.05, fill=WHITE, border=color, radius=0.08)
    shape.line.width = Pt(2)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = color
    p.font.name = FONT_BODY
    p.alignment = PP_ALIGN.CENTER

add_speaker_notes(slide, (
    "Let's anchor on a precise definition immediately. The NIST AI Risk Management "
    "Framework defines trustworthy AI through seven characteristics. I want to call "
    "out explicitly: explainability is ONE of seven — not the whole definition. "
    "A lot of industry discourse treats 'explainable' as synonymous with 'trustworthy,' "
    "and that conflation is exactly what we'll unpack next."
))
print("  Slide 4: What Is Trustworthy AI — filled placeholders, added NIST badges")

# ── SLIDE 5: Why Do We Need Trustworthy AI (existing slide 4, TITLE_AND_BODY) ──
slide = existing[4]
set_title(slide, "Why Do We Need Trustworthy AI?")
# Replace body text
for shape in slide.shapes:
    if shape.has_text_frame and "Something related to question" in shape.text_frame.text:
        update_placeholder_text(shape,
            "AI moved from recommendation systems (wrong answer = mild annoyance)\n"
            "to decision-making and agentic systems (wrong answer = financial loss,\n"
            "legal exposure, physical harm, denied opportunity).\n\n"
            "Three concrete failure categories — not abstract assertions:\n\n"
            "  Silent Failure — confidently wrong with no error signal\n"
            "  Adversarial Failure — manipulated by prompt injection, jailbreak, poisoning\n"
            "  Systemic Failure — individually correct predictions, harmful aggregate outcomes",
            font_name=FONT_BODY, font_size=17, color=DARK)
add_speaker_notes(slide, (
    "The fundamental shift: AI moved from recommending movies to making consequential "
    "decisions. Three concrete failure categories. Silent failure: the model is "
    "confidently wrong with no error signal. Adversarial failure: a bad actor "
    "deliberately manipulates the system. Systemic failure: individually correct "
    "predictions producing disparate impact across a protected group."
))
print("  Slide 5: Why This Matters — filled title and body")

# ── SLIDE 6: The Explainability Trap (existing slide 5, TITLE_AND_BODY) ──
slide = existing[5]
set_title(slide, "The Explainability Trap")
# This slide has one body shape with two text blocks:
# "<Something related to question(in red)>" and "<The answer>"
# They may be separate paragraphs or runs in the same shape.
for shape in slide.shapes:
    if shape.has_text_frame and "Something related to question" in shape.text_frame.text:
        tf = shape.text_frame
        # Update individual paragraphs based on their content
        for para in tf.paragraphs:
            para_text = para.text
            if "Something related to question" in para_text:
                # Update the red question paragraph
                for run in para.runs:
                    run.text = ""
                para.runs[0].text = "Why does \"we can explain it\""
                # Add another run for the second line
                run2 = para.add_run()
                run2.text = "\nno longer mean \"we can trust it\"?"
                # Set formatting
                for run in para.runs:
                    run.font.name = FONT_BODY
                    run.font.size = Pt(22)
                    run.font.bold = True
                    run.font.color.rgb = RED
            elif "The answer" in para_text:
                # Update the answer paragraph
                answer_text = (
                    "Five reasons the old assumption breaks down:\n\n"
                    "1. SHAP values are locally faithful but globally silent\n"
                    "2. Post-hoc explanations explain correlation, not causation\n"
                    "3. Explainable ≠ Fair, Secure, Private, or Reliable\n"
                    "4. LLMs hallucinate their own explanations\n"
                    "5. Adversarial robustness is orthogonal to explainability"
                )
                for run in para.runs:
                    run.text = ""
                para.runs[0].text = answer_text
                for run in para.runs:
                    run.font.name = FONT_BODY
                    run.font.size = Pt(16)
                    run.font.bold = False
                    run.font.color.rgb = DARK
        break  # Only process the first matching shape
add_speaker_notes(slide, (
    "This is the conceptual hinge. The historical assumption was reasonable when "
    "models were simpler. It doesn't hold anymore. Five distinct failure modes, "
    "each with concrete examples. Walk through each one."
))
print("  Slide 6: Explainability Trap — filled red question + answer")

# ── SLIDE 7: Codebase Mapping Table (existing slide 6, TITLE_AND_BODY with table) ──
slide = existing[6]
set_title(slide, "Codebase → Framework Mapping")
# Find and update the table
for shape in slide.shapes:
    if shape.has_table:
        table = shape.table
        # The template has a 4-row empty table. We need 9 rows.
        # Since python-pptx can't easily add/remove table rows, we'll remove the
        # existing table and add a new one in the same position
        left, top, width, height = shape.left, shape.top, shape.width, shape.height
        sp = shape._element
        sp.getparent().remove(sp)
        # Add new table
        rows, cols = 9, 2
        tbl_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
        tbl = tbl_shape.table
        tbl.columns[0].width = int(width * 0.45)
        tbl.columns[1].width = int(width * 0.55)

        data = [
            ("Principle / Concept", "What We Built"),
            ("Fairness (bias detection)",
             "Counterfactual test suite — same technique described in Core Principles"),
            ("Transparency / Accountability",
             "Governance plane, append-only audit log, policy-versioned constitution document"),
            ("Robustness / Safety (adversarial)",
             "Red-team harness (Garak / PyRIT), prompt injection defenses, input sanitization"),
            ("Privacy",
             "PII detection/redaction pipeline (Presidio-based). ⚠ Honest note: this is redaction/tokenization, not differential privacy."),
            ("Reliability",
             "Groundedness / hallucination checks, scheduled eval cadence, drift monitoring"),
            ("Human-AI collaboration",
             "HITL approval queue surfacing model reasoning vs. action divergence"),
            ("Regulatory (NIST functions)",
             "Govern → policy docs; Map → data classification tiers; Measure → eval suite; Manage → incident review loop"),
            ("Explainability vs. trustworthiness",
             "What we do NOT do: model-internals interpretability. Guardrails and governance, not SHAP/LIME integration."),
        ]
        for r, (left_text, right_text) in enumerate(data):
            for c, text in enumerate([left_text, right_text]):
                cell = tbl.cell(r, c)
                cell.text = ""
                p = cell.text_frame.paragraphs[0]
                p.text = text
                p.font.name = FONT_BODY
                p.font.size = Pt(12) if r > 0 else Pt(14)
                p.font.bold = (r == 0)
                if r == 0:
                    p.font.color.rgb = WHITE
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = BLUE
                elif r % 2 == 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = GRAY_LIGHT
                else:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = WHITE
                cell.margin_left = Inches(0.1)
                cell.margin_right = Inches(0.1)
                cell.margin_top = Inches(0.04)
                cell.margin_bottom = Inches(0.04)
        break  # only process the first table
add_speaker_notes(slide, (
    "This table is the payoff — every principle mapped to actual implementation. "
    "Walk through each row, connecting back to the relevant principle slide. "
    "The last row is the honesty row: we do NOT do model-internals interpretability."
))
print("  Slide 7: Codebase Mapping Table — replaced with full 9-row table")

# ══════════════════════════════════════════════════════════════════════════
# ADD NEW SLIDES (using template layouts)
# ══════════════════════════════════════════════════════════════════════════

print("\n=== Adding new slides (8-24) ===")

# ── SLIDE 8: Three Failure Categories ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Three Ways AI Systems Fail")
failures = [
    "●  Silent Failure — A model confidently wrong (hallucination, biased denial)",
    "     with no signal that anything went wrong. The system doesn't know",
    "     it doesn't know.",
    "",
    "●  Adversarial Failure — A system manipulated by a bad actor (prompt",
    "     injection, data poisoning, jailbreak). The model is functioning",
    "     exactly as designed; the input isn't.",
    "",
    "●  Systemic Failure — Individually \"correct\" predictions producing harmful",
    "     aggregate outcomes. Disparate impact across a protected group with",
    "     no single wrong prediction — this is why you can't evaluate",
    "     trustworthiness one prediction at a time.",
]
add_body_text(slide, _emu(0.45), _emu(1.6), _emu(9.1), _emu(3.5),
              failures, font_size=15, color=DARK, line_spacing=1.5, font_name=FONT_BODY)
add_speaker_notes(slide, (
    "Three concrete categories. Silent failure: hallucination is the canonical "
    "example. Adversarial failure: the model itself is functioning as designed — "
    "the input distribution has been weaponized. Systemic failure: disparate impact "
    "is the canonical example; you can't evaluate trustworthiness one prediction "
    "at a time."
))
print("  Slide 8: Three Failure Categories")

# ── SLIDE 9: Regulatory Reality ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Regulatory Reality: Trustworthiness Is No Longer Optional")
# Left column: EU AI Act
add_rect(slide, _emu(0.35), _emu(1.6), _emu(4.35), _emu(3.4), fill=WHITE, border=GRAY_LIGHT, radius=0.08)
add_rect(slide, _emu(0.35), _emu(1.6), _emu(4.35), _emu(0.5), fill=RED, radius=0.06)
add_single_text(slide, _emu(0.5), _emu(1.65), _emu(4.0), _emu(0.4),
                "EU AI Act — Binding Law", font_size=14, bold=True, color=WHITE, font_name=FONT_BODY)
eu_lines = [
    "Unacceptable risk → Prohibited",
    "High risk → Strict obligations (conformity",
    "  assessment, human oversight, transparency)",
    "Limited risk → Transparency obligations only",
    "Minimal risk → No mandatory obligations",
    "",
    "▸ Most rules effective August 2026",
    "▸ High-risk obligations phase in 2026-2027",
]
add_body_text(slide, _emu(0.5), _emu(2.25), _emu(4.0), _emu(2.6),
              eu_lines, font_size=11, color=DARK, line_spacing=1.35)

# Right column: NIST AI RMF
add_rect(slide, _emu(5.05), _emu(1.6), _emu(4.35), _emu(3.4), fill=WHITE, border=GRAY_LIGHT, radius=0.08)
add_rect(slide, _emu(5.05), _emu(1.6), _emu(4.35), _emu(0.5), fill=AMBER, radius=0.06)
add_single_text(slide, _emu(5.2), _emu(1.65), _emu(4.0), _emu(0.4),
                "NIST AI RMF — Voluntary Framework", font_size=14, bold=True, color=WHITE, font_name=FONT_BODY)
nist_lines = [
    "Four functions (continuous cycle):",
    "",
    "Govern → Policies, accountability, culture",
    "Map → Context, classification, risk assessment",
    "Measure → Quantitative/qualitative evaluation",
    "Manage → Risk treatment, incident response",
    "",
    "▸ Generative AI Profile (NIST AI 600-1, 2024)",
    "▸ Not certifiable (pair with ISO 42001)",
]
add_body_text(slide, _emu(5.2), _emu(2.25), _emu(4.0), _emu(2.6),
              nist_lines, font_size=11, color=DARK, line_spacing=1.35)

add_speaker_notes(slide, (
    "Regulation is a driver, not just ethics. EU AI Act is binding law — most rules "
    "effective August 2026. NIST AI RMF is voluntary but globally referenced. The "
    "four functions give you an operational cycle. These frameworks are complementary."
))
print("  Slide 9: Regulatory Reality")

# ── SLIDE 10: Five Reasons ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Five Reasons \"Explainable\" ≠ \"Trustworthy\"")
reasons = [
    ("1", "Local fidelity ≠ global safety",
     "SHAP tells you feature contribution to this prediction — not whether overall behavior is safe, fair, or robust."),
    ("2", "Post-hoc ≠ causal",
     "Most XAI explains correlational attribution, not why the model decided. A plausible explanation can accompany a wrong decision."),
    ("3", "One of seven, not all seven",
     "An explainable model can still be unfair, insecure, non-private, or unreliable. Explainability is necessary but not sufficient."),
    ("4", "LLMs hallucinate explanations too",
     "A model asked \"why did you say that\" generates plausible rationale — not necessarily its actual internal process."),
    ("5", "Adversarial robustness is orthogonal",
     "A perfectly interpretable decision boundary can still be trivially fooled by prompt injection or perturbation."),
]
for i, (num, title, desc) in enumerate(reasons):
    y = _emu(1.6) + i * _emu(0.72)
    # Number badge
    add_rect(slide, _emu(0.45), y, _emu(0.35), _emu(0.35), fill=RED, radius=0.06)
    add_single_text(slide, _emu(0.45), y + _emu(0.02), _emu(0.35), _emu(0.3),
                    num, font_size=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    # Title
    add_single_text(slide, _emu(0.95), y, _emu(3.8), _emu(0.3),
                    title, font_size=14, bold=True, color=DARK)
    # Description
    add_single_text(slide, _emu(4.9), y, _emu(4.7), _emu(0.3),
                    desc, font_size=12, color=GRAY)
add_speaker_notes(slide, (
    "Five distinct reasons the old assumption breaks down. Walk each one. "
    "This is the conceptual hinge of the entire talk — spend real time here."
))
print("  Slide 10: Five Reasons")

# ── SLIDE 11: Two Harder Problems ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Two Harder Problems")
# Left panel
add_rect(slide, _emu(0.35), _emu(1.6), _emu(4.35), _emu(3.3), fill=WHITE, border=PURPLE, radius=0.08)
add_rect(slide, _emu(0.35), _emu(1.6), _emu(4.35), _emu(0.5), fill=PURPLE, radius=0.06)
add_single_text(slide, _emu(0.5), _emu(1.65), _emu(4.0), _emu(0.4),
                "LLMs Hallucinate Their Own Explanations", font_size=13, bold=True, color=WHITE, font_name=FONT_BODY)
llm_lines = [
    "A model asked \"why did you say that\"",
    "generates plausible-sounding rationale —",
    "not necessarily its actual internal process.",
    "",
    "This is a known interpretability research",
    "problem, not a hypothetical.",
    "",
    "Practical implication: treat model self-",
    "reported reasoning as a useful signal,",
    "not ground truth. Corroborate with",
    "behavioral testing (counterfactuals,",
    "adversarial probes).",
]
add_body_text(slide, _emu(0.5), _emu(2.25), _emu(4.0), _emu(2.5),
              llm_lines, font_size=12, color=DARK, line_spacing=1.3)
# Right panel
add_rect(slide, _emu(5.05), _emu(1.6), _emu(4.35), _emu(3.3), fill=WHITE, border=AMBER, radius=0.08)
add_rect(slide, _emu(5.05), _emu(1.6), _emu(4.35), _emu(0.5), fill=AMBER, radius=0.06)
add_single_text(slide, _emu(5.2), _emu(1.65), _emu(4.0), _emu(0.4),
                "Adversarial Robustness Is Orthogonal", font_size=13, bold=True, color=WHITE, font_name=FONT_BODY)
adv_lines = [
    "A model with a perfectly clean,",
    "interpretable decision boundary can",
    "still be trivially fooled by:",
    "• An adversarial perturbation",
    "• A prompt injection attack",
    "• A jailbreak attempt",
    "",
    "Explainability tells you nothing about",
    "how the model behaves under attack.",
    "",
    "You need dedicated adversarial testing",
    "(red-teaming, Garak/PyRIT) — not just",
    "XAI tooling.",
]
add_body_text(slide, _emu(5.2), _emu(2.25), _emu(4.0), _emu(2.5),
              adv_lines, font_size=12, color=DARK, line_spacing=1.3)
add_speaker_notes(slide, (
    "Two particularly hard problems. Left: LLMs can hallucinate explanations — "
    "treat model self-reported reasoning as signal, not ground truth. Right: "
    "explainability and robustness are separate dimensions. You need dedicated "
    "adversarial testing infrastructure."
))
print("  Slide 11: Two Harder Problems")

# ── SLIDE 12: The Reframe ──
slide = add_slide("MAIN_POINT")
set_title(slide, "Explainability Is an Input to Trust,\nNot the Output")
# Old model (crossed out)
add_single_text(slide, _emu(0.6), _emu(2.5), _emu(3.5), _emu(0.4),
                "OLD MODEL", font_size=11, bold=True, color=GRAY, font_name=FONT_BODY)
add_single_text(slide, _emu(0.6), _emu(2.85), _emu(3.5), _emu(0.5),
                "Explainability  →  Trust", font_size=18, color=GRAY)
add_rect(slide, _emu(0.6), _emu(3.05), _emu(3.5), _emu(0.02), fill=RED)
# Arrow
add_single_text(slide, _emu(4.3), _emu(2.85), _emu(1.0), _emu(0.5),
                "➡", font_size=28, bold=True, color=TEAL, align=PP_ALIGN.CENTER)
# New model
add_single_text(slide, _emu(5.5), _emu(2.5), _emu(4.0), _emu(0.4),
                "NEW MODEL", font_size=11, bold=True, color=TEAL, font_name=FONT_BODY)
add_single_text(slide, _emu(5.5), _emu(2.85), _emu(4.5), _emu(0.5),
                "Explainability → Trust Judgment ← Everything Else",
                font_size=16, bold=True, color=DARK)
# Component grid
components = [
    "Data provenance", "Model behavior under shift", "Adversarial robustness",
    "Privacy guarantees", "Fairness across groups", "Human oversight",
    "Deployment monitoring", "Incident response"
]
for i, comp in enumerate(components):
    col = i % 4
    row = i // 4
    x = _emu(0.45) + col * _emu(2.35)
    y = _emu(3.8) + row * _emu(0.55)
    add_rect(slide, x, y, _emu(2.15), _emu(0.38), fill=BLUE_LIGHT, radius=0.06)
    add_single_text(slide, x + _emu(0.1), y + _emu(0.03), _emu(1.95), _emu(0.3),
                    comp, font_size=11, color=DARK, font_name=FONT_BODY)
# Bottom caption
add_single_text(slide, _emu(0.6), _emu(4.9), _emu(9.0), _emu(0.4),
    "Trust is a property of the whole system (data, model, deployment, monitoring, "
    "human oversight) — not something you get for free by visualizing attention weights.",
    font_size=13, bold=True, color=DARK, font_name=FONT_BODY)
add_speaker_notes(slide, (
    "The reframe: the old model was 'make it explainable = done.' The new model: "
    "explainability is one input to a trust judgment among many. A trust judgment "
    "without these other inputs is incomplete — sometimes dangerously so."
))
print("  Slide 12: The Reframe")

# ── SLIDES 13-18: Six Core Principles ──
principle_data = [
    ("Fairness", RED, [
        "Disparate treatment: intentionally different",
        "treatment based on a protected attribute.",
        "",
        "Disparate impact: a facially neutral policy",
        "that disproportionately harms a protected",
        "group — even with no discriminatory intent.",
        "",
        "Key tension: you generally cannot satisfy",
        "all fairness metrics simultaneously (the",
        "impossibility result — Kleinberg et al., 2016).",
    ], [
        "Training data encodes historical bias —",
        "the model learns and amplifies it.",
        "",
        "Fairness is not one metric — demographic",
        "parity, equalized odds, and calibration",
        "are mathematically incompatible outside",
        "of degenerate cases.",
        "",
        "Choosing a metric is a normative decision,",
        "not a purely technical one.",
    ], [
        "Counterfactual testing: take a test input,",
        "swap only the protected attribute, measure",
        "the output delta, flag if exceeds threshold.",
        "",
        "Mitigation at three stages:",
        "• Pre-processing: reweight/re-label data",
        "• In-processing: constrained training",
        "• Post-processing: calibrate outputs",
    ], (
        "Fairness is the most philosophically complex principle — it sits at the "
        "intersection of technical metrics and normative values. The impossibility "
        "result is worth sitting with: you generally cannot satisfy all fairness "
        "metrics simultaneously. Choosing a metric is inherently a normative decision. "
        "Source: NIST AI RMF; Kleinberg et al. (2016)."
    )),
    ("Transparency", BLUE, [
        "Transparency ≠ Explainability (these get",
        "conflated constantly):",
        "",
        "Transparency: can you see and audit HOW",
        "the system works — what data, training",
        "process, evaluation, governance.",
        "",
        "Explainability: can you interpret a",
        "SPECIFIC decision the model made.",
    ], [
        "Organizations deploy models without",
        "documenting training data provenance,",
        "evaluation scope, or known limitations.",
        "",
        "Without an audit trail, you cannot",
        "retrospectively determine whether a",
        "harmful output was a one-off or a",
        "systematic failure.",
    ], [
        "Structured transparency artifacts:",
        "",
        "• Model Cards (Mitchell et al., 2019):",
        "  standardized disclosure of intended use,",
        "  evaluation results, limitations, ethics.",
        "",
        "• Datasheets for Datasets (Gebru et al., 2018):",
        "  motivation, composition, collection,",
        "  preprocessing, recommended uses.",
    ], (
        "This is one of the most important distinctions in the entire talk. "
        "Transparency and explainability get used interchangeably constantly. "
        "A model can be explainable without being transparent, and vice versa. "
        "Sources: Mitchell et al. (2019); Gebru et al. (2018)."
    )),
    ("Accountability", GREEN, [
        "Who is answerable when the system",
        "causes harm?",
        "",
        "This is an organizational/governance",
        "property — not a technical one.",
        "",
        "A system with no human accountable for",
        "high-risk decisions cannot be accountable,",
        "no matter how good its metrics are.",
    ], [
        "Diffusion of responsibility: \"the data",
        "science team built it, ML ops deployed it,",
        "product chose the threshold\" — no single",
        "owner.",
        "",
        "Automation bias: human reviewers rubber-",
        "stamp model outputs because \"the AI",
        "usually gets it right.\"",
    ], [
        "Human-in-the-loop (HITL) design:",
        "",
        "• Designate accountable roles per decision",
        "  class BEFORE deployment.",
        "• Surface model reasoning alongside the",
        "  proposed action — not just the action.",
        "• Log every override with accountable",
        "  human's identity and stated rationale.",
    ], (
        "Accountability is the principle most likely to be overlooked by technical "
        "teams because it's not a dashboard metric. But it's the answer to 'who is "
        "answerable when this system causes harm.' Our implementation: HITL approval "
        "queue surfaces model reasoning vs. action divergence."
    )),
    ("Robustness / Safety", AMBER, [
        "Performance under distribution shift,",
        "adversarial inputs, and edge cases —",
        "not just average-case accuracy.",
        "",
        "General robustness: resilience to natural",
        "noise, edge cases, distribution drift.",
        "",
        "Adversarial robustness: resilience to",
        "inputs deliberately crafted to cause",
        "failure (prompt injection, jailbreaks).",
    ], [
        "Models are typically evaluated on IID",
        "held-out test sets — which tells you",
        "nothing about behavior under shift or",
        "attack.",
        "",
        "LLMs introduce novel attack surfaces:",
        "prompt injection, indirect injection via",
        "retrieved documents — these didn't exist",
        "for traditional ML.",
    ], [
        "Red-teaming and adversarial testing:",
        "",
        "• Structured red-teaming harness (Garak,",
        "  PyRIT) — systematically probe for",
        "  vulnerabilities across attack categories.",
        "• Prompt injection defenses: input",
        "  sanitization, instruction hierarchy.",
        "• Continuous monitoring, not one-time",
        "  pre-deployment eval.",
    ], (
        "Robustness is about how the model behaves when things go wrong. Two "
        "sub-dimensions requiring different testing strategies. LLMs introduce "
        "novel attack surfaces. Our implementation: red-team harness with "
        "Garak/PyRIT. Source: NIST AI 600-1."
    )),
    ("Privacy", PURPLE, [
        "Differential privacy (formal): add",
        "calibrated noise so no single individual's",
        "data materially changes the output —",
        "a mathematical (not just policy) guarantee.",
        "",
        "Contrast with simple anonymization or",
        "redaction: removing PII fields is data",
        "hygiene, not a formal privacy guarantee.",
    ], [
        "Simple anonymization can be defeated by",
        "linkage attacks — combining \"anonymized\"",
        "datasets with public data to re-identify",
        "individuals.",
        "",
        "Models themselves can memorize and",
        "regurgitate training data — a privacy",
        "failure redaction at inference time",
        "cannot prevent.",
    ], [
        "Layered approach — match technique to",
        "threat model:",
        "",
        "• PII detection/redaction (Presidio):",
        "  prevents PII in inputs and outputs.",
        "• Differential privacy (DP-SGD): formal",
        "  guarantee at training time.",
        "",
        "Be precise: these solve different",
        "problems. Redaction ≠ DP.",
    ], (
        "Privacy is where precision of language matters most. Conflation here "
        "creates false confidence. Our implementation: PII redaction with Presidio. "
        "We should be honest: this is redaction, not formal DP. "
        "Sources: Dwork & Roth; Presidio documentation."
    )),
    ("Reliability", TEAL, [
        "Consistent performance across time,",
        "environments, and inputs.",
        "",
        "Not just \"did it pass eval once\" — does it",
        "keep performing at the same level as",
        "data, users, and context change.",
        "",
        "Ties to NIST's Measure function being",
        "continuous, not a pre-deployment gate.",
    ], [
        "Data drift: the input distribution in",
        "production diverges from training data —",
        "accuracy silently degrades.",
        "",
        "Concept drift: what was \"correct\" last",
        "quarter may not be correct now.",
        "",
        "One-time evaluation gives a snapshot —",
        "it tells you nothing about the trend.",
    ], [
        "Continuous monitoring + scheduled",
        "re-evaluation:",
        "",
        "• Groundedness/hallucination checks as",
        "  a continuous signal, not pre-deploy only.",
        "• Scheduled eval cadence: run same",
        "  benchmark on fixed schedule.",
        "• Monitor input/output distributions for",
        "  statistical divergence.",
    ], (
        "Reliability is the temporal dimension of trustworthiness. A model that "
        "passes eval at deployment but silently degrades is not reliable. "
        "This is why NIST's Measure function is continuous. "
        "Our implementation: groundedness checks, scheduled eval cadence."
    )),
]

for pi, (name, color, definition, why_fails, technique, notes) in enumerate(principle_data):
    slide = add_slide("TITLE_ONLY")
    set_title(slide, f"Core Principle: {name}")

    # Three-column layout
    col_w = _emu(2.9)
    col_gap = _emu(0.25)
    start_x = _emu(0.45)
    start_y = _emu(1.7)
    card_h = _emu(3.2)  # total card body height

    # Definition column
    build_three_column_card(slide, start_x, start_y, col_w, card_h,
                            "DEFINITION", color, definition,
                            bg_color=WHITE, border_color=GRAY_LIGHT)

    # Why it fails column
    x2 = start_x + col_w + col_gap
    build_three_column_card(slide, x2, start_y, col_w, card_h,
                            "WHY IT FAILS IN PRACTICE", DARK, why_fails,
                            bg_color=WHITE, border_color=GRAY_LIGHT)

    # Technique column
    x3 = x2 + col_w + col_gap
    build_three_column_card(slide, x3, start_y, col_w, card_h,
                            "ONE CONCRETE TECHNIQUE", TEAL, technique,
                            bg_color=TEAL_LIGHT, border_color=TEAL)

    # Bottom insight bar
    add_rect(slide, _emu(0.45), _emu(5.15), _emu(9.1), _emu(0.4),
             fill=GRAY_LIGHT, radius=0.06)
    add_single_text(slide, _emu(0.6), _emu(5.18), _emu(8.8), _emu(0.35),
        f"Key: {name} is one dimension of trust — it interacts with the other five. "
        "Evaluating any single principle in isolation is a partial assessment.",
        font_size=10, color=DARK, font_name=FONT_BODY)

    add_speaker_notes(slide, notes)
    print(f"  Slide {13+pi}: Principle — {name}")

# ── SLIDE 19: Concept Map ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Related Terms & Concepts")
import math
cx, cy = _emu(5.0), _emu(3.5)

# Center hub
hub = add_rect(slide, cx - _emu(1.0), cy - _emu(0.4), _emu(2.0), _emu(0.8),
               fill=BLUE, radius=0.12)
tf = hub.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = "Core\nPrinciples"
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = FONT_BODY
p.alignment = PP_ALIGN.CENTER

# Six principles around center
principle_labels = [
    ("Fairness", RED), ("Transparency", BLUE), ("Accountability", GREEN),
    ("Robustness\n/ Safety", AMBER), ("Privacy", PURPLE), ("Reliability", TEAL),
]
for i, (label, color) in enumerate(principle_labels):
    angle = -math.pi/2 + i * 2*math.pi/6
    px = cx + _emu(1.8) * math.cos(angle) - _emu(0.5)
    py = cy + _emu(1.8) * math.sin(angle) - _emu(0.3)
    shape = add_rect(slide, _in(px), _in(py), _emu(1.0), _emu(0.6),
                     fill=color, radius=0.08)
    tf2 = shape.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = label
    p2.font.size = Pt(9)
    p2.font.bold = True
    p2.font.color.rgb = WHITE
    p2.font.name = FONT_BODY
    p2.alignment = PP_ALIGN.CENTER

# Outer concept boxes
concepts = [
    (_emu(0.2), _emu(1.1), _emu(2.5), _emu(1.6), AMBER, "Adversarial\nRobustness",
     "Resistance to inputs crafted\nto cause failure: adversarial\nexamples, prompt injection,\njailbreaks."),
    (_emu(7.3), _emu(1.1), _emu(2.5), _emu(1.6), PURPLE, "Model\nAuditing",
     "Independent review of data,\ntraining, and behavior against\na standard — increasingly\na regulatory requirement."),
    (_emu(0.2), _emu(3.3), _emu(2.5), _emu(1.6), TEAL, "Regulatory\nFrameworks",
     "NIST AI RMF (voluntary, 4 functions)\n+ EU AI Act (binding law, 4 risk\ntiers, effective Aug 2026).\nComplementary, not competing."),
    (_emu(7.3), _emu(3.3), _emu(2.5), _emu(1.6), GREEN, "Ethical\nConsiderations",
     "The normative layer: whose\nvalues are encoded, who bears\nrisk vs. benefit, and what happens\nwhen a metric conflicts with\nstakeholders' actual fairness sense."),
]
for (ox, oy, ow, oh, color, title, desc) in concepts:
    shape = add_rect(slide, _in(ox), _in(oy), _in(ow), _in(oh),
                     fill=WHITE, border=color, radius=0.08)
    shape.line.width = Pt(2)
    tf3 = shape.text_frame
    tf3.word_wrap = True
    p3 = tf3.paragraphs[0]
    p3.text = title
    p3.font.size = Pt(11)
    p3.font.bold = True
    p3.font.color.rgb = color
    p3.font.name = FONT_BODY
    p3.alignment = PP_ALIGN.CENTER
    p3b = tf3.add_paragraph()
    p3b.text = desc
    p3b.font.size = Pt(9)
    p3b.font.color.rgb = GRAY
    p3b.font.name = FONT_BODY
    p3b.alignment = PP_ALIGN.CENTER
    p3b.line_spacing = Pt(12)

add_speaker_notes(slide, (
    "Vocabulary map showing relationships, not definitions. None of these terms "
    "is independent. Adversarial robustness without accountability is a technical "
    "exercise. Regulation without ethics is compliance theater. They form an "
    "interconnected system."
))
print("  Slide 19: Concept Map")

# ── SLIDE 20: XAI × Causal AI ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "XAI × Causal AI: Association vs. Causation")
# Left: Association
add_rect(slide, _emu(0.35), _emu(1.6), _emu(4.35), _emu(3.3), fill=WHITE, border=GRAY_LIGHT, radius=0.08)
add_rect(slide, _emu(0.35), _emu(1.6), _emu(4.35), _emu(0.5), fill=RED, radius=0.06)
add_single_text(slide, _emu(0.5), _emu(1.65), _emu(4.0), _emu(0.4),
                "What SHAP / LIME / Attention Gives You", font_size=13, bold=True, color=WHITE, font_name=FONT_BODY)
assoc_lines = [
    "Correlational attribution:",
    "\"Feature X was associated with output Y\"",
    "",
    "Locally faithful — correct for this one",
    "prediction — but globally silent about",
    "whether the model would fail under",
    "distribution shift.",
    "",
    "A SHAP value can look reasonable while",
    "the model is latched onto a spurious",
    "correlate of a protected attribute.",
    "",
    "→ Right for the wrong reason.",
]
add_body_text(slide, _emu(0.5), _emu(2.25), _emu(4.0), _emu(2.5),
              assoc_lines, font_size=12, color=DARK, line_spacing=1.35)
# Right: Causation
add_rect(slide, _emu(5.05), _emu(1.6), _emu(4.35), _emu(3.3), fill=WHITE, border=TEAL, radius=0.08)
add_rect(slide, _emu(5.05), _emu(1.6), _emu(4.35), _emu(0.5), fill=TEAL, radius=0.06)
add_single_text(slide, _emu(5.2), _emu(1.65), _emu(4.0), _emu(0.4),
                "What Causal Explanations Add", font_size=13, bold=True, color=WHITE, font_name=FONT_BODY)
causal_lines = [
    "Counterfactual reasoning:",
    "\"If X had been different, would the",
    "outcome have changed?\"",
    "",
    "Causal graphs tie explanations to actual",
    "mechanisms — far more robust to",
    "distribution shift and harder to game.",
    "",
    "A causal explanation surviving a shift is",
    "genuine evidence of trustworthiness; a",
    "correlational one surviving is not",
    "evidence either way.",
    "",
    "→ Right for the right reason.",
]
add_body_text(slide, _emu(5.2), _emu(2.25), _emu(4.0), _emu(2.5),
              causal_lines, font_size=12, color=DARK, line_spacing=1.35)
# Bottom practical takeaway
add_rect(slide, _emu(0.35), _emu(5.15), _emu(9.1), _emu(0.45), fill=GRAY_LIGHT, radius=0.06)
add_single_text(slide, _emu(0.5), _emu(5.18), _emu(8.8), _emu(0.35),
    "Practical takeaway: You don't need a full causal model. Ask \"is this explanation "
    "counterfactually testable?\" — that alone is a meaningfully more rigorous bar.",
    font_size=12, bold=True, color=DARK, font_name=FONT_BODY)
add_speaker_notes(slide, (
    "The deepest section conceptually. Production XAI methods explain association, "
    "not causation. A correlational explanation can be right for the wrong reason. "
    "Causal explanations add counterfactual reasoning and mechanism-tied explanations. "
    "Practical framing: even asking 'is this counterfactually testable?' raises the bar."
))
print("  Slide 20: XAI x Causal AI")

# ── SLIDE 21: Putting It All Together ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Putting It All Together")
flow = [
    ("1", "Explainability\nis necessary", TEAL,
     "XAI methods give local, correlational explanations — useful for debugging, "
     "insufficient for trust. Explanations are inputs to trust judgments, not the judgment itself."),
    ("2", "Causal reasoning\nis the upgrade", AMBER,
     "Counterfactual reasoning and causal graphs give explanations tied to mechanisms — "
     "more robust to shift. Even asking 'is this counterfactually testable?' raises the bar."),
    ("3", "System-level trust\nis the answer", BLUE,
     "Trustworthiness isn't one property you measure once. It's a system-level property "
     "verified continuously across all seven NIST characteristics — and the next section shows how."),
]
for i, (num, title, color, desc) in enumerate(flow):
    y = _emu(1.7) + i * _emu(1.3)
    # Number circle
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(_in(_emu(0.55))), Inches(_in(y + _emu(0.2))),
        Inches(_in(_emu(0.55))), Inches(_in(_emu(0.55))))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.text = num
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = FONT_BODY
    p.alignment = PP_ALIGN.CENTER
    # Title
    add_single_text(slide, _emu(1.3), y + _emu(0.05), _emu(3.5), _emu(0.55),
                    title, font_size=16, bold=True, color=color, font_name=FONT_BODY)
    # Description
    add_single_text(slide, _emu(1.3), y + _emu(0.65), _emu(8.2), _emu(0.55),
                    desc, font_size=12, color=DARK, font_name=FONT_BODY)
add_speaker_notes(slide, (
    "Bridge slide connecting the conceptual deep-dive to practical application. "
    "Three beats: explainability is necessary but not sufficient, causal reasoning "
    "is the upgrade, and system-level trust is where we land. This is the transition "
    "moment — we've built the theory, now let's see the practice."
))
print("  Slide 21: Putting It All Together")

# ── SLIDE 22: Resources ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "Resources & Further Reading")
resources = [
    ("NIST AI Risk Management Framework (AI RMF 1.0)",
     "Four-function core (Govern/Map/Measure/Manage) + Generative AI Profile "
     "(NIST AI 600-1) for LLM/agentic risks. nist.gov"),
    ("Christoph Molnar — Interpretable Machine Learning",
     "Free online book; standard reference for XAI methods (LIME, SHAP, "
     "permutation importance). christophm.github.io/interpretable-ml-book"),
    ("Samek et al. — Explainable AI (2019)",
     "Deeper technical grounding on XAI specifically for deep learning. "
     "Springer LNCS vol. 11700."),
    ("EU AI Act — Official Text",
     "Binding EU law with four risk tiers, effective August 2026. "
     "artificialintelligenceact.eu"),
    ("Dwork & Roth — Algorithmic Foundations of Differential Privacy (2014)",
     "The foundational text on formal privacy guarantees via calibrated noise."),
    ("Mitchell et al. — Model Cards for Model Reporting (2019)",
     "Standardized framework for transparent model documentation. FAccT 2019."),
    ("Gebru et al. — Datasheets for Datasets (2018)",
     "Standardized dataset documentation: motivation, composition, collection. "
     "Communications of the ACM, 2021."),
]
for i, (title, desc) in enumerate(resources):
    y = _emu(1.55) + i * _emu(0.48)
    add_single_text(slide, _emu(0.5), y, _emu(9.0), _emu(0.22),
                    title, font_size=11, bold=True, color=DARK, font_name=FONT_BODY)
    add_single_text(slide, _emu(0.5), y + _emu(0.2), _emu(9.0), _emu(0.28),
                    desc, font_size=9, color=GRAY, font_name=FONT_BODY)
    if i < len(resources) - 1:
        add_rect(slide, _emu(0.5), y + _emu(0.5), _emu(9.0), _emu(0.005),
                 fill=GRAY_LIGHT)
add_single_text(slide, _emu(0.5), _emu(5.0), _emu(9.0), _emu(0.2),
    "This slide is designed to be screenshotted — all citations in one place.",
    font_size=10, color=GRAY, font_name=FONT_BODY)
add_speaker_notes(slide, (
    "Reference slide — not reading aloud. All primary sources cited in the talk. "
    "Molnar's book and NIST framework are free online."
))
print("  Slide 22: Resources")

# ── SLIDE 23: What We Don't Do (Honesty) ──
slide = add_slide("TITLE_ONLY")
set_title(slide, "What We Don't Do (Yet)")
gaps = [
    ("No model-internals interpretability",
     "We have guardrails and governance — not SHAP/LIME integration or attention "
     "visualization. Our trustworthiness comes from system-level controls, not "
     "from peering inside the model. This is a legitimate architectural choice, but "
     "it's worth naming explicitly."),
    ("Redaction ≠ Differential Privacy",
     "Our PII pipeline (Presidio) does detection and redaction/tokenization — it "
     "prevents PII in model inputs and outputs. It does NOT provide the formal "
     "mathematical guarantee of differential privacy. Different tools for different "
     "threat models; honesty is in not conflating them."),
    ("Causal explanations are aspirational",
     "The XAI × Causal AI section described where the field is going. Our current "
     "system does not implement counterfactual explanation generation or causal "
     "graph-based reasoning. The practical takeaway — ask whether an explanation is "
     "counterfactually testable — is a review discipline we can adopt today."),
]
for i, (title, desc) in enumerate(gaps):
    y = _emu(1.8) + i * _emu(1.3)
    add_rect(slide, _emu(0.5), y, _emu(0.06), _emu(0.9), fill=AMBER)
    add_single_text(slide, _emu(0.75), y, _emu(8.5), _emu(0.3),
                    title, font_size=16, bold=True, color=DARK, font_name=FONT_BODY)
    add_single_text(slide, _emu(0.75), y + _emu(0.32), _emu(8.5), _emu(0.55),
                    desc, font_size=12, color=GRAY, font_name=FONT_BODY, line_spacing=1.35)
add_speaker_notes(slide, (
    "Internal sessions are most valuable when honest. Three gaps to name explicitly. "
    "This is more credible than overclaiming."
))
print("  Slide 23: What We Don't Do")

# ── SLIDE 24: Discussion ──
slide = add_slide("SECTION_HEADER")
set_title(slide, "Which of These Seven Characteristics\nIs Hardest to Verify in Your Team's Systems Today — and Why?")
add_single_text(slide, _emu(0.55), _emu(3.8), _emu(8.0), _emu(0.5),
    "(No wrong answers — the goal is to surface where the gaps are,\n"
    "not to pretend every dimension is equally well-covered.)",
    font_size=14, color=GRAY, font_name=FONT_BODY)
add_single_text(slide, _emu(0.55), _emu(4.8), _emu(8.0), _emu(0.4),
    "Thank you. Questions, challenges, and pushback welcome.",
    font_size=13, color=GRAY, font_name=FONT_BODY)
add_speaker_notes(slide, (
    "Final slide — designed to start a conversation, not end one. The question "
    "is specific enough for concrete answers, open-ended with no right answer, "
    "and normalizes that every team has gaps. Offer your own answer first to "
    "break the ice."
))
print("  Slide 24: Discussion")

# ══════════════════════════════════════════════════════════════════════════
# REORDER SLIDES
# ══════════════════════════════════════════════════════════════════════════

print("\n=== Reordering slides ===")

# Current slide order (0-indexed):
# 0: Slide 1 - Title (existing)
# 1: Slide 2 - Agenda (existing)
# 2: Slide 3 - Agenda Cont. (existing)
# 3: Slide 4 - What Is Trustworthy AI (existing)
# 4: Slide 5 - Why This Matters (existing)
# 5: Slide 6 - Explainability Trap (existing)
# 6: Slide 7 - Codebase Table (existing)
# 7: Slide 8 - Three Failure Categories (new)
# 8: Slide 9 - Regulatory Reality (new)
# 9: Slide 10 - Five Reasons (new)
# 10: Slide 11 - Two Harder Problems (new)
# 11: Slide 12 - The Reframe (new)
# 12-17: Slides 13-18 - Six Principles (new)
# 18: Slide 19 - Concept Map (new)
# 19: Slide 20 - XAI x Causal (new)
# 20: Slide 21 - Bridge (new)
# 21: Slide 22 - Resources (new)
# 22: Slide 23 - Honesty (new)
# 23: Slide 24 - Discussion (new)

# Desired final order (slide numbers 1-24 map to indices 0-23):
# 0: Title (existing 0)
# 1: Agenda (existing 1)
# 2: Agenda Cont. (existing 2)
# 3: What Is Trustworthy AI (existing 3)
# 4: Three Failure Categories (new 7) — MOVED UP
# 5: Why This Matters (existing 4)
# 6: Regulatory Reality (new 8)
# 7: Explainability Trap (existing 5)
# 8: Five Reasons (new 9)
# 9: Two Harder Problems (new 10)
# 10: The Reframe (new 11)
# 11: Fairness (new 12)
# 12: Transparency (new 13)
# 13: Accountability (new 14)
# 14: Robustness (new 15)
# 15: Privacy (new 16)
# 16: Reliability (new 17)
# 17: Concept Map (new 18)
# 18: XAI x Causal (new 19)
# 19: Bridge (new 20)
# 20: Resources (new 21)
# 21: Codebase Table (existing 6) — MOVED DOWN
# 22: Honesty (new 22)
# 23: Discussion (new 23)

desired_order = [0, 1, 2, 3, 7, 4, 8, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 6, 22, 23]

# Access the slide ID list from the presentation XML element
sldIdLst = prs.part._element.find(qn('p:sldIdLst'))
sld_entries = list(sldIdLst)
# Get rIds from each entry
entries = [(entry.get(qn('r:id')), entry) for entry in sld_entries]

# Reorder
for entry in sld_entries:
    sldIdLst.remove(entry)
for idx in desired_order:
    rId, entry = entries[idx]
    sldIdLst.append(entry)

print(f"  Reordered {len(desired_order)} slides to final sequence")

# ══════════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════════

prs.save(OUTPUT_PATH)
print(f"\nSaved {len(prs.slides)} slides to {OUTPUT_PATH}")
print("Build complete!")
