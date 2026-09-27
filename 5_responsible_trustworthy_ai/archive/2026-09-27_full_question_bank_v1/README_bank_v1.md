# Module 5 — Responsible & Trustworthy AI (Question Bank)

Student-facing question set for the **KSS × Fusemachines Fellowship** module
*Responsible and Trustworthy AI* — with focus on **Explainable AI (XAI)**, **Causal AI**,
and the surrounding principles of **fairness, transparency, robustness, privacy and accountability**.

**Facilitators:** Sujan Sharma / Aashish Pokharel
**Reference book:** *Trustworthy AI*

---

## Why this folder exists

The fellowship runs simply: students need to see a **small set of questions tied to the major
concepts of the module**, and every one of those questions is **answered and discussed inside the
lecture session**. This folder is that question set — not a hidden end-of-course exam.

Each question is labelled with the concept it targets, the Bloom level it exercises, and how it is
meant to be used, so a facilitator can lift questions straight into slides.

---

## Session map

| File | Session | Time | Required? |
|---|---|---|---|
| [`01_foundations.md`](01_foundations.md) | **Session 1** — Foundations of Responsible & Trustworthy AI | 60–90 min | Required |
| [`02_explainable_ai.md`](02_explainable_ai.md) | **Session 2** — Explainable AI Techniques | 90–120 min | Required |
| [`03_causal_ai.md`](03_causal_ai.md) | **Session 3** — Causal AI for Deeper Trust | 90–120 min | ⚠️ Optional — *drop if causation was already covered in an earlier class* |
| [`04_integration_audit_regulation.md`](04_integration_audit_regulation.md) | **Session 4** — Integration, Auditing & Regulation | 60–90 min + project work | Required |
| [`05_internal_kss_engineers.md`](05_internal_kss_engineers.md) | **Internal KSS track** — for AI / Software Engineers (prompt & agentic focus) | drop-in | Internal |
| [`questions.json`](questions.json) | Machine-readable bank (all sessions, same IDs) — **generated, do not edit by hand** | — | — |
| [`build_questions.py`](build_questions.py) | Regenerates `questions.json` from the Markdown session files | — | — |
| [`quiz.py`](quiz.py) | Tiny CLI to drill the bank | — | — |

---

## How to use these questions

The module is built around **"Try First, Understand Later"** and **low floor / high ceiling / wide walls**.

| Type | When | Behaviour |
|---|---|---|
| `pre_poll` | **Before** the topic is taught | Surfaced as a quick poll / think-pair-share. No marks. Purpose is to expose intuition and misconceptions, then revisit at the end of the session. |
| `in_class` | During the plenary | Answered together; facilitator reveals the reasoning, not just the answer. |
| `quiz` | Chapter-level knowledge check | Short, can be closed-book. |
| `discussion` | Peer debugging / reflection | No single right answer; used to make thinking visible. |
| `essay` | Short written response | 1–2 paragraphs, assessed on reasoning quality. |
| `hands_on` | Notebook / project work | Applied in the scaffolded starter notebooks. |

### Tiers

- **`core`** — *all learners will be able to…* Remember → Apply. These are the must-see questions.
- **`stretch`** — *some learners will be able to…* Analyze → Evaluate → Create. Extension for depth.

### The 8 questions everyone must see

Even if a session runs long, these are the non-negotiables (one per major concept cluster):

`S1-Q4` · NIST AI RMF core functions · `S1-Q7` · EU AI Act risk tiers ·
`S2-Q2` · SHAP values in plain language · `S2-Q6` · the correlation trap in SHAP ·
`S3-Q2` · confounding · `S3-Q8` · why causal beats correlational ·
`S4-Q4` · human in / on / out of the loop · `S4-Q9` · explain a decision to a regulator

---

## Coverage matrix — learning objectives → questions

| Learning objective (Bloom) | Questions |
|---|---|
| Define/explain core principles of Responsible & Trustworthy AI (Remember/Understand) | `S1-Q1`, `S1-Q2`, `S1-Q3`, `S1-Q4`, `S1-Q5` |
| Apply basic XAI techniques and articulate strengths/limitations (Apply/Analyze) | `S2-Q1`–`S2-Q7` |
| Relate correlation vs causation; identify where causal reasoning improves trust (Understand/Analyze) | `S2-Q6`, `S3-Q1`–`S3-Q5` |
| Implement/compare multiple XAI methods, evaluate via fidelity or human studies (Analyze/Evaluate/Create) | `S2-Q9`, `S2-Q10`, `S2-Q11`, `S2-Q12` |
| Build/query a simple causal model for intervention or counterfactual analysis (Apply/Create) | `S3-Q6`, `S3-Q7`, `S3-Q9` |
| Critique a system against NIST AI RMF / EU AI Act and propose mitigations (Evaluate/Create) | `S4-Q1`–`S4-Q6`, `S4-Q8` |
| Recognise adversarial robustness, auditing, trust calibration (Understand/Apply) | `S4-Q4`, `S4-Q5`, `S4-Q6`, `S4-Q7` |
| Discuss ethics and incident accountability (Evaluate) | `S1-Q11`, `S4-Q9`, `S4-Q10` |
| Internal KSS: prompt injection, privacy/PII, validation, alignment, governance (Apply/Analyze) | `K1`–`K16` in `05_internal_kss_engineers.md` |

---

## Question bank format

Questions live in Markdown (for slides and reading) **and** in `questions.json` (for tooling).
Both use the same IDs.

```json
{
  "id": "S2-Q4",
  "session": 2,
  "session_title": "Explainable AI Techniques",
  "topic": "SHAP",
  "bloom": ["Understand", "Apply"],
  "tier": "core",
  "type": "in_class",
  "must_see": true,
  "question": "…",
  "answer": "…",
  "pitfalls": "…"
}
```

`tier` ∈ `core | stretch` · `type` ∈ `pre_poll | in_class | quiz | discussion | essay | hands_on`

---

## Practising the bank (optional)

`quiz.py` is a dependency-free stdlib CLI over `questions.json`:

```bash
python3 quiz.py --list                 # table of every question
python3 quiz.py --session 2            # walk through Session 2
python3 quiz.py --type pre_poll        # only the "Try First" prompts
python3 quiz.py --tier stretch         # only the high-ceiling questions
python3 quiz.py --random 5             # 5 random questions, answers hidden
python3 quiz.py --id S3-Q2             # a single question + full answer
python3 quiz.py --stats                # counts per session / type / Bloom level
```

---

## Facilitator guardrails (from the module plan)

Common pitfalls to call out **explicitly** when these questions come up:

- SHAP/LIME explain a **model**, not the world — attributions are not causal effects.
- **Confounding** is the default explanation for any observational association.
- Impurity-based feature importance is biased toward high-cardinality and continuous features.
- Explanations can **increase** over-trust ("explanation as a seal of approval") rather than improve it.
- Compliance (EU AI Act / NIST) is a **floor**, not proof of trustworthiness.

---

## Sources

- Christoph Molnar — *Interpretable Machine Learning* (core reference)
- *Trustworthy AI* (module reference book)
- **NIST AI Risk Management Framework (AI RMF 1.0)**
- **EU AI Act** risk categories and high-risk obligations
- DoWhy / EconML tutorials · Matheus Facure — *Causal Inference for the Brave and True*
- **Anthropic** alignment material (RLHF, RLAIF, Constitutional AI, Responsible Scaling)
- **OWASP Top 10 for LLM Applications** (prompt injection, excessive agency, sensitive info disclosure…)
- *XSTest* (exaggerated safety / over-refusal benchmarking)

