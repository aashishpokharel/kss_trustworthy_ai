#!/usr/bin/env python3
"""Regenerate ``questions.json`` from the Markdown session files.

The Markdown files are the **single source of truth**. Every question block has the
same shape::

    ### C2 · Three audiences, one truth ★ must-see
    **core** · Understand → Apply → Analyze · `in_class`

    **Fundamental problem:** ...                  # required
    **Phase:** development → deployment — ...     # required
    **Q.** ...
    **A.** ...
    **Pitfalls.** ...

``★ must-see`` is optional and marks the non-negotiable questions.

Two lines are **required** on every question in the core set (session 0, see
``REQUIRED_META_SESSIONS``) — they are the two tests a question has to pass to belong in the bank.
Session drills restored from the archive (v1) predate this schema, so they are not forced through it;
if they do carry a ``**Phase:**`` line it is validated the same way.

``**Fundamental problem:**``
    The durable problem the question answers — a question that outlives the tooling. Answers are
    marked against this, not against a checklist of topics.

``**Phase:**``
    The lifecycle phase(s) the question lands in: ``development``, ``deployment`` or ``serving``
    (end-user serving), joined with ``→`` / ``·`` / ``+`` / ``,``, then ``—`` and a clause saying
    which part of the question sits in which phase. A question may name **more than one** phase:
    the phases are a relation, not a slot — this bank is deliberately not one question per phase.

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

# session number, source file, human-readable session title.
# Session 0 is the whole-course core set: one question per domain (C1-C4).
SESSIONS = [
    (0, "00_core_questions.md", "Whole-Course Core Set — four questions, one per domain"),
]

# C1-C4 = whole-course core set; S{n}-Q{m} = per-session drills; K{n} = internal KSS track.
HEADING_RE = re.compile(r"^### (?P<id>C\d+|S[1-9]-Q\d+|K\d+) · (?P<title>.+?)\s*$")
META_RE = re.compile(
    r"^\*\*(?P<tier>core|stretch)\*\*\s*·\s*(?P<bloom>[^·`]+?)\s*·\s*`(?P<type>[a-z_]+)`\s*$"
)
Q_RE = re.compile(r"^\*\*Q\.\*\*\s*(?P<rest>.*)$")
A_RE = re.compile(r"^\*\*A\.\*\*\s*(?P<rest>.*)$")
BULLET_RE = re.compile(r"^(?:[-*+]|\d+\.)\s+\S")

# Required per question: the fundamental problem it answers and the lifecycle phase(s) it lands in.
PROBLEM_RE = re.compile(r"^\*\*(?:Fundamental problem|Problem):\*\*\s*(?P<value>\S.*?)\s*$")
PHASE_RE = re.compile(r"^\*\*Phase[s]?:\*\*\s*(?P<value>\S.*?)\s*$")
PHASE_SPLIT_RE = re.compile(r"\s*(?:→|->|·|\+|,|/)\s*")
PHASE_DASH = "—"

VALID_TYPES = {"pre_poll", "in_class", "quiz", "discussion", "essay", "hands_on"}
VALID_TIERS = {"core", "stretch"}
# Lifecycle phases. A question may name several: the phases are a relation, not a slot.
VALID_PHASES = ("development", "deployment", "serving")
# The two required statements apply to the whole-course core set (session 0). Session drills restored
# from the archive (v1) predate this schema, so they are not forced through it.
REQUIRED_META_SESSIONS = {0}
# Accepted spellings for a phase token → canonical name.
PHASE_ALIASES = {
    "development": "development",
    "dev": "development",
    "deployment": "deployment",
    "dep": "deployment",
    "serving": "serving",
    "end-user serving": "serving",
    "end user serving": "serving",
    "end-user-serving": "serving",
}


def canonical_phase(token: str) -> str | None:
    """Map a phase token (``end-user serving``, ``dep``, ``serving``) to its canonical name."""
    key = re.sub(r"\s+", " ", token.strip().lower().rstrip(".:;"))
    return PHASE_ALIASES.get(key)


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

    # Question blocks start with `### <id> · <title>`. Other headings (`##` sections, documentation
    # sub-headings) are not block starts, and a block never runs past the next heading of any level.
    starts: list[int] = []
    for i, ln in enumerate(lines):
        if not ln.startswith("### "):
            continue
        if HEADING_RE.match(ln):
            starts.append(i)
        elif " · " in ln:
            errors.append(f"{path.name}:{i + 1}: unrecognised question heading {ln!r}")

    questions: list[dict] = []

    for pos, start in enumerate(starts):
        heading = lines[start]
        m = HEADING_RE.match(heading)
        if not m:  # pragma: no cover - guarded when `starts` was built
            errors.append(f"{path.name}:{start + 1}: unrecognised heading {heading!r}")
            continue

        qid = m.group("id")
        raw_title = m.group("title")
        title = raw_title.replace("★ must-see", "").replace("◇", "").strip()
        must_see = "★ must-see" in raw_title

        # Body runs until the next heading of any level (or EOF); drop trailing rules/blanks.
        end = len(lines)
        for j in range(start + 1, len(lines)):
            if lines[j].startswith("## ") or lines[j].startswith("### "):
                end = j
                break
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

        # The two required statements: the fundamental problem and the lifecycle phase(s).
        required = session in REQUIRED_META_SESSIONS
        problem = ""
        phases: list[str] = []
        phase_note = ""
        for ln in content[:q_at]:
            stripped = ln.strip()
            m_problem = PROBLEM_RE.match(stripped)
            if m_problem:
                problem = m_problem.group("value")
            m_phase = PHASE_RE.match(stripped)
            if m_phase:
                head, _, note = m_phase.group("value").partition(PHASE_DASH)
                phases = [p for p in PHASE_SPLIT_RE.split(head.strip()) if p]
                phase_note = note.strip()

        if required:
            if not problem:
                errors.append(
                    f"{path.name}:{start + 1}: {qid} is missing a **Fundamental problem:** line"
                )
            elif len(problem.split()) < 4:
                errors.append(
                    f"{path.name}:{start + 1}: {qid} has a placeholder **Fundamental problem:** "
                    f"line ({problem!r})"
                )

        if not phases:
            if required:
                errors.append(f"{path.name}:{start + 1}: {qid} is missing a **Phase:** line")
        else:
            unknown = [p for p in phases if canonical_phase(p) is None]
            if unknown:
                errors.append(
                    f"{path.name}:{start + 1}: {qid} has unknown phase(s) "
                    f"{', '.join(repr(p) for p in unknown)} - expected one or more of "
                    f"{', '.join(VALID_PHASES)}"
                )
            phases = list(
                dict.fromkeys(c for c in (canonical_phase(p) for p in phases) if c)
            )
            if required and not phase_note:
                errors.append(
                    f"{path.name}:{start + 1}: {qid} **Phase:** needs a clause after "
                    f"{PHASE_DASH!r} saying which part of the question sits in which phase"
                )

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
                "problem": problem,
                "phases": phases,
                "phase_note": phase_note,
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
        "phases": list(VALID_PHASES),
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

    if not errors:
        stated = sum(1 for q in bank["questions"] if q["problem"])
        print()
        print("  Fundamental problems stated (one per question):")
        print(f"    {'with a **Fundamental problem:** line':36s} {stated:3d}/{bank['count']}")
        print("  Lifecycle phases (a question can land in more than one):")
        for phase in VALID_PHASES:
            n = sum(1 for q in bank["questions"] if phase in q["phases"])
            print(f"    {phase:36s} {n:3d} questions")

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

