# KSS Session: Trustworthy AI — Slide Plan & Agent Execution Prompt

**Purpose:** This is a content outline plus a ready-to-use prompt for your agentic system (using the `pptx` skill/tooling) to actually build the deck. Use §1–8 as the source-of-truth content architecture; use §9 as the literal prompt to hand the agent.

---

## 1. Slide-by-Slide Content Outline

### Slide Group 1 — Introduction to Trustworthy AI
- **Define it precisely, not just vibes:** Trustworthy AI = an AI system whose behavior can be justifiably relied upon by the people affected by it — not "AI that feels okay," but AI with demonstrable, verifiable properties.
- **Anchor to NIST's definition immediately** so the session has one shared vocabulary from slide 1: NIST AI RMF defines trustworthy AI through **seven characteristics** — valid & reliable, safe, secure & resilient, accountable & transparent, explainable & interpretable, privacy-enhanced, and fair with harmful bias managed. Note explicitly that "explainable" is *one of seven*, not the whole definition — this sets up Slide Group 3 later.
- **Frame the talk's arc on this slide:** we'll go from "why this matters" → "why explainability alone isn't enough" → "the actual principles" → "the vocabulary you'll hear in the wild" → "how it connects to causal reasoning" → "what we've actually built."

### Slide Group 2 — Why Do We Need Trustworthy AI
- **The shift in stakes:** AI moved from recommendation/ranking systems (wrong answer = mild annoyance) to decision-making and agentic systems (wrong answer = financial loss, legal exposure, physical/safety harm, denied opportunity).
- **Three concrete failure categories to illustrate, not abstractly assert:**
  - *Silent failure* — a model confidently wrong (hallucination, biased denial) with no signal that anything went wrong.
  - *Adversarial failure* — a system manipulated by a bad actor (prompt injection, data poisoning, jailbreak).
  - *Systemic failure* — a model that's individually "correct" per its training objective but produces harmful aggregate outcomes (disparate impact across a protected group, even with no single wrong prediction).
- **Regulatory reality as a driver, not just an ethical one:** the EU AI Act's high-risk obligations phase in through 2026–2027, and NIST's Generative AI Profile (2024) exists specifically because generic AI risk guidance wasn't sufficient once LLMs and agentic systems became mainstream — trustworthiness stopped being optional the moment regulation caught up to deployment.
- **Tie to your own project as the closing beat of this section:** "this is exactly why we built the guardrail/governance layer you'll see later."

### Slide Group 3 — Why Explainability Doesn't Mean Trustworthy Anymore
This is the conceptual hinge of the talk — spend real slide real-estate here, not one bullet.
- **The historical assumption:** early XAI (LIME, SHAP, saliency maps) treated "if we can explain the prediction, we can trust it." This made sense when models were simpler and stakes were lower.
- **Why that assumption breaks down now:**
  1. **Explanations can be locally faithful but globally misleading** — a SHAP value tells you a feature's contribution to *this one prediction*, not whether the model's overall behavior is safe, fair, or robust.
  2. **Explanations are post-hoc, not causal** — most popular XAI methods explain *correlational* attribution, not *why* the model actually decided something; a plausible-sounding explanation can accompany a wrong or unsafe decision (this sets up Slide Group 6).
  3. **Explainability doesn't cover the other six NIST characteristics** — an explainable model can still be unfair, insecure, non-private, or unreliable. Explainability is necessary-but-not-sufficient, not a proxy for trustworthiness.
  4. **LLM-specific problem: explanations can themselves be hallucinated** — a model asked "why did you say that" will generate a plausible-sounding rationale that may not reflect its actual internal process at all (this is a known, current interpretability research problem, not a hypothetical).
  5. **Adversarial robustness is orthogonal to explainability** — a model can have a perfectly clean, interpretable decision boundary and still be trivially fooled by an adversarial perturbation or prompt injection; explainability tells you nothing about how the model behaves under attack.
- **The reframe for the audience to leave with:** explainability is one *input* to a trust judgment, not the *output* of one. Trust is a property of the whole system (data, model, deployment, monitoring, human oversight), not a property you get for free once you can visualize attention weights.

