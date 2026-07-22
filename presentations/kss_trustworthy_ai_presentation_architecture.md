# KSS Trustworthy AI Presentation Architecture

**Document type:** Machine-actionable presentation architecture and generation specification  
**Target execution agents:** Codex, Claude Code, Claude, or comparable agentic systems  
**Audience:** Software Engineers and AI/ML Engineers  
**Purpose:** Guide an AI system in researching, reasoning about, architecting, and generating a technically coherent Knowledge Sharing Session (KSS) on Trustworthy AI.

---

## 0. Executive Instruction

This document is **not a slide deck** and **not a fixed slide-by-slide outline**.

It is a specification for an agent that will independently determine the final presentation structure.

The downstream presentation agent MUST:

1. Read the source architecture documents.
2. Inspect the actual repository and implementation where available.
3. Distinguish implemented, partially implemented, planned, and absent capabilities.
4. Build a concept dependency graph before deciding the slide sequence.
5. Build a threat and failure model for the AI system.
6. Select a coherent narrative and recurring case study.
7. Research external topics where the source documents require current or authoritative information.
8. Design the presentation around causal relationships rather than a disconnected list of Trustworthy AI terms.
9. Generate the final slide plan only after completing the above reasoning.
10. Validate the final deck against the architecture and implementation evidence.

The agent MUST NOT treat the existing slide plan as immutable. The existing plan is a valuable conceptual source, but the new presentation architecture supersedes its fixed ordering whenever a better structure is required to represent the complete safety architecture.

---

# 1. Source-of-Truth Hierarchy

The downstream agent MUST resolve conflicts using the following hierarchy.

## Priority 1: Actual implementation and tests

Use the repository, source code, configuration, tests, and executable behavior to determine what is actually implemented.

Classify each capability as one of:

- `IMPLEMENTED`
- `PARTIALLY_IMPLEMENTED`
- `PLANNED`
- `NOT_IMPLEMENTED`
- `UNKNOWN`

Never describe `PLANNED` functionality as implemented.

## Priority 2: `ai_trust_safety_architecture.md`

This is the primary source for the intended Trust, Safety, Governance, and Agent architecture.

It defines the defense-in-depth system:

```text
Gateway/Auth
    ↓
Input Guardrails
    ↓
Orchestrator
    ↓
LLM Core
    ↓
Output Guardrails
    ↓
Action/Tool Layer
```

with a cross-cutting Governance Plane.

The architecture explicitly treats safety as independently testable checkpoints rather than a single filter.

## Priority 3: `llm-integration-ui.md`

Use this as the source for:

- Provider abstraction
- Provider comparison
- Guardrail versus no-guardrail testing
- Governance dashboard
- HITL approval queue
- Provider-specific evaluation
- Operational UI and observability

The UI MUST be presented as an operational surface over the safety architecture, not as an independent safety mechanism.

## Priority 4: `kss-trustworthy-ai-slide-plan.md`

Use this as the source for:

- Existing Trustworthy AI conceptual framing
- NIST terminology
- Explainability versus Trustworthiness
- Fairness, transparency, accountability, robustness, privacy, reliability
- XAI and causal reasoning
- Existing codebase-to-concept mapping

However, its fixed slide order and slide count are not binding.

## Priority 5: Authoritative external sources

Use authoritative sources for topics requiring current or external verification, especially:

- NIST AI RMF and Generative AI Profile
- EU AI Act and official regulatory sources
- Anthropic's public Constitution, Responsible Scaling Policy, alignment research, and related primary publications
- Relevant academic literature and official project documentation

The downstream agent MUST distinguish between:

- Primary sources
- Official documentation
- Academic research
- Secondary commentary

Claims should be supported by the strongest available source.

---

# 2. Presentation Thesis

The presentation MUST be organized around this thesis:

> **Trustworthy AI is not a property of the model alone. It is an evidence-backed property of the complete socio-technical system surrounding the model.**

The presentation should repeatedly connect:

```text
Capability
    ↓
Failure Mode
    ↓
Potential Consequence
    ↓
Engineering Control
    ↓
Evaluation
    ↓
Evidence
    ↓
Deployment Decision
    ↓
Governance
```

The presentation should not merely answer:

> "What is Trustworthy AI?"

It should answer:

> "What can go wrong in an AI system, where can it go wrong, how can we control it, how do we know the control works, and who remains accountable?"

