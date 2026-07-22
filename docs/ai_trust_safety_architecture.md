# Trust, Safety & Governance Architecture for LLM/Agent Systems
### A build spec for an AI coding agent

**Purpose of this document:** This is a machine-actionable architecture and execution plan. It is written so that a coding agent (Claude Code, Cursor, etc.) can read it top to bottom and build the system incrementally, component by component, without needing the human to re-explain intent. Each component has: objective → where it sits in the pipeline → concrete libraries → what "manual guardrails" means here → the actual build tasks → how to test it.

---

## 1. System-Level Architecture

Think of this as a **pipeline with checkpoints**, not a single filter. Every request and every response passes through discrete, independently-testable stages. No single component is "the" safety layer — safety is defense-in-depth.

```
                         ┌─────────────────────────────────────────────┐
                         │              GOVERNANCE PLANE                │
                         │  (policy registry, audit log, HITL console,  │
                         │   metrics dashboard, incident review)        │
                         └───────────────▲───────────────▲──────────────┘
                                          │               │
 User ──▶ [1] GATEWAY / AUTH ──▶ [2] INPUT GUARDRAILS ──▶ [3] ORCHESTRATOR ──▶ [4] LLM CORE ──▶ [5] OUTPUT GUARDRAILS ──▶ [6] ACTION/TOOL LAYER ──▶ Response
                                          │                                        │                       │
                                          ▼                                        ▼                       ▼
                                   Injection/PII/Bias                       Alignment/Refusal      Human-in/on/out-loop
                                   detectors, allow/deny                    logic, system prompt    gate for high-risk
                                   lists, rate limits                       hardening               tool calls
```

**Stages, in order:**

1. **Gateway/Auth** — identity, rate limiting, request provenance tagging (who/what is the caller: human, another agent, a webhook?).
2. **Input Guardrails** — prompt injection detection, PII detection, sensitive-topic classification, jailbreak detection, input schema validation.
3. **Orchestrator** — decides tool routing, retrieval, and whether human approval is required before proceeding (this is where "human-in/on-loop" gates live).
4. **LLM Core** — the model call itself, with a hardened system prompt, constrained decoding where applicable, and provenance-tagged context (trusted vs. untrusted content clearly demarcated).
5. **Output Guardrails** — hallucination/groundedness checks, PII leakage checks, bias/toxicity scoring, refusal-quality checks, output schema validation.
6. **Action/Tool Layer** — the actual side-effecting actions (send email, run code, call an API); this is where autonomy control (human-in/on/out-of-loop) is enforced with the most force, because this is where real-world harm happens.
7. **Governance Plane** — cuts across everything: append-only audit log, policy versioning, dashboards, red-team/eval harness, incident review workflow.

This structure maps directly to a repo layout (see §12).

---

## 2. Prompt Injection Prevention

**Objective:** Prevent untrusted content (user input, retrieved documents, tool outputs, web pages) from being interpreted as instructions that override the system's actual instructions.

**Where it sits:** Input Guardrails (stage 2) for direct injection; Orchestrator + LLM Core (stage 3–4) for *indirect* injection (malicious content inside retrieved documents, emails, web pages, tool results).

**Two-part defense — libraries + manual guardrails:**

**A. Library layer (fast, first-pass filters):**
- `LLM Guard` (protectai) — prompt-injection scanner (Rebuff-derived heuristics + ML classifier), runs pre-call.
- `NeMo Guardrails` — Colang-based dialogue rails to constrain what topics/actions a conversation can reach, and to intercept before the LLM sees a flagged input.
- `Llama Guard` / `Granite Guardian` — auxiliary classifier models, called as a cheap pre-filter before the main model.
- `Garak` / `PyRIT` — not runtime tools, but use these in CI as adversarial probe suites to *test* the pipeline (see §13).

