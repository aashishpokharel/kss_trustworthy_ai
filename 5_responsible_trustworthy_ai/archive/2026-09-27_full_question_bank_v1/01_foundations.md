# Session 1 — Foundations of Responsible & Trustworthy AI

**Time:** 60–90 min · **Required** · **Concepts:** core principles (fairness, transparency,
accountability, robustness/safety, privacy, reliability), NIST AI RMF, EU AI Act risk tiers.

Legend: `tier` ∈ **core** (everyone) / **stretch** (some) · `type` ∈ `pre_poll` · `in_class` ·
`quiz` · `discussion` · `essay` · `hands_on`

---

### S1-Q1 · What makes an AI system trustworthy?
**core** · Remember → Understand · `pre_poll`

**Q.** Without looking anything up, list as many properties as you can that an AI system must have
before *you* would personally call it trustworthy. Now name one AI system you used this week and say
which property you are least sure it satisfies.

**A.** The session converges on the six principles: **fairness** (harmful bias managed),
**transparency/explainability**, **accountability**, **robustness & safety**, **privacy**, and
**reliability**. NIST phrases the same space as seven characteristics: valid & reliable, safe,
secure & resilient, accountable & transparent, explainable & interpretable, privacy-enhanced, and
fair with harmful bias managed.

**Pitfalls.** Most answers come back as *"it's accurate"* — accuracy is one input to validity, not
trustworthiness. Park the list on the board and revisit it at the end of Session 4.

---

### S1-Q2 · Principle → scenario matching
**core** · Understand → Apply · `in_class`

**Q.** Match each scenario to the principle it mainly stresses:

| # | Scenario | Principle? |
|---|---|---|
| a | A bank declines a loan and cannot tell the applicant which factors drove the decision | ? |
| b | A face-recognition system has a much higher error rate on darker skin tones | ? |
| c | A demand model trained pre-2020 collapses when behaviour shifts | ? |
| d | Support-chat transcripts, including health details, sit in an unencrypted log | ? |
| e | A model has been in production for two years and no team owns it | ? |

**A.** (a) transparency / explainability — (b) fairness (bias) — (c) robustness / reliability under
distribution shift — (d) privacy — (e) accountability.

**Pitfalls.** (c) is often answered "accuracy"; the point is that a *reliable* model can be
*non-robust*. (e) is often answered "maintenance", but "nobody is answerable" is the accountability
failure.

---

### S1-Q3 · Interpretability vs explainability vs transparency
**core** · Understand → Analyze · `quiz`

**Q.** Define **interpretability**, **explainability** and **transparency**. Why does the
distinction matter when you are standing in front of a regulator?

**A.** *Interpretability* is a property of the **model**: can a human grasp its mechanism (a linear
model or shallow tree, yes; a 100M-parameter net, not directly). *Explainability* is the **practice
and artifacts** of producing an account of the model or of a specific decision — and it may be
*post-hoc*, i.e. generated without knowing the mechanism (SHAP, LIME). *Transparency* is the broader
**organisational** property: disclosure about data, model, evaluations, limitations, ownership and
change history.

A regulator is usually asking for the third and the second (can you *account for* this decision, and
can I audit the process), while engineers often answer with the first ("our model is simple"). A
post-hoc explanation is not the same as an auditable process.

---

### S1-Q4 · NIST AI RMF core functions ★ must-see
**core** · Remember · `quiz`

**Q.** The NIST AI RMF is organised around four core functions. Name them. Which of the following is
**not** one of them: *Govern, Map, Measure, Manage, Monitor, Deploy*?

**A.** The four core functions are **GOVERN, MAP, MEASURE, MANAGE**. `Monitor` and `Deploy` are
**not** core functions — monitoring is performed inside MEASURE/MANAGE, and deployment is a
lifecycle stage, not a function.

**Pitfalls.** (1) Forgetting **GOVERN**, which is the cross-cutting one: culture, roles, policies,
and accountability — it is not a phase you complete. (2) Treating the RMF as a one-off audit rather
than a loop you keep running. The RMF is voluntary and process-oriented; it tells you *what* to
manage, not which threshold makes a model safe.