---

# 3. Target Audience and Technical Level

The primary audience consists of:

- Software Engineers
- AI Engineers
- Machine Learning Engineers
- Data Scientists working with LLMs or agentic systems

The presentation SHOULD assume familiarity with:

- APIs
- Software systems
- Machine learning terminology
- Basic model inference
- Data pipelines
- CI/CD
- Authentication and authorization

The presentation SHOULD explain, rather than assume, the following:

- Prompt injection
- PII
- Data poisoning
- Hallucination
- Alignment
- Guardrails
- Human-in/on/out-of-the-loop
- Governance
- Trust calibration

The presentation SHOULD avoid:

- Treating Trustworthy AI as purely philosophical
- Treating libraries as complete safety solutions
- Presenting generic AI ethics without engineering implications
- Using unexplained regulatory terminology
- Overloading the audience with isolated academic definitions

---

# 4. Primary Narrative Architecture

The downstream agent MUST use one recurring AI system as the narrative anchor.

The system SHOULD be an agent capable of:

- Receiving a user request
- Reading external or retrieved content
- Calling an LLM
- Using tools
- Handling sensitive data
- Producing a recommendation or decision
- Taking an external action

A suitable scenario is an agent that processes a confidential business document, determines an outcome, and can execute an external action.

The exact scenario may be changed if the downstream agent finds a better scenario, but it MUST satisfy the above constraints.

The scenario MUST persist throughout the presentation.

Do not create a completely unrelated example for every topic.

---

# 5. The Recurring Story Structure

Every major topic should use the following causal sequence where appropriate:

## 5.1 Normal operation

What is the system supposed to do?

```text
User Request
    ↓
Agent
    ↓
Retrieve Information
    ↓
Reason
    ↓
Validate
    ↓
Act
```

## 5.2 Failure scenario

What happens when the system fails?

```text
Unexpected Input / Data / Model Behavior
              ↓
          Failure
              ↓
          Consequence
```

## 5.3 Engineering response

What control should detect, prevent, contain, or recover from the failure?

```text
Threat
  ↓
Detection
  ↓
Policy Decision
  ↓
Containment
  ↓
Human or System Action
  ↓
Audit
```

## 5.4 Evidence

How do we know the control works?

```text
Claim
  ↓
Threat Model
  ↓
Test
  ↓
Metric
  ↓
Threshold
  ↓
Decision
  ↓
Residual Risk
```

The preferred narrative grammar is:

> **Capability → Failure → Consequence → Control → Evidence → Limitation**

---

# 6. System Architecture as the Presentation Spine

The downstream agent MUST use the following architecture as the principal structural model:

```text
                         GOVERNANCE PLANE
       Policy | Audit | Metrics | HITL | Evaluation | Incidents
                                  │
                                  ▼

User
  ↓
Gateway / Auth
  ↓
Input Guardrails
  ↓
Orchestrator
  ↓
LLM Core
  ↓
Output Guardrails
  ↓
Action / Tool Layer
  ↓
Response or External Side Effect
```

## 6.1 Gateway / Auth

Responsible for:

- Identity
- Rate limiting
- Caller provenance
- Authentication
- Request origin

## 6.2 Input Guardrails

Responsible for:

- Prompt injection
- Jailbreak detection
- PII detection
- Sensitive-topic classification
- Secrets scanning
- Input schema validation

## 6.3 Orchestrator

Responsible for:

- Retrieval
- Context assembly
- Tool routing
- Human approval decisions
- Task scope
- Risk-aware execution planning

## 6.4 LLM Core

Responsible for:

- Model inference
- System instructions
- Provenance-tagged context
- Provider selection
- Constrained generation where applicable

The LLM MUST be treated as a powerful but imperfect system component.

## 6.5 Output Guardrails

Responsible for:

- Groundedness
- Hallucination checks
- PII leakage
- Bias monitoring
- Refusal quality
- Schema validation
- Semantic validation

## 6.6 Action / Tool Layer

Responsible for:

- Tool authorization
- Side-effecting actions
- Risk-tier enforcement
- Human approval
- Circuit breakers

The action layer is the strongest boundary against real-world side effects.

## 6.7 Governance Plane

Responsible for:

- Append-only audit
- Policy versioning
- Metrics
- Red-team evaluation
- Incident review
- HITL workflow
- Deployment evidence