### Slide Group 4 — Core Principles of Trustworthy/Responsible AI
Build this as one principle per slide (or one principle per 2 slides if there's time), each with: definition → why it fails in practice → one concrete technique.

- **Fairness (bias detection/mitigation):** define via disparate treatment vs. disparate impact. Techniques: counterfactual testing (swap protected attributes, measure output delta), fairness metrics (demographic parity, equalized odds — mention the *impossibility result* that you generally can't satisfy all fairness metrics simultaneously, which is a good "make the audience think" moment), and mitigation stages (pre-processing the data, in-processing/constrained training, post-processing the outputs).
- **Transparency:** distinguish *transparency* (can you see/audit how the system works and what data it used) from *explainability* (can you interpret a specific decision) — these get conflated constantly and it's worth a slide just to separate them. Model cards, datasheets for datasets, and audit trails are transparency mechanisms; SHAP/LIME are explainability mechanisms.
- **Accountability:** who is answerable when the system causes harm — this is an organizational/governance property, not a technical one. Ties directly to NIST's Govern function and to human-in-the-loop design (a system with no human accountable for high-risk decisions cannot be accountable, no matter how good its metrics are).
- **Robustness/Safety:** performance under distribution shift, adversarial inputs, and edge cases — not just average-case accuracy. This is where adversarial robustness (Slide Group 5) and your own red-teaming work connect directly.
- **Privacy (e.g., differential privacy):** the core idea in one sentence — add calibrated noise so that no single individual's data materially changes the model's output/statistics, giving a mathematical (not just policy) privacy guarantee. Contrast with simple anonymization/redaction (what your PII pipeline does) vs. differential privacy (a formal guarantee, usually applied at training time or in aggregate statistics) — these solve different problems and it's worth being precise that they're not interchangeable.
- **Reliability:** consistent performance across time, environments, and inputs — ties to monitoring for drift, and to why a one-time eval isn't sufficient (echoes NIST's Measure function being continuous, not a pre-deployment gate).

### Slide Group 5 — Related Terms/Concepts
Treat this as a glossary/map slide (or two) — good as a visual (a concept map, not a bullet list) since it's explicitly a "vocabulary" section.
- **Adversarial robustness:** resistance to inputs deliberately crafted to cause failure (adversarial examples, prompt injection, jailbreaks) — distinct from general robustness to natural noise/edge cases.
- **Model auditing:** the practice (and increasingly regulatory requirement) of independently reviewing a model's data, training process, and behavior against a standard — internal or third-party, periodic or continuous.
- **Regulatory frameworks:**
  - *NIST AI RMF* — voluntary, four functions (Govern, Map, Measure, Manage), US-originated but globally referenced; not certifiable (ISO 42001 is the certifiable counterpart some organizations pair it with).
  - *EU AI Act* — binding law, four risk tiers (unacceptable/prohibited, high-risk/strict obligations, limited-risk/transparency-only, minimal-risk/no mandatory obligations); high-risk obligations phase in through 2026–2027, with most of the Act's rules taking effect August 2026.
- **Ethical considerations:** the normative layer underneath all of the above — whose values are encoded, who bears the risk vs. who gets the benefit, and what happens when technical mitigations (e.g., a fairness metric) conflict with a stakeholder's actual sense of fairness.
- **Human-AI collaboration/trust calibration:** the goal isn't maximal human trust — it's *calibrated* trust, where a human's confidence in the system's output matches the system's actual reliability in that context. Over-trust (rubber-stamping) and under-trust (ignoring correct outputs) are both failures; this is why your HITL approval queue shows the model's stated reasoning alongside the action, not just the action.

### Slide Group 6 — Intersections: XAI + Causal AI
- **The core claim, stated plainly:** most production XAI methods (SHAP, LIME, attention visualization) explain *association*, not *causation* — they tell you a feature was correlated with the output, not that changing it would actually change the outcome in the real world.
- **Why this matters for trust specifically:** a correlational explanation can be *right for the wrong reason* — e.g., a model correctly predicting an outcome by latching onto a spurious correlate of a protected attribute, with a SHAP explanation that looks perfectly reasonable while masking that the model would fail under distribution shift or actively encode bias.
- **What causal explanations add:** counterfactual reasoning ("if X had been different, would the outcome have changed?") and causal graphs give you an explanation that's tied to an actual mechanism, which is far more robust to shift and far harder to game — a causal explanation surviving a distribution shift is genuine evidence of trustworthiness; a correlational one surviving is not evidence either way.
- **Practical framing for the audience:** you don't need a full causal model to benefit from this lens — even asking "is this explanation counterfactually testable?" as a discipline when reviewing a SHAP output is a meaningfully more rigorous bar than accepting the attribution at face value.
- **Connect back to Slide Group 3's reframe:** this is precisely *why* explainability doesn't automatically mean trustworthy — correlational explanations are the default output of most XAI tooling, and causal grounding is the missing ingredient that would make an explanation actually load-bearing for a trust claim.

### Slide Group 7 — Resources to Prepare From (Reference Slide)
List as citable resources, not summarized content (this slide is a pointer, not a lecture):
- **NIST AI Risk Management Framework (AI RMF 1.0)** — the four-function core (Govern/Map/Measure/Manage) plus the Generative AI Profile (NIST AI 600-1) for LLM/agentic-specific risks.
- **Christoph Molnar, *Interpretable Machine Learning*** — free online book; the standard reference for the actual mechanics of XAI methods (LIME, SHAP, permutation importance, partial dependence, counterfactual explanations) that Slide Group 3 and 6 critique — worth citing directly since the critique lands better if the audience knows you're not dismissing these methods, just contextualizing their limits.
- **"Explainable AI: Interpreting, Explaining and Visualizing Deep Learning"** (Samek, Montavon, Vedaldi, Hansen, Müller, eds.) — deeper technical/academic grounding on XAI methods specifically for deep learning, useful for anyone in the room who wants to go past the survey level.
- **EU AI Act (official text / European Commission summary)** — for the regulatory-framework slide, so anyone who wants exact obligations per risk tier has the primary source rather than your summary.

---

## 2. How Your Codebase Maps to This Talk (dedicated closing section)

This is the payoff slide group — "here's this framework, now here's what we actually built against it." Map explicitly, one line per principle, so it doesn't feel like a separate advertisement bolted onto the theory:

| Principle/Concept from the talk | What you built |
|---|---|
| Fairness (bias detection) | Counterfactual test suite (Section 8, main architecture doc) — the same technique described in Slide Group 4, not a toy example |
| Transparency / Accountability | Governance plane, audit log, policy-versioned "constitution" document (Section 9.1/12) |
| Robustness/Safety, Adversarial robustness | Red-team harness (Garak/PyRIT), prompt injection defenses (Section 2/3) |
| Privacy | PII detection/redaction pipeline (Presidio-based, Section 5) — and worth being honest on this slide that what you built is redaction/tokenization, not differential privacy in the formal sense; a good moment to reference back to the distinction made in Slide Group 4 |
| Reliability | Groundedness/hallucination checks, scheduled eval cadence (Section 11/13) |
| Human-AI collaboration/trust calibration | HITL approval queue surfacing model reasoning vs. action divergence (Section 9.2), Streamlit test console (addendum §8.5) |
| Regulatory frameworks (NIST functions) | Your Govern → policy docs; Map → data classification tiers (Section 4); Measure → eval suite; Manage → incident review loop (Section 13) — genuinely worth drawing this as a direct 1:1 mapping, it's a strong closing visual |
| Explainability vs. trustworthiness (Slide Group 3) | Explicitly note what your system does NOT do — you have guardrails and governance, not model-internals interpretability — this honesty is more credible than overclaiming |

---

## 3. Suggested Deck Format Notes
- Roughly 20–28 slides for a KSS session: 2 for intro/agenda, 3–4 for "why," 4–5 for the explainability reframe (this is the section to linger on), 6–7 for core principles (one per principle), 2–3 for related terms (glossary/map), 2–3 for XAI+causal intersection, 1 for resources, 3–4 for the code-mapping closing section, 1 for Q&A/discussion prompts.
- Use one visual concept map for Slide Group 5 (glossary) instead of a bullet list — that section is explicitly about relationships between terms, which a diagram conveys better than bullets.
- End on a discussion prompt, not just a summary — e.g., "which of these seven characteristics is hardest to verify in your own team's systems today?" — KSS sessions land better with a live discussion close than a recap slide.
