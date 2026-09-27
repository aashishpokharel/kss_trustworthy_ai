# Session 4 — Integration, Auditing & Regulation

**Time:** 60–90 min + project work · **Concepts:** auditing and evidence; adversarial robustness;
regulatory frameworks (EU AI Act risk categories, NIST AI RMF); human-AI collaboration and trust
calibration; where XAI + Causal AI fit together; ethics, governance and incident accountability.

Legend: `tier` ∈ **core** (everyone) / **stretch** (some) · `type` ∈ `pre_poll` · `in_class` ·
`quiz` · `discussion` · `essay` · `hands_on`

---

### S4-Q1 · What counts as evidence of trustworthiness?
**core** · Analyze → Evaluate · `pre_poll`

**Q.** Rank these as evidence that a deployed model is trustworthy, then say what is wrong with each
**on its own**:

| # | Evidence |
|---|---|
| a | 95% accuracy on a random test split |
| b | A clean report from an external audit |
| c | Zero reported incidents in six months |
| d | The vendor's model card says so |

**A.** All four are weak in isolation, for different reasons. (a) measures one distribution and hides
**subgroup** performance and calibration; the test split is by construction the same distribution.
(b) Audits are **snapshots** whose value depends on scope, access, method, recency and who paid for
them. (c) **Absence of reporting is not absence of harm** — with no monitoring, no appeal path and
under-reporting, zero incidents often means zero *detection*. (d) Producer-authored, **selective**, and
unverifiable by outsiders.

The point to land: trustworthy evidence is **multi-source, adversarially produced and longitudinal** —
a test set is not an audit, an audit is not monitoring, and a document is not a control.

---

### S4-Q2 · NIST AI RMF functions → engineering actions
**core** · Understand → Apply · `in_class`

**Q.** Map the four NIST AI RMF core functions (**Govern, Map, Measure, Manage**) onto concrete
engineering actions for a credit-scoring model.

**A.** **GOVERN** (cross-cutting): a written AI policy; a **named accountable owner**; a model-risk
review board; approval gates in CI/CD; defined roles and escalation paths; training; and a register of
approved use cases. Governance is what makes the other three enforceable.

**MAP**: define context — intended purpose, affected population, out-of-scope uses, **misuse cases**,
threat model, and the applicable **risk tier** (EU AI Act mapping). Deliverable: a written
impact/risk assessment.

**MEASURE**: build the evidence — performance **disaggregated by subgroup**, calibration, robustness
and stress tests, adversarial evaluations, drift monitors, bias tests, red-teaming, and a reproducible
evaluation harness.