---

# 7. Concept Dependency Graph

The downstream agent MUST reason through concepts in dependency order.

```text
Trustworthy AI
      ↓
Why AI Systems Fail
      ↓
System Boundaries
      ↓
Input Risk
      ├── Prompt Injection
      ├── Data Privacy
      ├── PII
      ├── Sensitive Information
      └── Data Poisoning
      ↓
Model and Output Risk
      ├── Hallucination
      ├── Bias
      ├── Refusal
      └── Alignment
      ↓
Validation
      ├── Input Validation
      └── Output Validation
      ↓
Action Risk
      ├── Tool Authorization
      ├── Autonomy
      └── Human Oversight
      ↓
Governance
      ↓
Continuous Evaluation
      ↓
Evidence-Based Trust
```

The downstream agent may produce a different final slide sequence, but it MUST preserve conceptual dependencies unless it can justify the change.

---

# 8. Required Topic Coverage

The following topics are mandatory.

## 8.1 Trustworthy AI Foundations

Cover:

- What Trustworthy AI means
- Why reliability alone is insufficient
- NIST Trustworthy AI characteristics
- The difference between model trust and system trust
- Silent failures
- Adversarial failures
- Systemic failures

The NIST characteristics may be used as the conceptual vocabulary:

- Valid and reliable
- Safe
- Secure and resilient
- Accountable and transparent
- Explainable and interpretable
- Privacy-enhanced
- Fair with harmful bias managed

The presentation MUST make clear that Explainability is one characteristic, not a synonym for Trustworthiness.

---

## 8.2 Explainability and Its Limits

The existing XAI material should be retained, but it MUST be integrated into the broader system-safety narrative.

The presentation should explain:

- Explainability does not guarantee fairness
- Explainability does not guarantee privacy
- Explainability does not guarantee robustness
- Post-hoc explanations may be correlational
- LLM-generated rationales may not faithfully represent internal computation
- Explainability does not protect against prompt injection
- Explainability does not authorize external actions

The core reframe:

> **Explainability is evidence that may contribute to a trust judgment. It is not the trust judgment itself.**

The downstream agent may include causal reasoning and counterfactual explanations where useful, but MUST NOT allow XAI to displace the broader safety architecture.

---

## 8.3 Prompt Injection Prevention

The presentation MUST distinguish:

### Direct injection

```text
User
  ↓
Malicious Instruction
  ↓
Model
```

### Indirect injection

```text
User
  ↓
Agent
  ↓
Retrieved Document / Email / Web Page
  ↓
Malicious Instruction
  ↓
Context
  ↓
Model
```

The presentation MUST explain two layers of defense.

### Library layer

Examples may include:

- LLM Guard
- NeMo Guardrails
- Llama Guard
- Granite Guardian

### Manual architectural layer

Must include concepts such as:

- Instruction and data separation
- Provenance tagging
- Trust levels
- Explicit untrusted-content handling
- Instruction reassertion
- Canary tokens where appropriate
- Least-privilege tool binding
- PolicyGate
- Two-pass verification for high-risk actions

The presentation MUST explicitly state:

> **A detector is not the final safety boundary.**

Even if a malicious instruction influences the model, the tool layer must still prevent unauthorized actions.

---

## 8.4 Vulnerability Identification

Prompt injection prevention and vulnerability identification MUST be treated as distinct concepts.

```text
Prompt Injection Prevention
= Runtime Defense

Red Teaming
= Testing Discipline
```

Cover:

- Threat modeling
- Adversarial testing
- Red teaming
- Multi-turn attacks
- Jailbreak testing
- Prompt injection probes
- Data leakage probes
- Regression testing
- CI evaluation

Potential tools:

- Garak
- PyRIT
- DeepTeam
- Promptfoo

The presentation MUST explain that no single red-team run proves security.

The stronger model is:

```text
Threat Model
    ↓
Attack Suite
    ↓
Evaluation
    ↓
Regression Gate
    ↓
Incident Review
    ↓
Updated Test Set
```

---

## 8.5 Data Privacy: What Should and Should Not Be Provided

The presentation MUST establish that sending data to an LLM is a governance decision.

Use a classification framework such as:

| Tier | Example | Default Treatment |
|---|---|---|
| Public | Public documentation | Generally usable |
| Internal | Internal business data | Context-dependent |
| Confidential | Contracts, financial data | Minimize, redact, or tokenize |
| Restricted | Health, credentials, government ID | Block or explicitly authorize |

The presentation MUST cover:

- Data minimization
- Field-level allowlisting
- Purpose binding
- Provider data-use policies
- Retention
- Training-on-input policies
- Data residency
- Contractual requirements

The key engineering principle:

> **Do not pass the entire record merely because the model can process it.**

The orchestrator should provide only the fields required for the task.

---

## 8.6 PII: What It Is and How to Handle It

The presentation MUST distinguish:

### Direct identifiers

Examples:

- Name
- Email
- Phone
- National ID
- Passport

### Quasi-identifiers

Examples:

- Date of birth
- ZIP code
- Employer
- Rare condition

### Sensitive personal data

Examples:

- Health information
- Biometric information
- Financial information
- Credentials

The presentation MUST explain that re-identification can occur through combinations of attributes.

The handling decision should be:

```text
PII Detected
    ↓
Is identity needed later?
    ├── Yes → Tokenize with controlled re-identification
    └── No  → Redact / Mask / Hash
```

The system MUST inspect both:

- Input
- Output

because the model can generate PII that was not present in the input.

The presentation MUST clearly distinguish:

```text
PII Redaction / Tokenization
        ≠
Differential Privacy
```

Do not claim formal differential privacy when the implementation performs redaction or tokenization.

---

## 8.7 Sensitive Information Beyond PII

The presentation MUST distinguish PII from other sensitive information.

Examples:

- API keys
- Passwords
- Secrets
- Trade secrets
- Legal privilege
- Security vulnerabilities
- Sensitive operational data

The pipeline should be conceptualized as:

```text
Input / Output
      ↓
PII Detection
      ↓
Secrets Detection
      ↓
Sensitive Topic Classification
      ↓
Policy Decision
```

The presentation should explain that the treatment depends on category:

- Block
- Redact
- Route to a specialized handler
- Escalate
- Allow with authorization and audit

---

## 8.8 Input and Output Validation

The presentation MUST establish:

> **A fluent model output is not automatically valid output.**

### Input validation

May include:

- Length
- Encoding
- Unicode normalization
- Homoglyph detection
- Schema validation
- Allowed fields
- Allowed topic or language where relevant

### Output validation

Must include:

- Schema
- Type
- Range
- Tool signature
- Semantic constraints

Example:

```text
Model:
"Refund amount = $50,000"

Business Rule:
"Maximum refund = $500"
```

Valid JSON is not sufficient.

The critical rule is:

> **Never execute unvalidated model output.**

The default behavior for validation failure should be:

```text
Validation Failure
      ↓
Block
or
Corrective Retry
or
Human Escalation
```

Not silent pass-through.

---

## 8.9 Hallucinations

The presentation MUST treat hallucination as a reliability problem.

A useful model is:

```text
Claim
  ↓
Evidence
  ↓
Groundedness Check
  ↓
Confidence / Uncertainty
  ↓
Decision
```

Potential controls:

- Retrieval grounding
- Citation requirements
- Groundedness checks
- Known-answer evaluation
- Tool verification
- Self-consistency where appropriate
- Uncertainty surfacing

The presentation MUST avoid claiming that one technique eliminates hallucination.

A better claim is:

> **The system can reduce, detect, and contain hallucination under defined conditions.**

---

## 8.10 Bias Detection

The presentation MUST distinguish individual-message detection from statistical evaluation.

Use:

```text
Counterfactual Pair
      ↓
Change One Sensitive Attribute
      ↓
Compare Outputs
      ↓
Measure Divergence
```

Possible metrics include:

- Refusal-rate difference
- Sentiment difference
- Recommendation difference
- Quality difference
- Output disparity

The presentation MUST explain:

> Bias is often a distributional property and therefore requires aggregate evaluation.

Runtime classifiers may provide signals, but they are not a complete fairness solution.

The presentation should cover:

- Counterfactual evaluation
- Aggregate monitoring
- Human review sampling
- Drift monitoring

---

## 8.11 Alignment

Alignment MUST be presented as an engineering problem involving:

- Intended objective
- System constraints
- User instructions
- Policy
- Tool permissions
- Actual behavior

Use:

