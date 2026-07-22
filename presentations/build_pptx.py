"""
Build the Trustworthy AI KSS PowerPoint deck.
Source: kss-trustworthy-ai-slide-plan.md Sections 1–2
Output: Trustworthy_AI_KSS.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR_TYPE
from pptx.oxml.ns import qn

# ── Presentation setup ──────────────────────────────────────────────
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# ── Color palette ───────────────────────────────────────────────────
NAVY      = RGBColor(0x1B, 0x2A, 0x4A)
TEAL      = RGBColor(0x00, 0x89, 0x7B)
AMBER     = RGBColor(0xFF, 0x8F, 0x00)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT  = RGBColor(0x2D, 0x37, 0x48)
LIGHT_BG  = RGBColor(0xF5, 0xF7, 0xFA)
CORAL     = RGBColor(0xE5, 0x3E, 0x3E)
MID_GRAY  = RGBColor(0xA0, 0xAE, 0xC0)
DARK_SLATE = RGBColor(0x25, 0x2D, 0x3A)
TEAL_LIGHT = RGBColor(0xE0, 0xF2, 0xF1)
AMBER_LIGHT = RGBColor(0xFF, 0xF8, 0xE1)
NAVY_LIGHT = RGBColor(0xE8, 0xEA, 0xF0)
PURPLE    = RGBColor(0x6B, 0x46, 0xC1)
GREEN     = RGBColor(0x38, 0xA1, 0x69)
BLUE_STEEL = RGBColor(0x4A, 0x55, 0x68)

PRINCIPLE_COLORS = {
    "Fairness":       RGBColor(0xE5, 0x3E, 0x3E),
    "Transparency":   RGBColor(0x31, 0x81, 0xCE),
    "Accountability": RGBColor(0x38, 0xA1, 0x69),
    "Robustness":     RGBColor(0xFF, 0x8F, 0x00),
    "Privacy":        RGBColor(0x6B, 0x46, 0xC1),
    "Reliability":    RGBColor(0x00, 0x89, 0x7B),
}

# ── Helper functions ─────────────────────────────────────────────────

def add_blank_slide():
    """Add a blank slide."""
    layout = prs.slide_layouts[6]  # blank
    return prs.slides.add_slide(layout)

def add_speaker_notes(slide, text):
    """Set speaker notes on a slide."""
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = text

def add_textbox(slide, left, top, width, height, text="",
                font_size=18, bold=False, color=DARK_TEXT,
                alignment=PP_ALIGN.LEFT, font_name="Calibri",
                anchor=MSO_ANCHOR.TOP, line_spacing=1.15):
    """Add a text box with styled text."""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                      Inches(width), Inches(height))
    txBox.text_frame.word_wrap = True
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.paragraphs[0].alignment = alignment
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.space_after = Pt(4)
    p.line_spacing = Pt(font_size * line_spacing)
    tf.paragraphs[0].space_before = Pt(0)
    return txBox

def add_multiline_textbox(slide, left, top, width, height, lines,
                          font_size=16, color=DARK_TEXT, bold_first=False,
                          alignment=PP_ALIGN.LEFT, font_name="Calibri",
                          anchor=MSO_ANCHOR.TOP, line_spacing=1.3,
                          bullet=False):
    """Add a text box with multiple paragraphs."""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                      Inches(width), Inches(height))
    txBox.text_frame.word_wrap = True
    tf = txBox.text_frame
    tf.paragraphs[0].text = ""
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = line
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = font_name
        p.alignment = alignment
        p.line_spacing = Pt(font_size * line_spacing)
        p.space_after = Pt(4)
        if bold_first and i == 0:
            p.font.bold = True
    return txBox

def add_rect(slide, left, top, width, height, fill_color=NAVY,
             border_color=None, corner_radius=None):
    """Add a filled rectangle shape."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if corner_radius else MSO_SHAPE.RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape

def add_title_bar(slide, title, subtitle=None, color=NAVY):
    """Add a standard title bar at the top of a content slide."""
    add_rect(slide, 0, 0, 13.333, 1.35, fill_color=color)
    add_textbox(slide, 0.8, 0.2, 11.7, 0.7, text=title,
                font_size=30, bold=True, color=WHITE)
    if subtitle:
        add_textbox(slide, 0.8, 0.75, 11.7, 0.45, text=subtitle,
                    font_size=14, color=RGBColor(0xCC, 0xD5, 0xE0))
    # thin accent line
    add_rect(slide, 0, 1.35, 13.333, 0.04, fill_color=TEAL)

def add_section_divider(slide, section_num, title, subtitle=""):
    """Full-bleed section divider slide."""
    add_rect(slide, 0, 0, 13.333, 7.5, fill_color=NAVY)
    add_textbox(slide, 0.8, 2.0, 11.7, 0.6, text=f"PART {section_num}",
                font_size=16, color=TEAL, bold=True)
    add_textbox(slide, 0.8, 2.6, 11.7, 1.2, text=title,
                font_size=40, bold=True, color=WHITE)
    if subtitle:
        add_textbox(slide, 0.8, 3.8, 11.7, 0.8, text=subtitle,
                    font_size=18, color=RGBColor(0xCC, 0xD5, 0xE0))
    add_rect(slide, 0.8, 5.0, 2.0, 0.05, fill_color=TEAL)

def add_page_number(slide, num):
    """Add a subtle page number at bottom right."""
    add_textbox(slide, 11.8, 7.0, 1.2, 0.4, text=str(num),
                font_size=10, color=MID_GRAY, alignment=PP_ALIGN.RIGHT)

def add_principle_badge(slide, left, top, width, height, label, color):
    """Small colored label/badge for principle names."""
    shape = add_rect(slide, left, top, width, height,
                     fill_color=color, corner_radius=0.1)
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = "Calibri"
    p.alignment = PP_ALIGN.CENTER
    tf.paragraphs[0].space_before = Pt(0)
    tf.paragraphs[0].space_after = Pt(0)

def add_connector_line(slide, x1, y1, x2, y2, color=MID_GRAY, width=1.5):
    """Add a straight connector line between two points."""
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR_TYPE.STRAIGHT,
        Inches(x1), Inches(y1), Inches(x2), Inches(y2)
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(width)
    return connector

