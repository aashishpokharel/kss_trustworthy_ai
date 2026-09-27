# Archive — full question bank v1 (frozen 2026-09-27)

**Status: frozen snapshot. Do not edit these files.** They are kept only so the wide
version of the question bank can be revisited. The live course lives one level up.

This is the first, *wide* version of the "Responsible & Trustworthy AI" question bank
(71 questions spread across four sessions plus an internal KSS engineer track), kept
intact at the point where the course was narrowed to a small whole-course question set.

## What's in here

| File | Contents |
|---|---|
| `01_foundations.md` | Session 1 — Foundations: `S1-Q1` … `S1-Q14` (14 questions) |
| `02_explainable_ai.md` | Session 2 — Explainable AI: `S2-Q1` … `S2-Q15` (15 questions) |
| `03_causal_ai.md` | Session 3 — Causal AI: `S3-Q1` … `S3-Q13` (13 questions) |
| `04_integration_audit_regulation.md` | Session 4 — Integration / Auditing / Regulation: `S4-Q1` … `S4-Q13` (13 questions) |
| `05_internal_kss_engineers.md` | Internal KSS track: `K1` … `K16` (16 questions) |
| `README_bank_v1.md` | The README as it read for this version |
| `questions.json` | Generated machine-readable bank (71 entries, same IDs) |
| `build_questions.py` | Markdown → `questions.json` generator + validator |
| `quiz.py` | Terminal drill CLI |

## Totals

**71 questions** — Session 1 = 14, Session 2 = 15, Session 3 = 13, Session 4 = 13,
KSS track = 16. Every question carries `tier` (core/stretch), `type`
(pre_poll/in_class/quiz/discussion/essay/hands_on), a Bloom progression, a full answer,
and — where useful — a **Pitfalls** paragraph.

## How to revisit this version

Both scripts are **self-contained**: `quiz.py` reads the `questions.json` sitting next to
it, and `build_questions.py` reads the sibling Markdown files. So this folder keeps
working even after the top-level course files change.

```bash
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --stats
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --list
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --session 2
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --type pre_poll
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --tier stretch
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --random 5 --seed 7
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --id S3-Q2

# re-validate the Markdown without rewriting anything
python3 archive/2026-09-27_full_question_bank_v1/build_questions.py --check
```

## Second copy in git

The same content is committed on branch `fusemachines-fellowship` (no push), so it is
also recoverable without this folder, e.g.:

```bash
git show HEAD:5_responsible_trustworthy_ai/archive/2026-09-27_full_question_bank_v1/03_causal_ai.md
git log --oneline -- 5_responsible_trustworthy_ai
```