---

### S1-Q5 · Where the principles conflict
**core** · Analyze · `in_class`

**Q.** NIST's characteristics include *privacy-enhanced* and *fair with harmful bias managed*.
Explain the tension between them in a hiring system, and propose a resolution.

**A.** Measuring fairness requires **sensitive attributes** (gender, ethnicity, age, disability);
privacy protection discourages collecting and retaining exactly those attributes. Naively "solving"
this by dropping the attributes does *not* fix bias — correlated proxies (postcode, school, name,
hobbies) carry the same signal, which is a classic trap.

Resolutions: collect sensitive data with explicit consent and a stated purpose; keep it out of the
model features but retain it in a restricted fairness-audit store; report aggregated results rather
than individual records; use differential privacy or secure aggregation where feasible; and set a
documented retention limit.

**Pitfalls.** Believing that "we don't use the gender column" makes the model fair. Also worth
naming: privacy ↔ utility and robustness ↔ accuracy are the other two live trade-offs.

---

### S1-Q6 · EU AI Act risk tiers
**core** · Understand → Apply · `quiz`

**Q.** Give one concrete example system for each EU AI Act risk tier: **unacceptable**,
**high**, **limited**, **minimal**.

**A.** *Unacceptable (prohibited):* government social scoring, manipulative or subliminal
techniques, exploitation of vulnerabilities, untargeted scraping of facial images, emotion
recognition in the workplace or at school, most real-time remote biometric identification in public
spaces. *High:* CV screening and recruitment ranking, credit scoring, access to education and
exams, medical devices, safety components of critical infrastructure, migration/asylum decision
support. *Limited:* chatbots and deepfakes — the duty is mainly **transparency** (tell the user they
are dealing with AI; label generated content). *Minimal:* spam filters, recommended playlists, NPC
AI in games.

**Pitfalls.** Confusing "high-risk" with "important or popular". It is a **legal category** with a
defined checklist, and the *provider* carries more duties than the *deployer*.

---

### S1-Q7 · Obligations of high-risk systems ★ must-see
**core** · Understand → Analyze · `in_class`

**Q.** Under the EU AI Act, what extra obligations does a **high-risk** system carry compared with a
**limited-risk** one?

**A.** A limited-risk system mainly owes **transparency**: disclose that the user is interacting with
an AI, and label synthetic/generated content. A high-risk system owes a full lifecycle regime:
a **risk-management system** maintained across the lifecycle; **data governance** (training,
validation and testing data relevant, representative and as free of errors and bias as possible);
**technical documentation**; **record-keeping / logging** of events; **transparency and instructions
for use** passed to the deployer; **human oversight** designed in; appropriate **accuracy,
robustness and cybersecurity**; a **conformity assessment** with CE marking and registration in the
EU database; **post-market monitoring**; and **serious-incident reporting** to the market
surveillance authority.

**Pitfalls.** Thinking obligations end at deployment. Most of the leverage is in post-market
monitoring and human oversight, and those are exactly the parts teams skip.

---

### S1-Q8 · Reliability vs robustness
**core** · Understand · `quiz`

**Q.** Define **reliability** and **robustness**, then construct an example of a model that is
reliable but *not* robust.

**A.** *Reliability* = the system performs as intended, consistently, on its intended input
distribution, and that behaviour can be validated and reproduced. *Robustness* = performance is
maintained when inputs are perturbed, adversarially crafted, or drawn from a shifted distribution.

Example: a credit model trained on 2015–2019 applications is flawless on a held-out 2019 test set
(reliable) but its ranking degrades badly when interest rates or income distributions shift in
2022, and it is fully non-robust to adversarially crafted application data.

**Pitfalls.** Treating "held-out test set accuracy" as a robustness argument. A test set is, by
construction, the *same* distribution.

---

### S1-Q9 · Differential privacy, intuitively
**core** · Understand → Apply · `quiz`

**Q.** You have two versions of a model trained with differential privacy, one at **ε = 0.1** and
one at **ε = 8**. Which is more private, and what do you give up for it?

