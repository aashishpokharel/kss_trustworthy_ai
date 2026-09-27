# Session 3 — Causal AI for Deeper Trust

> ⚠️ **Optional module.** *Drop this session if causation was already covered in an earlier class.*
> `S3-Q2`, `S3-Q5` and `S3-Q8` are the minimum viable subset if you only have 30 minutes.

**Time:** 90–120 min · **Concepts:** the ladder of causation (association, intervention,
counterfactual); structural causal models and DAGs; confounding, colliders, mediation; `do`-calculus
and DoWhy; correlation → actionable insight; why causal explanations are more reliable.

Reference: Matheus Facure, *Causal Inference for the Brave and True*; DoWhy tutorials; Pearl's
ladder of causation.

Legend: `tier` ∈ **core** (everyone) / **stretch** (some) · `type` ∈ `pre_poll` · `in_class` ·
`quiz` · `discussion` · `essay` · `hands_on`

---

### S3-Q1 · The three rungs
**core** · Understand → Analyze · `pre_poll`

**Q.** Label each question as **association** (rung 1), **intervention** (rung 2) or
**counterfactual** (rung 3):

| # | Question | Rung? |
|---|---|---|
| a | Do people who take the drug tend to recover more often? | ? |
| b | If we gave the drug to everyone, would recovery improve? | ? |
| c | Did *this* patient recover because of the drug? | ? |

**A.** (a) association — `P(Y | X)`, a fact about the data you already have. (b) intervention —
`P(Y | do(X))`, a claim about a world you have to *change* or *assume* your way into.
(c) counterfactual — a claim about a specific unit in a world that did not happen. It needs the
richest assumptions of the three, which is why rung 3 is hardest — and why it is exactly what courts
and "what-if" fairness questions ask for.

---

### S3-Q2 · Ice cream and drowning ★ must-see
**core** · Analyze · `in_class`

**Q.** Ice-cream sales correlate strongly with drowning deaths. Does ice cream cause drowning?
Identify the confounder, write the DAG, and say what adjusting for it buys you.

**A.** **No.** The confounder is **temperature/season** (with swimming activity downstream):

```
Temperature ──▶ IceCreamSales
     │
     └────────▶ Swimming ──▶ Drowning
```

The association between ice cream and drowning travels along the **backdoor path**
`IceCreamSales ◀── Temperature ──▶ … ──▶ Drowning`. Adjusting for temperature (backdoor adjustment)
**blocks** that path, and the remaining ice-cream association should collapse to roughly zero.

Two caveats worth making explicit: adjustment only works if you actually **measure** the confounder
well — residual or unmeasured confounding remains; and if you want the *total* effect you must not
adjust for mediators such as swimming.

**Pitfall.** "Control for all available variables" is not a safe default — adjusting for **mediators**
and **colliders** can create bias that was not there.

---

### S3-Q3 · Simpson's paradox
**core** · Analyze · `quiz`

**Q.** A treatment looks **better in every subgroup** yet **worse overall**. Explain how that is
possible and give an example.

**A.** Because the **aggregate is a mixture weighted by subgroup composition**, and subgroups can have
very different baseline risk and very different treatment allocation. Classic example: a treatment
looks worse overall because it is given mostly to the *severe* cases, even though it beats the
alternative within both the mild and the severe subgroups.

Lesson: the aggregate contrast and the subgroup contrast answer **different questions**, and
aggregation can even reverse the sign of the answer. This is why a headline metric can mislead even
when every per-segment metric is fine. Stratify or adjust deliberately, and state which contrast the
decision actually requires.

---

### S3-Q4 · Colliders and the danger of adjusting
**core** · Analyze · `quiz`

**Q.** What is a **collider**, why does conditioning on one create a *spurious* association, and what
is a concrete example?

**A.** A collider is a variable with **two or more arrows pointing into it**: `A → C ← B`. A confounder
creates a backdoor path you must **block**; a collider *blocks* a path by default — and
**conditioning on it** (stratifying, matching, selecting, or sampling the dataset that way) **opens
that path** and induces an association between `A` and `B` that does not exist in the population.

Examples: **Berkson's paradox** — among hospitalised patients only, two unrelated diseases appear
negatively associated, because hospitalisation is caused by *either*. Or `talent → celebrity ←
beauty`: among celebrities, talent and beauty look negatively correlated. Everyday version: if you
only keep successful experiments in a dataset, you can manufacture a spurious relationship between
"success" and unrelated factors.

**Pitfall.** "We adjusted for every variable we had" is a classic way to *introduce* bias. Derive that
a variable is a confounder before adjusting for it. And selection bias in the **dataset itself** is
usually a collider problem hiding in plain sight.

---

### S3-Q5 · P(y|x) vs P(y|do(x)) for a product manager
**core** · Understand → Apply · `in_class`