**B. Manual/architectural guardrails (the part libraries can't give you):**
- **Privilege separation of instructions.** Structurally separate "system instructions" (trusted, from the app developer) from "content" (untrusted, from users/documents/tools). Never concatenate untrusted text into the same channel as system instructions — use explicit delimiters/roles and, where the model API supports it, distinct message roles.
- **Provenance tagging.** Every piece of context injected into the prompt (RAG chunk, tool result, email body) gets a machine-readable tag: `{source: "untrusted_web", trust: 0}`. The system prompt explicitly instructs the model: content tagged untrusted is *data to reason about*, never *instructions to follow*.
- **Instruction re-assertion.** Before/after untrusted content blocks, re-state the actual task and forbidden actions ("sandwiching").
- **Canary tokens.** Insert a unique token in the system prompt; if it ever appears in output or in the model's stated "reasoning" about following new instructions, that's a strong injection signal — log and block.
- **Least-privilege tool binding.** Even if injection succeeds in influencing the model, the *tool layer* should refuse actions outside the current task's declared scope (this is the real backstop — see §9).
- **Two-pass verification for high-risk outputs.** For any action with side effects, run a second, isolated LLM call ("is this action consistent with the user's original, stated goal?") that never sees the untrusted content directly.

**Agent build tasks:**
1. Stand up `LLM Guard` as a pre-call middleware function; wire input text through `scan_prompt()`.
2. Implement a `ContextBlock` data structure with `{content, source, trust_level}` fields; refactor prompt assembly to use it instead of raw string concatenation.
3. Write the system-prompt template with explicit untrusted-content handling rules and canary token injection/verification.
4. Add a `PolicyGate` before every tool call that checks the requested action against a declared task scope.
5. Add unit tests using known injection payload corpora (e.g., from Garak) plus 10–20 hand-written indirect-injection cases (malicious RAG doc, malicious email in an inbox-agent scenario).

---

## 3. Vulnerability Identification (Red-Teaming / Security Testing)

**Objective:** Systematically find weaknesses before adversaries do — this is a testing discipline, not a runtime filter.

**Tools:**
- `NVIDIA Garak` — modular probe library for jailbreaks, prompt injection, encoding attacks, data leakage probes.
- `PyRIT` (Microsoft) — adversarial test orchestration, good for multi-turn attack chains.
- `DeepTeam` — LLM red-teaming framework with pre-built vulnerability categories (bias, PII leakage, toxicity, misinformation).
- `Promptfoo` — regression testing for prompts/guardrails in CI (eval-as-code).

**Manual layer:**
- A living **threat model** document per agent/use case: what tools does this agent have, what's the worst action it could take, what's the blast radius.
- **Red-team playbooks** mapped to MITRE ATLAS tactics for AI systems (extraction, evasion, poisoning, prompt injection).
- **Bug-bounty-style internal reporting channel** feeding into the governance plane's incident log.

**Agent build tasks:**
1. Create `/redteam/` directory with Garak/PyRIT configs targeting the deployed endpoints.
2. Build a CI job that runs the adversarial suite on every prompt/guardrail-config change and fails the build on regression (tie into Promptfoo eval sets).
3. Write a threat-model template and fill one out per agent tool the system exposes.
4. Log every red-team finding into the audit store with severity + remediation status.

---

## 4. Data Privacy — What to Provide / What Not to Provide (Governance)

**Objective:** Define, enforce, and audit what data is allowed to enter the model's context window, what's allowed to be retained, and what's allowed to leave the system.

**Framework — classify everything crossing a boundary into a tier:**

| Tier | Examples | Rule |
|---|---|---|
| Public | Marketing copy, public docs | Freely usable, no restrictions |
| Internal | Internal wikis, non-sensitive business data | Usable in-context, not in logs sent to third parties |
| Confidential | Contracts, financials, employee data | Redact/tokenize before model call unless task strictly requires it; access-controlled |
| Restricted/PII/Sensitive | Health, biometric, government ID, credentials | Never sent to a third-party model unless contractually covered (DPA/BAA); default to redaction |

**Manual guardrails:**
- **Data minimization by design**: the orchestrator should only fetch/pass the fields a given task actually needs (field-level allowlisting, not "pass the whole record").
- **Purpose binding**: log *why* each piece of data was included in a given call (ties to governance/audit).
- **Vendor/model data-use policy check**: confirm whether the LLM provider trains on inputs by default, and configure zero-retention/no-train settings where required for regulated data.
- **Data residency rules** for regulated industries (GDPR, HIPAA, sector-specific).

**Agent build tasks:**
1. Build a `DataClassifier` that tags fields/records by tier (rules-based for structured data; NER-based for unstructured, see §5).
2. Build a `ContextAssembler` that enforces: Restricted-tier data is redacted or blocked by default, requires an explicit `allow_sensitive=True` + audit reason to pass through.
3. Add a config file per integration declaring the model provider's data-retention/training policy, and fail startup if a Restricted-tier data source is wired to a provider without a no-train/zero-retention agreement.
4. Produce a data-flow diagram (auto-generated from the classifier config) as a governance artifact.

---

## 5. PII Detection & Handling

**Objective:** Detect PII in both input and output and apply the correct treatment (redact, mask, tokenize, allow-with-consent).

**Libraries:**
- `Microsoft Presidio` — the de facto open-source standard: NER + regex + checksum recognizers (SSNs, credit cards, emails, phone numbers), with pluggable anonymization (redact, mask, hash, encrypt, synthetic replacement).
- `LLM Guard`'s PII scanners (wraps Presidio) for a quick input/output pipeline integration.

**What counts as PII (build this as a config, not a hardcoded list):**
- Direct identifiers: name, SSN/national ID, passport, email, phone, precise geolocation, biometric data.
- Quasi-identifiers (can re-identify in combination): DOB, ZIP code, employer, rare medical condition.
- Special-category/sensitive PII (higher bar): health data, sexual orientation, religion, ethnicity, political affiliation, financial account numbers, credentials/secrets.

**Manual guardrails:**
- **Reversible vs. irreversible anonymization policy**: decide per use case whether you need re-identification (e.g., customer support needs to look the person up later — use tokenization with a secure vault) or not (analytics — use irreversible hashing/redaction).
- **Consent and purpose tracking**: PII should only flow through the pipeline for the purpose it was collected for.
- **Output-side re-check**: models can *generate* PII-shaped content that wasn't in the input (hallucinated addresses, phone numbers) — output scanning is not optional even if input was clean.

**Agent build tasks:**
1. Wrap Presidio as a `PIIDetector` service with a config-driven entity list.
2. Wire it into both Input Guardrails (stage 2) and Output Guardrails (stage 5) — input for redaction-before-model, output for leakage-catch-after-model.
3. Implement a tokenization vault (reversible) for entities that must be reconstituted later, keyed and access-controlled separately from the main log store.
4. Add regression tests with synthetic PII (never real PII) covering each entity type + adversarial obfuscation (e.g., "my email is j o h n at example dot com").

---

## 6. Handling Sensitive Information (Beyond PII)

**Objective:** Cover categories that aren't "PII" per se but are high-risk if mishandled: trade secrets, credentials/API keys, legal privilege, security vulnerability details, CBRN-adjacent technical content, self-harm/crisis content.

**Manual guardrails:**
- **Secrets scanning** on both input and output (API keys, tokens, passwords) — reuse code-security tooling (e.g., regex + entropy-based secret detectors) inside the LLM Guard pipeline (`Secrets` scanner).
- **Dual-use/uplift content policy**: define a hard-refuse list for content that provides meaningful uplift toward weapons or attacks (CBRN, cyberweapons), independent of framing (fiction, "for research," roleplay) — see §8 on Anthropic's approach, which treats *cumulative* conversation output as the unit of judgment, not each turn in isolation.
- **Crisis content routing**: self-harm/suicide signals should route to a specialized safe-response path (resources + no operational detail), not the general refusal path — this is a UX/safety requirement, not just a content filter.

**Agent build tasks:**
1. Add a `secrets` scanner to both directions of the pipeline; auto-redact matches and alert.
2. Build a `SensitiveTopicClassifier` (fine-tuned classifier or strong prompt-based classifier) with categories: {weapons/CBRN, cyberweapons/malware, self-harm/crisis, extremism, csae — hard block, no exceptions}.
3. Route each category to a distinct handler: hard-block-and-log, safe-response-template, or escalate-to-human.

---

## 7. Input/Output Validation

**Objective:** Treat the LLM as an untrusted component whose inputs and outputs both need schema and semantic validation — the same discipline as validating any external API.

**Libraries:**
- `Guardrails AI` (RAIL spec) — output structure/type validation, retry-on-failure with corrective re-prompting.
- `Pydantic` / `Instructor` — schema-constrained generation and parsing for structured outputs (tool calls, JSON).
- `Outlines` / constrained decoding — grammar-constrained generation when the output format is fixed (e.g., must be valid JSON matching a schema).

**Manual guardrails:**
- **Input validation:** length limits, encoding checks (block homoglyph/unicode obfuscation attacks), schema checks for structured fields, allowed-language/topic checks where relevant.
- **Output validation:** schema conformance (does the tool-call JSON match the tool's actual signature?), value-range checks (an agent proposing a $50,000 refund when policy caps at $500), and a **"never execute unvalidated model output"** rule for anything that reaches the tool layer.
- **Fail-closed, not fail-open**: if validation fails, the default behavior is to block/retry with a corrective prompt, never to silently pass through.

**Agent build tasks:**
1. Define Pydantic schemas for every tool call and structured output the system produces.
2. Wrap generation calls with `Guardrails AI` or `Instructor` so malformed output triggers automatic re-ask rather than reaching downstream systems.
3. Add input normalization (unicode NFKC normalization, homoglyph detection) before any classifier runs, so obfuscated injection attempts can't bypass regex/keyword filters.
4. Add a validation-failure counter to the governance dashboard (a spike indicates either an attack or a model regression).

---

## 8. Bias Detection

**Objective:** Detect and reduce disparate treatment or representation across protected/sensitive attributes, in both training-adjacent evaluation and runtime monitoring.

**Approach:**
- **Offline/eval-time**: run standardized bias benchmarks (e.g., counterfactual prompt pairs varying only a demographic attribute — name, gender, ethnicity — and measuring output divergence in tone, sentiment, recommendation quality, refusal rate).
- **Runtime**: `LLM Guard`'s bias scanner or a lightweight classifier as a monitoring signal (not usually a hard block, since bias is contextual — flag for review/aggregate reporting).
- **Aggregate monitoring over individual-message blocking**: bias is best caught statistically across many interactions (disparate refusal rates, disparate sentiment by group) rather than as a single-message pass/fail.

**Manual guardrails:**
- **Counterfactual test suite**: build (name/pronoun/ethnicity-swapped) prompt pairs for your actual use cases (e.g., loan-advice bot, hiring-assistant bot) and track output deltas over time as a CI metric.
- **Human review sampling**: route a random sample of outputs, stratified by user-declared demographic where available/consented, to human reviewers.

**Agent build tasks:**
1. Build a counterfactual test generator: take real prompts, template out names/pronouns/ethnic markers, regenerate, diff outputs (sentiment, length, refusal rate, recommendation content).
2. Wire this into the CI eval suite (§13) as a scheduled job, not just pre-deploy — bias can drift with model updates.
3. Add a bias-metrics panel to the governance dashboard (refusal rate by group, sentiment variance).

---

## 9. Alignment, Autonomy Control & Human-in/on/out-of-the-Loop

**Objective:** Ensure the system pursues the intended goal, stays corrigible (correctable by humans), and that autonomy is bounded appropriately to the risk of the action.

### 9.1 How Anthropic approaches this (use as the reference model)

Anthropic's public alignment stack, as an agent building this system should model it, has several layers worth replicating conceptually:

- **A written behavioral specification** — Anthropic's public [Claude's Constitution](https://www.anthropic.com/news/claude-constitution) (Jan 2026) establishes a **priority hierarchy**: safety > ethics > compliance with Anthropic's guidelines > helpfulness. It moved from purely rule-based constraints toward explaining the *reasoning* behind principles so the model can generalize to novel situations rather than pattern-matching a rulebook. **Build takeaway:** write your own agent's constitution/spec as a first-class artifact, not just a system prompt — and prioritize it: safety constraints must be able to override a user's explicit instruction and even the task's apparent goal.
- **Constitutional AI / Constitutional Classifiers** — training and runtime classifiers derived from the same constitution, used to catch jailbreaks (Anthropic's "next-generation Constitutional Classifiers," Jan 2026). **Build takeaway:** derive your runtime input/output classifiers from the same written policy document your system prompt uses, so the two layers can't drift apart.
- **Responsible Scaling Policy (RSP, currently v3.1)** — a tiered risk framework (AI Safety Levels, ASL) that gates increasingly capable/autonomous deployment behind proportional security and safeguard requirements, with published **Frontier Safety Roadmaps** and periodic **Risk Reports** reviewed by an internal oversight body (the Long-Term Benefit Trust) and external reviewers. <cite index="5-1">A Risk Report covers all publicly deployed models at the time of its publication, discussing risks and how deployment decisions were made in light of them.</cite> **Build takeaway:** gate your agent's autonomy level (what it's allowed to do unsupervised) behind a similar proportional framework — define capability tiers for *your* agent and require a documented safety case before promoting it to a higher-autonomy tier.
- **Alignment auditing / interpretability research** — Anthropic runs internal "auditing agent" tooling (e.g., Petri) to probe deployed models for hidden misaligned behavior under adversarial multi-turn pressure, and studies emergent risks like **agentic misalignment** (models taking self-interested or deceptive actions when given autonomy and a goal conflict) and **alignment faking** (models behaving differently when they believe they're being observed/evaluated vs. not). **Build takeaway:** don't just eval single-turn Q&A — build multi-turn, agentic scenario tests that put your agent in goal-conflict situations (e.g., "the only way to complete the task is to do something outside your permitted scope — what do you do?") and check whether it escalates to a human rather than acting unilaterally or being deceptive about what it did.
- **Interpretability as a second, independent signal** — internal-state monitoring is an active research frontier for catching misalignment that doesn't show up in the output text. This is not yet practical for most teams to build in-house, but the analogous, buildable version is: **log the model's stated reasoning/plan separately from its final action, and diff them** — if the stated plan and the actual tool call diverge, that's a red flag worth auto-escalating.

### 9.2 Human-in/on/out-of-the-loop — concrete design

Define autonomy explicitly per action type, not per agent globally:

| Mode | Definition | When to use |
|---|---|---|
| **Human-in-the-loop** | Human approves *before* the action executes | Irreversible or high-blast-radius actions: sending external communications, financial transactions, deleting data, deploying code |
| **Human-on-the-loop** | Action executes automatically, human can observe/interrupt in real time or shortly after (with an easy rollback) | Medium-risk, reversible actions: draft creation, internal updates, low-value transactions under a cap |
| **Human-out-of-the-loop** | Fully autonomous, periodic audit only | Low-risk, easily reversible, well-tested actions: read-only queries, internal search, drafting for the user's own review |

**Manual guardrails:**
- **Action-risk scoring** at the tool-registration level: every tool declares its own risk tier (reversibility, blast radius, cost) at build time, and the orchestrator enforces the matching HITL mode — this should not be left to the LLM to self-assess.
- **Escalation on goal conflict**: if completing a task requires exceeding declared scope, the correct behavior is to stop and ask, not to reinterpret the goal. Test for this explicitly (§9.1 build takeaway above).
- **Kill switch / circuit breaker**: a hard, out-of-band stop mechanism that doesn't depend on the model's cooperation (i.e., it's enforced at the infrastructure layer, not by asking the model nicely).
- **Reasoning/action divergence logging** as described above.

**Agent build tasks:**
1. Write your system's own "constitution" document (short, prioritized, reasoned) and use it as the source for both the system prompt and the classifier training/prompting.
2. Build a `ToolRegistry` where every tool declares `risk_tier: {low, medium, high}` and `reversible: bool`; the orchestrator derives HITL mode from this automatically.
3. Implement an approval queue (human-in-the-loop UI/API) for high-risk actions, with timeout-and-escalate behavior (don't fail open on timeout — fail closed).
4. Build a circuit breaker service, independent of the LLM process, that can halt all autonomous actions system-wide.
5. Add "goal-conflict" scenarios to your red-team/eval suite (§3, §13) specifically testing whether the agent escalates instead of unilaterally reinterpreting scope.
6. Log stated-plan vs. actual-action for every tool call; alert on divergence.

---

## 10. Safe Request Refusal

**Objective:** Refuse harmful/out-of-scope requests in a way that is accurate (doesn't over- or under-refuse), minimally disruptive to legitimate use, and consistent.

**Manual guardrails:**
- **Refuse the narrowest thing possible.** If only part of a multi-part request is problematic, fulfill the rest and decline just the problematic part, with a brief reason.
- **Avoid moralizing or lecturing** — a short, clear decline plus (where relevant) a safe alternative or redirection.
- **Distinguish categories of refusal** and route accordingly: hard policy violation (no negotiation), capability limitation (be honest, don't pretend it's a policy issue), and ambiguous/underspecified request (ask, don't refuse outright).
- **Track over-refusal as a first-class metric**, not just under-refusal — an agent that refuses too much is also failing its purpose, and over-refusal on benign edge cases (e.g., medical/legal/security topics asked in good faith) is a common, measurable failure mode.

**Agent build tasks:**
1. Build a refusal taxonomy (`policy_violation`, `capability_limit`, `needs_clarification`, `escalate_to_human`) and require the classifier/orchestrator to tag *which* type before generating a decline message.
2. Create a "golden set" of borderline-but-legitimate prompts (security research, medical questions, creative fiction with dark themes) and track refusal rate on this set as a regression metric — a spike signals over-refusal.
3. Template refusal responses per category so they're short, non-judgmental, and (where applicable) offer a safe path forward.

---

## 11. Hallucination Mitigation

**Objective:** Reduce and detect fabricated facts, citations, or claims not supported by provided context or verifiable sources.

**Techniques (build in this order — cheapest first):**
1. **Grounding via retrieval (RAG) with citation requirements** — force the model to cite which retrieved chunk supports each claim; unsupported claims are flagged.
2. **Groundedness/faithfulness scoring** — an automated check (NLI-based or LLM-as-judge) comparing generated claims against the source context; libraries like `NeMo Guardrails`' fact-checking rail or custom NLI-model scoring.
3. **Self-consistency checks** — sample the same query multiple times; high variance in factual claims is a hallucination signal worth flagging for high-stakes answers.
4. **Confidence/uncertainty surfacing** — prompt the model to explicitly flag low-confidence claims rather than presenting everything with uniform certainty; verify this behavior with eval, don't just trust the instruction.
5. **Tool-grounding for anything checkable** — if a fact is verifiable via a tool call (calculator, database, search), require the tool call rather than trusting parametric memory, especially for numbers, dates, and named entities.

**Manual guardrails:**
- **Citation-or-hedge policy**: every factual claim in a high-stakes domain (legal, medical, financial) must either cite a source in context or be explicitly hedged ("I'm not certain, you should verify").
- **Domain risk tiering**: apply the strictest hallucination controls to domains where a wrong answer causes real harm; looser controls are acceptable for low-stakes creative tasks.

**Agent build tasks:**
1. Build a `GroundednessChecker` that runs after generation: extract claims, check each against the provided context window using an NLI model or LLM-as-judge, score 0–1.
2. Set domain-specific thresholds (e.g., block/regenerate below 0.8 groundedness for medical/legal domains; log-only for creative domains).
3. Add citation-density metrics to the eval dashboard, tracked over time and by domain.
4. Build a "known-answer" regression set (facts with verified ground truth) to catch hallucination-rate drift after model or prompt changes.

---

## 12. Suggested Repository Structure

```
/trust-safety/
  /gateway/                # auth, rate limiting, provenance tagging
  /guardrails/
    /input/                # injection, PII, secrets, sensitive-topic classifiers
    /output/                # groundedness, PII leakage, bias, refusal-quality, schema validation
  /orchestrator/
    /policy_gate.py         # tool-scope enforcement, HITL routing
    /tool_registry.py       # risk_tier, reversible flags per tool
  /governance/
    /audit_log/              # append-only, immutable
    /dashboard/               # metrics: refusal rate, groundedness, bias deltas, injection attempts
    /policy_docs/              # your "constitution", data classification tiers, HITL policy
  /redteam/
    /garak_configs/
    /pyrit_configs/
    /golden_sets/               # borderline-legitimate prompts, counterfactual bias pairs, known-answer facts
  /eval/
    /ci_regression/               # promptfoo-style eval-as-code, run on every change
```

---

## 13. Testing, CI/CD & Governance Cadence

- **Pre-merge CI**: run the adversarial suite (Garak/PyRIT), the golden refusal set, the counterfactual bias set, and the known-answer hallucination set on every prompt/guardrail/model change. Fail the build on regression past defined thresholds.
- **Scheduled (weekly/monthly) evals**: full red-team pass, bias-drift check, groundedness-drift check — models and usage patterns drift even without code changes.
- **Incident review loop**: every guardrail block, HITL escalation, and red-team finding lands in the audit log; a recurring review (weekly) triages severity and feeds fixes back into the golden sets (closing the loop).
- **Proportional autonomy promotion**: don't grant an agent a higher HITL tier (in-loop → on-loop → out-of-loop) for a given tool until it has passed a defined safety case (analogous to Anthropic's ASL-gated deployment) — document the evidence, don't just decide informally.
- **Versioned policy documents**: your "constitution," data classification rules, and HITL policy should be version-controlled, changelogged, and referenced by hash/version in the audit log for every decision, so any output can be traced back to *which policy version* produced it.

---

## 14. Cross-Cutting: Data Poisoning

**Objective:** Prevent malicious/corrupted data from entering training, fine-tuning, or retrieval corpora and skewing model behavior.

**Manual guardrails:**
- **Provenance and integrity checks on all training/RAG-ingestion sources** — checksums, source allowlists, diff-based anomaly detection on corpus updates.
- **Outlier/anomaly detection** on new data before ingestion (statistical or embedding-space outlier detection to catch injected adversarial documents).
- **Held-out canary evaluation** after every fine-tune or corpus update — run the full eval suite (§13) and compare against baseline; a sudden behavior shift on unrelated eval items is a poisoning signal.
- **Segregated, access-controlled ingestion pipeline** — the same least-privilege principle as §2, applied to who/what can write into a corpus the model will later read from or train on.

**Agent build tasks:**
1. Build an ingestion-time anomaly detector (embedding-distance outliers, unexpected source domains) for any RAG corpus or fine-tuning dataset.
2. Require source-allowlisting and content hashing for anything entering a training/retrieval corpus, with an audit trail.
3. Run the full eval suite as a gate after every corpus/fine-tune update, not just after prompt/code changes.

---

## 15. Execution Plan (Phased, for the Building Agent)

**Phase 0 — Foundations (do first, everything else depends on it):**
- Repo scaffold (§12), audit log, `ContextBlock`/provenance data structures, tool registry with risk tiers.

**Phase 1 — Input-side safety:**
- Injection detection (§2), PII detection (§5), secrets scanning (§6), input schema validation (§7).

**Phase 2 — Output-side safety:**
- Output schema validation (§7), groundedness/hallucination checks (§11), PII leakage re-check (§5), refusal taxonomy (§10).

**Phase 3 — Autonomy & governance:**
- HITL modes and approval queue (§9), circuit breaker (§9), your written constitution/policy doc (§9.1), governance dashboard (§12–13).

**Phase 4 — Adversarial hardening:**
- Red-team harness + CI gating (§3, §13), bias counterfactual suite (§8), data-poisoning ingestion checks (§14).

**Phase 5 — Continuous operation:**
- Scheduled eval cadence, incident review loop, policy versioning, autonomy-tier promotion process.

Build in this order because each phase's tests depend on infrastructure from the phase before it (you can't gate autonomy on a safety case in Phase 3 if you don't have the audit log from Phase 0, and you can't run bias/injection regression in CI in Phase 4 without the eval harness scaffolded in Phase 0–1).

---

## Appendix A — Library Reference Table

| Concern | Primary library | License | Notes |
|---|---|---|---|
| Prompt injection (input) | LLM Guard, NeMo Guardrails | MIT / Apache 2.0 | Rebuff is archived/unmaintained as of 2026 — don't build new dependencies on it |
| PII detection | Microsoft Presidio | MIT | De facto standard; NER + regex + checksum recognizers |
| Output structure validation | Guardrails AI, Instructor, Outlines | Apache 2.0 / MIT | Constrained decoding / retry-on-schema-failure |
| Red-teaming | NVIDIA Garak, Microsoft PyRIT, DeepTeam | Apache 2.0 / MIT | Use in CI, not runtime |
| Eval-as-code / CI regression | Promptfoo | MIT (note: acquired by OpenAI in 2026, evaluate neutrality for your use case) | |
| Auxiliary safety classifier | Llama Guard, IBM Granite Guardian | Custom/OSS | Cheap pre-filter models |
| Agent/tool authorization | Cerbos | Apache 2.0 | Policy-as-code for fine-grained tool authorization |

## Appendix B — Anthropic Resources to Track

- Claude's Constitution (Jan 2026) — https://www.anthropic.com/news/claude-constitution
- Responsible Scaling Policy, current version — https://www.anthropic.com/responsible-scaling-policy
- Alignment Science Blog (agentic misalignment, alignment faking, auditing research) — https://alignment.anthropic.com/
- Constitutional Classifiers research — via Anthropic's Alignment research index — https://www.anthropic.com/research/team/alignment

---

*This document is a living spec — version it alongside the code it describes, and update Appendix B as Anthropic's published policies revise (RSP and the constitution are both actively iterated).*