**MANAGE**: act on it — deployment **thresholds and gates**, mitigations (retrain, constrain features,
add human review, cap the model's authority), monitoring dashboards, rollback and kill switches,
**incident response**, and documentation.

**Pitfall.** Teams skip GOVERN and MAP and jump straight to MEASURE, ending up with dashboards nobody
is accountable for and no rule about what happens when a metric goes red.

---

### S4-Q3 · Build the audit checklist
**core** · Apply → Evaluate · `in_class`

**Q.** You are auditing a high-risk credit-scoring system. What artifacts do you request, and what
does a complete audit actually require?

**A.** Request: technical documentation; stated intended purpose and **out-of-scope** uses;
training/validation/test **data provenance and governance**; model card and dataset datasheet;
evaluation results **disaggregated by protected subgroup**, with the metric choice and its
justification; calibration; robustness, stress and distribution-shift tests; adversarial results;
**explanation method** plus its fidelity and stability evaluations; **human oversight design and actual
override rates**; logs and their retention; version/change history; approval records; the incident
register; the post-market monitoring plan; vendor/third-party risk review; a data-protection impact
assessment; and the retraining/rollback policy.

A complete audit also **reproduces** something: re-run the evaluation on a held sample, and walk a
handful of individual decisions end to end (**case audit**). Finally ask the two questions documents
dodge: **who signed off, and who is accountable when it fails?**

---

### S4-Q4 · Human in / on / out of the loop ★ must-see
**core** · Understand → Apply · `in_class`

**Q.** Define **human-in-the-loop**, **human-on-the-loop** and **human-out-of-the-loop**. Then assign
the right mode to:

| # | System |
|---|---|
| a | Medical diagnosis aid used when the model is uncertain |
| b | Spam filtering at mailbox scale |
| c | Content moderation for graphic violence |
| d | Loan approval for high-risk applicants |

**A.** **Human-in-the-loop (HITL):** a human must approve or decide before the action takes effect.
**Human-on-the-loop (HOTL):** the system acts autonomously, but a human monitors and can intervene or
stop it. **Human-out-of-the-loop (HOOL):** fully autonomous, with only post-hoc oversight.

- (a) **HITL**, or HOTL with **mandatory escalation** on low confidence — harm to a person is direct
  and hard to reverse.
- (b) **HOOL** for the bulk plus HITL on **appeals** — low stakes, reversible, enormous volume, and a
  human adds no value per message.
- (c) **HITL** for escalations, takedowns and downgrades — irreversible, legally consequential, and
  psychologically damaging to moderators, so wellness protections are part of the design.
- (d) **HITL for declines** (adverse action, explanation duty, appeal rights) and HOOL for approvals
  inside policy limits.

**The decisive test:** choose by **cost and reversibility of error**, and by whether a human can
*actually* improve the decision. A human who lacks the time, information or authority to disagree is
**oversight theatre** — and, worse, a **moral crumple zone** who absorbs blame without real control.

---

### S4-Q5 · When explanations make things worse
**core** · Analyze → Evaluate · `quiz`

**Q.** What is **automation bias**, and how can adding an explanation interface *reduce* safety?

**A.** **Automation bias** is the tendency to over-trust automated advice and stop checking it. It
produces **omission errors** (failing to act when you should have, because the system said nothing) and
**commission errors** (following advice you should have rejected).

The uncomfortable finding: **explanations can increase over-trust.** People accept an incorrect
recommendation more readily when plausible reasons are attached, even when the explanation is
meaningless or wrong — plausibility is read as correctness ("explanation as a seal of approval"). So a
"transparency" feature can *lower* effective oversight while *raising* reported trust.

Mitigations: show **calibrated uncertainty** and known failure modes rather than a confident story;
make the human **commit to their own judgement first** (predict-then-reveal); surface disagreeing
evidence; and measure **appropriate reliance**, not trust. Remember the accountability framing too: if
the human cannot realistically catch the error, blaming them afterwards is a governance failure, not
human error.

---

### S4-Q6 · Trust calibration
**core** · Understand → Apply · `quiz`

**Q.** Define **over-trust** and **under-trust**, and design one interface element that improves trust
**calibration**.

**A.** **Calibration** means trust matches reliability — trust the model when it is right, distrust it
when it is wrong. **Over-trust** produces **misuse** (accepting wrong outputs, e.g. automation bias);
**under-trust** produces **disuse** (ignoring good outputs, wasting the system and falling back to
worse manual processes). Both are real failures; low trust is not automatically virtuous.

A design that improves calibration: display a **calibrated confidence** alongside the **known failure
modes** of the model in context — e.g. *"unreliable for applicants with no credit history"* — plus a
**predict-then-reveal** flow where the user commits their own judgement before seeing the model's
output, an explicit **abstention** path, and access to exemplar cases where the model was wrong.

Evaluate it correctly: plot a **reliance curve** (does reliance track correctness?) and audit override
rates and their outcomes — rather than asking users whether they found the interface trustworthy.

---

### S4-Q7 · Adversarial robustness
**stretch** · Analyze → Evaluate · `quiz`

**Q.** Why can adding **imperceptible** noise to an input change a model's prediction? Name one defence
and its cost.

**A.** A classifier implements a **decision boundary** in a high-dimensional space. Many small
perturbations, each invisible on its own, **accumulate** across dimensions, and an attacker can follow
the gradient toward the nearest boundary to cross it with a tiny change measured in an L∞ or L2 norm
(FGSM; iterated PGD is stronger). Adversarial examples are not random noise — they are *optimised*
noise, which is also why they transfer between models.

Defences and their costs: **adversarial training** (train on adversarial examples) improves robustness
but **lowers clean accuracy**, is computationally expensive, and can **overfit to the specific attack
and threat model** you trained against — robustness to one perturbation budget is not robustness to
all. Input sanitisation and quantisation help against some attacks and are bypassable. **Certified**
defences such as randomised smoothing provide a probabilistic guarantee within a radius, at genuine
accuracy cost.

Framing to keep: security is a **process against a stated adversary model**, not a property you bolt
on. "Robust" is meaningless without saying *against whom and under what threat model*.

---

### S4-Q8 · Designing the XAI + causal + fairness release gate
**stretch** · Evaluate → Create · `in_class`

**Q.** Design a deployment pipeline where **XAI, causal and fairness** checks gate the release. Where
does each fit, and what blocks a release?

**A.** Sequence them, because the checks answer different questions.

**Before training — causal.** Write the DAG and a **feature policy**: no protected attributes, no
obvious proxies, and a documented justification for every retained feature. This is where causal
reasoning has the most leverage, because it constrains the problem instead of auditing it afterwards.
Add data-governance checks (consent/legal basis, retention, PII/DP handling).

**Before release — four gates:**

1. **Fairness & performance.** Subgroup metrics against **pre-agreed thresholds**, calibration, and
   disaggregated error analysis. Block if any threshold fails.
2. **Robustness.** Stress tests, perturbation and distribution-shift slices, and adversarial evaluation
   under a *stated* threat model.
3. **Explanation quality.** Fidelity and **stability** tests on samples, plus a plain-language reason
   generated for a random sample of decisions and reviewed by a non-author. Block if explanations are
   unstable or cannot be produced consistently for individual cases.
4. **Causal sanity.** Test whether the model relies on relationships that **do not transfer** — compare
   attributions and invariance across environments or shifted slices, and check the model is not acting
   through a spurious proxy. A feature whose association *reverses* across environments is a release
   blocker.

**In production:** drift **and** fairness monitors feed back; version-pin the model, thresholds and
explanation code together; define retraining triggers; wire the incident process and kill switch.

**Pitfall.** Treating causal AI as a fifth gate bolted on at the end. Causal work is strongest
*upstream* (which features are legitimate, which relationships are stable) and weakest as a late
accuracy-style check.

---

### S4-Q9 · Explaining a decision to a regulator ★ must-see
**core** · Evaluate → Create · `essay`

**Q.** *"How would you explain this model decision to a regulator?"* Write the explanation for one
specific declined decision.

**A.** A strong answer follows a fixed structure: (1) the **decision** and the applicable legal basis or
risk category; (2) the system's **role** — advisory or decisive, who the deployer is, and the intended
purpose; (3) the **inputs and which were influential**, with direction and magnitude, in plain
language, together with the **limitations of the method** used (an attribution is not a cause);
(4) the **counterfactual** — what would have changed the outcome — with feasibility caveats; (5) the
**human oversight actually exercised**: who reviewed it, what they saw, and their authority to
override; (6) the **appeal path** and how it was communicated to the applicant; (7) the **evidence
base**: monitoring, testing, subgroup performance and drift status; (8) what you would do differently
if the decision turns out to be wrong.

**Traps to penalise.** Over-claiming ("the model is 94% accurate, therefore…"); presenting SHAP values
as if they were causal effects; unexplained jargon and log-odds quoted without units; hiding behind the
vendor ("that is the supplier's model"); and omitting the appeal path entirely.

---

### S4-Q10 · Who bears the cost of an incident?
**core** · Evaluate · `discussion`

**Q.** A deployed model has wrongfully denied loans to thousands of people over six months. Who bears
the cost?

**A.** The honest answer is: **currently, mostly the affected people** — because the harm is diffuse,
redress is slow, and proving causation in court is hard.

Candidate allocation by role: the **provider** (built the model — the EU AI Act places duties on both
provider and deployer), the **deployer** (chose the context, the data, the oversight level and the
integration), the **vendor or data supplier** (provenance and quality), the **institution** itself
(fiduciary and consumer-protection duties), and potentially the **state** or an insurance pool through
compensation funds or mandatory AI liability cover.

Mechanisms worth discussing: contractual indemnities and SLAs; tiered duties by role; insurance;
mandatory serious-incident reporting; independent redress with compensation; and internal incentives —
if no individual's performance metric is affected by a fairness failure, nobody will catch it.

**Framing to surface:** without real redress, "accountability" is a press release. And the sharper
question — is the deployer who ignored the vendor's documented limitation *more or less* culpable than
the vendor who shipped it? Argue it both ways.

---

### S4-Q11 · Minimum viable governance
**stretch** · Evaluate → Create · `quiz`

**Q.** What is the minimum viable governance for a 10-person team shipping LLM-powered features?

**A.** Small enough to actually run, complete enough to matter: a **named accountable owner** per model
(not "the team"); a **model registry** with versions, data and evaluation artifacts pinned together; a
written **impact/risk assessment** per use case with a **risk tier** assigned (EU AI Act / NIST MAP);
a **release gate** with a checklist and a sign-off, not a Slack approval; **logging with a retention
policy**; an **incident process** with on-call, kill switch, rollback and a disclosure path; **vendor
risk review** for model/API providers (no-training clauses, data residency, subprocessors, breach
notification); scheduled **red-teaming and evals** rather than one-off testing; PII/DLP controls on
prompts and logs; **deny-by-default** for new use cases; and basic training so people know the policy
exists.

**Pitfall.** The failure mode is not "too little governance", it is governance that is **documented but
not wired into the release process**. If the gate can be bypassed under deadline pressure, the gate does
not exist.

---

### S4-Q12 · Drawing the line on autonomy
**core** · Evaluate · `discussion`

**Q.** Where do you draw the line on autonomy as you scale? Defend your criteria.

**A.** Criteria that hold up: **cost and reversibility of error**; whether harm falls on
**non-consenting third parties**; whether a human can *actually* add value (time, information,
authority); **latency and volume** constraints; the model's **uncertainty** and whether the case is
out of distribution; and whether the action is *outside the policy* the system was designed for.

The principle worth defending: **autonomy should scale with our ability to oversee it, not with our
ability to deploy it.** Deploy autonomy only where you can monitor, intervene and roll back — and treat
that as a capability threshold that must be met *before* expansion.

Add the uncomfortable part: oversight must be **real**, not nominal. A human who cannot catch the error
is not a control, and cannot be the answer to "who is responsible?"

---

### S4-Q13 · Incident post-mortem against the frameworks
**stretch** · Evaluate → Create · `hands_on`

**Q.** Pick a real, public AI incident. Classify it against the **NIST AI RMF** functions and the
**EU AI Act** categories; identify the principle(s) that failed; and propose two mitigations.

**A.** Open-ended. Assessment criteria: (1) correct and specific use of the frameworks rather than name
dropping; (2) distinguishing a **technical** failure (model behaviour) from a **governance** failure
(no monitoring, no owner, no escalation, incentive to ignore); (3) whether the mitigations address
*both* layers — most real incidents are governance failures with a technical trigger; and (4) whether
the student states what evidence would have caught the incident **earlier**, which is the actual goal of
the MEASURE and MANAGE functions.

**Facilitator note.** Close the module here by returning to `S1-Q1`: ask students to re-read the list of
principles they wrote before Session 1 and delete anything they can no longer defend.