**Q.** Explain the difference between `P(y | x)` and `P(y | do(x))` in words a product manager would
understand, and explain why it matters for deployment.

**A.** `P(y | x)` — *"among the people we happened to observe with x, what did y look like?"* An
observational comparison between groups that **chose themselves**.
`P(y | do(x))` — *"if we intervened and set x for everyone, what would happen to y?"* An intervention.

Product translation:

- Rung 1: *"Users who use feature X churn less."*
- Rung 2: *"If we push feature X at all users, will churn go down?"*

These come apart whenever the groups differ for other reasons — active users are precisely the ones
who use features, so feature use is largely a **marker of engagement**, not a cause of retention.

Why deployment cares: a model trained to predict `y` from `x` is a **rung-1 machine**. It works while
the distribution is stable, but the moment you **intervene** on a feature (a promotion, a pricing
change, a nudge campaign) you have changed the data-generating process the model was fitted to, and
the association it learned is no longer the association that holds.

**Pitfall.** Presenting `P(y|x)` numbers as if they were `P(y|do(x))` — the most common analytics error
that reaches executive decks.

---

### S3-Q6 · Adjust for what? (a small DAG)
**core** · Apply → Analyze · `in_class`

**Q.** Consider `exercise → weight → cholesterol`, plus `age → exercise` and `age → cholesterol`.
Which variables must you adjust for to estimate the **total effect of exercise on cholesterol**? Which
must you **not** adjust for, and why?

**A.** **Adjust for `age`** — it is a confounder (a common cause of exercise and cholesterol), so it
opens a backdoor path that must be blocked.

**Do not adjust for `weight`** if your question is the **total** effect: weight is a **mediator** on
the causal path `exercise → weight → cholesterol`. Adjusting for it blocks part of the very effect you
are trying to measure, giving you a *direct* effect that is smaller and answers a different question.

Rule of thumb: adjust for **common causes** of treatment and outcome (confounders). Do not adjust for
**mediators**, **colliders**, or **descendants of the outcome** — unless you deliberately want a
direct-effect or path-specific quantity, in which case say so explicitly.

**Pitfall.** Predictive-modelling habits ("keep whatever is predictive") are the wrong instinct here.
What matters is **structural position in the graph**, not predictive power.

---

### S3-Q7 · DoWhy's four steps
**core** · Understand → Apply · `quiz`

**Q.** Name and explain the four steps of a DoWhy analysis, and say why the last one matters so much.

**A.** 1. **Model** — write your assumptions down as an explicit causal graph (this is the step that
cannot be automated away).
2. **Identify** — express the target quantity purely in terms of the **observed** data
(backdoor / instrumental variable / frontdoor): do-calculus, not estimation.
3. **Estimate** — compute the estimand with a concrete estimator: propensity-score weighting, matching,
regression adjustment, doubly robust methods, or IV.
4. **Refute** — stress-test the estimate: a **placebo treatment** should produce ≈ 0 effect; a
**random common cause** should not move the estimate much; a **data-subset** run should stay stable;
adding a random confounder should not shift it.

Refutation matters because **identification rests on assumptions the data cannot verify**. The
refutation step is a deliberate attempt to *falsify* your own conclusion. "The number came out at 0.34"
is not evidence; surviving refutation is *weak* evidence. If a refutation fails, report that honestly —
a refuted estimate that you still ship is worse than no estimate.

---

### S3-Q8 · Why causal beats correlational for deployment ★ must-see
**core** · Analyze → Evaluate · `in_class`

**Q.** Why is a causal explanation "more trustworthy" than a purely correlational one for deployment?
Give two mechanisms.

**A.** **Invariance / stability.** Causal relationships tend to be **invariant across environments**,
whereas spurious correlations are accidents of the dataset you happened to collect. A model keyed on a
stable mechanism keeps working when the distribution shifts; a model keyed on a proxy breaks the moment
the proxy relationship changes.

**Actionability.** Deployment decisions *are* interventions — a pricing change, an outreach campaign, a
policy rule. Only rung-2 quantities tell you what happens when you **do** something. Rung-1
associations tell you what happened to people who were already different.

Two supporting mechanisms worth crediting: causal structure resists **spurious-feature** failure (to
the extent the structure is right), and causal grounding enables genuine **counterfactual**
accountability — *"what would have happened if we had decided differently?"* — which is what
regulators and appeals actually ask for, and what fairness notions like equal opportunity implicitly
assume.

**Discussion prompt.** *"How might causal insights change deployment decisions compared with
correlational ones?"*

---

### S3-Q9 · Run a DoWhy analysis end to end
**stretch** · Apply → Create · `hands_on`

**Q.** On a small dataset of your choice: state the causal graph, identify the estimand, estimate the
effect with **two** different methods, and run at least two **refutations**. Report where the methods
agree and disagree — and what evidence would change your conclusion.

