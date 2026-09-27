# Whole-Course Core Set — Four Questions

Four questions, one per domain, for a course that runs
**Foundations → Explainable AI → Causal AI → Integration, Auditing & Regulation**.

Each question is *anchored* in one domain but **cannot be answered inside it**: a strong answer
reaches into the other three and into the engineering discussions behind them. That is the whole
point of the set — by the end, students should move between the domains without being told that
the domains are connected.

| ID | Anchored in | Must also reach into | Use it as | Time |
|---|---|---|---|---|
| [`C1`](#c1--deconstruct-the-trustworthiness-pitch-★-must-see) | **Session 1** — Foundations | S2 (explanations) · S3 (causal reading) · S4 (EU AI Act / NIST RMF) | Cold opener / plenary, no prep | 15–20 min |
| [`C2`](#c2--three-audiences-one-truth-★-must-see) | **Session 2** — Explainable AI | S1 (rights & transparency) · S3 (causal reading) · S4 (logging & audit trail) | In-class writing + plenary | 20–25 min |
| [`C3`](#c3--the-29-trap-★-must-see) | **Session 3** — Causal AI | S1 (validity & measurement) · S2 (explanation misuse) · S4 (decision gates, monitoring) | In-class or take-home | 25–30 min |
| [`C4`](#c4--the-90-minute-pre-deployment-review) | **Session 4** — Integration, Auditing & Regulation | S1–S3 (all of them) | Workshop / assessment | 30–45 min |

Two things make this a *whole-course* set rather than four session drills:

1. **Every** question is a synthesis question — each is anchored in its own domain and still
   needs the other three to be answered well. None of the four can be closed inside a single
   session.
2. `C4` is additionally the **capstone**: it assumes the artifacts students produced in
   `C1`–`C3` and asks them to pack those artifacts for an audit and defend a go / no-go call.

---

## The running case

**Northline Bank — "CreditBoost"**

Composite case, but nothing in it is fanciful. Read it once; all four questions draw on it.
Facilitators can hand out **only this section** at the start of the course and let each session
add its own lens.

**The bank.** A mid-size retail bank, 1.4M cardholders, operating in the EU and the UK. In scope
for the **EU AI Act**, **GDPR** (incl. Art. 15 and 22), **UK GDPR**, and its national supervisor's
model-risk guidance.

**The system.** One product name, two components:

1. **The decision model** — every night, a gradient-boosted tree model (XGBoost, 240 features,
   AUC 0.81, calibrated, retrained monthly) scores each cardholder and **raises the credit limit
   by one band** when the expected value of doing so clears a threshold. About **40,000 limits per
   month** are raised automatically. Customers who *request* an increase and are refused receive a
   refusal letter.
2. **The explanation layer** — an LLM drafts the customer-facing letter (increase or refusal) from
   a structured **SHAP** attribute list plus the account summary. Its wording adapts to the tone of
   the customer's message.

**Features that matter later.** Bureau score, income band, tenure, utilisation, missed payments
(24 months), **postcode**, **app usage**, **merchant-category spend**.

**The pitch.** At the pre-deployment review the team says:

> *"94% of the model's predictions for accounts that repaid were correct, we publish a model card,
> every decision is logged, and we passed the EU AI Act conformity assessment — so CreditBoost is
> trustworthy."*

**What the file already contains** (evidence students may use or dispute):

- **Fairness audit** — refusal rates are **1.7× higher** in two postcode clusters that correlate
  with ethnicity. The auditors controlled for credit history. Confidence interval ±0.4. The audit
  is not repeated on a schedule.
- **The 2024 pilot** — a limit increase was tested against a control group: **+3.2% spend** and
  **+2.9% 12-month default rate** in the treatment group. The pilot ran during a **promotional
  cashback period**, only **60% of eligible customers took** the increase, and it ran for
  **6 months**. No causal estimate of the effect of *raising* a limit on default exists anywhere
  else in the bank.
- **The letters** — they occasionally state a reason that is **not in the SHAP list**, and the
  tone shifts noticeably when the customer's message is angry.
- **Monitoring** — monthly **AUC drift** on a dashboard. **No group-level refusal-rate tracking.**
  No post-market monitoring plan on file.
- **Incidents, last quarter** — 480 letters sent with the **wrong customer name**; a 3-day scoring
  outage during which the pipeline **defaulted to "no increase"** for everyone.
- **Governance** — a named model owner; a **DPIA signed in 2023**; the LLM prompt that controls
  the letters is owned by a **contractor** and lives in a notebook.

**Roles you can assign in the room:** model owner · risk officer · auditor · customer advocate ·
engineer on call. Nobody in the room gets to be the CEO.

---

### C1 · Deconstruct the trustworthiness pitch ★ must-see
**core** · Understand → Analyze → Evaluate · `in_class`

**Anchored in:** Session 1 (Foundations) · **Also requires:** Session 2 (explanations), Session 3 (causal reading), Session 4 (EU AI Act / NIST AI RMF) · **~15–20 min, cold**

**Q.** Take the team's pitch, clause by clause. For **each clause**, say (a) which trustworthiness
property it actually supplies evidence for, (b) which property it leaves completely untouched, and
(c) the single cheapest piece of evidence that would settle it. Then classify CreditBoost under the
EU AI Act and justify the classification in one sentence, name the **NIST AI RMF function** that is
most clearly missing from the file, and finally quote the **one sentence of the pitch you would
refuse to let the team say in public** — with the reason a non-technical reader would be misled by it.

**A.**

**1. The clause table** (keep this — `C4` uses it as the front page of the risk register)

| Clause in the pitch | What it really evidences | What it does not touch | Evidence that would settle it |
|---|---|---|---|
| "94% of predictions for accounts that repaid were correct" | **Validity**, partially, and only as a **class-conditional** claim on the benign majority class | safety · fairness · robustness · privacy · accountability — and validity itself on the harmful class | confusion matrix, calibration curve, and the **cost-weighted** error split (a wrongly raised limit vs a wrongly refused customer) |
| "we publish a model card" | **Transparency / documentation**; an accountability artifact | whether the documented behaviour is *true* | independent replication, plus a **data sheet** for the 240 training features |
| "every decision is logged" | **Traceability** — a precondition for accountability, not a substitute | whether any decision was *justified* | log retention and access policy, a replay test, and a **sampled audit** comparing logged reasons with the model's actual reasons |
| "we passed the EU AI Act conformity assessment" | **Legal compliance**, and only if the classification is right | trustworthiness: compliance is a **floor**, not proof | the assessment itself, who signed it, and whether the system was classified high-risk at all |
| "**so CreditBoost is trustworthy**" | nothing | everything — a property claim built out of compliance and accuracy claims | — |

**2. Read the 94% properly before you accept it.** The claim is about the *repaid* class, i.e. it is
precision-shaped on the majority outcome. With a low default base rate, a model that raises nothing,
or raises for everyone with a decent bureau score, can look impressive on that number. The disparity
and the incidents in this file are exactly why one majority-class figure is not a validity argument.
Ask instead: **what is the error rate on customers who default after a raise, and what does each
error cost the bank and the customer?**

**3. Classification — high-risk, Annex III point 5(b).** CreditBoost evaluates the creditworthiness
of natural persons and feeds decisions on access to credit, which is Annex III 5(b) — so the whole
Chapter III stack attaches: risk management, data governance, technical documentation, logging,
transparency and instructions for use, **human oversight**, and accuracy / robustness /
cybersecurity. Two sharp consequences:

- Northline develops the system in-house and puts it into service **under its own name**, so it is
  not only a deployer — **provider duties attach to it as well**, including the very conformity
  assessment the pitch is waving.
- The **letter generator is a second system** with its own failure modes. A conformity assessment of
  the scoring model says nothing about a hallucinated refusal reason.

**4. The missing NIST AI RMF function — GOVERN.** The file shows plausible MAP and MEASURE work (the
fairness audit, the pilot, the model card) and almost nothing in GOVERN or MANAGE: no risk-tolerance
statement for the 1.7× disparity, no post-market monitoring plan, no escalation path, and the prompt
that writes customer-facing letters is owned by a **contractor** and lives in a notebook. GOVERN is
the cross-cutting function — with it missing, audit and pilot results have nowhere to go, which is
exactly why the disparity was measured once and never driven to a treatment.

**5. The sentence to refuse: *"so CreditBoost is trustworthy."*** Everything before it is a claim
about evidence; this last clause silently converts *compliance plus one accuracy figure* into a
**property of the system**. A non-technical reader hears "independently verified safe", when the file
contains an unexplained 1.7× refusal disparity, two incidents in one quarter, and no post-market
monitoring. The defensible replacement: *"CreditBoost is legally compliant and its majority-class
accuracy is high; its fairness and post-market behaviour are unresolved."*

**Rubric.**

| Dimension | Full marks | Partial credit |
|---|---|---|
| Clause-by-clause evidence | All four clauses, each tied to a *different* property with a concrete missing artifact | Lists properties generically, or repeats "accuracy ≠ trust" four times |
| Cross-domain reach | Uses the letter layer, the pilot and the disparity as counter-evidence instead of accepting the pitch | Stays inside Session 1 vocabulary; never mentions the letter layer |
| Classification | Names Annex III 5(b) / high-risk plus at least one provider-side duty | Says "high-risk" with no legal anchor, or calls it limited-risk |
| RMF gap | Picks GOVERN and shows the consequence for the MAP/MEASURE outputs | Lists all four functions without committing to one |
| Communication | Refuses the *property* sentence and offers a defensible replacement | Refuses the "94%" clause instead of the conclusion |

**Pitfalls.** Reading "94%" as accuracy; treating a model card as verification; hearing "conformity
assessment" as "independently audited and safe"; classifying by *impact* ("a limit increase is
harmless") rather than by **legal category**; forgetting the letter generator is a second system.

**Discussion prompt.** Which clause could be made true within 30 days, and which one cannot be made
true this year without changing how the bank works? (Expected: logging and the model card are cheap;
the fairness and post-market claims require governance that does not exist yet.)

**Artifact for `C4`.** Your clause table + the classification memo. `C4` asks you to file them in an
audit pack and defend a go / no-go decision.

---

### C2 · Three audiences, one truth ★ must-see
**core** · Understand → Apply → Analyze · `in_class`

**Anchored in:** Session 2 (Explainable AI) · **Also requires:** Session 1 (rights & transparency), Session 3 (causal reading), Session 4 (logging & audit trail) · **~20–25 min**

**Q.** Customer #4471 asked for a credit-limit increase and was refused. The SHAP list behind that
decision, in descending magnitude, is: `utilisation +0.41 · missed payment (recent) +0.28 · app usage
+0.13 · merchant-category spend −0.07 · postcode +0.04`. Write **three versions of the explanation** —
for (a) the customer, (b) the internal risk committee, (c) the supervisor/auditor — and for each say
one thing it must **not** contain. Then explain where that SHAP list would mislead a reader who treats
it as causal, and specify **two guardrails plus one evaluation** you would put on the letter generator
before it writes to a customer again.

**A.**

**1. Three explanations, three jobs.**

| Audience | What the explanation must do | What it must **not** contain |
|---|---|---|
| **Customer (#4471)** | Answer *why* and *what next* in her language: the main reasons in her terms ("your balance is high relative to your limit", "a payment was missed a few months ago"), the evidence she can challenge, and how to request human review. | Raw SHAP values, internal feature names, a ranked list that reads like the scoring formula — and above all, reasons the model did not use. |
| **Risk committee** | Model-level behaviour *plus* the case in context: attribution with direction, model version, calibration, error rates for this segment, the unresolved 1.7× disparity, and the asymmetric cost of the two error types. | A single case presented as evidence about the model, and attributions quoted as effects ("lower utilisation would have got her approved"). |
| **Supervisor / auditor** | Reproducibility: the decision, model version, inputs, method (SHAP / TreeSHAP, background dataset), log-entry ID, human-oversight path, and the letter template with the mapping from generated text back to the attribute list. | A narrative. An auditor needs an artifact trail; fluent prose proves nothing and is not traceable. |

**2. Rights check before you write a word** (this is where `C1` comes back): the customer is entitled
to meaningful information about the logic of an individual decision — GDPR Art. 15(1)(h) read with
Art. 22, and Art. 86 of the AI Act for high-risk systems. So the customer letter is not a courtesy
layer, it is a **legal instrument**. That is why "the LLM writes something plausible" is a bigger
problem than "the letter has a bug".

**3. Where the SHAP list misleads a causal reader.** SHAP decomposes *this model's prediction*, so it
describes the model's behaviour, not the world. Three specific traps:

- **Attribution ≠ effect.** "App usage +0.13" is not "if she used the app more she would have been
  approved". Nothing in the list is an intervention response.
- **Correlated features split the credit — and the legally dangerous one looks small.** `postcode
  +0.04` is tiny only because it is entangled with utilisation and spend inside the tree. A small
  attribution is **not** evidence of no fair-lending exposure; the 1.7× refusal disparity lives in
  exactly these entanglements.
- **Attribution ≠ the model's real reason.** TreeSHAP values can disagree with what the model would
  actually do under a feature change. The story you tell the customer and the mechanism that produced
  the decision are two different claims.

And note what is missing from the plot entirely: the question that matters to the customer and to the
regulator — *"what would have to change, and would that change be fair?"* — is a **causal** question,
which is `C3`.

**4. Two guardrails and one evaluation for the letter generator.**

| Guardrail | Failure it stops | Concrete rule |
|---|---|---|
| **Grounded generation** | The hallucinated reason (the letter cites something absent from the SHAP list) | The letter may only cite reasons present in the attribute list; every sentence maps to a supporting attribute; enforce with constrained generation or a post-generation entailment check that blocks the send. |
| **Immutable template + tone clamp** | Tone drift on angry messages — an undocumented second policy leaking into a regulated communication | Fixed structure and approved reason vocabulary; tone may vary only inside a pre-approved band; the prompt is versioned, reviewed, and moved out of the contractor's notebook onto the model-owner's account. |

**Evaluation:** a **golden set** of approved and refused cases — including cases from both disparity
clusters — with human-written correct explanations. Score: (i) every stated reason is necessary,
(ii) the top reasons are present, (iii) zero new reasons, (iv) tone stability under adversarial and
emotional inputs, (v) readability at the customer's language level. Re-run it on **every prompt, model
or template change**: this is a regression suite, not a one-off study.

**Rubric.**

| Dimension | Full marks | Partial credit |
|---|---|---|
| Audience separation | Three genuinely different explanations, and the *not-contains* column is specific (raw scores vs narrative vs ungrounded reasons) | Three lengths of the same text; "don't be confusing" as the only prohibition |
| Rights framing | Connects the customer letter to Art. 15/22 + Art. 86 and treats it as a legal instrument | Says "transparency is important" with no instrument named |
| Causal reading | Names attribution ≠ effect **and** uses the small `postcode` attribution to show why attribution size is a bad fairness proxy | Only the generic "SHAP is not causal" line |
| Guardrails | Two mechanisms that would actually block the two observed failures, enforceable in code | "Review the output", "add a disclaimer" |
| Evaluation | A reusable golden-set suite tied to prompt/model changes | A one-time user study, or "test it manually" |

**Pitfalls.** Turning the customer letter into a data dump; assuming a method is objective because it
is mathematical; reading "small attribution" as "no legal risk"; treating the LLM layer as presentation
rather than a regulated, testable system; forgetting that the explanation must be *challengeable* —
naming a human review path is part of the answer.

**Discussion prompt.** If you can afford exactly one of these before the next batch runs: (a) the
grounded-generation check, (b) the golden set, or (c) the human-review path in the letter — which do
you pick, and what does the choice say about which failure you consider most likely?

**Artifact for `C4`.** Your three-audience explanation set, plus the two guardrails and the evaluation
spec — `C4` files these as the transparency and post-market evidence in the audit pack.

---

### C3 · The 2.9% trap ★ must-see
**core** · Understand → Analyze → Evaluate → Create · `in_class`

**Anchored in:** Session 3 (Causal AI) · **Also requires:** Session 1 (validity & measurement), Session 2 (explanation misuse), Session 4 (decision gates, monitoring) · **~25–30 min**

**Q.** The head of risk reads the pilot — *+2.9% 12-month default rate in the treatment group* — and
wants CreditBoost switched off. The growth lead reads the same table — *+3.2% spend* — and wants to
stop testing and raise limits everywhere. Both are holding one number. (a) Name the **three distinct
questions** hiding in that argument and say which rung of the ladder each one lives on. (b) Draw the
**DAG** the pilot is really inside, and label the confounders, the mediator and the selection problem.
(c) State what you must assume to read the pilot as *"raising limits causes more defaults"*. (d) Write
the **estimand** you actually need. (e) Design the study that would answer it. (f) Finally, say whether
the study is worth its cost — and whether the fairness finding is a causal question too.

**A.**

**1. Three questions, three rungs.**

| Question actually being argued | Rung | What answers it |
|---|---|---|
| "Did customers who got increases default more often?" | **Association** (Rung 1) | The pilot table, nothing more — it is a comparison of observed outcomes |
| "Would raising the limit *cause* more defaults than not raising it?" | **Intervention** (Rung 2) | A design that makes the increase independent of the customer's underlying repayment ability — an intervention `do(L=1)` vs `do(L=0)`, not a comparison of who happened to get one |
| "Would customer #4471 have defaulted if we had *not* raised her limit?" | **Counterfactual** (Rung 3) | A model, plus assumptions — this is the rung the letter generator implicitly reaches for when it says anything about "what would have changed the decision" |

The pilot is only evidence on Rung 2 if its design is clean. It is not: it ran during a **promotional
cashback period**, only **60% of eligible customers took** the increase, and the window (**6 months**)
is shorter than the outcome (**12-month default**).

**2. The DAG the pilot is inside.**

```
   Income stability ───────┐
                           ├──► Baseline risk ────────────────┐
   Promo / cashback period ┘        (confounder)              │
                                                              ▼
                        [ Limit increase ] ──► Utilisation ──► 12-mo default
                                 │               (mediator)       ▲
                                 └──► Spend ──────────────────────┘
                                                (take-up: only 60% complied)
```

- **Confounders:** `Income stability` and `Baseline risk` drive both the likelihood of getting an
  increase and the likelihood of default. `Promo period` drives spend *and* take-up, so it also
  changes who ends up with the treatment.
- **Mediator:** `Utilisation`. The effect of an increased limit runs *through* it — a genuinely
  counter-intuitive result explains it: the increase only matters if the customer draws on it.
- **Selection / compliance:** with 60% take-up, "got an increase" is partly self-selected. The offer is
  random-ish; *who acts on it* is not. This creates a fork in the estimand (see §4).

**3. What you must assume to call the pilot causal.** All four, and the pilot violates at least two:

- **Exchangeability / no confounding** — treatment assigned independently of unobserved repayment
  behaviour. The promotional period and self-selection break this.
- **Positivity** — every kind of customer has some chance of either treatment. Fine here.
- **Consistency** — "raise the limit" is one well-defined intervention (one band? automatic? any
  amount?). Unstated in the file, so it is not yet a well-defined treatment.
- **No interference** — one customer's increase does not change another's default risk. Plausible, but
  not free at 40,000 increases a month in the same local market.

**4. The estimand you actually need** — write it down *before* looking at results, because the choice
decides the answer:

| Piece | Value |
|---|---|
| **Contrast** | Raise the limit by one band vs leave it unchanged |
| **Version 1 — ITT** | Effect of the **offer** of an increase, averaged over all eligible cardholders — this is what a rollout policy changes, and it survives non-compliance |
| **Version 2 — TOT/ATT** | Effect of **actually receiving** the increase, among compliers — requires using the random offer as an instrument, plus monotonicity |
| **Population** | Existing cardholders eligible for an automatic increase (say it out loud: this will not generalise to new customers) |
| **Outcomes** | 12-month default/write-off (defined precisely), spend, interest income — with a declared trade-off rule between them, because risk and growth are arguing about which outcome dominates |
| **Horizon** | 12 months, handling right-censoring (a 6-month window cannot see a 12-month outcome) |
| **Heterogeneity** | CATE by baseline-risk segment — a mean hides the case where all the harm sits in one stratum |

**5. The design that answers it.**

1. **Randomised holdout with automatic application** — randomise *eligibility* at customer level, apply
   the increase automatically wherever the contract allows instead of relying on an offer, keep a
   holdout share, run **≥12 months**, pre-register the analysis, and keep the promotional context fixed.
   Randomising an *action* rather than an *offer* removes the 60%-take-up ambiguity.
2. **If randomisation is not possible: regression discontinuity.** The system already applies a hard
   score cutoff, so customers just above and just below it are comparable by construction, and the jump
   in default at the cutoff is a **local** causal effect. It costs almost nothing and uses data the bank
   already generates; its limitation — that it speaks only about *marginal* customers — is exactly the
   population the decision is about.
3. **Weak fallbacks, and say so:** instrumental variables using the offer as an instrument for take-up
   (needs monotonicity); panel/difference-in-differences (weak here — the rollout was uniform, so there
   is little timing variation to exploit).
4. **Whatever the design, add:** sensitivity analysis for unmeasured confounding (E-value), and a
   negative-control outcome that should not move if the story is causal.

**6. Is the study worth its cost? Yes — but for a specific reason.** 40,000 increases a month means the
*sign* of this effect moves a number large enough that the evaluation cost is a rounding error. The
general rule: **the value of causal precision scales with the cost and irreversibility of the decision
it feeds**, not with how interesting the question is. If the effect had been obviously huge, or if both
teams would have made the same call either way, the right answer is "don't spend the money".

And a decisive point for the meeting: a 2.9% *average* effect is not a verdict on the system. If the
harm is concentrated in the highest-risk decile, the answer is not "switch CreditBoost off" — it is
"stop raising limits for the stratum where expected harm exceeds expected benefit". That is a subgroup
decision, and it needs CATE, not an average.

**7. Yes — fairness is a causal question too.** The audit's 1.7× disparity is an *association*:
refusal rates differ across postcode clusters, holding credit history fixed. The question a regulator
(and a court) actually asks is counterfactual: **would the decision have been different if the only
thing that changed were the group marker?** Three consequences:

- "We controlled for credit history" is not automatically a defence. If the postcode effect operates
  *through* credit-history variables — themselves shaped by past exclusion — then adjusting for them
  blocks part of the very pathway you are testing. Over-control is the classic way to make a
  disparity disappear on paper.
- Build the disparity DAG as well: `group marker → postcode → refusal` alongside `group marker →
  credit history → refusal`. Decide, explicitly, which variables are legitimate adjusters, which are
  **proxies**, and which are mediators.
- Group membership is not in the data, so the audit leans on proxies. The strongest design here is
  not a regression at all: **matched-pair counterfactual testing** — pairs of applications that differ
  only in the group-correlated marker, scored by the live model.

**Rubric.**

| Dimension | Full marks | Partial credit |
|---|---|---|
| Rung discipline | Keeps the three questions separate and says which evidence supports which rung | Answers everything on one rung; talks about "significance" throughout |
| DAG | Correctly labels confounder (*baseline risk, income stability*), mediator (*utilisation*) and take-up selection, and refuses to adjust for the mediator when the total effect is wanted | Draws a box-and-arrow picture without stating which arrow does what |
| Assumptions | Names exchangeability, consistency, positivity, no interference and points at the specific one the pilot violates | "Correlation isn't causation" with no structure |
| Estimand | States contrast, population, outcome, horizon and ITT vs TOT explicitly | Describes the analysis in code-level terms without a target quantity |
| Design | Proposes a design that genuinely identifies the effect (randomised holdout with application, or RD at the existing cutoff) and states its limits | "Run an A/B test" with no note on take-up, duration or pre-registration |
| Cost–benefit | Decision-theoretic reasoning tied to 40,000 increases/month and irreversibility | "More data is always better" |
| Fairness as causal | Treats disparity as a counterfactual question and questions the credit-history adjustment | Repeats the audit's numbers as if they settled fairness |

**Pitfalls.** Adjusting for the **mediator** (`utilisation`) and then reporting "no effect";
letting a p-value from a flawed pilot decide a policy; assuming take-up is random; generalising a
6-month promotion-period test to a 12-month outcome; reading "we controlled for X" as "it is causal";
switching off a whole system when the harm is confined to one stratum; treating fairness as a purely
statistical property rather than a counterfactual one.

**Discussion prompt.** Both leads are holding one number. What **single number** would you put on the
table to make the meeting productive — and what would you refuse to let either of them conclude before
it exists? (Expected: an RD-based estimate of the effect on the marginal customer, sliced by risk
decile.)

**Artifact for `C4`.** Your DAG, your estimand statement, the study protocol and the decision rule —
`C4` files these as the accuracy, robustness and post-market evidence.

---

### C4 · The 90-minute pre-deployment review ★ must-see
**stretch** · Analyze → Evaluate → Create · `hands_on`

**Anchored in:** Session 4 (Integration, Auditing & Regulation) · **Also requires:** Sessions 1–3 — the artifacts produced in `C1`–`C3` · **~30–45 min workshop**

**Q.** You have 90 minutes before Northline's pre-deployment review. Using the artifacts from `C1`–`C3`,
assemble the pack and defend a decision: (a) map the **four NIST AI RMF functions** to what CreditBoost
actually has, and mark the gaps; (b) list the **evidence pack** for a high-risk provider *and* deployer,
including the instruments already on file; (c) design **post-market monitoring** that gets refusal
disparity, letter quality and drift onto one page, with thresholds, owners and actions; (d) write the
**incident response** for the two recorded incidents — severity, who is notified, which clock; (e) state
your **go / no-go** with conditions, what you escalate to a human decision-maker, and the trigger for
**decommissioning**.

**A.**

**1. NIST AI RMF mapping — and the pattern in the gaps.**

| Function | What exists | What is missing | Who owns it |
|---|---|---|---|
| **GOVERN** | A named model owner; DPIA signed 2023 | A **risk-tolerance statement** (how large a disparity is acceptable, who signs); ownership of the letter prompt; a fairness policy; an escalation path with names; contractor oversight | Board / risk committee |
| **MAP** | Model card; feature list | Purpose and context **including the LLM layer**; affected-persons analysis; the disparity mapped to an identified risk with a treatment owner | Risk officer |
| **MEASURE** | Monthly AUC drift; one fairness audit; the 2024 pilot | Reproducible evaluation suite; group-level refusal tracking; letter golden set; robustness/adversarial tests; calibration **by segment** | Model risk / ML engineering |
| **MANAGE** | An incident log (unstructured) | A post-market monitoring plan; a treatment for the disparity; thresholds, owners and actions; contingency for scoring outages | Model owner + operations |

**The pattern matters more than the list.** There is real MAP and MEASURE output, and almost nothing in
**GOVERN** or **MANAGE**. That is exactly why a measured 1.7× disparity went nowhere for a year: no
threshold, no owner, no treatment — measurement without governance produces reports, not remediation.
Also state plainly: the RMF is a **loop**, not a one-off conformity exercise.

**2. The evidence pack — what a reviewer must be able to open.**

| Area | Instrument / obligation | Artifact CreditBoost must file |
|---|---|---|
| Risk management | **AI Act Art. 9** — iterative, documented process | Risk register with the disparity, the letter risk, the outage risk; owners; review dates |
| Data governance | **Art. 10** | Data sheet for the 240 features; bias examination; representativeness and provenance notes; legal basis for behavioural and postcode data |
| Technical documentation | **Art. 11 + Annex IV** | System description, architecture (both components), metrics, intended purpose, limitations |
| Logging | **Art. 12** | Decision logs **plus the mapping from each generated letter back to its attribute list**; retention and access policy; a replay test |
| Transparency | **Art. 13** | Instructions for use: known limitations, performance characteristics, the oversight model, the human-review route |
| Human oversight | **Art. 14** | The oversight design, **named** overseers, ability to override and stop, and evidence the ability is used |
| Accuracy / robustness / security | **Art. 15** | Calibration and error analysis by segment; robustness tests; the outage fail-safe behaviour |
| Post-market | **Art. 72 / 73** | Monitoring plan (below); serious-incident procedure and its clock |
| Deployer duties | **Art. 27 FRIA**, **Art. 86** | Fundamental-rights impact assessment; a *demonstrated* individual-explanation route with the case file for #4471 |
| Already on file | **GDPR** | DPIA (2023 — needs a refresh now that the letter layer and the disparity are known), Art. 22 safeguards, Art. 15/13/14 notices, records of processing, retention |

Two things that a reviewer will notice before anything else: the pack documents **one system** when
there are **two** (scoring model + letter generator, the latter with a contractor-owned prompt in a
notebook), and none of the artifacts carry dates, versions or signatures. **Unversioned, unsigned
documents are not evidence** — they are notes.

**3. Post-market monitoring on one page.** Every row needs a **threshold, an owner and an action** —
a metric without an action is decoration.

| Signal | Metric & window | Warning → Action | Owner |
|---|---|---|---|
| **Refusal disparity** | Refusal-rate ratio across postcode/proxy clusters; rolling 3-month window (small samples need pooling) | 1.3× → investigate; **1.5× or a CI excluding 1** → stop automatic refusals for the affected segment, human review, escalate to the risk committee | Model risk |
| **Calibration** | Predicted vs observed default, overall and top decile, by segment | Drift beyond tolerance → recalibrate before the next batch; segment failure → suspend that segment | ML engineering |
| **Model & data drift** | AUC drift (already live) + PSI on the top 20 features | PSI/AUC breach → retrain with a **documented** change and a fresh evaluation, not a silent monthly retrain | ML engineering |
| **Letter groundedness** | Share of letters whose stated reasons all appear in the attribute list; golden-set regression | **Anything below 100% is a P2** — block the send path, regenerate, log the incident | Model owner |
| **Letter tone & comprehension** | Tone-stability across adversarial inputs; readability vs the customer's language level; complaint rate mentioning letter content | Regression → freeze the prompt version, roll back | Model owner |
| **Human oversight** | Reviews requested, override rate, and what happened after overrides | Override rate ≈ 0 → oversight exists on paper only; investigate | Named overseer |
| **Operational** | Batch success; **behaviour on failure**; pre-send name/address match | Any fail-safe deviation kills the batch that night; a name mismatch is a P1 | Operations |

Two design rules that come straight out of the file: the dashboard must show **group-level refusal
rates**, not just AUC, and the system must **fail to human review, never to "no increase"** — a wrongly
granted limit costs money, a wrongfully refused customer is a rights event.

**4. Incident response — severity first, then the clock.** Procedure in six steps:
**detect → triage → contain → investigate → remediate → notify/close**, with a corrective-action log and
a regression test added to the golden set for each root cause.

| Incident | Severity | Why | Who is told, and when |
|---|---|---|---|
| **480 mis-addressed letters** | **P1** | Personal data disclosed to the wrong recipient — a confidentiality breach, not a formatting bug | DPO and head of risk immediately; **GDPR Art. 33 within 72 hours** if the risk to individuals is not negligible; customers informed in plain language; contain by adding a pre-send identity match and re-checking the affected batch |
| **3-day outage defaulting to "no increase"** | **P2** | Availability event with a fairness signature — a whole cohort was refused for an operational reason, not a credit one | Incident review immediately; risk committee at the next meeting; check whether any affected customer suffered harm (essential spending, declined transactions); verify against **Art. 73** serious-incident criteria; fix the fail-safe |

Note what makes this defensible rather than merely correct: **the file records no clock and no
severity scale at all**, which is itself a finding, and the fail-safe direction is the design decision
that a reviewer will ask about first.

**5. Go / no-go.**

**Conditional go for the scoring model. No-go for customer-facing letters until two things are fixed.**

| Condition | Evidence of resolution | Owner | By when |
|---|---|---|---|
| Letter generator out of the contractor notebook; prompt versioned and reviewed | Versioned prompt with an approved change process | Model owner | Before the next batch |
| Groundedness gate blocking any ungrounded reason | Gate in the send path + golden-set pass | ML engineering | Before the next batch |
| Post-market monitoring plan with the thresholds and owners above | Signed plan; the dashboard live | Risk officer | 30 days |
| The 1.7× disparity driven to a treatment or a **signed tolerance decision** | Risk-committee minute with the tolerance and its rationale | Risk committee | 60 days |
| Fail-safe direction changed: outage → human review | Design change + a test of the failure path | Operations | 30 days |
| The RD study launched, analysis pre-registered | Pre-registration + assignment logs | Head of risk | 60 days |
| A named human-oversight role with authority to override and stop | Named individual, documented authority, evidence of use | Risk committee | Immediate |

**What you escalate is not the technology — it is the residual risk acceptance.** Take the disparity
evidence, the *unknown* causal effect of the intervention, and the letter risk to a human
decision-maker, and ask for a **signature on the tolerance**, not a nod. The question you are handing
over is: *"which of these unresolved risks are we prepared to own, in writing, and for how long?"*

**Decommissioning triggers** (decide them now, not in a crisis): the disparity stop-threshold breached
in two consecutive monitoring windows with no accepted remediation; the RD study showing harm exceeding
benefit across the population, not just a stratum; a serious incident whose root cause cannot be
remediated; the named oversight role falling vacant; or a model whose behaviour can no longer be
explained to the customers it declines.

Finally: **record the decision, the conditions, the owners and the review date.** An audit pack with no
decision record is an unfinished pack — and the record is the artifact that makes anyone accountable.

**Rubric.**

| Dimension | Full marks | Partial credit |
|---|---|---|
| RMF mapping | Diagnoses the gap as **GOVERN/MANAGE** and connects it to why the measured disparity was never treated | Lists all four functions with artifacts, no diagnosis |
| Evidence pack | Covers **both components and both roles** (provider + deployer) across Art. 9–15, 27, 72/73 and Art. 86, plus the GDPR refresh; flags versioning and signature | A generic list of "model card + DPIA + logs" |
| Monitoring | Every signal has a threshold, an owner and an action, including group-level refusals and the letter gate | A dashboard wish list with no thresholds or names |
| Incident response | Severity scale, notification list, the **72-hour** clock, and the fail-safe direction | "We would fix the bug and apologise" |
| Decision | Conditional go with owners and dates, residual-risk acceptance escalated **for signature**, decommissioning triggers stated | "Go, but carefully"; escalates the technology instead of the risk |
| Synthesis | The `C1` clause table, the `C2` guardrails and the `C3` estimand all appear *inside* the pack | Treats this as a standalone compliance exercise disconnected from the first three questions |

**Pitfalls.** Producing a compliance checklist with no owners or dates; treating conformity assessment
as the finish line; using "the audit passed" as a mitigation; monitoring without thresholds or actions;
severity without a clock; escalating a tool decision instead of a risk tolerance; forgetting the second
system (the letter generator); forgetting that a customer can *ask* and must receive a reproducible
answer; and writing a pack that nobody signs.

**Discussion prompt.** Which single condition in your go/no-go list, left unmet for twelve months, turns
CreditBoost from *high-risk, managed* into *high-risk, unacceptable* — and who pays for it first, the
bank or the customer?

---

## How to run the four questions

| Format | Sequence | Notes |
|---|---|---|
| **Half-day workshop** | `C1` → `C2` → `C3` → `C4`, artifacts pinned to the wall as you go | `C4` works best with assigned roles (model owner, risk officer, auditor, customer advocate) and the facilitator as an adversarial reviewer |
| **Across the course** | One question at the end of each domain session; artifacts kept in a shared folder; `C4` as the closing workshop | The carry-forward is the point: `C4` is not answerable from memory of `C4` alone |
| **As an assessment** | `C1`–`C3` written, then `C4` as a 45-minute oral review defending the pack | Mark against the per-question rubrics; the synthesis row is the discriminator between a good and an excellent candidate |

## The whole-course checklist (what a full-mark answer keeps doing)

1. Separate **what the evidence shows** from **what the sentence claims** (`C1`).
2. Name the **audience** before writing the explanation (`C2`).
3. Ask **which rung** the question is on before choosing a method (`C3`).
4. Give every metric a **threshold, an owner and an action** (`C4`).
5. Never let compliance stand in for trustworthiness, attribution for causation, or a **report** for
   **remediation**.

## Coverage — the four questions against the four domains

| Domain | Question | Objective exercised |
|---|---|---|
| **Session 1** — Foundations | `C1` (and assumed by all) | Apply the trustworthiness properties to a real claim; classify under the EU AI Act; place work inside the NIST AI RMF |
| **Session 2** — Explainable AI | `C2` (with `C1`, `C3`) | Produce audience-appropriate explanations; state the limits of attribution; specify and evaluate a generative explanation layer |
| **Session 3** — Causal AI | `C3` (with `C2`, `C4`) | Move between association, intervention and counterfactual; build a DAG; write an estimand; design an identification strategy; judge when causal precision is worth its cost |
| **Session 4** — Integration, Auditing & Regulation | `C4` (with all) | Critique a system against NIST AI RMF and the EU AI Act; assemble an evidence pack; design post-market monitoring and incident response; defend a go / no-go decision |

Wider per-session question sets (71 questions, v1) are preserved — see
[`archive/2026-09-27_full_question_bank_v1/MANIFEST.md`](archive/2026-09-27_full_question_bank_v1/MANIFEST.md)
if you want the finer-grained drills behind any of these four.