**A.** ε = 0.1 is the **more private** one. Smaller ε means a stronger privacy guarantee, which in
practice means **more noise** injected and therefore lower accuracy/utility. Larger ε means less
noise and better utility but a weaker guarantee.

Also worth stating: the guarantee is about **any single individual's** contribution being
indistinguishable, it composes (the budget is spent across queries/releases), and it usually comes
with a failure probability δ. Privacy is a **budget you spend**, not a switch you flip.

**Pitfalls.** Reading ε as "accuracy" or "privacy level where bigger is better". Also assuming DP
equals anonymisation — DP is a quantifiable, adversary-relative guarantee; "we removed the names"
is not.

---

### S1-Q10 · Model cards and datasheets
**core** · Analyze · `discussion`

**Q.** Which principle is served by publishing a **model card** and a **datasheet**? What can they
*not* fix?

**A.** They serve **transparency** and, indirectly, **accountability**: documented intended use,
out-of-scope uses, evaluation results (ideally disaggregated by subgroup), known limitations,
training-data provenance, and a named owner/contact.

They cannot fix: model behaviour (documentation is not mitigation), and they can degrade into
marketing. A stale card is worse than no card, because it produces false confidence. Accountability
requires a real owner and a real consequence, not a document.

---

### S1-Q11 · Is compliance enough?
**core** · Evaluate · `essay`

**Q.** "Our system passes the EU AI Act conformity assessment, therefore it is trustworthy." Write
1–2 paragraphs responding to this claim.

**A.** Strong answers separate **legality** from **trustworthiness**. Compliance is a *floor* and is
largely backward-looking: it asks whether process obligations were met at assessment time. It does
not prove the model is fair for *this* population, that it will stay reliable under drift, that the
explanation shown to a user is faithful, or that affected people consider the outcome legitimate.

Trustworthiness is also a property of the **sociotechnical system** — the people, incentives,
monitoring and escalation paths around the model — not of the artifact alone. And regulation lags
capability, so a novel failure mode can be fully compliant and still harmful. The strongest answers
add that minimal-compliance behaviour ("checkbox ethics") is itself a governance risk.

**Pitfalls.** Either extreme: "compliance means nothing" (it does create real obligations and
audit trails) or "compliance is sufficient" (it is not).

---

### S1-Q12 · Personal reflection on trust
**core** · Analyze → Evaluate · `discussion`

**Q.** Think of an AI system you personally rely on. Which **single** principle do you worry about
most, and what **evidence** would change your mind?

**A.** Open-ended. Grade the *evidence*, not the opinion. Weak answers name adjectives
("it feels biased"). Strong answers name measurable things: error/refusal rates disaggregated by
subgroup, drift monitors, calibration curves, incident history, who is accountable, what an audit
found, whether the system abstains when uncertain.

---

### S1-Q13 · Read a real system card
**stretch** · Analyze → Evaluate · `hands_on`

**Q.** Find the model card/system card of a deployed model you have access to. Record (a) one
evaluation the provider reports, (b) one limitation they admit, and (c) one question a regulator
would still not be able to answer from the card.

**A.** Open-ended. The teaching point: system cards are **producer-authored and selective**. The
typical gap in (c) is verifiability — an external party usually cannot reproduce the evaluations,
inspect training data provenance, or see subgroup breakdowns for the populations they care about.

---

### S1-Q14 · Interrogating a vendor claim
**stretch** · Evaluate → Create · `in_class`

**Q.** A vendor says: *"Our model is 94% accurate and fully compliant with the EU AI Act."* Give
three follow-up questions that would genuinely test trustworthiness.

**A.** Any three of: Accuracy on **what distribution**, and disaggregated for **which subgroups**?
Which **risk tier** does this fall under, and who performed the **conformity assessment**? How do you
monitor **drift** post-deployment and what triggers a retrain or rollback? What is your **incident**
process and who bears the cost when it fails? What is the **data provenance** and the legal basis
for processing? How is **human oversight** actually implemented, not just promised? Can I reproduce
your evaluation?

**Pitfalls.** Vague questions ("is it safe?") get vague answers. Precision is the skill being taught.