```text
User Objective
      ↓
Agent Plan
      ↓
Policy Constraints
      ↓
Tool Permissions
      ↓
Actual Action
```

An alignment failure occurs when the agent's behavior diverges from the intended objective and constraints.

The presentation MUST include goal-conflict scenarios.

Example:

```text
Goal:
"Complete the task at all costs."

Constraint:
"Do not access restricted data."

Conflict:
The fastest route requires restricted data.

Expected:
Stop, explain the conflict, and escalate.
```

---

## 8.12 Anthropic as an Alignment Reference

Anthropic's work should be used as an external reference model, not as evidence that the project implements Anthropic's systems.

The downstream agent SHOULD research current primary sources from Anthropic.

Concepts to investigate may include:

- Written behavioral specifications
- Claude's Constitution
- Constitutional AI
- Constitutional Classifiers
- Responsible Scaling Policy
- Risk-proportional deployment
- Alignment auditing
- Agentic misalignment
- Alignment faking
- Interpretability research

The presentation should extract engineering principles:

```text
Written Policy
      ↓
Behavioral Priorities
      ↓
Runtime Controls
      ↓
Adversarial Evaluation
      ↓
Alignment Auditing
      ↓
Deployment Gating
```

The project-level analogue may be:

```text
Constitution / Policy
      ↓
System Instructions
      ↓
Classifiers and Guardrails
      ↓
Goal-Conflict Tests
      ↓
Tool Authorization
      ↓
Autonomy Promotion Criteria
```

The presentation MUST clearly distinguish:

```text
Anthropic Research / Deployment Approach
        ≠
This Project's Implementation
```

---

## 8.13 Safe Request Refusal

The presentation MUST distinguish:

- Under-refusal
- Over-refusal
- Correct refusal
- Safe redirection
- Clarification
- Human escalation

Use:

```text
Request
  ↓
Classification
  ├── Allowed
  ├── Needs Clarification
  ├── Partially Allowed
  ├── Refuse + Safe Alternative
  └── Escalate
```

The core principle:

> **Refuse the unsafe part as narrowly as possible while preserving legitimate assistance.**

The presentation should include a failed scenario showing:

```text
Unsafe Request
      ↓
Overly Broad Refusal
      ↓
Legitimate User Need Unmet
```

This demonstrates that excessive refusal is also a system failure.

---

## 8.14 Autonomy Control

Autonomy MUST be treated as a property of actions, not merely of agents.

Use:

| Action | Risk | Human Control |
|---|---|---|
| Read document | Low | Human-out-of-loop may be acceptable |
| Draft email | Medium | Human-on-loop |
| Send external email | High | Human-in-loop |
| Delete production data | Very high | Strong approval and independent controls |

The presentation MUST explain:

### Human-in-the-loop

Human approves before action.

### Human-on-the-loop

Human supervises and can intervene.

### Human-out-of-the-loop

System acts independently under predefined controls and periodic review.

The presentation MUST also cover:

- Reversibility
- Blast radius
- Cost
- Scope
- Circuit breakers
- Kill switches

The LLM should not be the ultimate authority over its own permissions.

---

## 8.15 Governance

Governance MUST be presented as an operational control system, not merely as documentation.

Governance should answer:

- What happened?
- Which model was used?
- Which provider was used?
- Which policy version was active?
- Which data was included?
- Which guardrails triggered?
- Was a human involved?
- What action occurred?
- What evidence supports the decision?

Conceptual loop:

```text
System Behavior
      ↓
Audit Evidence
      ↓
Evaluation
      ↓
Incident Review
      ↓
Policy / Code Change
      ↓
New Evaluation
```

The governance plane should include:

- Audit logs
- Policy versioning
- Metrics
- HITL queue
- Red-team findings
- Incident review
- Evaluation history
- Autonomy promotion evidence

---

## 8.16 Data Poisoning

The presentation MUST clearly distinguish data poisoning from prompt injection.

### Prompt injection

Occurs at inference-time context or instruction boundaries.

```text
Malicious Content
      ↓
Prompt / Context
      ↓
Model
```

### Data poisoning

Occurs when malicious or corrupted data enters:

- Training
- Fine-tuning
- Retrieval corpora
- Knowledge bases

```text
Malicious Data
      ↓
Ingestion
      ↓
Corpus / Model
      ↓
Future Behavior
```

