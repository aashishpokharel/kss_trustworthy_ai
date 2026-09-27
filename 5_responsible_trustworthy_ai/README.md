# Module 5 — Responsible & Trustworthy AI (Question Bank)

Student-facing question set for the **KSS × Fusemachines Fellowship** module
*Responsible and Trustworthy AI* — with focus on **Explainable AI (XAI)**, **Causal AI**,
and the surrounding principles of **fairness, transparency, robustness, privacy and accountability**.

**Facilitators:** Sujan Sharma / Aashish Pokharel
**Reference book:** *Trustworthy AI*

---

## Why this folder exists

The fellowship runs on a **small set of whole-course questions** — not a hidden end-of-course exam and
not a long drill list. This folder holds exactly **four questions, one per domain**, and every one of
them is answered and discussed inside the session.

The design rule is simple: **each of the four is a whole-course synthesis question** — anchored in
its own domain, and *not* answerable inside it. A strong answer reaches into the other three domains.
`C4` is additionally the **capstone**: it assumes the artifacts produced in `C1`–`C3`.

## The four questions

| ID | Question | Anchored in | Also requires | Use it as | Time |
|---|---|---|---|---|---|
| `C1` | **Deconstruct the trustworthiness pitch** | Session 1 — Foundations | S2 (explanations) · S3 (causal reading) · S4 (EU AI Act / RMF) | cold opener / plenary | 15–20 min |
| `C2` | **Three audiences, one truth** | Session 2 — Explainable AI | S1 (rights & transparency) · S3 (causal reading) · S4 (logging & audit trail) | in-class writing + plenary | 20–25 min |
| `C3` | **The 2.9% trap** | Session 3 — Causal AI | S1 (validity & measurement) · S2 (explanation misuse) · S4 (decision gates & monitoring) | in-class or take-home | 25–30 min |
| `C4` | **The 90-minute pre-deployment review** | Session 4 — Integration, Auditing & Regulation | S1–S3 (all of the above) | workshop / assessment | 30–45 min |

All four are ★ **must-see**. Full text, model answers, per-question rubrics, pitfalls and discussion
prompts live in **[`00_core_questions.md`](00_core_questions.md)**.

## The running case

All four questions work on **one case**, so students walk a whole lifecycle instead of four
disconnected exercises: **Northline Bank — "CreditBoost"**, a nightly model that raises customers'
credit limits automatically (≈40,000/month) plus an **LLM layer that writes the customer letters**,
deployed in the EU and UK, and carrying an unexplained **1.7× refusal disparity**, a flawed pilot, two
incidents in a quarter, and no post-market monitoring plan.

