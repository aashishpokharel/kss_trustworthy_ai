#!/usr/bin/env python3
"""Render the Learning Resources Markdown to a PDF.

The Markdown file is the single source of truth::

    Responsible_and_Trustworthy_AI_Learning_Resources.md

This script turns it into a printable PDF that mirrors the layout of
``Template_Learning_Resources.pdf`` (title, section headings, bullet lists and
a monospaced repository map).

It uses only ``reportlab`` (a build-time dependency, not a runtime one) with the
built-in Helvetica / Courier fonts, so it needs no system fonts and no other
packages::

    python3 learning_resources/build_pdf.py

Two glyph families are transliterated because they are not part of the base
PDF font encoding:

* arrows  ``->``  (for the Unicode right-arrow)
* the box-drawing characters used in the repository map (``+--`` / ``|``)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)

HERE = Path(__file__).resolve().parent
MD_PATH = HERE / "Responsible_and_Trustworthy_AI_Learning_Resources.md"
PDF_PATH = HERE / "Responsible_and_Trustworthy_AI_Learning_Resources.pdf"

NAVY = colors.HexColor("#10243f")
SLATE = colors.HexColor("#33475b")
RULE = colors.HexColor("#c7d2de")
CODE_BG = colors.HexColor("#f4f6f9")

# Bullet glyphs for nesting levels 0 (topic), 1 (subtopic), 2 (sub-subtopic).
BULLETS = ("\u2022", "\u2013", "\u00b7")

# ---------------------------------------------------------------------------
# Text normalisation (make the Markdown safe for the base PDF fonts)
# ---------------------------------------------------------------------------

_ARROWS = {
    "\u2192": "->",
    "\u2190": "<-",
    "\u2194": "<->",
}


def _latin1_safe(text: str) -> str:
    """Replace characters that are not representable in the base PDF fonts."""
    for src, dst in _ARROWS.items():
        text = text.replace(src, dst)
    out = []
    for ch in text:
        try:
            ch.encode("cp1252")
            out.append(ch)
        except UnicodeEncodeError:
            out.append("?")
    return "".join(out)


_BOX = [
    ("\u251c\u2500\u2500", "|--"),
    ("\u2514\u2500\u2500", "`--"),
    ("\u2500", "-"),
    ("\u2502", "|"),
    ("\u251c", "|"),
    ("\u2514", "`"),
]


def _demux_box_drawing(text: str) -> str:
    for src, dst in _BOX:
        text = text.replace(src, dst)
    return text


# ---------------------------------------------------------------------------
# Inline Markdown -> ReportLab markup
# ---------------------------------------------------------------------------

def inline(text: str) -> str:
    text = text.replace("&nbsp;", "\u00a0").replace("\u00a0", " ")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)
    return _latin1_safe(text)



# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

def build_styles():
    ss = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "h1", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=19,
            leading=23, textColor=NAVY, alignment=0, spaceAfter=2,
        ),
        "h2": ParagraphStyle(
            "h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=13.5,
            leading=17, textColor=NAVY, spaceBefore=14, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "h3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=11,
            leading=14, textColor=SLATE, spaceBefore=8, spaceAfter=3,
        ),
        "h4": ParagraphStyle(
            "h4", parent=ss["Heading4"], fontName="Helvetica-Bold", fontSize=10,
            leading=13, textColor=SLATE, spaceBefore=6, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=colors.HexColor("#1c1c1c"),
            alignment=TA_JUSTIFY, spaceAfter=6,
        ),
        "bullet1": ParagraphStyle(
            "bullet1", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=colors.HexColor("#1c1c1c"),
            leftIndent=14, bulletIndent=3, spaceAfter=3,
        ),
        "bullet2": ParagraphStyle(
            "bullet2", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=colors.HexColor("#1c1c1c"),
            leftIndent=26, bulletIndent=15, spaceAfter=2,
        ),
        "bullet3": ParagraphStyle(
            "bullet3", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=colors.HexColor("#1c1c1c"),
            leftIndent=38, bulletIndent=27, spaceAfter=2,
        ),
        "number": ParagraphStyle(
            "number", parent=ss["BodyText"], fontName="Helvetica", fontSize=9.5,
            leading=13.5, textColor=colors.HexColor("#1c1c1c"),
            leftIndent=18, bulletIndent=3, spaceAfter=3,
        ),
        "quote": ParagraphStyle(
            "quote", parent=ss["BodyText"], fontName="Helvetica-Oblique",
            fontSize=9.5, leading=13.5, textColor=SLATE,
            leftIndent=12, rightIndent=8, spaceBefore=2, spaceAfter=6,
        ),
        "code": ParagraphStyle(
            "code", parent=ss["Code"], fontName="Courier", fontSize=7.8,
            leading=10.2, textColor=colors.HexColor("#12263a"),
        ),
        "cell": ParagraphStyle(
            "cell", parent=ss["BodyText"], fontName="Helvetica", fontSize=8.2,
            leading=10.5, textColor=colors.HexColor("#1c1c1c"), spaceAfter=0,
        ),
        "cellh": ParagraphStyle(
            "cellh", parent=ss["BodyText"], fontName="Helvetica-Bold", fontSize=8.2,
            leading=10.5, textColor=colors.white, spaceAfter=0,
        ),
    }


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def add_code(styles, buf, flow):
    code = _latin1_safe(_demux_box_drawing("\n".join(buf)))
    pre = Preformatted(code, styles["code"])
    table = Table([[pre]], colWidths=[17.4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("BOX", (0, 0), (-1, -1), 0.4, RULE),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    flow.append(table)
    flow.append(Spacer(1, 6))


def _col_widths(cells, avail):
    """Proportional column widths that never split a single word."""
    ncol = len(cells[0])
    per_char = 8.2 * 0.5
    pad = 12.0
    natural, minimum = [], []
    for j in range(ncol):
        colvals = [_latin1_safe(r[j]) for r in cells]
        longest_cell = max((len(c) for c in colvals), default=1)
        longest_word = max(
            (max((len(w) for w in c.split()), default=1) for c in colvals), default=1
        )
        natural.append(min(longest_cell, 46) * per_char + pad)
        minimum.append(longest_word * per_char + pad)
    total = sum(natural) or 1.0
    if total <= avail:
        extra = avail - total
        natural = [w + extra * (w / total) for w in natural]
    else:
        scale = avail / total
        natural = [max(minimum[j], w * scale) for j, w in enumerate(natural)]
        total2 = sum(natural)
        if total2 > avail:
            room = [w - minimum[j] for j, w in enumerate(natural)]
            room_sum = sum(room)
            if room_sum > 0:
                over = total2 - avail
                natural = [
                    w - min(room[j], over * room[j] / room_sum)
                    for j, w in enumerate(natural)
                ]
    return natural


def add_table(styles, rows, flow):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(set(c) <= set("-: ") and c for c in r)]
    if not cells:
        return
    ncol = max(len(r) for r in cells)
    cells = [r + [""] * (ncol - len(r)) for r in cells]

    widths = _col_widths(cells, 17.4 * cm)

    data = []
    for i, r in enumerate(cells):
        style = styles["cellh"] if i == 0 else styles["cell"]
        data.append([Paragraph(inline(c), style) for c in r])

    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef2f7")]),
        ("GRID", (0, 0), (-1, -1), 0.3, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 8))


def markdown_to_flowables(text, styles):
    flow = []
    lines = text.split("\n")
    i = 0
    n = len(lines)
    num_re = re.compile(r"^\d+\.\s+")

    def is_block_start(s):
        return (
            not s
            or s == "---"
            or s.startswith("#")
            or s.startswith("|")
            or s.startswith(">")
            or s.startswith("```")
            or s.startswith("- ")
            or bool(num_re.match(s))
        )

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            flow.append(Spacer(1, 4))
            flow.append(HRFlowable(width="100%", thickness=0.6, color=RULE))
            flow.append(Spacer(1, 6))
            i += 1
            continue

        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            add_code(styles, buf, flow)
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            title = stripped[level:].strip()
            style = {1: styles["h1"], 2: styles["h2"], 3: styles["h3"]}.get(level, styles["h4"])
            flow.append(Paragraph(inline(title), style))
            if level == 2:
                flow.append(Spacer(1, 1))
                flow.append(HRFlowable(width="100%", thickness=0.5, color=RULE))
            i += 1
            continue

        if stripped.startswith("|"):
            buf = []
            while i < n and lines[i].strip().startswith("|"):
                buf.append(lines[i].strip())
                i += 1
            add_table(styles, buf, flow)
            continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            flow.append(Paragraph(inline(" ".join(buf)), styles["quote"]))
            continue

        if num_re.match(stripped):
            m = num_re.match(stripped)
            flow.append(Paragraph(
                inline(stripped[m.end():]), styles["number"], bulletText=m.group().strip(),
            ))
            i += 1
            continue

        m_bullet = re.match(r"^(\s*)- (.*)$", line)
        if m_bullet:
            level = min(len(m_bullet.group(1)) // 2, 2)
            flow.append(Paragraph(
                inline(m_bullet.group(2)),
                styles["bullet%d" % (level + 1)],
                bulletText=BULLETS[level],
            ))
            i += 1
            continue

        buf = [stripped]
        i += 1
        while i < n and not is_block_start(lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        flow.append(Paragraph(inline(" ".join(buf)), styles["body"]))

    return flow



# ---------------------------------------------------------------------------
# Page decoration
# ---------------------------------------------------------------------------

def decorate(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(1.8 * cm, A4[1] - 1.35 * cm, A4[0] - 1.8 * cm, A4[1] - 1.35 * cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(SLATE)
    canvas.drawString(
        1.8 * cm, A4[1] - 1.15 * cm,
        "Responsible & Trustworthy AI - Learning Resources",
    )
    canvas.drawRightString(
        A4[0] - 1.8 * cm, A4[1] - 1.15 * cm,
        "KSS x Fusemachines Fellowship",
    )
    canvas.setFont("Helvetica", 7.5)
    canvas.drawCentredString(A4[0] / 2, 1.0 * cm, "Page %d" % doc.page)
    canvas.restoreState()


def build():
    if not MD_PATH.exists():
        sys.exit("missing source markdown: %s" % MD_PATH)
    text = MD_PATH.read_text(encoding="utf-8")
    styles = build_styles()
    story = markdown_to_flowables(text, styles)

    doc = BaseDocTemplate(
        str(PDF_PATH), pagesize=A4,
        leftMargin=1.8 * cm, rightMargin=1.8 * cm,
        topMargin=1.7 * cm, bottomMargin=1.4 * cm,
        title="Responsible & Trustworthy AI - Learning Resources",
        author="KSS x Fusemachines Fellowship",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="body")
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=decorate)])
    doc.build(story)
    print("Wrote %s" % PDF_PATH)


if __name__ == "__main__":
    build()