Controls should include:

- Source allowlisting
- Provenance
- Content hashing
- Access-controlled ingestion
- Anomaly detection
- Embedding-space outlier detection
- Held-out canary evaluation
- Full evaluation after corpus or fine-tuning updates

The key principle:

> **Runtime guardrails cannot fully solve a poisoned data source.**

---

# 9. The Failure Taxonomy

The presentation should use the following taxonomy to organize failure scenarios.

## Silent Failure

The system produces an incorrect output without a clear signal.

Examples:

- Hallucination
- Incorrect classification
- Biased recommendation

## Adversarial Failure

An attacker deliberately manipulates the system.

Examples:

- Prompt injection
- Jailbreak
- Data poisoning
- Data exfiltration

## Systemic Failure

The system behaves according to its local objective but creates unacceptable aggregate or organizational outcomes.

Examples:

- Disparate impact
- Over-automation
- Poor governance
- Accountability gaps

The downstream agent SHOULD use these categories to ensure the presentation covers more than attack scenarios.

---

# 10. The Failure-to-Control Matrix

The downstream agent MUST construct a matrix similar to the following before generating slides.

| Failure | Location | Consequence | Control | Evidence |
|---|---|---|---|---|
| Prompt injection | Input/context | Unauthorized instruction following | Provenance, scanners, policy gate | Injection test suite |
| Data poisoning | Ingestion | Persistent behavior shift | Integrity, provenance, anomaly detection | Post-update eval |
| PII exposure | Input/output | Privacy violation | Detection, redaction, tokenization | Synthetic PII tests |
| Secret leakage | Input/output | Credential compromise | Secret scanner | Secret regression tests |
| Hallucination | Model/output | Incorrect decision | Grounding, verification | Known-answer eval |
| Bias | Model/system | Disparate treatment | Counterfactual tests | Group-level metrics |
| Over-refusal | Output | Lost utility | Refusal taxonomy | Golden refusal set |
| Under-refusal | Output | Unsafe assistance | Safety policy | Adversarial eval |
| Invalid output | Output/tool boundary | Tool failure | Schema and semantic validation | Schema tests |
| Excessive autonomy | Tool layer | Real-world harm | Risk tiers, HITL | Safety case |
| Misalignment | Planning/action | Scope violation | Policy, goal-conflict eval | Multi-turn scenarios |
| Governance failure | Lifecycle | No accountability | Audit and policy versioning | Audit completeness |

The final presentation does not need to show this entire table, but the downstream agent should use it as an internal planning artifact.

---

# 11. The Evidence Model

Every significant Trustworthy AI claim MUST be converted into an evidence question.

Bad claim:

> "The system is secure."

Better claim:

> "The evaluated prompt-injection suite achieved a defined detection rate under the tested attack conditions, with the tool authorization layer preventing unauthorized side effects in the tested scenarios."

The evidence model is:

```text
Claim
  ↓
Threat Model
  ↓
Test Dataset / Attack Suite
  ↓
Metric
  ↓
Threshold
  ↓
Decision
  ↓
Residual Risk
```

The presentation agent MUST avoid absolute claims such as:

- "The model is safe."
- "The system cannot be hacked."
- "Hallucinations are solved."
- "Bias is eliminated."
- "The guardrail guarantees privacy."

Use bounded claims instead.

---

# 12. Codebase-to-Architecture Validation

Before designing the final deck, the downstream agent MUST inspect the codebase and create a validation matrix.

Required structure:

| Concept | Architecture Layer | Implementation | Status | Test | Demonstration |
|---|---|---|---|---|---|
| Prompt injection | Input Guardrails | Actual implementation | Status | Test | Available? |
| PII | Input/Output | Actual implementation | Status | Test | Available? |
| Validation | Output | Actual implementation | Status | Test | Available? |
| Bias | Evaluation | Actual implementation | Status | Test | Available? |
| Alignment | Policy/Orchestration | Actual implementation | Status | Test | Available? |
| Autonomy | Tool Layer | Actual implementation | Status | Test | Available? |
| Governance | Cross-cutting | Actual implementation | Status | Test | Available? |

The agent MUST explicitly identify gaps.

Example:

```text
Architecture Requirement:
Output groundedness scoring

Repository:
No implementation found

Status:
PLANNED / NOT_IMPLEMENTED

Presentation Treatment:
Describe as planned architecture, not completed capability.
```