**A.** A complete submission contains, in order: (1) the graph as code or a diagram, with **justification
per edge**; (2) the estimand and *why* it is identified (backdoor/IV/frontdoor); (3) two estimates with
confidence intervals — e.g. propensity-score weighting vs. doubly robust — and an explicit statement of
whether the intervals overlap; (4) refutation results (placebo, random common cause, subset) with
numbers, not adjectives; (5) a **sensitivity** statement: how much unmeasured confounding would be
needed to overturn the result?

**Assessment focus.** The graph's justification and the honesty of the sensitivity analysis — *not* the
point estimate. A student who reports "my estimate is fragile to unmeasured confounding" has produced
better work than one who reports a confident number with no refutation.

---

### S3-Q10 · "Drug A patients died more often"
**stretch** · Analyze → Evaluate · `essay`

**Q.** A hospital dataset shows: *patients given drug A died more often.* Is this causal? What could
explain it, and how would you design the analysis?

**A.** **Not causal as stated.** The primary suspect is **confounding by indication**: drug A is
prescribed *because* the patients are sicker, so severity is a common cause of both treatment and death
— and sicker patients die more. Other real candidates: **immortal time bias** (survival required to
receive the treatment), **survivorship/selection** (collider effects from who is in the dataset), and
simple measurement error in severity.

Design sketch: write the DAG including indication/severity; emulate a **target trial** (eligibility,
treatment strategies, follow-up window, outcome, causal contrast) so the comparison is well defined;
adjust for severity via **propensity scores** or a doubly robust estimator; consider an **instrument**
such as physician prescribing preference; run **refutations** and a **sensitivity analysis** for
unmeasured confounding; and report the answer with uncertainty.

**Pitfalls.** Believing adjustment fully solves it. Residual confounding is the honest limit — and this
is exactly the case where a confident causal claim from observational data can cost lives.

---

### S3-Q11 · Mediator vs confounder
**stretch** · Analyze · `quiz`

**Q.** What is the difference between a **mediator** and a **confounder**, and how does it change which
variables you adjust for?

**A.** A **confounder** is a *common cause* of treatment and outcome (`X ← C → Y`): fail to adjust and
your effect estimate is biased by the backdoor path. A **mediator** lies *on the causal path*
(`X → M → Y`): adjusting for it **blocks part of the effect you are trying to measure**, so it turns a
total-effect question into a direct-effect question.

The test is structural, not statistical: **does the variable lie on a directed path from treatment to
outcome?** If yes, it is a candidate mediator; if it causes both, it is a confounder.

Consequences: "adjust for everything" is wrong in both directions — it leaves biases in *and*
introduces new ones (through mediators and colliders). If you report a direct effect, say so, and
explain that interventions which act through the mediator will not be captured by it.

---

### S3-Q12 · When causal AI is not worth it
**stretch** · Evaluate · `discussion`

**Q.** Give honest limits: when is causal analysis *not* worth the trouble?

**A.** When you only need prediction inside a **stable** distribution and nobody will intervene —
a recommender ranking items under an unchanged policy is mostly a rung-1 problem. When the assumptions
**cannot be defended** and no experiment or instrument exists, you are buying false confidence. When
**sensitivity analysis shows the conclusion flips** under plausible unmeasured confounding. When the
data is too small or the confounders are badly **mismeasured** (adjusting for a noisy proxy can be
worse than not adjusting). And when there is no domain expert available to defend the graph — causal
work is a *sociotechnical* exercise, not an algorithm you can drop in.

Also worth saying plainly: **automated causal discovery is oversold**. Algorithms can suggest candidate
structures (and often only up to Markov equivalence), but the justification of edges is human, domain
work. Owning that limit is part of trustworthy practice.

---

### S3-Q13 · Why rung 2 and 3 need more than data
**stretch** · Analyze · `quiz`

**Q.** Why can't interventional and counterfactual questions be answered from observational data alone,
without assumptions?

**A.** Because the same observational distribution is compatible with **many different causal
structures** (Markov equivalence) and with many different interventional regimes. The data tells you
what happened under the regime that *actually ran*; it cannot tell you what would happen under a regime
that never ran, unless you **assume** a structure and a set of mechanisms — and assume which parts stay
invariant when you intervene.

Pearl's slogan: **"no causes in, no causes out."** Assumptions must enter somewhere — a graph, an
instrument, an experiment, or a domain invariance claim.

A useful asymmetry to leave students with: a **randomised experiment** buys you rung 2 with far weaker
assumptions (randomisation blocks backdoor paths by design), but it still does **not** answer rung 3 for
a specific individual without a model — and it may be unethical, impossible, or too slow. That is the
gap causal graphs and observational estimators are trying to fill.


