# Session 2 — Explainable AI Techniques

**Time:** 90–120 min · **Required** · **Concepts:** black-box vs interpretable models; post-hoc
methods (LIME, SHAP, PDP, counterfactuals); intrinsic interpretability (trees, rule-based,
monotonic models); evaluation of explanations (fidelity, stability, human-understandability).

Reference: Christoph Molnar, *Interpretable Machine Learning*.

Legend: `tier` ∈ **core** (everyone) / **stretch** (some) · `type` ∈ `pre_poll` · `in_class` ·
`quiz` · `discussion` · `essay` · `hands_on`

---

### S2-Q1 · Black-box or interpretable?
**core** · Understand → Apply · `pre_poll`

**Q.** Classify each as **intrinsically interpretable** or **black-box**: logistic regression;
depth-3 decision tree; gradient-boosted trees (XGBoost); 12-layer CNN; an if–then rule list;
1-nearest-neighbour. Which would you be comfortable using to justify an individual loan decision, and
why?

**A.** Intrinsically interpretable: logistic regression (weights are log-odds per unit), depth-3
tree (readable paths), rule list (literally a list). Black-box: XGBoost (thousands of trees),
CNN (learned filters).

1-NN is the interesting case: it has **no global model at all**, but it is *locally* explainable
because the single neighbour *is* the explanation ("you were treated like this applicant"). That is
case-based reasoning, not mechanism.

A depth-3 tree is readable — but readably *wrong* if it is a poor fit. Interpretability buys you the
ability to see the reasoning; it says nothing about whether the reasoning is good.

---

### S2-Q2 · Reading SHAP values in plain language ★ must-see
**core** · Understand → Apply · `in_class`

**Q.** A credit model outputs **P(default) = 0.72**. SHAP reports `base_value = 0.18`,
`income = −0.31`, `debt_ratio = +0.45`, `age = +0.02`. Explain this to the applicant in plain
language — and state which **units** your numbers are in.

**A.** SHAP values are **additive attributions relative to a reference**, so
`prediction = base_value + Σ SHAP values` (0.18 − 0.31 + 0.45 + 0.02 ≈ 0.34; the remainder comes
from the other features). Each value answers: *how much did this feature push the output away from
the average prediction of the reference population, and in which direction?*

Plain language: *"Compared with a typical applicant, your debt-to-income ratio was the biggest factor
raising your estimated risk, while your income level pulled it back down. Your age made almost no
difference."*

**Units are not optional.** For boosted trees, SHAP values are typically in **log-odds** (the raw
margin), not probability. Saying "+0.45" without units is uninterpretable, and you cannot linearly
add log-odds to a probability.

**Pitfalls.** The forbidden sentence: *"if you lowered your debt ratio, your risk would fall by
0.45."* Attribution is **not** intervention — see `S2-Q6`.

---

### S2-Q3 · Why does SHAP need a background dataset?
**core** · Understand · `quiz`

**Q.** SHAP requires a background/reference dataset. What does it define, and what happens if you
change it?

**A.** The Shapley value is defined **relative to a baseline**: the expected model output
`E[f(X)]` over the background distribution (shown as `base_value`). It answers "how much does this
feature move *this* prediction away from the average prediction for the reference set?"

Change the background and the attributions change — often substantially. This is why a SHAP number
without a stated reference population is scientifically incomplete.

The Shapley framework gives desirable properties: **efficiency** (attributions sum exactly to
prediction − base), **symmetry**, **dummy** (a feature that never affects output gets 0) and
**additivity**. Cost: exact computation is exponential in the number of features, so KernelSHAP
samples and Tabular/TreeSHAP use structure — a larger background is more accurate and slower.

---

### S2-Q4 · "Most important feature = 0.42"
**core** · Analyze · `quiz`

**Q.** A colleague reports: *"For the RandomForest, `debt_ratio` is the most important feature with
importance 0.42"* — read off `feature_importances_`. Give two reasons this can mislead.

