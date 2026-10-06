#!/usr/bin/env python3
"""Regenerate ``questions.json`` from the Markdown session files.

The Markdown files are the **single source of truth**. Every question block has the
same shape::

    ### S2-Q4 · "Most important feature = 0.42"
    **core** · Understand → Apply · `in_class`

    **Q.** ...
    **A.** ...
    **Pitfalls.** ...

This script parses those blocks and writes ``questions.json`` so the Markdown (slides,
reading) and the CLI (``quiz.py``) always agree on IDs and content.

Usage::

    python3 build_questions.py            # validate + regenerate questions.json
    python3 build_questions.py --check    # validate only, write nothing

Stdlib only, no dependencies.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_PATH = HERE / "questions.json"

# session number, source file, human-readable session title
SESSIONS = [
    (1, "01_foundations.md", "Foundations of Responsible & Trustworthy AI"),
    (2, "02_explainable_ai.md", "Explainable AI Techniques"),
    (3, "03_causal_ai.md", "Causal AI for Deeper Trust"),
    (4, "04_integration_audit_regulation.md", "Integration, Auditing & Regulation"),
    (5, "05_internal_kss_engineers.md", "Internal KSS Track — AI for Software & AI Engineers"),
]

HEADING_RE = re.compile(r"^### (?P<id>S[1-9]-Q\d+|K\d+) · (?P<title>.+?)\s*$")
META_RE = re.compile(
    r"^\*\*(?P<tier>core|stretch)\*\*\s*·\s*(?P<bloom>[^·`]+?)\s*·\s*`(?P<type>[a-z_]+)`\s*$"
)
Q_RE = re.compile(r"^\*\*Q\.\*\*\s*(?P<rest>.*)$")
A_RE = re.compile(r"^\*\*A\.\*\*\s*(?P<rest>.*)$")
BULLET_RE = re.compile(r"^(?:[-*+]|\d+\.)\s+\S")

VALID_TYPES = {"pre_poll", "in_class", "quiz", "discussion", "essay", "hands_on"}
VALID_TIERS = {"core", "stretch"}


def unwrap(text: str) -> str:
    """Join soft-wrapped Markdown lines into paragraphs.

    Blank lines separate paragraphs; table rows and list items keep their own lines
    (an indented line continues the list item above it) so structure survives the
    round trip into JSON.
    """
    out: list[str] = []
    para: list[str] = []
    item: str | None = None
    in_fence = False

    def flush_para() -> None:
        if para:
            out.append(" ".join(para))
            para.clear()

    def flush_item() -> None:
        nonlocal item
        if item is not None:
            out.append(item)
            item = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if in_fence:
            out.append(raw.rstrip())
            if stripped.startswith("```"):
                in_fence = False
            continue
        if stripped.startswith("```"):
            flush_para()
            flush_item()
            out.append(stripped)
            in_fence = True
            continue
        if not stripped:
            flush_para()
            flush_item()
            if out and out[-1] != "":
                out.append("")
            continue
        if item is not None and raw.startswith((" ", "\t")):
            item = f"{item} {stripped}"  # continuation of the list item above
            continue
        if stripped.startswith("|"):
            flush_para()
            flush_item()
            out.append(stripped)
            continue
        if BULLET_RE.match(stripped):
            flush_para()
            flush_item()
            item = stripped
            continue
        flush_item()
        para.append(stripped)

    flush_para()
    flush_item()
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def split_pitfalls(answer: str) -> tuple[str, str]:
    """Pop ``**Pitfall.**`` / ``**Pitfalls.**`` paragraphs out of the answer text."""
    paras = [p for p in answer.split("\n\n") if p.strip()]
    pitfalls, kept = [], []
    for p in paras:
        if p.startswith("**Pitfall"):
            pitfalls.append(p)
        else:
            kept.append(p)
    return "\n\n".join(kept), "\n\n".join(pitfalls)


def parse_file(session: int, session_title: str, path: Path, errors: list[str]) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()

    # Start of every question block in this file.
    starts = [i for i, ln in enumerate(lines) if ln.startswith("### ")]
    questions: list[dict] = []

    for pos, start in enumerate(starts):
        heading = lines[start]
        m = HEADING_RE.match(heading)
        if not m:
            errors.append(f"{path.name}:{start + 1}: unrecognised heading {heading!r}")
            continue

        qid = m.group("id")
        raw_title = m.group("title")
        title = raw_title.replace("★ must-see", "").replace("◇", "").strip()
        must_see = "★ must-see" in raw_title

        # Body runs until the next heading (or EOF); drop trailing rules/blanks.
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        body = lines[start + 1 : end]
        while body and body[-1].strip() in {"", "---"}:
            body.pop()

        meta_idx = next((i for i, ln in enumerate(body) if ln.strip()), None)
        if meta_idx is None:
            errors.append(f"{path.name}:{start + 1}: {qid} has an empty body")
            continue

        meta = META_RE.match(body[meta_idx].strip())
        if not meta:
            errors.append(
                f"{path.name}:{start + 1}: {qid} has a malformed metadata line "
                f"{body[meta_idx]!r}"
            )
            continue

        tier = meta.group("tier")
        qtype = meta.group("type")
        bloom = [b.strip() for b in meta.group("bloom").split("→") if b.strip()]
        if tier not in VALID_TIERS:
            errors.append(f"{path.name}:{start + 1}: {qid} has invalid tier {tier!r}")
        if qtype not in VALID_TYPES:
            errors.append(f"{path.name}:{start + 1}: {qid} has invalid type {qtype!r}")

        content = body[meta_idx + 1 :]

        q_at = next((i for i, ln in enumerate(content) if Q_RE.match(ln)), None)
        a_at = next((i for i, ln in enumerate(content) if A_RE.match(ln)), None)
        if q_at is None or a_at is None or a_at < q_at:
            errors.append(f"{path.name}:{start + 1}: {qid} is missing a **Q.** or **A.** marker")
            continue

        preamble = unwrap("\n".join(content[:q_at]))
        q_first = Q_RE.match(content[q_at]).group("rest")
        question = unwrap("\n".join([q_first, *content[q_at + 1 : a_at]]))
        if preamble:
            question = f"{preamble}\n\n{question}"

        a_first = A_RE.match(content[a_at]).group("rest")
        raw_answer = unwrap("\n".join([a_first, *content[a_at + 1 :]]))
        answer, pitfalls = split_pitfalls(raw_answer)

        if not question or not answer:
            errors.append(f"{path.name}:{start + 1}: {qid} has an empty question or answer")

        questions.append(
            {
                "id": qid,
                "session": session,
                "session_title": session_title,
                "topic": title,
                "bloom": bloom,
                "tier": tier,
                "type": qtype,
                "must_see": must_see,
                "question": question,
                "answer": answer,
                "pitfalls": pitfalls,
            }
        )

    return questions


def build() -> tuple[dict, list[str]]:
    errors: list[str] = []
    questions: list[dict] = []

    for session, filename, title in SESSIONS:
        path = HERE / filename
        if not path.exists():
            errors.append(f"missing session file: {filename}")
            continue
        questions.extend(parse_file(session, title, path, errors))

    seen: dict[str, int] = {}
    for q in questions:
        seen[q["id"]] = seen.get(q["id"], 0) + 1
    for qid, n in seen.items():
        if n > 1:
            errors.append(f"duplicate question id: {qid} ({n} occurrences)")

    bank = {
        "module": "Responsible & Trustworthy AI — Question Bank",
        "generated_by": "build_questions.py",
        "sessions": [{"session": s, "title": t, "file": f} for s, f, t in SESSIONS],
        "count": len(questions),
        "questions": questions,
    }
    return bank, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate questions.json from Markdown.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the Markdown files only; do not write questions.json",
    )
    args = parser.parse_args()

    bank, errors = build()

    for err in errors:
        print(f"ERROR  {err}", file=sys.stderr)

    per_session: dict[int, int] = {}
    for q in bank["questions"]:
        per_session[q["session"]] = per_session.get(q["session"], 0) + 1
    for session, filename, _ in SESSIONS:
        print(f"  {filename:38s} {per_session.get(session, 0):3d} questions")
    print(f"  {'TOTAL':38s} {bank['count']:3d} questions")

    if errors:
        print(f"\n{len(errors)} problem(s) found - questions.json NOT written.", file=sys.stderr)
        return 1

    if args.check:
        print("\nOK - Markdown bank is valid (questions.json untouched).")
        return 0

    OUT_PATH.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nWrote {OUT_PATH.name} ({bank['count']} questions).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