Hand out that case section at the start of the course
([`#the-running-case`](00_core_questions.md#the-running-case)) and let each session add its own lens.
The pitch students have to attack: *"94% of predictions were correct, we publish a model card, every
decision is logged, and we passed the EU AI Act conformity assessment — so CreditBoost is
trustworthy."*

## What's in this folder

| File | Contents |
|---|---|
| [`00_core_questions.md`](00_core_questions.md) | **The question set** — the running case + `C1`–`C4` with model answers, rubrics, pitfalls, discussion prompts |
| [`questions.json`](questions.json) | Machine-readable bank (same IDs) — **generated, do not edit by hand** |
| [`build_questions.py`](build_questions.py) | Regenerates `questions.json` from the Markdown |
| [`quiz.py`](quiz.py) | Dependency-free CLI to drill the set |
| [`archive/2026-09-27_full_question_bank_v1/`](archive/2026-09-27_full_question_bank_v1/MANIFEST.md) | The earlier **71-question** per-session bank (v1) — frozen, self-contained, still runnable |

## Session map — where each question plugs into the course

| Session | Focus | Question | Wider drills, if you want them (archive v1) |
|---|---|---|---|
| **1** | Foundations: principles, NIST AI RMF, EU AI Act | `C1` | `S1-Q1` … `S1-Q14` |
| **2** | Explainable AI: SHAP / LIME / counterfactuals, explanation quality | `C2` | `S2-Q1` … `S2-Q15` |
| **3** | Causal AI: DAGs, interventions, counterfactuals | `C3` | `S3-Q1` … `S3-Q13` |
| **4** | Integration, auditing & regulation | `C4` | `S4-Q1` … `S4-Q13` |
| — | Internal KSS track (AI / software engineers) | not in the core set | `K1` … `K16` |

Session 3 stays the *optional* session: if causation was already covered in an earlier class, run
`C3` as a short reading and keep the artifacts for `C4`.

---

## How to use these questions

The module is built around **"Try First, Understand Later"** and **low floor / high ceiling / wide
walls** — the set keeps that spirit: `C1` can be attempted cold, before any vocabulary, and still
produce useful disagreement in the room.

| Type | When | Behaviour |
|---|---|---|
| `in_class` | During the plenary (`C1`–`C3`) | Answered together; the facilitator reveals the reasoning, not just the answer. |
| `hands_on` | Workshop / project work (`C4`) | Artifacts are produced in the room and carried into the review. |

The bank vocabulary also allows `pre_poll`, `quiz`, `discussion` and `essay`, and
`build_questions.py` validates against that list — so a new question can be tagged any of them.

### Tiers

- **`core`** — *all learners will be able to…* → `C1`–`C3`
- **`stretch`** — *some learners will be able to…* → `C4`, the synthesis

### Three ways to run the set

| Format | Sequence | Notes |
|---|---|---|
| **Half-day workshop** | `C1` → `C2` → `C3` → `C4`, artifacts pinned to the wall as you go | Assign roles in `C4` (model owner, risk officer, auditor, customer advocate) and play the adversarial reviewer yourself |
| **Across the course** | One question at the end of each domain session; `C4` closes | Keep a shared folder of artifacts — the carry-forward is the point |
| **Assessment** | `C1`–`C3` written, then `C4` as a 45-minute oral defence of the pack | Mark with the per-question rubrics; the "Synthesis" row separates good from excellent |

### The whole-course checklist (what a full-mark answer keeps doing)

1. Separate **what the evidence shows** from **what the sentence claims** (`C1`).
2. Name the **audience** before writing the explanation (`C2`).
3. Ask **which rung** the question is on before choosing a method (`C3`).
4. Give every metric a **threshold, an owner and an action** (`C4`).
5. Never let compliance stand in for trustworthiness, attribution for causation, or a **report** for
   **remediation**.

## Coverage matrix — learning objectives → questions

| Learning objective (Bloom) | Question | Where it is exercised |
|---|---|---|
| Apply the trustworthiness properties to a real claim; classify under the EU AI Act; use the NIST AI RMF (Understand/Apply) | `C1` | clause-by-clause evidence table · Annex III 5(b) · the GOVERN gap |
| Produce audience-appropriate explanations; state the limits of attribution (Apply/Analyze) | `C2` | three-audience table · SHAP-vs-causal traps |
| Specify, guardrail and evaluate a generative explanation layer (Apply/Evaluate) | `C2` (+`C1`) | grounded generation · tone clamp · golden set |
| Move between association, intervention and counterfactual; build a DAG; write an estimand (Understand/Analyze) | `C3` | the ladder table · the pilot DAG · ITT vs TOT |
| Design an identification strategy and judge when causal precision is worth its cost (Evaluate/Create) | `C3` | randomised holdout with application · RD at the existing cutoff |
| Critique a system against NIST AI RMF / EU AI Act and assemble an evidence pack (Evaluate/Create) | `C4` | RMF mapping · Art. 9–15 / 27 / 72–73 / 86 pack |
| Design post-market monitoring and incident response (Apply/Evaluate) | `C4` | one-page monitoring table · P1/P2 with the 72-hour clock |
| Discuss ethics and accountability; defend a go / no-go decision (Evaluate) | `C4` | conditions with owners and dates · residual-risk acceptance · decommissioning triggers |

---

## Question bank format

Questions live in Markdown (for slides and reading) **and** in `questions.json` (for tooling). Both use
the same IDs, and the **Markdown is the source of truth**.

```json
{
  "id": "C3",
  "session": 0,
  "session_title": "Whole-Course Core Set — four questions, one per domain",
  "topic": "The 2.9% trap",
  "bloom": ["Understand", "Analyze", "Evaluate", "Create"],
  "tier": "core",
  "type": "in_class",
  "must_see": true,
  "question": "…",
  "answer": "…",
  "pitfalls": "…"
}
```

`tier` ∈ `core | stretch` · `type` ∈ `pre_poll | in_class | quiz | discussion | essay | hands_on`
· `session` is `0` for the whole-course set · `question`, `answer`, `pitfalls` keep their Markdown
(tables, bullet lists and fenced DAG blocks survive the round trip).

**To add a fifth question:** write a block in `00_core_questions.md` in the same shape as the others —

```
### C5 · Title here ★ must-see
**core** · Understand → Apply · `in_class`

**Q.** …
**A.** …
**Pitfalls.** …
```

— then run `python3 build_questions.py` to regenerate `questions.json` (and `--check` to validate
without writing).

---

## Practising the set (optional)

`quiz.py` is a dependency-free stdlib CLI over `questions.json`:

```bash
python3 quiz.py --list                 # table of all four questions
python3 quiz.py --tier core            # C1-C3
python3 quiz.py --type hands_on        # the workshop question
python3 quiz.py --must-see --list      # all four
python3 quiz.py --random 2 --seed 7    # two random questions, answers hidden
python3 quiz.py --id C3                # one question with the full answer
python3 quiz.py --stats                # counts per session / type / tier / Bloom
python3 build_questions.py --check     # validate the Markdown, write nothing
```

---

## Facilitator guardrails

Common pitfalls to name **explicitly** when these questions come up — they are the ones students
reproduce in real work:

- SHAP / LIME explain a **model**, not the world — attributions are not causal effects.
- **Confounding** is the default explanation for any observational association.
- A **small attribution is not safety**: the legally dangerous feature is often entangled, so it can
  look small while the protected attribute does the work.
- Explanations can **increase** over-trust ("explanation as a seal of approval") instead of improving
  decisions.
- Compliance with the EU AI Act or NIST AI RMF is a **floor**, not proof of trustworthiness.
- A **measured** disparity that nobody owns is a reporting habit, not governance.
- Monitoring without thresholds, owners and actions is decoration.
- Escalate **risk tolerance** to a human for signature — never escalate a tool or model choice.

## Where the 71-question version went

The earlier *wide* bank (14 + 15 + 13 + 13 + 16 = **71 questions** across the four domain sessions and
the internal KSS engineer track) is preserved in two places, both still runnable:

1. **Frozen snapshot** —
   [`archive/2026-09-27_full_question_bank_v1/`](archive/2026-09-27_full_question_bank_v1/MANIFEST.md),
   self-contained with its own `questions.json`, `quiz.py` and `build_questions.py`.
2. **Git** — branch `fusemachines-fellowship` (see `git log --oneline -- 5_responsible_trustworthy_ai`).

```bash
# revisit the wide bank without touching this folder
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --stats
python3 archive/2026-09-27_full_question_bank_v1/quiz.py --id S3-Q2

# restore the five session files to the top level (git copy)
git checkout 34d3ee9 -- 5_responsible_trustworthy_ai/01_foundations.md \
  5_responsible_trustworthy_ai/02_explainable_ai.md \
  5_responsible_trustworthy_ai/03_causal_ai.md \
  5_responsible_trustworthy_ai/04_integration_audit_regulation.md \
  5_responsible_trustworthy_ai/05_internal_kss_engineers.md
```

(If you restore them, point `SESSIONS` in `build_questions.py` back at those files so they appear in
`questions.json` again.)

## Sources

- Christoph Molnar — *Interpretable Machine Learning* (core reference)
- *Trustworthy AI* (module reference book)
- **NIST AI Risk Management Framework (AI RMF 1.0)** — GOVERN / MAP / MEASURE / MANAGE
- **EU AI Act** — Annex III high-risk categories, Chapter III obligations, Arts. 72–73, 86, 27
- **GDPR** — Arts. 15, 22, 33, 35
- DoWhy / EconML tutorials · Matheus Facure — *Causal Inference for the Brave and True*
- **Anthropic** alignment material (RLHF, RLAIF, Constitutional AI, Responsible Scaling)
- **OWASP Top 10 for LLM Applications** (prompt injection, excessive agency, sensitive info disclosure…)
- *XSTest* — exaggerated safety / over-refusal benchmarking
