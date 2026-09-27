#!/usr/bin/env python3
"""Drill the "Responsible & Trustworthy AI" question bank from the terminal.

Reads ``questions.json`` (regenerate it with ``python3 build_questions.py``).
Stdlib only, no dependencies.

    python3 quiz.py --list
    python3 quiz.py --session 2
    python3 quiz.py --type pre_poll
    python3 quiz.py --tier stretch
    python3 quiz.py --random 5
    python3 quiz.py --id S3-Q2
    python3 quiz.py --stats
"""

from __future__ import annotations

import argparse
import json
import random
import re
import shutil
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANK_PATH = HERE / "questions.json"

TYPES = ("pre_poll", "in_class", "quiz", "discussion", "essay", "hands_on")
TIERS = ("core", "stretch")
BULLET_RE = re.compile(r"^(?:[-*+]|\d+\.)\s+\S")


def load_bank(path: Path = BANK_PATH) -> dict:
    if not path.exists():
        sys.exit(f"{path.name} not found - generate it first: python3 build_questions.py")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def term_width() -> int:
    return max(40, min(100, shutil.get_terminal_size((100, 24)).columns))


def session_title(bank: dict, number: int) -> str:
    for entry in bank["sessions"]:
        if entry["session"] == number:
            return entry["title"]
    return f"Session {number}"


def rule(char: str = "-") -> None:
    print(char * term_width())


def print_block(text: str, indent: str = "") -> None:
    """Print Markdown-ish text, wrapping prose but leaving tables/lists intact."""
    width = term_width() - len(indent)
    for para in text.split("\n\n"):
        lines = [ln.strip() for ln in para.splitlines() if ln.strip()]
        if not lines:
            continue
        if any(ln.startswith("|") for ln in lines):
            for ln in lines:
                print(indent + ln)
        elif len(lines) > 1 and any(BULLET_RE.match(ln) for ln in lines):
            for ln in lines:
                if BULLET_RE.match(ln):
                    print(
                        textwrap.fill(
                            ln,
                            width=term_width(),
                            initial_indent=indent,
                            subsequent_indent=indent + "   ",
                        )
                    )
                else:
                    print(
                        textwrap.fill(
                            ln,
                            width=term_width(),
                            initial_indent=indent + "  ",
                            subsequent_indent=indent + "  ",
                        )
                    )
        else:
            joined = " ".join(lines)
            print(
                textwrap.fill(
                    joined,
                    width=term_width(),
                    initial_indent=indent,
                    subsequent_indent=indent,
                )
            )
        print()


def print_question(q: dict, *, show_answer: bool) -> None:
    tags = [q["tier"], " → ".join(q["bloom"]), q["type"]]
    if q["must_see"]:
        tags.append("★ must-see")
    print(f"{q['id']} · {q['topic']}")
    print(f"  {q['session_title']}  [{q['session']}]")
    print(f"  {' · '.join(tags)}")
    print()
    print_block(q["question"], indent="  ")
    if show_answer:
        print("  ANSWER")
        print_block(q["answer"], indent="  ")
        if q["pitfalls"]:
            print("  PITFALLS")
            print_block(q["pitfalls"], indent="  ")
    rule()


def select(bank: dict, args: argparse.Namespace) -> list[dict]:
    rows = bank["questions"]
    if args.session is not None:
        rows = [q for q in rows if q["session"] == args.session]
    if args.qtype:
        rows = [q for q in rows if q["type"] == args.qtype]
    if args.tier:
        rows = [q for q in rows if q["tier"] == args.tier]
    if args.must_see:
        rows = [q for q in rows if q["must_see"]]
    return rows


def cmd_list(rows: list[dict]) -> None:
    if not rows:
        print("No questions match those filters.")
        return
    id_w = max(len("ID"), max(len(q["id"]) for q in rows))
    tier_w = max(len("TIER"), max(len(q["tier"]) for q in rows))
    type_w = max(len("TYPE"), max(len(q["type"]) for q in rows))
    room = term_width() - (id_w + tier_w + type_w + 9)
    print(f"{'ID':<{id_w}}  {'TIER':<{tier_w}}  {'TYPE':<{type_w}}  S  TOPIC")
    print("-" * term_width())
    for q in rows:
        topic = q["topic"]
        if room > 12 and len(topic) > room:
            topic = topic[: room - 2].rstrip(" ,;:") + " …"
        star = "*" if q["must_see"] else " "
        print(
            f"{q['id']:<{id_w}}  {q['tier']:<{tier_w}}  {q['type']:<{type_w}}  "
            f"{q['session']}  {star}{topic}"
        )
    print("-" * term_width())
    print(f"{len(rows)} question(s).  * = must-see.  Walk them with: python3 quiz.py --session 2")