---

# 13. Provider Abstraction and Model Comparison

If the system supports multiple LLM providers, the presentation SHOULD treat provider abstraction as an engineering capability rather than a safety guarantee.

The conceptual model is:

```text
Same Input
    ↓
Provider A
    ↓
Guardrails
    ↓
Evaluation

Same Input
    ↓
Provider B
    ↓
Guardrails
    ↓
Evaluation
```

Provider comparison should examine:

- Safety behavior
- Refusal behavior
- Hallucination
- Groundedness
- Bias
- Latency
- Cost
- Reliability

The presentation MUST not imply:

> "Provider X is safe and Provider Y is unsafe."

Instead:

> **Safety is a property of the provider-system configuration under defined evaluation conditions.**

Provider-specific evaluation is necessary because model behavior can vary by provider, model version, system prompt, and configuration.

---

# 14. Required Intermediate Planning Artifacts

The downstream agent MUST create the following artifacts before final slide generation.

## Artifact A: Concept Dependency Graph

Shows which concepts must precede others.

## Artifact B: System Threat Map

Maps threats to system boundaries.

```text
Boundary
  ↓
Threat
  ↓
Failure
  ↓
Control
```

## Artifact C: Narrative Scenario Matrix

```text
Scenario
  ↓
Failure
  ↓
Consequence
  ↓
Control
  ↓
Evidence
```

## Artifact D: Codebase Validation Matrix

Maps architecture claims to actual implementation.

## Artifact E: Source and Claim Register

For every external factual claim:

```text
Claim
  ↓
Source
  ↓
Source Type
  ↓
Confidence
  ↓
Where Used
```

## Artifact F: Final Presentation Architecture

Only after A–E are complete should the agent determine:

- Section order
- Number of slides
- Visual types
- Speaker-note depth
- Case-study placement
- Codebase demonstrations

---

# 15. Presentation Generation Workflow

The downstream agent MUST follow this workflow.

## Phase 1: Read

Read:

- This document
- `ai_trust_safety_architecture.md`
- `llm-integration-ui.md`
- `kss-trustworthy-ai-slide-plan.md`
- Relevant source code
- Tests
- Configuration

## Phase 2: Inspect

Determine:

- What exists
- What is incomplete
- What is planned
- What is absent

## Phase 3: Model

Build:

- Concept dependency graph
- Threat model
- Failure taxonomy
- Control map

## Phase 4: Research

Research only where needed.

Prioritize:

1. Primary sources
2. Official documentation
3. Academic literature
4. High-quality secondary sources

For Anthropic-related content, consult current primary Anthropic sources and do not rely on stale summaries.

## Phase 5: Select Narrative

Choose one persistent case study.

The case study MUST support:

- Input risk
- Privacy
- Model failure
- Output validation
- Action risk
- Human oversight
- Governance

## Phase 6: Architect

Construct the presentation around:

```text
Why Trust Matters
      ↓
Where AI Systems Fail
      ↓
How Defense-in-Depth Works
      ↓
Input Safety
      ↓
Model and Output Safety
      ↓
Alignment and Autonomy
      ↓
Governance and Evidence
      ↓
Codebase Mapping
```

The final order may differ if the dependency graph justifies it.

## Phase 7: Validate

Check:

- All mandatory topics are covered.
- No planned feature is described as implemented.
- No library is presented as a guarantee.
- Prompt injection is distinguished from data poisoning.
- PII is distinguished from general sensitive information.
- Redaction is distinguished from differential privacy.
- Runtime defense is distinguished from red-team evaluation.
- Anthropic's work is not misrepresented as the project's implementation.
- Governance is cross-cutting.
- The narrative is coherent.

## Phase 8: Generate

Only now generate:

- Slide architecture
- Slide content
- Speaker notes
- Visual specifications
- Citations
- Final presentation artifact

---

# 16. Visual Reasoning Rules

The downstream agent should select visuals based on the type of reasoning required.

## Use a pipeline when showing:

- System architecture
- Data flow
- Guardrail flow
- Governance flow

## Use a threat path when showing:

- Prompt injection
- Data poisoning
- Data leakage
- Unauthorized action

## Use a decision tree when showing:

- PII handling
- Refusal
- Escalation
- Human approval

## Use a comparison when showing:

- With versus without guardrails
- Provider behavior
- Human-in/on/out-of-loop
- PII versus sensitive information

## Use a causal loop when showing:

- Governance
- Incident review
- Continuous evaluation

## Use a counterfactual pair when showing:

- Bias detection
- Fairness evaluation

## Use a layered architecture when showing:

- Defense in depth
- Anthropic-inspired alignment stack
- System trust model

Do not use a bullet list when a relationship, process, or boundary is the main idea.

---

# 17. Story, Case Study, and Failed Scenario Guidelines

The presentation MUST include:

## One persistent story

The same AI agent should appear throughout the session.

## Multiple failure scenarios

The scenarios should include, where appropriate:

1. A malicious user input.
2. A malicious retrieved document.
3. PII or sensitive data entering the context.
4. A hallucinated answer.
5. A biased output.
6. An unsafe request.
7. An over-refusal.
8. A goal conflict.
9. An unauthorized tool action.
10. A poisoned data source.

## One final integrated walkthrough

At the end, replay one request through the complete architecture:

```text
Request
  ↓
Gateway
  ↓
Input Safety
  ↓
Context Assembly
  ↓
LLM
  ↓
Output Safety
  ↓
Policy Gate
  ↓
Human Approval if Required
  ↓
Tool
  ↓
Audit
```

This final walkthrough should demonstrate that the controls are not isolated concepts.

They form a system.

---

# 18. Rules for Technical Accuracy

The downstream agent MUST:

- Verify current facts when they may have changed.
- Cite external claims in speaker notes or references.
- Separate implementation evidence from architectural intent.
- State uncertainty where evidence is incomplete.
- Avoid absolute security or safety claims.
- Avoid claiming that detection is prevention.
- Avoid claiming that a classifier understands intent perfectly.
- Avoid treating model reasoning text as proof of internal reasoning.
- Avoid treating a successful demo as evidence of general safety.
- Avoid treating one benchmark as a complete evaluation.

The preferred language is:

- "Under the evaluated conditions..."
- "The implementation currently supports..."
- "The architecture proposes..."
- "This control reduces the risk of..."
- "Residual risk remains because..."
- "This is a monitoring signal rather than a complete guarantee..."

---

# 19. Definition of a Successful Presentation

The presentation is successful if a technically capable audience can answer:

1. What does Trustworthy AI mean beyond model accuracy?
2. Where can an AI system fail?
3. Why are agentic systems different from static model inference?
4. What is the difference between prompt injection and data poisoning?
5. What data should and should not enter an LLM context?
6. What is PII, and how should it be handled?
7. Why is model output not automatically trusted?
8. How should hallucinations be detected and contained?
9. How can bias be evaluated?
10. What does alignment mean in an engineering system?
11. How does autonomy create new safety requirements?
12. When should a human be involved?
13. What does governance actually provide?
14. How do we know whether a safety control works?
15. What has the actual codebase implemented?

The presentation should leave the audience with this conclusion:

> **Trustworthy AI is engineered through architecture, controlled through guardrails and authorization, evaluated through evidence, and maintained through governance.**

---

# 20. Final Instruction to the Presentation-Generation Agent

You are not being asked to convert a fixed outline into slides.

You are being asked to architect a technically coherent presentation from a system architecture, an implementation, and a set of Trustworthy AI concepts.

Before generating slides:

1. Read the source documents.
2. Inspect the repository.
3. Build the concept dependency graph.
4. Build the failure and threat model.
5. Build the codebase validation matrix.
6. Select a persistent case study.
7. Research external topics using authoritative sources.
8. Construct the narrative architecture.
9. Decide what must be shown visually.
10. Decide what belongs in speaker notes.
11. Validate all claims against implementation evidence.
12. Generate the final slide plan.
13. Generate the presentation.

Do not optimize for maximum topic coverage.

Optimize for:

> **Causal understanding of how trustworthy AI systems are engineered.**

The core narrative must remain:

```text
AI Capability
    ↓
Failure Mode
    ↓
Potential Harm
    ↓
Control
    ↓
Evaluation
    ↓
Evidence
    ↓
Governance
```

The final presentation should demonstrate that Trustworthy AI is not achieved by selecting a trustworthy model.

It is achieved by engineering, testing, monitoring, governing, and continuously evaluating the complete system around the model.