# ══════════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE SLIDE
# ══════════════════════════════════════════════════════════════════════
def build_slide_01_title():
    slide = add_blank_slide()
    add_rect(slide, 0, 0, 13.333, 7.5, fill_color=NAVY)
    # decorative accent
    add_rect(slide, 0.8, 2.2, 0.08, 2.0, fill_color=TEAL)
    add_textbox(slide, 1.3, 2.2, 11.0, 0.5, text="KNOWLEDGE SHARING SESSION",
                font_size=14, color=TEAL, bold=True)
    add_textbox(slide, 1.3, 2.65, 11.0, 1.2, text="Trustworthy AI",
                font_size=48, bold=True, color=WHITE)
    add_textbox(slide, 1.3, 3.8, 11.0, 0.8,
                text="From Explainability to Verifiable Trust:\nA Framework for Building AI Systems People Can Rely On",
                font_size=18, color=RGBColor(0xCC, 0xD5, 0xE0))
    add_textbox(slide, 1.3, 5.8, 11.0, 0.4,
                text="Internal Knowledge Sharing  •  July 2026",
                font_size=13, color=MID_GRAY)
    add_speaker_notes(slide,
        "Welcome everyone. Today's session is about Trustworthy AI — not as a buzzword, "
        "but as an engineering discipline with concrete properties we can measure, verify, "
        "and build against. We'll work through what trustworthy AI actually means under "
        "the NIST AI RMF definition, why explainability alone isn't enough, the six core "
        "principles, how they connect to causal reasoning, and then we'll ground it all "
        "in what our own codebase implements against each principle. The goal is that you "
        "leave with a shared vocabulary and a mental model you can apply to your own work "
        "immediately."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE 2 — AGENDA / TALK ARC
# ══════════════════════════════════════════════════════════════════════
def build_slide_02_agenda():
    slide = add_blank_slide()
    add_title_bar(slide, "Today's Agenda", "The arc of this session, in six movements")
    agenda_items = [
        ("1", "Why This Matters", "The stakes have shifted — AI now makes consequential decisions"),
        ("2", "The Explainability Trap", "Why \"we can explain it\" ≠ \"we can trust it\""),
        ("3", "Core Principles", "Fairness, Transparency, Accountability, Robustness, Privacy, Reliability"),
        ("4", "The Vocabulary Map", "How related terms connect to the principles"),
        ("5", "XAI × Causal AI", "Why correlational explanations aren't enough"),
        ("6", "Our Codebase, Mapped", "What we've built against each principle — and what we haven't"),
    ]
    for i, (num, title, desc) in enumerate(agenda_items):
        y = 1.9 + i * 0.85
        add_rect(slide, 0.8, y, 0.55, 0.55, fill_color=TEAL, corner_radius=0.08)
        add_textbox(slide, 0.8, y + 0.05, 0.55, 0.45, text=num,
                    font_size=22, bold=True, color=WHITE, alignment=PP_ALIGN.CENTER)
        add_textbox(slide, 1.6, y + 0.02, 4.5, 0.35, text=title,
                    font_size=20, bold=True, color=DARK_TEXT)
        add_textbox(slide, 1.6, y + 0.35, 10.5, 0.35, text=desc,
                    font_size=13, color=BLUE_STEEL)
    add_page_number(slide, 2)
    add_speaker_notes(slide,
        "Quick roadmap so everyone knows where we're headed. Six sections, each building on "
        "the last. We start with motivation — why this isn't optional anymore — then the "
        "conceptual hinge: why the industry's default answer ('just make it explainable') "
        "isn't sufficient. From there we build up the actual principles, map the vocabulary "
        "you'll hear in the wild, connect to causal reasoning, and then ground everything "
        "in our own implementation. The last section is the payoff — here's the framework, "
        "here's what we built against it, and here's where we're honest about the gaps."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 1 — INTRODUCTION TO TRUSTWORTHY AI
# ══════════════════════════════════════════════════════════════════════

def build_slide_03_definition():
    """Slide 3: What is Trustworthy AI — NIST definition."""
    slide = add_blank_slide()
    add_title_bar(slide, "What Is Trustworthy AI?", "Not vibes. Verifiable properties.")

    # Definition block
    add_rect(slide, 0.8, 1.8, 11.7, 1.5, fill_color=TEAL_LIGHT, corner_radius=0.12)
    add_multiline_textbox(slide, 1.1, 1.9, 11.1, 1.3,
        lines=[
            "Trustworthy AI = an AI system whose behavior can be justifiably relied upon "
            "by the people affected by it.",
            "Not \"AI that feels okay\" — AI with demonstrable, verifiable properties.",
        ],
        font_size=17, color=DARK_TEXT, bold_first=True, line_spacing=1.4)

    # NIST 7 characteristics
    add_textbox(slide, 0.8, 3.7, 11.7, 0.45,
                text="NIST AI RMF defines trustworthy AI through seven characteristics:",
                font_size=16, bold=True, color=DARK_TEXT)

    nist_chars = [
        ("Valid &\nReliable", TEAL),
        ("Safe", CORAL),
        ("Secure &\nResilient", PURPLE),
        ("Accountable &\nTransparent", GREEN),
        ("Explainable &\nInterpretable", AMBER),
        ("Privacy-\nEnhanced", BLUE_STEEL),
        ("Fair — Harmful\nBias Managed", PRINCIPLE_COLORS["Fairness"]),
    ]
    for i, (label, color) in enumerate(nist_chars):
        x = 0.8 + i * 1.75
        shape = add_rect(slide, x, 4.3, 1.55, 1.3, fill_color=WHITE,
                         border_color=color, corner_radius=0.1)
        shape.line.width = Pt(2)
        tf = shape.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = label
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = color
        p.font.name = "Calibri"
        p.alignment = PP_ALIGN.CENTER
        tf.paragraphs[0].space_before = Pt(8)

    # Key insight callout
    add_rect(slide, 0.8, 5.95, 11.7, 0.6, fill_color=NAVY, corner_radius=0.08)
    add_textbox(slide, 1.1, 6.0, 11.1, 0.5,
                text='Key insight: "Explainable" is one of seven — not the whole definition. '
                     'This sets up everything that follows.',
                font_size=14, bold=True, color=WHITE)
    add_page_number(slide, 3)
    add_speaker_notes(slide,
        "Let's anchor on a precise definition immediately so we have one shared vocabulary "
        "for the rest of the session. The NIST AI Risk Management Framework defines "
        "trustworthy AI through seven characteristics: valid and reliable, safe, secure "
        "and resilient, accountable and transparent, explainable and interpretable, "
        "privacy-enhanced, and fair with harmful bias managed.\n\n"
        "I want to call out explicitly: explainability is ONE of seven. It's not the whole "
        "definition. A lot of industry discourse treats 'explainable' as synonymous with "
        "'trustworthy,' and that conflation is exactly what we'll unpack in the next section. "
        "Trust is a property of the whole system — data, model, deployment, monitoring, "
        "human oversight — not a property you get for free once you can visualize attention "
        "weights.\n\n"
        "Source: NIST AI RMF 1.0"
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 2 — WHY DO WE NEED TRUSTWORTHY AI
# ══════════════════════════════════════════════════════════════════════

def build_slide_04_shift_in_stakes():
    """Slide 4: The shift in stakes."""
    slide = add_blank_slide()
    add_title_bar(slide, "Why Do We Need Trustworthy AI?",
                  "The stakes have shifted — and regulation has caught up")

    # Before / After comparison
    add_textbox(slide, 0.8, 1.8, 5.5, 0.4, text="BEFORE: Recommendation Systems",
                font_size=18, bold=True, color=MID_GRAY)
    add_multiline_textbox(slide, 0.8, 2.3, 5.5, 1.2,
        lines=["• Wrong answer = mild annoyance", "• Stakes: click-through rate, engagement",
               "• Failure mode: user scrolls past"],
        font_size=15, color=BLUE_STEEL, line_spacing=1.5)

    add_textbox(slide, 7.0, 1.8, 5.5, 0.4, text="NOW: Decision-Making & Agentic Systems",
                font_size=18, bold=True, color=CORAL)
    add_multiline_textbox(slide, 7.0, 2.3, 5.5, 1.2,
        lines=["• Wrong answer = financial loss, legal exposure,", "  physical/safety harm, denied opportunity",
               "• Stakes: people's lives, livelihoods, rights"],
        font_size=15, color=DARK_TEXT, line_spacing=1.5)

    # Three failure categories
    add_textbox(slide, 0.8, 3.9, 11.7, 0.45,
                text="Three concrete failure categories (not abstract assertions):",
                font_size=17, bold=True, color=DARK_TEXT)

    failures = [
        ("Silent Failure", CORAL,
         "A model confidently wrong — hallucination, biased denial — with no signal "
         "that anything went wrong. The system doesn't know it doesn't know."),
        ("Adversarial Failure", AMBER,
         "A system manipulated by a bad actor — prompt injection, data poisoning, "
         "jailbreak. The model is functioning exactly as designed; the input isn't."),
        ("Systemic Failure", PURPLE,
         "Individually 'correct' predictions producing harmful aggregate outcomes — "
         "disparate impact across a protected group, even with no single wrong prediction."),
    ]
    for i, (label, color, desc) in enumerate(failures):
        y = 4.55 + i * 0.95
        add_rect(slide, 0.8, y, 2.0, 0.38, fill_color=color, corner_radius=0.06)
        add_textbox(slide, 0.95, y + 0.02, 1.8, 0.34, text=label,
                    font_size=14, bold=True, color=WHITE, alignment=PP_ALIGN.CENTER)
        add_textbox(slide, 3.1, y + 0.02, 9.6, 0.35, text=desc,
                    font_size=13, color=DARK_TEXT, line_spacing=1.2)

    add_page_number(slide, 4)
    add_speaker_notes(slide,
        "The fundamental shift: AI moved from recommending movies to making consequential "
        "decisions about people's lives. The failure modes are qualitatively different now.\n\n"
        "I want to ground this in three concrete categories rather than abstract claims. "
        "First, silent failure — the model is confidently wrong and there's no error signal. "
        "This is the hallucination problem but broader: any time the model is wrong with "
        "high confidence and no uncertainty flag.\n\n"
        "Second, adversarial failure — a bad actor deliberately manipulates the system. "
        "Prompt injection, data poisoning, jailbreaks. The model itself is functioning "
        "as designed; the input distribution has been weaponized.\n\n"
        "Third, systemic failure — every individual prediction might be correct by the "
        "training objective, but the aggregate outcome is harmful. Disparate impact is "
        "the canonical example: no single prediction is wrong, but a protected group "
        "is systematically disadvantaged. This is why you can't evaluate trustworthiness "
        "one prediction at a time."
    )
    return slide

def build_slide_05_regulatory_reality():
    """Slide 5: Regulatory reality + tie to project."""
    slide = add_blank_slide()
    add_title_bar(slide, "Regulatory Reality",
                  "Trustworthiness stopped being optional when regulation caught up to deployment")

    # EU AI Act
    add_rect(slide, 0.8, 1.8, 5.5, 3.6, fill_color=WHITE, border_color=MID_GRAY, corner_radius=0.1)
    add_rect(slide, 0.8, 1.8, 5.5, 0.55, fill_color=TEAL, corner_radius=0.08)
    add_textbox(slide, 1.1, 1.85, 5.0, 0.45, text="EU AI Act — Binding Law",
                font_size=18, bold=True, color=WHITE)
    eu_tiers = [
        "● Unacceptable risk → Prohibited (social scoring, etc.)",
        "● High risk → Strict obligations (conformity assessment,",
        "   human oversight, risk management, transparency)",
        "● Limited risk → Transparency obligations only",
        "● Minimal risk → No mandatory obligations",
        "",
        "▸ Most rules effective August 2026",
        "▸ High-risk obligations phase in through 2026–2027",
    ]
    add_multiline_textbox(slide, 1.1, 2.55, 5.0, 2.7, lines=eu_tiers,
                          font_size=13, color=DARK_TEXT, line_spacing=1.45)

    # NIST AI RMF
    add_rect(slide, 7.0, 1.8, 5.5, 3.6, fill_color=WHITE, border_color=MID_GRAY, corner_radius=0.1)
    add_rect(slide, 7.0, 1.8, 5.5, 0.55, fill_color=AMBER, corner_radius=0.08)
    add_textbox(slide, 7.3, 1.85, 5.0, 0.45, text="NIST AI RMF — Voluntary Framework",
                font_size=18, bold=True, color=WHITE)
    nist_items = [
        "Four functions: Govern → Map → Measure → Manage",
        "",
        "● Govern: Policies, accountability, culture",
        "● Map: Context, classification, risk assessment",
        "● Measure: Quantitative/qualitative evaluation",
        "● Manage: Risk treatment, incident response",
        "",
        "▸ Generative AI Profile (NIST AI 600-1) — 2024",
        "▸ Not certifiable (pair with ISO 42001)",
    ]
    add_multiline_textbox(slide, 7.3, 2.55, 5.0, 2.7, lines=nist_items,
                          font_size=13, color=DARK_TEXT, line_spacing=1.45)

    # Bottom tie-in
    add_rect(slide, 0.8, 5.75, 11.7, 0.55, fill_color=NAVY_LIGHT, corner_radius=0.08)
    add_textbox(slide, 1.1, 5.82, 11.1, 0.4,
                text="This is exactly why we built the guardrail / governance layer you'll see in the final section.",
                font_size=15, bold=True, color=DARK_TEXT)
    add_page_number(slide, 5)
    add_speaker_notes(slide,
        "Regulation is a driver here, not just ethics. The EU AI Act is binding law with "
        "four risk tiers — most rules take effect August 2026, with high-risk obligations "
        "phasing in through 2026–2027. If you're deploying AI that makes consequential "
        "decisions about people, you're likely in the high-risk tier and there are concrete "
        "obligations you need to meet.\n\n"
        "NIST's AI RMF is voluntary but globally referenced. Its four functions — Govern, "
        "Map, Measure, Manage — give you an operational cycle. The Generative AI Profile "
        "from 2024 exists specifically because generic AI risk guidance wasn't sufficient "
        "once LLMs and agentic systems became mainstream.\n\n"
        "The closing line here isn't marketing — it's context. The reason our codebase has "
        "a governance plane, an eval suite, and an incident review loop is because these "
        "frameworks demand them. We'll see the 1:1 mapping at the end.\n\n"
        "Sources: EU AI Act official text; NIST AI RMF 1.0; NIST AI 600-1"
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 3 — WHY EXPLAINABILITY ≠ TRUSTWORTHY
# ══════════════════════════════════════════════════════════════════════

def build_slide_06_xai_assumption():
    """Slide 6: The historical assumption."""
    slide = add_blank_slide()
    add_title_bar(slide, "The Explainability Trap",
                  "Why \"we can explain it\" stopped meaning \"we can trust it\"")

    # Historical box
    add_rect(slide, 0.8, 1.8, 11.7, 1.3, fill_color=TEAL_LIGHT, corner_radius=0.1)
    add_multiline_textbox(slide, 1.1, 1.9, 11.1, 1.1,
        lines=[
            "The historical assumption (roughly 2016–2022):",
            "Early XAI — LIME, SHAP, saliency maps, integrated gradients — treated "
            "\"if we can explain the prediction, we can trust it\" as self-evident.",
            "This made sense when models were simpler and stakes were lower. It doesn't hold anymore.",
        ],
        font_size=16, color=DARK_TEXT, bold_first=True, line_spacing=1.4)

    # Five reasons
    add_textbox(slide, 0.8, 3.45, 11.7, 0.4,
                text="Five reasons that assumption breaks down now:",
                font_size=17, bold=True, color=DARK_TEXT)

    reasons = [
        ("1", "Local fidelity ≠ global safety",
         "SHAP tells you feature contribution to this prediction — not whether overall behavior is fair or robust."),
        ("2", "Post-hoc ≠ causal",
         "Most XAI explains correlational attribution, not why the model decided. A plausible explanation can accompany a wrong decision."),
        ("3", "One of seven, not all seven",
         "An explainable model can still be unfair, insecure, non-private, or unreliable. Explainability is necessary but not sufficient."),
        ("4", "LLMs hallucinate explanations too",
         "A model asked \"why did you say that\" generates plausible-sounding rationale — not necessarily its actual internal process."),
        ("5", "Adversarial robustness is orthogonal",
         "A perfectly interpretable decision boundary can still be trivially fooled by prompt injection or perturbation."),
    ]
    for i, (num, title, desc) in enumerate(reasons):
        y = 4.05 + i * 0.65
        add_rect(slide, 0.8, y, 0.4, 0.4, fill_color=CORAL, corner_radius=0.06)
        add_textbox(slide, 0.8, y + 0.02, 0.4, 0.36, text=num,
                    font_size=16, bold=True, color=WHITE, alignment=PP_ALIGN.CENTER)
        add_textbox(slide, 1.45, y + 0.02, 3.8, 0.36, text=title,
                    font_size=15, bold=True, color=DARK_TEXT)
        add_textbox(slide, 5.4, y + 0.02, 7.1, 0.36, text=desc,
                    font_size=13, color=BLUE_STEEL)
    add_page_number(slide, 6)
    add_speaker_notes(slide,
        "This is the conceptual hinge of the entire talk, so let's spend real time here.\n\n"
        "The historical assumption was reasonable: early XAI methods like LIME and SHAP "
        "emerged when models were simpler and stakes were lower. The logic was: if we can "
        "surface which features drove a prediction, we can decide whether to trust it.\n\n"
        "That assumption has five failure modes today:\n\n"
        "1. SHAP values are locally faithful but globally silent. A feature attribution "
        "tells you about this one prediction — not whether the model's overall behavior "
        "is safe, fair, or robust.\n\n"
        "2. These are post-hoc, correlational explanations — not causal ones. A plausible-"
        "sounding explanation can accompany a completely wrong or unsafe decision. The "
        "explanation reads well, but it's explaining the wrong thing.\n\n"
        "3. Explainability is one of NIST's seven characteristics. An explainable model "
        "can fail on the other six — it can be unfair, insecure, non-private, unreliable. "
        "Explainability is necessary but not sufficient.\n\n"
        "4. LLMs have a unique problem: they can hallucinate their own explanations. Ask "
        "a model 'why did you say that' and it generates plausible rationale that may not "
        "reflect its actual internal process. This is a known, current interpretability "
        "research problem, not a hypothetical.\n\n"
        "5. Adversarial robustness is orthogonal to explainability. A model with a clean, "
        "interpretable decision boundary can be trivially fooled by an adversarial "
        "perturbation or prompt injection. Explainability tells you nothing about behavior "
        "under attack.\n\n"
        "Sources: Molnar, Interpretable Machine Learning (for LIME/SHAP mechanics); "
        "Samek et al., Explainable AI (for deep learning XAI limitations)"
    )
    return slide

def build_slide_06b_llm_specific():
    """Slide 6b: LLM-specific interpretability problems & adversarial angle."""
    slide = add_blank_slide()
    add_title_bar(slide, "Two Harder Problems",
                  "LLM explanations can be hallucinated — and adversarial robustness is orthogonal to explainability")

    # Left panel: LLMs hallucinate explanations
    add_rect(slide, 0.8, 1.85, 5.5, 4.5, fill_color=WHITE, border_color=PURPLE, corner_radius=0.1)
    add_rect(slide, 0.8, 1.85, 5.5, 0.55, fill_color=PURPLE, corner_radius=0.08)
    add_textbox(slide, 1.1, 1.9, 5.0, 0.45, text="LLMs Hallucinate Their Own Explanations",
                font_size=16, bold=True, color=WHITE)
    llm_lines = [
        "The problem: a model asked \"why did you",
        "say that\" generates a plausible-sounding",
        "rationale — not necessarily an accurate",
        "description of its internal process.",
        "",
        "This is a known, current interpretability",
        "research problem — not hypothetical.",
        "",
        "Implication for practice:",
        "• The model's self-reported reasoning",
        "  is a useful signal, not ground truth",
        "• Treat it as one input to a trust",
        "  judgment, not the judgment itself",
        "• Corroborate with behavioral testing",
        "  (counterfactuals, adversarial probes)",
        "",
        "Example: a model denies a loan and",
        "explains \"income too low\" — but a",
        "counterfactual test shows a higher-",
        "income applicant with the same profile",
        "also gets denied. The explanation was",
        "plausible — and wrong about the cause.",
    ]
    add_multiline_textbox(slide, 1.1, 2.6, 5.0, 3.5,
                          lines=llm_lines, font_size=13, color=DARK_TEXT, line_spacing=1.35)

    # Right panel: Adversarial robustness is orthogonal
    add_rect(slide, 7.0, 1.85, 5.5, 4.5, fill_color=WHITE, border_color=AMBER, corner_radius=0.1)
    add_rect(slide, 7.0, 1.85, 5.5, 0.55, fill_color=AMBER, corner_radius=0.08)
    add_textbox(slide, 7.3, 1.9, 5.0, 0.45, text="Adversarial Robustness Is Orthogonal",
                font_size=16, bold=True, color=WHITE)
    adv_lines = [
        "A model can have a perfectly clean,",
        "interpretable decision boundary and",
        "still be trivially fooled by:",
        "• An adversarial perturbation",
        "• A prompt injection attack",
        "• A jailbreak attempt",
        "",
        "Explainability tells you nothing about",
        "how the model behaves under attack.",
        "",
        "Implication for practice:",
        "• Explainability and robustness are",
        "  separate evaluation dimensions",
        "• Passing one doesn't imply the other",
        "• You need dedicated adversarial",
        "  testing (red-teaming, Garak/PyRIT)",
        "  — not just XAI tooling",
        "",
        "These are not edge cases — they're",
        "the primary attack surface for LLM",
        "applications in production.",
    ]
    add_multiline_textbox(slide, 7.3, 2.6, 5.0, 3.5,
                          lines=adv_lines, font_size=13, color=DARK_TEXT, line_spacing=1.35)

    add_page_number(slide, 7)
    add_speaker_notes(slide,
        "This slide goes deeper on two particularly hard problems that don't get enough "
        "attention in XAI discussions.\n\n"
        "Left side — LLMs hallucinate their own explanations: when you ask an LLM 'why "
        "did you say that,' it generates plausible-sounding rationale. But there's no "
        "guarantee this reflects its actual internal process. This is a known, current "
        "interpretability research problem. The practical implication: treat model self-"
        "reported reasoning as a useful signal, not ground truth. Corroborate it with "
        "behavioral testing — counterfactuals, adversarial probes. The loan denial example "
        "on the slide is a concrete case: the explanation says 'income too low' but a "
        "counterfactual test with a higher-income identical applicant also gets denied, "
        "revealing the explanation was plausible but wrong about the actual cause.\n\n"
        "Right side — adversarial robustness is orthogonal: a model with a perfectly clean, "
        "interpretable decision boundary can still be trivially fooled by adversarial "
        "inputs. Explainability tools don't test for this. You need dedicated adversarial "
        "testing infrastructure — Garak, PyRIT, red-teaming harnesses. These are separate "
        "evaluation dimensions and passing one tells you nothing about the other.\n\n"
        "Source: Molnar, Interpretable Machine Learning; Samek et al., Explainable AI; "
        "NIST AI 600-1 (adversarial robustness for generative AI)"
    )
    return slide

def build_slide_07_xai_reframe():
    """Slide 8: The reframe."""
    slide = add_blank_slide()
    add_title_bar(slide, "The Reframe",
                  "Explainability is an input to trust, not the output")

    # The reframe - dominant visual
    add_rect(slide, 0.8, 2.0, 11.7, 4.5, fill_color=NAVY, corner_radius=0.15)

    # Explainability → Trust (crossed out)
    add_textbox(slide, 1.5, 2.4, 4.5, 0.5, text="OLD MODEL",
                font_size=13, color=MID_GRAY, bold=True)
    add_textbox(slide, 1.5, 2.8, 4.5, 0.6, text="Explainability  →  Trust",
                font_size=24, bold=False, color=RGBColor(0x88, 0x95, 0xA5))
    # strike-through line
    add_rect(slide, 1.5, 3.05, 4.5, 0.03, fill_color=CORAL)

    # Big arrow
    add_textbox(slide, 6.0, 3.1, 1.5, 0.6, text="⟶",
                font_size=36, bold=True, color=TEAL, alignment=PP_ALIGN.CENTER)

    # New model
    add_textbox(slide, 7.5, 2.4, 4.5, 0.5, text="NEW MODEL",
                font_size=13, color=TEAL, bold=True)
    add_textbox(slide, 7.5, 2.8, 4.5, 0.6,
                text="Explainability → Trust Judgment ← Everything Else",
                font_size=20, bold=True, color=WHITE)

    # "Everything Else" components
    components = [
        "Data provenance", "Model behavior under shift", "Adversarial robustness",
        "Privacy guarantees", "Fairness across groups", "Human oversight",
        "Deployment monitoring", "Incident response"
    ]
    for i, comp in enumerate(components):
        col = i % 4
        row = i // 4
        x = 1.2 + col * 2.9
        y = 3.8 + row * 0.7
        add_rect(slide, x, y, 2.6, 0.45, fill_color=RGBColor(0x2D, 0x3A, 0x55),
                 corner_radius=0.06)
        add_textbox(slide, x + 0.15, y + 0.05, 2.3, 0.35, text=comp,
                    font_size=13, color=RGBColor(0xCC, 0xD5, 0xE0))

    # Bottom text
    add_textbox(slide, 1.1, 5.5, 11.0, 0.6,
                text="Trust is a property of the whole system (data, model, deployment, monitoring, "
                     "human oversight) — not a property you get for free once you can visualize attention weights.",
                font_size=15, bold=True, color=DARK_TEXT)
    add_page_number(slide, 7)
    add_speaker_notes(slide,
        "So here's the reframe I want everyone to leave with.\n\n"
        "The old model was: make it explainable → done, we can trust it. That's the mental "
        "model that LIME, SHAP, and attention visualization gave us — and it was useful for "
        "its time, but it's insufficient now.\n\n"
        "The new model: explainability is ONE input to a trust judgment. The trust judgment "
        "also needs data provenance, model behavior under distribution shift, adversarial "
        "robustness, privacy guarantees, fairness metrics across groups, human oversight "
        "structure, deployment monitoring, and incident response capability.\n\n"
        "Explainability is an input to trust, not the output of a trust assessment. And "
        "a trust judgment without the other inputs is incomplete — sometimes dangerously so, "
        "because a plausible-looking explanation can create over-trust in a system that's "
        "failing on dimensions you haven't measured yet."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 4 — CORE PRINCIPLES (one slide per principle)
# ══════════════════════════════════════════════════════════════════════

def build_principle_slide(slide_num, name, color, definition, why_fails, technique, notes):
    """Build a consistent principle slide template."""
    slide = add_blank_slide()
    # Title bar with principle color
    add_rect(slide, 0, 0, 13.333, 1.35, fill_color=color)
    add_textbox(slide, 0.8, 0.2, 11.7, 0.7,
                text=f"Core Principle: {name}",
                font_size=30, bold=True, color=WHITE)
    # Section label
    add_textbox(slide, 0.8, 0.78, 11.7, 0.4,
                text="Slide Group 4  •  One principle per slide  •  Definition → Failure → Technique",
                font_size=12, color=RGBColor(0xEE, 0xEE, 0xEE))
    add_rect(slide, 0, 1.35, 13.333, 0.04, fill_color=WHITE)

    # Three-column layout
    col_w = 3.6
    col_gap = 0.35
    col_y = 1.85

    # --- Definition ---
    add_rect(slide, 0.8, col_y, col_w, 0.5, fill_color=color, corner_radius=0.06)
    add_textbox(slide, 0.95, col_y + 0.05, col_w - 0.3, 0.4,
                text="DEFINITION", font_size=14, bold=True, color=WHITE)
    add_rect(slide, 0.8, col_y + 0.5, col_w, 3.6, fill_color=WHITE,
             border_color=RGBColor(0xE2, 0xE8, 0xF0), corner_radius=0.08)
    add_multiline_textbox(slide, 1.0, col_y + 0.7, col_w - 0.4, 3.2,
                          lines=definition, font_size=14, color=DARK_TEXT, line_spacing=1.45)

    # --- Why It Fails ---
    x2 = 0.8 + col_w + col_gap
    add_rect(slide, x2, col_y, col_w, 0.5, fill_color=NAVY, corner_radius=0.06)
    add_textbox(slide, x2 + 0.15, col_y + 0.05, col_w - 0.3, 0.4,
                text="WHY IT FAILS IN PRACTICE", font_size=14, bold=True, color=WHITE)
    add_rect(slide, x2, col_y + 0.5, col_w, 3.6, fill_color=WHITE,
             border_color=RGBColor(0xE2, 0xE8, 0xF0), corner_radius=0.08)
    add_multiline_textbox(slide, x2 + 0.2, col_y + 0.7, col_w - 0.4, 3.2,
                          lines=why_fails, font_size=14, color=DARK_TEXT, line_spacing=1.45)

    # --- Technique ---
    x3 = x2 + col_w + col_gap
    add_rect(slide, x3, col_y, col_w, 0.5, fill_color=TEAL, corner_radius=0.06)
    add_textbox(slide, x3 + 0.15, col_y + 0.05, col_w - 0.3, 0.4,
                text="ONE CONCRETE TECHNIQUE", font_size=14, bold=True, color=WHITE)
    add_rect(slide, x3, col_y + 0.5, col_w, 3.6, fill_color=TEAL_LIGHT,
             border_color=TEAL, corner_radius=0.08)
    add_multiline_textbox(slide, x3 + 0.2, col_y + 0.7, col_w - 0.4, 3.2,
                          lines=technique, font_size=14, color=DARK_TEXT, line_spacing=1.45)

    # Bottom insight bar
    add_rect(slide, 0.8, 6.3, 11.7, 0.45, fill_color=NAVY_LIGHT, corner_radius=0.06)
    add_textbox(slide, 1.0, 6.33, 11.3, 0.38,
                text=f"Key takeaway: This principle is one dimension of trust — it interacts with the other five. "
                     f"Evaluating any one in isolation is a partial assessment.",
                font_size=12, color=DARK_TEXT)

    add_page_number(slide, slide_num)
    add_speaker_notes(slide, notes)
    return slide

def build_slides_group_4():
    """Build all 6 principle slides."""
    slides = []

    # FAIRNESS
    slides.append(build_principle_slide(8, "Fairness",
        PRINCIPLE_COLORS["Fairness"],
        definition=[
            "Disparate treatment: intentionally",
            "different treatment based on a",
            "protected attribute.",
            "",
            "Disparate impact: a facially neutral",
            "policy/practice that disproportionately",
            "harms a protected group — even with",
            "no discriminatory intent.",
            "",
            "Key tension: you generally cannot",
            "satisfy all fairness metrics",
            "simultaneously (the impossibility",
            "result — Kleinberg et al., 2016).",
        ],
        why_fails=[
            "Training data encodes historical bias",
            "— the model learns and amplifies it.",
            "",
            "Fairness is not one metric —",
            "demographic parity, equalized odds,",
            "equal opportunity, and calibration",
            "are mathematically incompatible",
            "outside of degenerate cases.",
            "",
            "Choosing a metric is a normative",
            "decision, not a purely technical one.",
            "",
            "Proxy variables can reintroduce bias",
            "even when protected attributes are",
            "removed (e.g., ZIP code → race).",
        ],
        technique=[
            "Counterfactual testing:",
            "",
            "1. Take a test input.",
            "2. Swap only the protected attribute",
            "   (e.g., gender, race).",
            "3. Measure the output delta.",
            "4. Flag if the delta exceeds threshold.",
            "",
            "Mitigation stages:",
            "• Pre-processing: reweight/re-label",
            "  training data",
            "• In-processing: constrained training",
            "• Post-processing: calibrate outputs",
        ],
        notes=(
            "Fairness is the most philosophically complex of the six principles because "
            "it sits at the intersection of technical metrics and normative values.\n\n"
            "The definition: disparate treatment is intentional discrimination — you "
            "explicitly treat people differently based on a protected attribute. Disparate "
            "impact is harder: a policy that's neutral on its face but produces "
            "disproportionately negative outcomes for a protected group.\n\n"
            "The impossibility result is worth sitting with: you generally cannot satisfy "
            "demographic parity, equalized odds, and calibration simultaneously outside "
            "of degenerate cases. This means choosing a fairness metric is inherently a "
            "normative decision — whose definition of fairness are we optimizing for? "
            "Technical teams should not make this choice in isolation.\n\n"
            "For technique: counterfactual testing is the most direct approach — swap "
            "protected attributes and measure output change. This is exactly what our "
            "codebase's counterfactual test suite (Section 8 of the architecture doc) does. "
            "Mitigation can happen at three stages: pre-processing the data, constraining "
            "the training process, or post-processing model outputs.\n\n"
            "Source: NIST AI RMF; Kleinberg et al. 'Inherent Trade-Offs in the Fair "
            "Determination of Risk Scores' (2016)"
        )
    ))

    # TRANSPARENCY
    slides.append(build_principle_slide(9, "Transparency",
        PRINCIPLE_COLORS["Transparency"],
        definition=[
            "Transparency ≠ Explainability",
            "(these get conflated constantly):",
            "",
            "Transparency: can you see and audit",
            "HOW the system works — what data",
            "was used, what training process,",
            "what evaluation, what governance.",
            "",
            "Explainability: can you interpret",
            "a SPECIFIC decision the model made.",
            "",
            "Transparency mechanisms: model cards,",
            "datasheets for datasets, audit trails.",
            "Explainability mechanisms: SHAP,",
            "LIME, attention visualization.",
        ],
        why_fails=[
            "Organizations deploy models without",
            "documenting training data provenance,",
            "evaluation scope, or known limitations.",
            "",
            "Without an audit trail, you cannot",
            "retrospectively determine whether",
            "a harmful output was a one-off error",
            "or a systematic failure.",
            "",
            "Model cards are often treated as",
            "marketing documents rather than",
            "accurate disclosure — defeating",
            "their entire purpose.",
        ],
        technique=[
            "Structured transparency artifacts:",
            "",
            "• Model Cards (Mitchell et al., 2019):",
            "  standardized disclosure of intended",
            "  use, evaluation results, limitations,",
            "  ethical considerations.",
            "",
            "• Datasheets for Datasets (Gebru et al.,",
            "  2018): motivation, composition,",
            "  collection process, preprocessing,",
            "  recommended uses.",
            "",
            "• Audit trails: every decision/override",
            "  is logged with timestamp, actor,",
            "  and rationale.",
        ],
        notes=(
            "This distinction is one of the most important in the entire talk. Transparency "
            "and explainability get used interchangeably constantly, and they shouldn't be.\n\n"
            "Transparency answers: can I see how this system was built? What data? What "
            "training? What evaluation? Who approved it? Explainability answers: can I "
            "understand this specific decision?\n\n"
            "The mechanisms for each are different. For transparency: model cards, datasheets "
            "for datasets, audit trails, governance documentation. For explainability: SHAP, "
            "LIME, attention maps, counterfactual explanations.\n\n"
            "A model can be explainable without being transparent (you can run SHAP on a "
            "model whose training data provenance is unknown), and transparent without "
            "being explainable (you have perfect documentation of how a black-box model "
            "was trained, but can't interpret individual decisions). Both matter.\n\n"
            "Our codebase implements transparency through the governance plane, audit log, "
            "and policy-versioned constitution document.\n\n"
            "Sources: Mitchell et al., 'Model Cards for Model Reporting' (2019); "
            "Gebru et al., 'Datasheets for Datasets' (2018)"
        )
    ))

    # ACCOUNTABILITY
    slides.append(build_principle_slide(10, "Accountability",
        PRINCIPLE_COLORS["Accountability"],
        definition=[
            "Who is answerable when the system",
            "causes harm?",
            "",
            "This is an organizational/governance",
            "property — not a technical one.",
            "",
            "A system with no human accountable",
            "for high-risk decisions cannot be",
            "accountable, no matter how good",
            "its metrics are.",
            "",
            "Ties directly to NIST's Govern",
            "function and human-in-the-loop",
            "design requirements.",
        ],
        why_fails=[
            "Diffusion of responsibility: 'the data",
            "science team built it, the ML ops team",
            "deployed it, the product team chose",
            "the threshold' — no single owner.",
            "",
            "Automation bias: human reviewers",
            "rubber-stamp model outputs because",
            "'the AI usually gets it right.'",
            "",
            "Without a designated accountable",
            "human per decision class, no one can",
            "meaningfully answer 'why was this",
            "decision made.'",
        ],
        technique=[
            "Human-in-the-loop (HITL) design:",
            "",
            "• Designate accountable roles per",
            "  decision class BEFORE deployment.",
            "",
            "• Surface model reasoning alongside",
            "  the proposed action — not just the",
            "  action itself — so the human can",
            "  judge divergence.",
            "",
            "• Log every override and approval",
            "  with the accountable human's",
            "  identity and stated rationale.",
        ],
        notes=(
            "Accountability is the principle that's most likely to be overlooked by technical "
            "teams because it's not a metric you can put in a dashboard. But it's arguably "
            "the most important — it's the answer to 'who is answerable when this system "
            "causes harm.'\n\n"
            "The failure mode is diffusion of responsibility: the data science team built "
            "it, the ML ops team deployed it, the product team chose the threshold — no "
            "single person owns the outcome. This is a governance design problem, not a "
            "technical one.\n\n"
            "Automation bias compounds this: human reviewers tend to rubber-stamp model "
            "outputs because 'the AI usually gets it right,' which means the human in the "
            "loop provides accountability theater rather than actual accountability.\n\n"
            "Our implementation: the HITL approval queue surfaces model reasoning vs. "
            "action divergence (Section 9.2 of the architecture doc), and every override "
            "is logged with identity and rationale. This connects directly to the trust "
            "calibration concept we'll cover in the related terms section.\n\n"
            "Source: NIST AI RMF Govern function"
        )
    ))

    # ROBUSTNESS/SAFETY
    slides.append(build_principle_slide(11, "Robustness / Safety",
        PRINCIPLE_COLORS["Robustness"],
        definition=[
            "Performance under distribution shift,",
            "adversarial inputs, and edge cases —",
            "not just average-case accuracy.",
            "",
            "General robustness: resilience to",
            "natural noise, edge cases, and",
            "distribution drift over time.",
            "",
            "Adversarial robustness: resilience to",
            "inputs deliberately crafted to cause",
            "failure (perturbations, prompt",
            "injection, jailbreaks, data poisoning).",
        ],
        why_fails=[
            "Models are typically evaluated on",
            "IID held-out test sets — which tells",
            "you nothing about behavior under",
            "distribution shift or attack.",
            "",
            "LLMs are particularly vulnerable to",
            "prompt injection, jailbreaking, and",
            "indirect injection via retrieved",
            "documents — attack surfaces that",
            "didn't exist for traditional ML.",
            "",
            "Robustness is not binary — it's",
            "context-dependent: a model robust",
            "to one attack type may be fragile",
            "to another.",
        ],
        technique=[
            "Red-teaming and adversarial testing:",
            "",
            "• Structured red-teaming harness",
            "  (Garak, PyRIT) — systematically",
            "  probe for vulnerabilities across",
            "  known attack categories.",
            "",
            "• Prompt injection defenses: input",
            "  sanitization, instruction hierarchy,",
            "  delimiter-based separation.",
            "",
            "• Continuous monitoring, not",
            "  one-time pre-deployment eval.",
        ],
        notes=(
            "Robustness and safety are about how the model behaves when things go wrong — "
            "distribution shift, adversarial inputs, edge cases. This is distinct from "
            "average-case accuracy, which is what most ML evaluation measures.\n\n"
            "There are two sub-dimensions: general robustness (natural noise, drift) and "
            "adversarial robustness (deliberately crafted attacks). They require different "
            "testing strategies — testing against natural distribution shift doesn't tell "
            "you anything about how the system handles a jailbreak attempt.\n\n"
            "LLMs introduce novel attack surfaces: prompt injection, indirect injection "
            "via retrieved documents, jailbreaking. These didn't exist for traditional ML "
            "systems and require new defense strategies.\n\n"
            "Our implementation: the red-team harness uses Garak and PyRIT to systematically "
            "probe for vulnerabilities across attack categories (Sections 2 and 3 of the "
            "architecture doc), plus prompt injection defenses.\n\n"
            "Source: NIST AI 600-1 (Generative AI Profile); adversarial robustness literature"
        )
    ))

    # PRIVACY
    slides.append(build_principle_slide(12, "Privacy",
        PRINCIPLE_COLORS["Privacy"],
        definition=[
            "Differential privacy (formal definition):",
            "add calibrated noise so that no",
            "single individual's data materially",
            "changes the model's output or",
            "aggregate statistics — a mathematical",
            "(not just policy) privacy guarantee.",
            "",
            "Contrast with simple anonymization",
            "or redaction: removing PII fields is",
            "a data hygiene practice, not a formal",
            "privacy guarantee. These solve",
            "different problems.",
        ],
        why_fails=[
            "Simple anonymization/redaction can",
            "be defeated by linkage attacks —",
            "combining 'anonymized' datasets",
            "with public data to re-identify",
            "individuals.",
            "",
            "Models themselves can memorize",
            "and later regurgitate training data",
            "(training data extraction attacks)",
            "— a privacy failure that redaction",
            "at inference time cannot prevent.",
        ],
        technique=[
            "Layered approach — match the",
            "technique to the threat model:",
            "",
            "• PII detection/redaction (Presidio):",
            "  prevents PII from appearing in",
            "  model inputs and outputs.",
            "",
            "• Differential privacy (DP-SGD, DP",
            "  aggregation): formal guarantee at",
            "  training time or in aggregate stats.",
            "",
            "Be precise: these solve different",
            "problems. Redaction ≠ DP.",
        ],
        notes=(
            "Privacy is where precision of language matters most in this talk. There's a "
            "critical distinction between differential privacy and simple anonymization/"
            "redaction, and conflation here creates false confidence.\n\n"
            "Differential privacy gives a mathematical guarantee: adding calibrated noise "
            "such that no single individual's data materially changes the output. The "
            "privacy budget ε quantifies the guarantee. This is a formal property, not "
            "a policy statement.\n\n"
            "Simple redaction or anonymization — removing names, emails, phone numbers — "
            "is data hygiene, not a privacy guarantee. It can be defeated by linkage attacks "
            "where 'anonymized' datasets are combined with public data to re-identify "
            "individuals. And models can memorize and regurgitate training data, which "
            "inference-time redaction cannot prevent.\n\n"
            "Our implementation: PII detection/redaction pipeline using Presidio (Section 5 "
            "of the architecture doc). We should be honest on the codebase-mapping slide "
            "that this is redaction/tokenization, not formal differential privacy.\n\n"
            "Sources: Dwork & Roth, 'The Algorithmic Foundations of Differential Privacy'; "
            "Presidio documentation"
        )
    ))

    # RELIABILITY
    slides.append(build_principle_slide(13, "Reliability",
        PRINCIPLE_COLORS["Reliability"],
        definition=[
            "Consistent performance across time,",
            "environments, and inputs.",
            "",
            "Not just 'did it pass eval once' —",
            "does it keep performing at the",
            "same level as data, users, and",
            "context change.",
            "",
            "Ties directly to NIST's Measure",
            "function being continuous, not",
            "a pre-deployment gate.",
        ],
        why_fails=[
            "Data drift: the distribution of inputs",
            "in production diverges from training",
            "data — model accuracy silently",
            "degrades over time.",
            "",
            "Concept drift: the relationship",
            "between inputs and correct outputs",
            "changes — what was 'correct' last",
            "quarter may not be correct now.",
            "",
            "One-time evaluation gives a",
            "snapshot — it tells you nothing",
            "about the trend.",
        ],
        technique=[
            "Continuous monitoring + scheduled",
            "re-evaluation:",
            "",
            "• Groundedness/hallucination checks",
            "  as a continuous signal (not just",
            "  pre-deployment).",
            "",
            "• Scheduled eval cadence: run the",
            "  same benchmark suite on a fixed",
            "  schedule to detect drift.",
            "",
            "• Monitor input/output distributions",
            "  for statistical divergence from",
            "  the reference distribution.",
        ],
        notes=(
            "Reliability is about consistent performance over time — it's the temporal "
            "dimension of trustworthiness. A model that passes evaluation at deployment "
            "but silently degrades over six months is not reliable, even if the architecture "
            "and code haven't changed.\n\n"
            "The two drift mechanisms: data drift (the input distribution changes — new "
            "types of queries, new user demographics) and concept drift (the relationship "
            "between inputs and correct outputs changes — what was a correct answer last "
            "quarter may not be correct now due to policy changes, new knowledge, etc.).\n\n"
            "This is why NIST's Measure function is described as continuous, not a pre-"
            "deployment gate. You need ongoing measurement.\n\n"
            "Our implementation: groundedness/hallucination checks as a continuous signal, "
            "scheduled eval cadence running the same benchmark suite on a fixed schedule "
            "(Sections 11 and 13 of the architecture doc).\n\n"
            "Source: NIST AI RMF Measure function"
        )
    ))
    return slides

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 5 — RELATED TERMS / CONCEPT MAP
# ══════════════════════════════════════════════════════════════════════

def build_slide_14_concept_map():
    """Slide 14: Visual concept map of related terms."""
    slide = add_blank_slide()
    add_title_bar(slide, "Related Terms & Concepts",
                  "How the vocabulary connects to the core principles — a concept map")

    # Central hub - Core Principles
    cx, cy = 6.666, 4.0
    hub = add_rect(slide, cx - 1.3, cy - 0.5, 2.6, 1.0,
                   fill_color=NAVY, corner_radius=0.15)
    tf = hub.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Core\nPrinciples"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = "Calibri"
    p.alignment = PP_ALIGN.CENTER

    # Six principle nodes around center
    principles = [
        ("Fairness", PRINCIPLE_COLORS["Fairness"]),
        ("Transparency", PRINCIPLE_COLORS["Transparency"]),
        ("Accountability", PRINCIPLE_COLORS["Accountability"]),
        ("Robustness\n/ Safety", PRINCIPLE_COLORS["Robustness"]),
        ("Privacy", PRINCIPLE_COLORS["Privacy"]),
        ("Reliability", PRINCIPLE_COLORS["Reliability"]),
    ]
    import math
    p_nodes = []
    for i, (label, color) in enumerate(principles):
        angle = -math.pi/2 + i * 2*math.pi/6
        px = cx + 2.1 * math.cos(angle) - 0.6
        py = cy + 2.1 * math.sin(angle) - 0.35
        shape = add_rect(slide, px, py, 1.2, 0.7, fill_color=color, corner_radius=0.1)
        tf2 = shape.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = label
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = WHITE
        p2.font.name = "Calibri"
        p2.alignment = PP_ALIGN.CENTER
        p_nodes.append((px + 0.6, py + 0.35, color))

    # Outer ring - Related concepts
    outer_concepts = [
        (0.5, 1.85, 2.8, 1.15, AMBER, "Adversarial\nRobustness",
         "Resistance to inputs crafted\nto cause failure: adversarial\nexamples, prompt injection,\njailbreaks."),
        (9.8, 1.85, 2.8, 1.15, PURPLE, "Model\nAuditing",
         "Independent review of data,\ntraining, and behavior against\na standard — increasingly\na regulatory requirement."),
        (0.5, 5.2, 2.8, 1.55, TEAL, "Regulatory\nFrameworks",
         "NIST AI RMF (voluntary, US-originated,\nglobally referenced, 4 functions) + EU AI\nAct (binding law, 4 risk tiers, effective\nAug 2026). NIST is not certifiable;\nISO 42001 is the certifiable counterpart."),
        (9.8, 5.2, 2.8, 1.55, GREEN, "Ethical\nConsiderations",
         "The normative layer: whose values\nare encoded, who bears risk vs.\nwho gets benefit, and what happens\nwhen a fairness metric conflicts\nwith stakeholders' actual sense\nof fairness."),
        (5.1, 0.85, 3.0, 0.7, BLUE_STEEL, "Trust Calibration",
         "Goal: calibrated trust — human\nconfidence matches actual system\nreliability. Over-trust and under-\ntrust are both failures."),
    ]
    for (ox, oy, ow, oh, color, title, desc) in outer_concepts:
        shape = add_rect(slide, ox, oy, ow, oh, fill_color=WHITE,
                         border_color=color, corner_radius=0.1)
        shape.line.width = Pt(2)
        tf3 = shape.text_frame
        tf3.word_wrap = True
        p3 = tf3.paragraphs[0]
        p3.text = title
        p3.font.size = Pt(12)
        p3.font.bold = True
        p3.font.color.rgb = color
        p3.font.name = "Calibri"
        p3.alignment = PP_ALIGN.CENTER
        p3b = tf3.add_paragraph()
        p3b.text = desc
        p3b.font.size = Pt(9)
        p3b.font.color.rgb = BLUE_STEEL
        p3b.font.name = "Calibri"
        p3b.alignment = PP_ALIGN.CENTER
        p3b.line_spacing = Pt(13)

    # Connector lines (center to principle nodes)
    for (px, py, color) in p_nodes:
        add_connector_line(slide, cx, cy, px, py, color=MID_GRAY, width=1)

    add_page_number(slide, 15)
    add_speaker_notes(slide,
        "This is a vocabulary map, not a lecture slide — the goal is to show relationships, "
        "not list definitions.\n\n"
        "At center: the six core principles from the previous section. Radiating outward: "
        "the terms you'll hear in industry conversations, regulatory discussions, and "
        "research papers.\n\n"
        "Adversarial robustness connects most directly to Robustness/Safety — it's the "
        "deliberate-attack subset of general robustness. Model auditing connects to "
        "Transparency and Accountability — auditing is how you verify those properties "
        "externally. Regulatory frameworks (NIST, EU AI Act) provide the structure that "
        "makes accountability enforceable. Ethical considerations are the normative "
        "foundation underneath all of this — the 'why' behind the 'what.' And trust "
        "calibration is the human-factors goal: not maximal trust, but appropriately "
        "calibrated trust.\n\n"
        "The key relationship to notice: none of these terms is independent. Adversarial "
        "robustness without accountability is a technical exercise. Regulation without "
        "ethics is compliance theater. The principles and related concepts form an "
        "interconnected system, not a checklist.\n\n"
        "Sources: NIST AI RMF; EU AI Act; Molnar's Interpretable Machine Learning"
    )
    return slide

def build_slide_15_regulatory_deepdive():
    """Slide 15: Regulatory frameworks deep-dive."""
    slide = add_blank_slide()
    add_title_bar(slide, "Regulatory Frameworks in Detail",
                  "NIST AI RMF vs. EU AI Act — two frameworks, different teeth")

    # NIST column
    add_rect(slide, 0.8, 1.85, 5.5, 4.5, fill_color=WHITE, border_color=TEAL, corner_radius=0.1)
    add_rect(slide, 0.8, 1.85, 5.5, 0.7, fill_color=TEAL, corner_radius=0.08)
    add_textbox(slide, 1.1, 1.9, 5.0, 0.25, text="NIST AI RMF 1.0",
                font_size=18, bold=True, color=WHITE)
    add_textbox(slide, 1.1, 2.2, 5.0, 0.25, text="Voluntary framework — US-originated, globally referenced",
                font_size=12, color=RGBColor(0xCC, 0xE5, 0xE0))

    nist_detail = [
        "Four functions (continuous cycle):",
        "",
        "GOVERN → organizational context,",
        "  policies, accountability, risk culture",
        "MAP → system context, classification,",
        "  risk assessment, impact analysis",
        "MEASURE → quantitative & qualitative",
        "  evaluation — continuous, not one-time",
        "MANAGE → risk treatment, incident",
        "  response, ongoing monitoring",
        "",
        "▸ Not certifiable — pair with ISO 42001",
        "  for a certifiable management system",
        "▸ Gen AI Profile (NIST AI 600-1, 2024)",
        "  addresses LLM/agentic-specific risks",
        "▸ Free, publicly available, widely adopted",
        "  as the shared vocabulary for AI risk",
    ]
    add_multiline_textbox(slide, 1.1, 2.7, 5.0, 3.4,
                          lines=nist_detail, font_size=12, color=DARK_TEXT, line_spacing=1.35)

    # EU AI Act column
    add_rect(slide, 7.0, 1.85, 5.5, 4.5, fill_color=WHITE, border_color=CORAL, corner_radius=0.1)
    add_rect(slide, 7.0, 1.85, 5.5, 0.7, fill_color=CORAL, corner_radius=0.08)
    add_textbox(slide, 7.3, 1.9, 5.0, 0.25, text="EU AI Act",
                font_size=18, bold=True, color=WHITE)
    add_textbox(slide, 7.3, 2.2, 5.0, 0.25, text="Binding law — enforceable, with penalties",
                font_size=12, color=RGBColor(0xFD, 0xD8, 0xD5))

    eu_detail = [
        "Four risk tiers:",
        "",
        "UNACCEPTABLE → prohibited entirely",
        "  (social scoring, manipulative AI, etc.)",
        "HIGH RISK → strict obligations:",
        "  conformity assessment, human",
        "  oversight, risk management system,",
        "  technical documentation, transparency",
        "LIMITED RISK → transparency obligations",
        "  only (e.g., chatbot disclosure)",
        "MINIMAL RISK → no mandatory obligations",
        "",
        "▸ Most rules effective August 2026",
        "▸ High-risk obligations phase in through",
        "  2026–2027 — this is now, not later",
        "▸ Extraterritorial scope — applies to",
        "  any system deployed in the EU market",
    ]
    add_multiline_textbox(slide, 7.3, 2.7, 5.0, 3.4,
                          lines=eu_detail, font_size=12, color=DARK_TEXT, line_spacing=1.35)

    # Bottom insight
    add_rect(slide, 0.8, 6.6, 11.7, 0.45, fill_color=NAVY_LIGHT, corner_radius=0.08)
    add_textbox(slide, 1.1, 6.63, 11.1, 0.38,
                text="Practical guidance: Use NIST's vocabulary for internal risk conversations. "
                     "Use the EU AI Act's risk tiers to determine your compliance obligations. "
                     "They're complementary, not competing.",
                font_size=13, bold=True, color=DARK_TEXT)
    add_page_number(slide, 15)
    add_speaker_notes(slide,
        "This slide provides the detail behind the concept map's 'Regulatory Frameworks' "
        "node. Two frameworks, different authority, complementary in practice.\n\n"
        "NIST AI RMF is voluntary but globally referenced. Its four functions — Govern, "
        "Map, Measure, Manage — form a continuous cycle, not a linear checklist. The "
        "Generative AI Profile (NIST AI 600-1, 2024) specifically addresses LLM and "
        "agentic AI risks. NIST is not certifiable — organizations that need certification "
        "typically pair it with ISO 42001, which provides the certifiable management "
        "system structure.\n\n"
        "The EU AI Act is binding law with four risk tiers and real enforcement teeth. "
        "Most rules are effective August 2026 — that's next month. High-risk obligations "
        "phase in through 2026–2027. The Act has extraterritorial scope: it applies to "
        "any system deployed in the EU market, regardless of where it was built.\n\n"
        "Practical guidance: use NIST's vocabulary for internal risk conversations (it's "
        "richer and more operational). Use the EU AI Act's risk tiers to determine your "
        "actual compliance obligations (they're legally binding). They're complementary "
        "frameworks, not competing ones.\n\n"
        "Sources: NIST AI RMF 1.0; NIST AI 600-1; EU AI Act official text (Regulation "
        "2024/1689)"
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 6 — XAI + CAUSAL AI
# ══════════════════════════════════════════════════════════════════════

def build_slide_15_xai_causal():
    """Slide 15: The core claim — association vs causation."""
    slide = add_blank_slide()
    add_title_bar(slide, "XAI × Causal AI",
                  "The core problem: most XAI explains association, not causation")

    # Left: Association
    add_rect(slide, 0.8, 1.9, 5.5, 4.3, fill_color=WHITE, border_color=MID_GRAY, corner_radius=0.1)
    add_rect(slide, 0.8, 1.9, 5.5, 0.55, fill_color=CORAL, corner_radius=0.08)
    add_textbox(slide, 1.1, 1.95, 5.0, 0.45, text="What SHAP / LIME / Attention Gives You",
                font_size=16, bold=True, color=WHITE)
    assoc_lines = [
        "Correlational attribution:",
        "\"Feature X was associated with output Y\"",
        "",
        "The explanation is locally faithful",
        "— correct for this prediction — but",
        "globally silent about whether the model",
        "would fail under distribution shift.",
        "",
        "A SHAP value can look perfectly",
        "reasonable while the model is latched",
        "onto a spurious correlate of a",
        "protected attribute.",
        "",
        "→ Right for the wrong reason.",
    ]
    add_multiline_textbox(slide, 1.1, 2.65, 5.0, 3.3,
                          lines=assoc_lines, font_size=13, color=DARK_TEXT, line_spacing=1.4)

    # Right: Causation
    add_rect(slide, 7.0, 1.9, 5.5, 4.3, fill_color=WHITE, border_color=TEAL, corner_radius=0.1)
    add_rect(slide, 7.0, 1.9, 5.5, 0.55, fill_color=TEAL, corner_radius=0.08)
    add_textbox(slide, 7.3, 1.95, 5.0, 0.45, text="What Causal Explanations Add",
                font_size=16, bold=True, color=WHITE)
    causal_lines = [
        "Counterfactual reasoning:",
        "\"If X had been different, would the",
        "outcome have changed?\"",
        "",
        "Causal graphs give you an explanation",
        "tied to an actual mechanism — far",
        "more robust to distribution shift",
        "and far harder to game.",
        "",
        "A causal explanation surviving a",
        "distribution shift is genuine evidence",
        "of trustworthiness; a correlational one",
        "surviving is not evidence either way.",
        "",
        "→ Right for the right reason.",
    ]
    add_multiline_textbox(slide, 7.3, 2.65, 5.0, 3.3,
                          lines=causal_lines, font_size=13, color=DARK_TEXT, line_spacing=1.4)

    # Bottom practical framing
    add_rect(slide, 0.8, 6.5, 11.7, 0.55, fill_color=NAVY_LIGHT, corner_radius=0.08)
    add_textbox(slide, 1.1, 6.53, 11.1, 0.45,
                text="Practical takeaway: You don't need a full causal model. Ask \"is this explanation "
                     "counterfactually testable?\" as a discipline — that alone is a meaningfully more rigorous bar.",
                font_size=14, bold=True, color=DARK_TEXT)
    add_page_number(slide, 15)
    add_speaker_notes(slide,
        "This is the deepest section conceptually, so let's be precise.\n\n"
        "Production XAI methods — SHAP, LIME, attention visualization — explain "
        "association, not causation. They tell you a feature was correlated with the "
        "output, not that changing it would actually change the outcome in the real world. "
        "This matters for trust specifically: a correlational explanation can be right "
        "for the wrong reason. A model correctly predicting an outcome by latching onto "
        "a spurious correlate of a protected attribute, with a SHAP explanation that "
        "looks perfectly reasonable while the model would fail under distribution shift "
        "or actively encode bias.\n\n"
        "Causal explanations add counterfactual reasoning: 'if X had been different, "
        "would the outcome have changed?' Causal graphs tie explanations to actual "
        "mechanisms, making them more robust to shift and harder to game. A causal "
        "explanation that survives a distribution shift is genuine evidence of "
        "trustworthiness; a correlational one surviving is not evidence either way.\n\n"
        "Practical framing: you don't need to build a full structural causal model to "
        "benefit from this lens. Even asking 'is this SHAP explanation counterfactually "
        "testable?' as a review discipline is a meaningfully more rigorous bar than "
        "accepting the attribution at face value.\n\n"
        "This connects directly back to Slide Group 3: this is precisely WHY explainability "
        "doesn't automatically mean trustworthy. Correlational explanations are the default "
        "output of most XAI tooling, and causal grounding is the missing ingredient that "
        "would make an explanation actually load-bearing for a trust claim.\n\n"
        "Sources: Molnar, Interpretable Machine Learning (XAI mechanics); "
        "Samek et al., Explainable AI (deep learning XAI); Pearl & Mackenzie, "
        "The Book of Why (causal reasoning foundations)"
    )
    return slide

def build_slide_17_xai_bridge():
    """Slide 17: Bridge from theory to practice — connecting XAI insights back to principles."""
    slide = add_blank_slide()
    add_title_bar(slide, "Putting It All Together",
                  "From explainability → causal reasoning → verifiable trust")

    # Three-part flow
    flow = [
        ("1", "Explainability\nis necessary", TEAL,
         "What we learned: XAI methods (SHAP, LIME) give local, correlational explanations "
         "— useful for debugging, insufficient for trust. Explanations are an input to "
         "trust judgments, not the output."),
        ("2", "Causal reasoning\nis the upgrade", AMBER,
         "What we learned: counterfactual reasoning and causal graphs give explanations "
         "tied to mechanisms — more robust to shift, harder to game. Even the discipline "
         "of asking 'is this counterfactually testable?' raises the bar meaningfully."),
        ("3", "System-level trust\nis the answer", NAVY,
         "Where we land: trustworthiness isn't one property you measure once. It's a "
         "system-level property verified continuously across all seven NIST characteristics "
         "— and the next section shows exactly what that looks like in our codebase."),
    ]
    for i, (num, title, color, desc) in enumerate(flow):
        y = 2.0 + i * 1.75
        # Number circle
        shape = slide.shapes.add_shape(
            MSO_SHAPE.OVAL, Inches(1.0), Inches(y + 0.2), Inches(0.7), Inches(0.7)
        )
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        tf = shape.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = num
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = WHITE
        p.font.name = "Calibri"
        p.alignment = PP_ALIGN.CENTER

        # Title
        add_textbox(slide, 2.0, y + 0.05, 4.5, 0.7, text=title,
                    font_size=19, bold=True, color=color, line_spacing=1.2)
        # Description
        add_textbox(slide, 2.0, y + 0.8, 10.5, 0.7, text=desc,
                    font_size=13, color=DARK_TEXT, line_spacing=1.4)

    add_page_number(slide, 17)
    add_speaker_notes(slide,
        "This bridge slide connects the conceptual deep-dive back to the practical "
        "application we're about to see in the codebase mapping section.\n\n"
        "Three beats:\n"
        "1. Explainability is necessary but not sufficient. We've established that XAI "
        "methods give correlational, local explanations — useful for debugging, not "
        "sufficient for trust. Explanations are inputs to trust judgments.\n"
        "2. Causal reasoning is the upgrade. Counterfactual reasoning gives mechanism-"
        "tied explanations that are more robust. Even without full causal infrastructure, "
        "the discipline of asking 'is this counterfactually testable?' raises the bar.\n"
        "3. System-level trust is where we land. Trustworthiness is verified continuously "
        "across all seven NIST characteristics, not measured once. The next section shows "
        "what this looks like in our actual implementation.\n\n"
        "This is the transition moment — we've built the theory, now let's see the practice."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# SLIDE GROUP 7 — RESOURCES
# ══════════════════════════════════════════════════════════════════════

def build_slide_18_resources():
    """Slide 16: Resources / References."""
    slide = add_blank_slide()
    add_title_bar(slide, "Resources & Further Reading",
                  "For those who want to go deeper — all primary sources cited in this talk")

    resources = [
        ("NIST AI Risk Management Framework (AI RMF 1.0)",
         "National Institute of Standards and Technology. The four-function core "
         "(Govern / Map / Measure / Manage) plus the Generative AI Profile "
         "(NIST AI 600-1) for LLM/agentic-specific risks. "
         "Available at: nist.gov/itl/ai-risk-management-framework"),

        ("Christoph Molnar — Interpretable Machine Learning",
         "Free online book; the standard reference for the actual mechanics of XAI "
         "methods (LIME, SHAP, permutation importance, partial dependence, "
         "counterfactual explanations) that Slide Groups 3 and 6 critique. "
         "Available at: christophm.github.io/interpretable-ml-book"),

        ("Explainable AI: Interpreting, Explaining and Visualizing Deep Learning",
         "Samek, Montavon, Vedaldi, Hansen, Müller (eds.). Deeper technical/academic "
         "grounding on XAI methods specifically for deep learning — useful for anyone "
         "who wants to go past the survey level. Springer LNCS vol. 11700, 2019."),

        ("EU AI Act — Official Text / European Commission Summary",
         "Binding EU law establishing four risk tiers (unacceptable, high, limited, "
         "minimal) with staggered compliance deadlines through 2026–2027. "
         "Primary source at: artificialintelligenceact.eu"),

        ("Dwork & Roth — The Algorithmic Foundations of Differential Privacy",
         "The foundational text on differential privacy — the mathematical framework "
         "for formal privacy guarantees. Foundations and Trends in Theoretical "
         "Computer Science, 2014."),

        ("Mitchell et al. — Model Cards for Model Reporting (2019)",
         "Standardized framework for transparent model documentation: intended use, "
         "evaluation, limitations, ethical considerations. FAccT 2019."),

        ("Gebru et al. — Datasheets for Datasets (2018)",
         "Companion to Model Cards: standardized documentation for datasets — "
         "motivation, composition, collection, preprocessing, recommended uses. "
         "Communications of the ACM, 2021."),
    ]

    for i, (title, desc) in enumerate(resources):
        y = 1.65 + i * 0.82
        add_textbox(slide, 0.8, y, 11.7, 0.3, text=title,
                    font_size=14, bold=True, color=DARK_TEXT)
        add_textbox(slide, 0.8, y + 0.28, 11.7, 0.45, text=desc,
                    font_size=11, color=BLUE_STEEL, line_spacing=1.2)
        if i < len(resources) - 1:
            add_rect(slide, 0.8, y + 0.76, 11.7, 0.01, fill_color=RGBColor(0xE2, 0xE8, 0xF0))

    add_textbox(slide, 0.8, 6.8, 11.7, 0.4,
                text="This slide is designed to be screenshotted — all citations are in one place.",
                font_size=11, color=MID_GRAY)
    add_page_number(slide, 18)
    add_speaker_notes(slide,
        "This is a reference slide — I'm not going to read it aloud. The purpose is to give "
        "everyone a single place to screenshot or copy citations for further reading.\n\n"
        "The key calls: NIST AI RMF 1.0 and the Generative AI Profile (NIST AI 600-1) for "
        "the framework; Molnar's book for the XAI mechanics that we critiqued in Slide "
        "Groups 3 and 6 (it's important we cite it directly — we're not dismissing these "
        "methods, just contextualizing their limits); Samek et al. for the deep learning "
        "XAI volume; the EU AI Act for regulatory specifics; Dwork & Roth for differential "
        "privacy foundations; and Mitchell et al. / Gebru et al. for transparency artifacts.\n\n"
        "All of these are publicly available. Molnar's book and the NIST framework are free online."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# CODEBASE MAPPING SECTION
# ══════════════════════════════════════════════════════════════════════

def build_slide_17_codebase_section_title():
    """Slide 17: Section divider for codebase mapping."""
    slide = add_blank_slide()
    add_section_divider(slide, "FINAL SECTION",
                        "Our Codebase, Mapped to the Framework",
                        "Here's the framework. Here's what we actually built against it.")
    add_speaker_notes(slide,
        "This is the payoff section. We've built the conceptual framework — now let's map "
        "it directly to what our codebase implements. This is peer-to-peer: here's what "
        "we did, here's what we didn't, and here's where we're being honest about the gaps."
    )
    return slide

def build_slide_18_codebase_table():
    """Slide 18: Codebase mapping table."""
    slide = add_blank_slide()
    add_title_bar(slide, "Codebase → Framework Mapping",
                  "One line per principle — what we built against what we talked about")

    # Build table
    rows = 9  # header + 8 rows
    cols = 2
    table_shape = slide.shapes.add_table(rows, cols,
                                         Inches(0.6), Inches(1.65),
                                         Inches(12.1), Inches(5.3))
    table = table_shape.table

    # Column widths
    table.columns[0].width = Inches(5.2)
    table.columns[1].width = Inches(6.9)

    data = [
        ("Principle / Concept from the talk", "What we built"),
        ("Fairness (bias detection)",
         "Counterfactual test suite (Section 8, architecture doc) — same technique "
         "described in Core Principles, not a toy example"),
        ("Transparency / Accountability",
         "Governance plane, audit log, policy-versioned 'constitution' document "
         "(Sections 9.1 / 12)"),
        ("Robustness / Safety (adversarial)",
         "Red-team harness (Garak / PyRIT), prompt injection defenses (Sections 2 / 3)"),
        ("Privacy",
         "PII detection/redaction pipeline (Presidio-based, Section 5). ⚠ Honest note: "
         "this is redaction/tokenization, not differential privacy in the formal sense — "
         "see the distinction made in the Privacy principle slide."),
        ("Reliability",
         "Groundedness / hallucination checks, scheduled eval cadence (Sections 11 / 13)"),
        ("Human-AI collaboration / trust calibration",
         "HITL approval queue surfacing model reasoning vs. action divergence (Section 9.2), "
         "Streamlit test console (Addendum §8.5)"),
        ("Regulatory frameworks (NIST functions)",
         "Govern → policy docs; Map → data classification tiers (§4); "
         "Measure → eval suite; Manage → incident review loop (§13) — direct 1:1 mapping"),
        ("Explainability vs. trustworthiness (Slide Group 3)",
         "What we do NOT do: model-internals interpretability. We have guardrails and "
         "governance, not SHAP/LIME integration — and being explicit about this gap is "
         "more credible than overclaiming."),
    ]

    for r, (principle, impl) in enumerate(data):
        for c, text in enumerate([principle, impl]):
            cell = table.cell(r, c)
            cell.text = ""
            p = cell.text_frame.paragraphs[0]
            p.text = text
            p.font.name = "Calibri"
            p.font.size = Pt(13) if r == 0 else Pt(12)
            p.font.bold = (r == 0)
            p.font.color.rgb = WHITE if r == 0 else DARK_TEXT

            # Header row styling
            if r == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = NAVY
            elif r % 2 == 0:
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor(0xF0, 0xF4, 0xF8)
            else:
                cell.fill.solid()
                cell.fill.fore_color.rgb = WHITE

            # Cell margins
            cell.margin_left = Inches(0.15)
            cell.margin_right = Inches(0.15)
            cell.margin_top = Inches(0.06)
            cell.margin_bottom = Inches(0.06)

    # Bottom note
    add_textbox(slide, 0.8, 7.05, 11.7, 0.35,
                text="Sections refer to the main architecture document. All implementations are in this repository.",
                font_size=10, color=MID_GRAY)
    add_page_number(slide, 18)
    add_speaker_notes(slide,
        "This table is the payoff — here's the entire conceptual framework mapped to "
        "actual implementation. Every principle from the talk has a corresponding "
        "component in our codebase.\n\n"
        "Walk through each row and connect back to the relevant principle slide:\n\n"
        "Fairness → Counterfactual test suite: exactly the technique described in the "
        "Fairness slide — swap protected attributes, measure output delta.\n\n"
        "Transparency/Accountability → Governance plane, audit log, policy-versioned "
        "constitution: the transparency artifacts and accountability mechanisms from "
        "the principles.\n\n"
        "Robustness/Safety → Red-team harness with Garak/PyRIT: systematic adversarial "
        "testing as described in the Robustness slide.\n\n"
        "Privacy → PII detection/redaction with Presidio: and here's the honesty moment — "
        "we call out explicitly that this is redaction, not differential privacy. These "
        "are different tools for different threat models, and conflating them creates "
        "false confidence.\n\n"
        "Reliability → Groundedness checks and scheduled eval cadence: continuous "
        "monitoring, not one-time evaluation.\n\n"
        "Human-AI collaboration → HITL approval queue with reasoning/action divergence "
        "displayed: this is trust calibration in practice — the human sees not just what "
        "the model wants to do, but why.\n\n"
        "Regulatory → Direct 1:1 NIST function mapping: Govern, Map, Measure, Manage "
        "all have concrete implementations.\n\n"
        "And the last row is the honesty row: we do NOT do model-internals interpretability. "
        "We have guardrails and governance, not SHAP/LIME integration. Being explicit "
        "about what you don't do is more credible than overclaiming."
    )
    return slide

def build_slide_19_nist_mapping():
    """Slide 19: NIST functions 1:1 mapping visual."""
    slide = add_blank_slide()
    add_title_bar(slide, "NIST AI RMF Functions → Our Implementation",
                  "A direct 1:1 mapping — each NIST function has a concrete counterpart")

    nist_map = [
        ("GOVERN", TEAL,
         "Policy documents, accountability\nstructure, risk appetite statements",
         "Establishes the organizational context\nand governance culture"),
        ("MAP", AMBER,
         "Data classification tiers (Section 4),\ncontext definition, risk assessment",
         "Understand the system's context,\nidentify and categorize risks"),
        ("MEASURE", PURPLE,
         "Eval suite: fairness, robustness,\ngroundedness, privacy checks",
         "Quantitative and qualitative evaluation\n— continuous, not pre-deployment only"),
        ("MANAGE", CORAL,
         "Incident review loop (Section 13),\ncontinuous monitoring, HITL overrides",
         "Risk treatment, response, and ongoing\nmanagement based on measurement"),
    ]

    for i, (label, color, our_impl, nist_desc) in enumerate(nist_map):
        y = 1.85 + i * 1.35

        # Function label
        add_rect(slide, 0.8, y, 1.8, 0.6, fill_color=color, corner_radius=0.08)
        add_textbox(slide, 0.8, y + 0.1, 1.8, 0.4, text=label,
                    font_size=16, bold=True, color=WHITE, alignment=PP_ALIGN.CENTER)

        # Arrow
        add_textbox(slide, 2.8, y + 0.1, 0.5, 0.4, text="→",
                    font_size=22, bold=True, color=TEAL, alignment=PP_ALIGN.CENTER)

        # Our implementation
        add_rect(slide, 3.4, y, 5.0, 0.95, fill_color=WHITE,
                 border_color=color, corner_radius=0.08)
        add_textbox(slide, 3.55, y + 0.08, 4.7, 0.2, text="OUR IMPLEMENTATION",
                    font_size=9, bold=True, color=color)
        add_multiline_textbox(slide, 3.55, y + 0.28, 4.7, 0.6,
                              lines=our_impl.split("\n"),
                              font_size=13, color=DARK_TEXT, line_spacing=1.3)

        # NIST description
        add_textbox(slide, 8.8, y + 0.08, 3.8, 0.25, text="NIST DEFINITION",
                    font_size=9, bold=True, color=MID_GRAY)
        add_multiline_textbox(slide, 8.8, y + 0.28, 3.8, 0.6,
                              lines=nist_desc.split("\n"),
                              font_size=12, color=BLUE_STEEL, line_spacing=1.3)

    add_page_number(slide, 19)
    add_speaker_notes(slide,
        "This slide draws the 1:1 mapping between NIST's four functions and our "
        "implementation — it's genuinely worth calling out because it shows that the "
        "framework isn't abstract; every function has a concrete counterpart in our system.\n\n"
        "Govern → policy docs: this is the organizational layer that says who is "
        "accountable and what our risk appetite is.\n\n"
        "Map → data classification tiers (Section 4): understanding what data we're "
        "handling, at what sensitivity level, and what the risk context is.\n\n"
        "Measure → our eval suite: fairness, robustness, groundedness, privacy checks — "
        "continuous measurement, not a one-time pre-deployment gate.\n\n"
        "Manage → incident review loop (Section 13): when measurement finds something, "
        "what happens? This is the feedback loop that makes the whole cycle operational.\n\n"
        "This is a strong closing visual because it shows the framework isn't theoretical — "
        "every function has been operationalized."
    )
    return slide

def build_slide_20_honesty():
    """Slide 20: What we don't do — honesty slide."""
    slide = add_blank_slide()
    add_title_bar(slide, "What We Don't Do (Yet)",
                  "Being explicit about gaps is more credible than overclaiming")

    gaps = [
        ("No model-internals interpretability",
         "We have guardrails and governance — not SHAP/LIME integration or attention "
         "visualization. Our trustworthiness comes from system-level controls, not "
         "from peering inside the model. This is a legitimate architectural choice, "
         "not an omission, but it's worth naming explicitly."),
        ("Redaction ≠ Differential Privacy",
         "Our PII pipeline (Presidio) does detection and redaction/tokenization — this "
         "prevents PII from appearing in model inputs and outputs. It does NOT provide "
         "the formal mathematical guarantee of differential privacy. Different tools "
         "for different threat models; the honesty is in not conflating them."),
        ("Causal explanations are aspirational",
         "The XAI × Causal AI section described where the field is going. Our current "
         "system does not implement counterfactual explanation generation or causal "
         "graph-based reasoning. The practical takeaway from that section — 'ask whether "
         "an explanation is counterfactually testable' — is a review discipline we can "
         "adopt today without full causal infrastructure."),
    ]

    for i, (title, desc) in enumerate(gaps):
        y = 2.0 + i * 1.65
        add_rect(slide, 0.8, y, 0.08, 1.2, fill_color=AMBER)
        add_textbox(slide, 1.2, y, 11.0, 0.35, text=title,
                    font_size=18, bold=True, color=DARK_TEXT)
        add_textbox(slide, 1.2, y + 0.4, 11.3, 0.8, text=desc,
                    font_size=14, color=BLUE_STEEL, line_spacing=1.4)

    add_page_number(slide, 20)
    add_speaker_notes(slide,
        "This slide exists because internal knowledge-sharing sessions are most valuable "
        "when they're honest. Three things we should be explicit about:\n\n"
        "1. No model-internals interpretability: we've built system-level trustworthiness "
        "(guardrails, governance, monitoring) rather than model-internals interpretability "
        "(SHAP, LIME, attention visualization). This is a legitimate architectural choice "
        "— guardrails work at the system boundary rather than inside the model — but we "
        "shouldn't let anyone walk away thinking we've implemented the XAI methods from "
        "Slide Group 3. We critiqued their limitations precisely because we're operating "
        "at a different layer.\n\n"
        "2. Redaction ≠ differential privacy: we need to be precise here. Our Presidio "
        "pipeline is PII redaction/tokenization — it prevents PII from appearing in model "
        "inputs and outputs. It is not differential privacy. The distinction matters "
        "because they solve different problems and provide different levels of guarantee.\n\n"
        "3. Causal explanations are aspirational: the XAI × Causal AI section described "
        "where the field is going, not what the current system implements. The practical "
        "takeaway — 'ask whether an explanation is counterfactually testable' — is a "
        "review discipline we can adopt immediately, even without full causal infrastructure."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# CLOSING — DISCUSSION / Q&A
# ══════════════════════════════════════════════════════════════════════

def build_slide_21_discussion():
    """Slide 21: Discussion question — closing slide."""
    slide = add_blank_slide()
    add_rect(slide, 0, 0, 13.333, 7.5, fill_color=NAVY)
    add_rect(slide, 0.8, 2.4, 0.08, 2.0, fill_color=TEAL)

    add_textbox(slide, 1.3, 2.4, 11.0, 0.5, text="DISCUSSION",
                font_size=16, color=TEAL, bold=True)

    add_textbox(slide, 1.3, 2.95, 11.0, 1.2,
                text="Which of these seven characteristics\nis hardest to verify in your own\nteam's systems today — and why?",
                font_size=32, bold=True, color=WHITE, line_spacing=1.3)

    add_textbox(slide, 1.3, 4.6, 11.0, 0.7,
                text="(No wrong answers — the goal is to surface where the gaps are,\n"
                     "not to pretend every dimension is equally well-covered.)",
                font_size=15, color=RGBColor(0xAA, 0xB5, 0xC5))

    # Seven characteristics as small labels for reference
    chars = ["Valid &\nReliable", "Safe", "Secure &\nResilient",
             "Accountable &\nTransparent", "Explainable &\nInterpretable",
             "Privacy-\nEnhanced", "Fair"]
    for i, ch in enumerate(chars):
        x = 1.3 + i * 1.7
        add_rect(slide, x, 5.6, 1.5, 0.75, fill_color=RGBColor(0x2D, 0x3A, 0x55),
                 border_color=TEAL, corner_radius=0.08)
        add_textbox(slide, x + 0.1, 5.63, 1.3, 0.7, text=ch,
                    font_size=11, bold=False, color=RGBColor(0xCC, 0xD5, 0xE0),
                    alignment=PP_ALIGN.CENTER)

    add_textbox(slide, 1.3, 6.7, 11.0, 0.4,
                text="Thank you. Questions, challenges, and pushback welcome.",
                font_size=14, color=MID_GRAY)
    add_speaker_notes(slide,
        "This is the final slide and it's designed to start a conversation, not end one. "
        "KSS sessions land better with a live discussion close than a recap slide.\n\n"
        "The question: 'Which of these seven NIST characteristics is hardest to verify "
        "in your own team's systems today — and why?'\n\n"
        "This works as a discussion prompt because:\n"
        "- It's specific enough that people can give concrete answers\n"
        "- It's open-ended — there's no right answer\n"
        "- It normalizes the fact that every team has gaps somewhere\n"
        "- It surfaces where the organization might need to invest next\n\n"
        "Give people a moment to think, then open the floor. If nobody volunteers, "
        "offer your own answer first — that usually breaks the ice.\n\n"
        "The seven characteristics are listed on the slide as a reference so people "
        "don't have to remember them from the beginning of the talk."
    )
    return slide

# ══════════════════════════════════════════════════════════════════════
# BUILD ALL SLIDES
# ══════════════════════════════════════════════════════════════════════

print("Building slides...")

# Slide Group 1: Introduction (3 slides)
build_slide_01_title()          # 1
build_slide_02_agenda()         # 2
build_slide_03_definition()     # 3

# Slide Group 2: Why (2 slides)
build_slide_04_shift_in_stakes()       # 4
build_slide_05_regulatory_reality()    # 5

# Slide Group 3: Explainability ≠ Trustworthy (3 slides)
build_slide_06_xai_assumption()        # 6
build_slide_06b_llm_specific()         # 7
build_slide_07_xai_reframe()           # 8

# Slide Group 4: Core Principles (6 slides)
build_slides_group_4()                 # 9-14

# Slide Group 5: Related Terms (2 slides)
build_slide_14_concept_map()           # 15
build_slide_15_regulatory_deepdive()   # 16

# Slide Group 6: XAI + Causal AI (2 slides)
build_slide_15_xai_causal()            # 17
build_slide_17_xai_bridge()            # 18

# Slide Group 7: Resources (1 slide)
build_slide_18_resources()             # 19

# Codebase Mapping Section (4 slides)
build_slide_17_codebase_section_title()  # 20
build_slide_18_codebase_table()          # 21
build_slide_19_nist_mapping()            # 22
build_slide_20_honesty()                 # 23

# Closing (1 slide)
build_slide_21_discussion()            # 24

# ── Save ─────────────────────────────────────────────────────────────
output_path = "Trustworthy_AI_KSS.pptx"
prs.save(output_path)
print(f"Done! Saved to {output_path}")
print(f"Total slides: {len(prs.slides)}")