**A.** (1) **Impurity (Gini) importance is biased toward high-cardinality and continuous features**:
it sums impurity decreases over splits, and continuous features simply get more split opportunities,
so they inflate. (2) It is computed **on the training data**, so it *rewards overfitting* — a noisy
identifier-like column that the tree memorised can look highly "important".

Better options: **permutation importance on held-out data** (with the caveat that it too is
misleading under correlated features, and it's measured against a specific metric), or SHAP.
And note the deeper gap: importance gives you **no direction, no magnitude, and no interaction
information**. "0.42" does not mean "42% of the decision was debt ratio".

---

### S2-Q5 · LIME vs SHAP
**core** · Analyze · `quiz`

**Q.** What does each method actually approximate, and what is each one's characteristic failure mode?

**A.** **LIME** fits a *local surrogate*: sample points around the instance, weight them by proximity,
discretise features, and fit a sparse linear model. Model-agnostic and fast, and the result reads
like a familiar linear model. Failure modes: the **neighbourhood is an arbitrary choice**, sampling
makes it **non-deterministic** (re-run and you can get a different top feature for the *same*
instance), and in high dimensions or with correlated features the perturbations land **off the data
manifold**, so the surrogate is fit on unrealistic points.

**SHAP** is a *game-theoretic additive attribution* with consistency guarantees **relative to a
chosen background**. TreeSHAP is exact for tree ensembles; KernelSHAP is a sampled approximation and
slow. Failure modes: with **correlated features the credit is split arbitrarily** between them (both
look important, neither is fully responsible), and it explains the **model, not reality** — a faithful
explanation of a wrong model is still a wrong explanation.

Both are **post-hoc**: they approximate the model's behaviour and can disagree with each other.
Disagreement is itself informative and worth showing students.

---

### S2-Q6 · The correlation trap in SHAP ★ must-see
**core** · Analyze → Evaluate · `in_class`

**Q.** SHAP flags `daily_sunscreen_use` as a strong **positive** predictor of `sunburn`. Your
colleague concludes: *"so we should advise people to stop using sunscreen."* What is wrong with this
reasoning, and what would you need before making the claim?

**A.** Two distinct errors stacked:

1. **Interpretation error** — SHAP attributes the *model's* output. You have learned what the model
   does, not what the world does.
2. **Causal error** — the model has learned a *correlational* pattern. The obvious explanation is
   **confounding by exposure**: people who use sunscreen are precisely the people spending long hours
   outdoors (beach, hiking, sports). Sunscreen use is largely a **marker of sun exposure**, and
   exposure causes burns. Remove sun exposure from the model and sunscreen looks harmful.

What you would need to make the causal claim: state the assumptions as a **DAG** (exposure, outcome,
confounders such as outdoor hours, skin type, latitude/season); **adjust** for the confounders via the
backdoor criterion, or find an **intervention** (RCT, natural experiment, policy change); then run
identification and estimation (DoWhy) and **refute** the estimate (placebo treatment, random common
cause, subset validation). Crucially: causal claims rest on **assumptions that data alone cannot
verify** — which is exactly why this question is the bridge into Session 3.

**Discussion prompt.** *"How might causal insights change this deployment decision compared with the
correlational one?"*

---

### S2-Q7 · Fidelity vs stability
**core** · Understand → Analyze · `quiz`

**Q.** Define **fidelity** and **stability** for an explanation. Can an explanation have high fidelity
but low stability — and why does that matter to a regulator?

**A.** **Fidelity** = how faithfully the explanation represents the model: for a surrogate, how well
it reproduces the black box locally (e.g. the local R²); for an additive attribution, whether the
values sum to the prediction.

**Stability** (robustness) = the explanation should not change drastically for a semantically
irrelevant change in the input — a perturbation below measurement precision, or resampling LIME's
neighbourhood.

**Yes, and this is the common case.** A local surrogate can fit its neighbourhood beautifully while
two near-identical applicants receive **different top reasons for rejection**, because the surrogate
was refit on a different random sample.

Why a regulator cares: the stated reason for a decision becomes **arbitrary** and **not reproducible**,
which undermines appeal rights, accountability and audit. It also creates a **fairness** problem —
similar people get different explanations for the same outcome. Molnar's axis list also includes
**compactness** and **human-understandability**; you should always be able to say which axis you are
optimising.

---

### S2-Q8 · Global vs local explanations
**core** · Understand → Apply · `in_class`

**Q.** Define a **global surrogate**. Which would you use for (a) a regulator auditing the model's
overall behaviour, and (b) telling one customer why their application was declined?

**A.** A **global surrogate** is an interpretable model (often a shallow tree or sparse linear model)
trained to **mimic the black box's predictions** across the whole input space. Its honesty depends
entirely on reporting the **fidelity** to the black box — an undocumented surrogate is just a
different, worse model presented as an explanation.

(a) **Regulator / overall behaviour:** global and aggregate evidence — a surrogate for an overview,
plus **disaggregated performance metrics per subgroup**, drift monitoring and documentation. A
surrogate alone is not audit-grade.
(b) **Individual customer:** a **local** explanation — SHAP/LIME attribution or, better for a
non-technical person, a **counterfactual** ("had your debt ratio been under 0.35…").

In practice you need both, plus a case-audit path where a human can inspect the model's behaviour for
an appealed decision.

---

### S2-Q9 · Choosing intrinsic interpretability on purpose
**stretch** · Evaluate → Create · `in_class`

**Q.** When would you deliberately choose an **intrinsically interpretable** model even at some cost
in accuracy — and how would you argue it to a product owner?

**A.** Choose intrinsic when: the decision is high-stakes or regulated; explanations must be
**guaranteed rather than approximated**; decisions will be **appealed at scale** so per-case reasons
must be cheap and consistent; you need **monotonicity** as a legal/domain constraint; or the data is
small, tabular and relatively simple — where interpretable models (EBMs/GAMs, shallow trees, rule
lists) are often **close to** gradient-boosted performance.

The argument to a product owner is quantitative, not philosophical: **measure the accuracy gap on
your own data first** (on tabular problems it is frequently small), then weigh it against the costs on
the other side — compliance and audit burden, cost of unexplainable errors, appeal-handling cost,
trust and adoption. A strong proposal is a **hybrid**: an interpretable model as the explainable
baseline, with the black box as a challenger behind guardrails.

**Pitfalls.** Arguing for interpretability by principle alone, with no measured gap, invites dismissal.

---

### S2-Q10 · Partial dependence plots and their failure mode
**stretch** · Analyze · `quiz`

**Q.** What does a **partial dependence plot (PDP)** show, what is its known failure mode, and what
are the alternatives?

**A.** A PDP shows the **average model prediction** as one feature varies, marginalising over the
others. Its core assumption is that **features are independent** — so it can evaluate impossible
combinations (e.g. `age = 25` with `years_of_experience = 40`) and produce a curve describing
predictions the model will never actually be asked for. With correlated features the PDP is
**misleading**, not just imprecise.

Alternatives: **ALE plots** (accumulated local effects, which use local differences and avoid the
off-manifold problem), **ICE curves** (one line per instance, revealing that the "average" effect may
be shared by nobody), or fitting separate PDPs per subgroup.

Also remember PDPs are **averages**: by construction they hide heterogeneity and interactions.
"Average effect" is a summary, and a summary can be an artefact.

---

### S2-Q11 · Monotonic constraints
**stretch** · Analyze → Evaluate · `quiz`

**Q.** Gradient boosting libraries let you set **monotonic constraints** per feature. How does this
help trustworthiness, and what does it cost?

**A.** A monotonic constraint encodes a **domain or legal prior** — "higher income must never increase
predicted default risk", "more study hours must never reduce predicted score". Benefits: it prevents
implausible non-monotone behaviour; it makes legal and regulatory review tractable (the direction of
effect is guaranteed); and it tends to **improve behaviour outside the training distribution**,
because extrapolation can no longer bend the wrong way.

Costs: if the assumption is wrong it **reduces accuracy** and can hide genuine non-monotonicity (very
high income might plausibly raise risk via leverage). Constraints are per-feature, so they do not
capture **multivariate** monotonicity or interactions. And critically: a monotonic model is **still a
black box** — monotonicity is a guarantee about direction, not an explanation of the decision.

---

### S2-Q12 · Counterfactual explanations
**stretch** · Analyze → Evaluate · `quiz`

**Q.** *"Your loan was declined; had your debt-to-income ratio been below 0.35 you would have been
approved."* Give one strength and three problems with this kind of explanation.

**A.** **Strength:** it is **actionable** — it tells the person what to change, in their own terms, and
it maps naturally onto appeal conversations and the regulatory expectation of *meaningful
information* ("actionable recourse").

**Problems:**

1. **Multiplicity.** There are usually **many** valid counterfactuals, and the single one delivered may
   be arbitrary. Deliver **several, diverse** ones — and beware the Rashomon effect: an equally good
   alternative model would give different advice.
2. **Feasibility and ethics.** Suggested changes may be impossible or protected (age, medical history,
   disability), and at scale the advice degenerates into "be richer". This creates **recourse
   disparity**: marginalised groups may need far larger changes for the same outcome.
3. **It is not a causal promise.** The counterfactual describes a different *model output*, not the
   real-world effect of changing your circumstances. If the threshold, the data distribution or the
   model changes, the promise can simply be false. Counterfactuals can also be **gamed** and can leak
   information about the training data.

---

### S2-Q13 · Designing an evaluation study for explanations
**stretch** · Evaluate → Create · `essay`

**Q.** Pick one evaluation axis — **fidelity**, **stability**, **compactness** or
**human-understandability** — and design a study to evaluate an explanation method against it. What
are the traps?

**A.** With **human-understandability**: a randomised controlled experiment in which participants
solve a task with help from explanation type **A**, type **B**, or **none**. Measure **decision
accuracy with the model**, **appropriate reliance** (not merely trust), and a **comprehension check** —
not satisfaction.

Traps to name: measuring **satisfaction instead of comprehension**; recruiting ML experts so the result
does not transfer to real users; using too few instances or a single dataset; no filler/placebo task;
novelty effects; teaching to the test. Above all, **do not treat "trust went up" as success** —
explanations can increase *inappropriate* reliance ("explanation as a seal of approval"), so the target
is **calibrated** trust: trust more when the model is right, less when it is wrong.

If you chose **fidelity** instead, the classic trap is measuring it on the same data used to fit the
surrogate (circular), or never reporting it alongside the surrogate at all.

---

### S2-Q14 · Peer debugging prompt
**core** · Analyze → Evaluate · `discussion`

**Q.** *"Share a case where an XAI explanation surprised you or seemed misleading. Why did it happen?"*

**A.** Open-ended — the facilitator's job is to route each story to its mechanism. Common sources:
**correlated features splitting credit** between two variables; an "important" feature that was really
a **data leak** (an ID-like column, a post-outcome field); a **PDP describing impossible inputs**;
SHAP run on a badly **calibrated** model, so the attributions look meaningful while the probabilities
do not; and explaining a model trained on a **shifted** distribution.

Good answers end with *"what I would check next time"* — that is the learning habit being built.

---

### S2-Q15 · Try first, understand later (pre-attempt assignment)
**stretch** · Apply → Analyze · `hands_on`

**Q.** *Do this **before** the XAI lecture.* Train a black-box model (XGBoost or a small neural net) on
a tabular dataset. Explain **one** prediction using only (a) **feature importance** and (b) a
**partial dependence plot**. Then answer: what did you conclude — and why might that conclusion be
misleading about **causality**?

**A.** The intended experience is productive frustration. Students typically conclude "feature X drives
the outcome", then discover three things in the lecture: importance gives **no direction** (and is
biased toward continuous features), the PDP assumed **feature independence**, and neither method
supports a causal reading.

The reflection *is* the assessment: does the student reach *"this tells me about the model, and the
model learned correlations — so I cannot yet say what causes what"*? Ask them to name **one confounder**
their dataset could plausibly contain.

**Facilitator note.** Revisit this question at the end of Session 3 — students should now answer it
differently.