def cmd_stats(bank: dict) -> None:
    qs = bank["questions"]
    print(bank["module"])
    print(f"{bank['count']} questions total")
    print()

    def tally(values, label: str) -> None:
        counts: dict[str, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        print(label)
        for key, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {key:<38} {count:3d}")
        print()

    tally(
        (f"Session {q['session']} - {q['session_title']}" for q in qs),
        "By session",
    )
    tally((q["type"] for q in qs), "By question type")
    tally((q["tier"] for q in qs), "By tier")
    tally((level for q in qs for level in q["bloom"]), "By Bloom level")
    print("Extras")
    print(f"  {'must-see (usable cold)':<38} {sum(1 for q in qs if q['must_see']):3d}")
    print(f"  {'with pitfalls block':<38} {sum(1 for q in qs if q['pitfalls']):3d}")


def cmd_random(rows: list[dict], count: int, seed: int | None) -> None:
    if not rows:
        print("No questions match those filters.")
        return
    if count <= 0:
        print("--random needs a positive number, e.g. --random 5")
        return
    picks = random.Random(seed).sample(rows, min(count, len(rows)))
    for index, q in enumerate(picks, 1):
        print(f"[{index}/{len(picks)}] {q['id']} · {q['topic']}")
        tags = [q["tier"], " → ".join(q["bloom"]), q["type"]]
        if q["must_see"]:
            tags.append("★ must-see")
        print(f"  {' · '.join(tags)}  (session {q['session']})")
        print_block(q["question"], indent="  ")
        rule()
    print("Answers hidden. Reveal one with:  python3 quiz.py --id " + picks[0]["id"])


def cmd_walk(rows: list[dict], *, no_pause: bool) -> None:
    if not rows:
        print("No questions match those filters.")
        return
    print(f"Walking {len(rows)} question(s). Enter reveals the answer, 'q' quits.\n")
    for index, q in enumerate(rows, 1):
        print(f"[{index}/{len(rows)}]")
        print_question(q, show_answer=False)
        if not pause("  ... Enter to reveal the answer (q to quit) ", not no_pause):
            print("Stopped.")
            return
        print("  ANSWER")
        print_block(q["answer"], indent="  ")
        if q["pitfalls"]:
            print("  PITFALLS")
            print_block(q["pitfalls"], indent="  ")
        if index < len(rows) and not pause(
            "  ... Enter for the next question (q to quit) ", not no_pause
        ):
            print("Stopped.")
            return


def pause(prompt: str, enabled: bool) -> bool:
    """Wait for Enter. Returns False if the user wants to stop."""
    if not enabled or not sys.stdin.isatty():
        return True
    try:
        typed = input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if typed.strip().lower() in {"q", "quit"}:
        return False
    print()
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quiz.py",
        description="Drill the Responsible & Trustworthy AI question bank.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python3 quiz.py --list\n"
            "  python3 quiz.py --session 2\n"
            "  python3 quiz.py --type pre_poll\n"
            "  python3 quiz.py --tier stretch --session 3\n"
            "  python3 quiz.py --random 5 --seed 7\n"
            "  python3 quiz.py --must-see --list\n"
            "  python3 quiz.py --id S3-Q2\n"
            "  python3 quiz.py --stats\n"
        ),
    )
    parser.add_argument("--session", type=int, metavar="N", help="filter by session number (5 = KSS track)")
    parser.add_argument("--type", dest="qtype", choices=TYPES, help="filter by question type")
    parser.add_argument("--tier", choices=TIERS, help="filter by tier")
    parser.add_argument("--must-see", action="store_true", help="only the * must-see questions")
    parser.add_argument("--list", action="store_true", help="print a table of matching questions")
    parser.add_argument("--stats", action="store_true", help="counts per session / type / tier / Bloom")
    parser.add_argument("--id", metavar="ID", help="print a single question with its answer")
    parser.add_argument("--random", type=int, metavar="N", help="show N random questions, answers hidden")
    parser.add_argument("--seed", type=int, help="seed for --random, for repeatable drills")
    parser.add_argument("--no-pause", action="store_true", help="do not wait for Enter between Q and A")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None and len(sys.argv) == 1:
        parser.print_help()
        print("\nStart with:  python3 quiz.py --stats")
        return 0
    args = parser.parse_args(argv)
    bank = load_bank()

    if args.id:
        wanted = args.id.strip().lower()
        match = next((q for q in bank["questions"] if q["id"].lower() == wanted), None)
        if match is None:
            print(f"No question with id {args.id!r}.", file=sys.stderr)
            print("Available: " + ", ".join(q["id"] for q in bank["questions"]), file=sys.stderr)
            return 1
        print_question(match, show_answer=True)
        return 0

    if args.stats:
        cmd_stats(bank)
        return 0

    rows = select(bank, args)

    if args.list:
        cmd_list(rows)
        return 0

    if args.random is not None:
        cmd_random(rows, args.random, args.seed)
        return 0

    if not rows:
        print("No questions match those filters.")
        return 1

    cmd_walk(rows, no_pause=args.no_pause)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


