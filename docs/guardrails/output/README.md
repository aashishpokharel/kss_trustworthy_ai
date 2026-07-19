# Output Guardrails Module

## 1. Purpose

Stage [5] of the pipeline. Validates LLM output for schema conformance, factual groundedness, PII leakage, and refusal classification. Architecture doc: Sections 5, 7, 10, 11.

## 2. Public Interface

### Pipeline (main entry point)

**`OutputGuardrailPipeline`** — `trust_safety/guardrails/output/pipeline.py`

| Method | Signature | Description |
|---|---|---|
| `run(output_text, source_context, expected_schema, domain, input_was_benign, context)` | `output_text: str, source_context: str\|None=None, expected_schema: dict\|None=None, domain: str="general", input_was_benign: bool=True, context: ContextBlock\|None=None` → `OutputGuardrailReport` | Runs all detectors. Fails-closed: schema failure or groundedness below threshold → blocked. |

### Schema Validator

**`OutputSchemaValidator`** — `trust_safety/guardrails/output/schema_validator.py`

| Method | Signature | Description |
|---|---|---|
| `validate(output_text, expected_schema)` | `str, dict\|None` → `SchemaValidationResult` | Extract JSON, validate types + required fields + value ranges. Generates corrective re-prompt on failure. |

### Groundedness Checker

**`GroundednessChecker`** — `trust_safety/guardrails/output/groundedness_checker.py`

| Method | Signature | Description |
|---|---|---|
| `check(output_text, source_context, domain)` | `str, str\|None, str="general"` → `GroundednessResult` | Extract claims, check support via keyword overlap, detect hedging. Domain thresholds: medical/legal 0.85, financial 0.80, general 0.70, creative 0.0 (log-only). |

### Refusal Classifier

**`RefusalClassifier`** — `trust_safety/guardrails/output/refusal_classifier.py`

| Method | Signature | Description |
|---|---|---|
| `classify(output_text)` | `str` → `RefusalClassification` | Pattern-based classification into 4 types. |
| `check_over_refusal(output_text, was_input_benign)` | `str, bool` → `RefusalClassification` | Same as classify, but sets `over_refusal=True` if a benign input was refused. |
| `refusal_template(refusal_type)` | `str` → `str` | Static method — returns template response per type. |

Refusal types: `policy_violation`, `capability_limit`, `needs_clarification`, `escalate_to_human`.

## 3. Configuration

No module-specific env vars. Domain thresholds are hardcoded in `DOMAIN_THRESHOLDS` dict (medical/legal=0.85, financial=0.80, general=0.70, creative=0.0).

## 4. Data Flow

```
output_text → SchemaValidator.validate()
            → GroundednessChecker.check()    [blocks if score < domain threshold]
            → PIIDetector.detect()           [reuses Phase 1 detector; blocks if PII found]
            → RefusalClassifier.classify()   [classifies but does NOT block — flags over-refusal]
            → OutputGuardrailReport
```

**This module does NOT:**
- Re-prompt the LLM on schema failure (the Orchestrator handles retry with the corrective prompt)
- Compare against multiple sources (groundedness uses a single source_context string)
- Run bias analysis (that's in `eval/counterfactual_bias.py`, not runtime)

## 5. Dependencies

- **Internal**: `trust_safety.guardrails.input.pii_detector` (reused for output PII leak check), `trust_safety.models`
- **External**: None beyond stdlib. No ML models. Groundedness uses keyword overlap, refusal uses regex patterns.

> **Divergence from architecture doc**: Architecture suggests NLI-based faithfulness scoring (e.g., `NeMo Guardrails` fact-checking rail). Current implementation uses keyword overlap — simpler, no external model dependency, but less accurate for complex entailment. A future phase can swap in an NLI model without changing the `GroundednessChecker` interface.

## 6. Usage Example

```python
from trust_safety.guardrails.output import OutputGuardrailPipeline
from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from pathlib import Path

store = AppendOnlyFileStore(Path("./data/audit.jsonl"))
logger = AuditLogger(store)
pipeline = OutputGuardrailPipeline(audit_logger=logger)

# Clean output — passes
report = pipeline.run(
    "The capital of France is Paris.",
    source_context="Paris is the capital of France."
)
print(report.allowed)  # True
print(report.groundedness.score)  # 1.0

# Hallucinated output — blocked (general domain, threshold 0.70)
report = pipeline.run(
    "The moon is made of green cheese and orbits at 500,000 km.",
    source_context="The moon orbits Earth at approximately 384,400 km.",
    domain="general"
)
print(report.allowed)  # False (if unsupported claims pull score below 0.70)
print(report.groundedness.unsupported_claims)  # ["The moon is made of green cheese..."]

# PII leak — blocked
report = pipeline.run(
    "The user's email is john.doe@example.com and phone is (555) 123-4567."
)
print(report.allowed)  # False
print(report.block_reason)  # "PII leak detected in output: ..."

# Refusal classification
report = pipeline.run("I cannot help with that request.")
print(report.refusal.is_refusal)  # True
print(report.refusal.refusal_type)  # "policy_violation"
```

## 7. Testing

Tests: `trust_safety/tests/test_schema_validator.py`, `test_groundedness_checker.py`, `test_refusal_classifier.py`, `test_output_pipeline.py`

Run: `pytest trust_safety/tests/test_schema_validator.py trust_safety/tests/test_groundedness_checker.py trust_safety/tests/test_refusal_classifier.py trust_safety/tests/test_output_pipeline.py -v`

Coverage: Schema edges (arrays, markdown code blocks, value ranges), golden hallucination set (15 outputs), golden refusal set (15 outputs across all 4 types), pipeline integration with audit logging.

## 8. Failure Modes

- **Schema validator**: FAIL-CLOSED. Any validation error → `passed=False`. Retry prompt is generated for the orchestrator to use.
- **Groundedness checker**: FAIL-CLOSED for non-creative domains. If no source_context is provided, score defaults to 1.0 (can't verify what you can't check — logged for audit). Creative domain (0.0 threshold) always passes.
- **Refusal classifier**: Does NOT block. Over-refusal is flagged for review but doesn't prevent the response from being served. This is deliberate — refusing to serve a response because the classifier thinks it's a refusal would create a self-referential loop.
- **PII leak check**: FAIL-CLOSED. Reuses the same Presidio detector as input. Same failure mode as input PII detector (Presidio failure → no findings, effectively fail-open for that detector).

## 9. Related Modules

- Called by: `LLMOrchestrator`, gateway routes
- Calls: `trust_safety.guardrails.input.pii_detector`, `trust_safety.governance.audit_log`
- See also: [../input/README.md](../input/README.md), [../../orchestrator/README.md](../../orchestrator/README.md)
