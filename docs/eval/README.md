# Eval Module

## 1. Purpose

Evaluation infrastructure: CI regression gating, bias counterfactual testing, and scheduled eval cadence. Architecture doc: Sections 8, 13.

## 2. Public Interface

### CI Eval Runner

**`EvalRunner`** — `trust_safety/eval/ci_runner.py`

| Method | Signature | Description |
|---|---|---|
| `load_suite(path)` | `str \| Path` → `EvalSuite` | Load YAML eval suite. |
| `run_suite(suite)` | `EvalSuite` → `EvalResult` | Execute all tests. Compares block rate against baseline. Flags regression. |
| `check_regression(result, baseline, threshold)` | `EvalResult, float, float` → `bool` | True if block_rate dropped below baseline by more than threshold. |

### Eval Scheduler

**`EvalScheduler`** — `trust_safety/eval/scheduler.py`

| Method | Signature | Description |
|---|---|---|
| `add_schedule(name, cadence, suite_paths)` | `str, EvalCadence, list[str]` → `EvalSchedule` | Register a scheduled eval. |
| `run_due()` | → `dict[str, list[EvalResult]]` | Execute all due schedules. |
| `get_history(schedule_name)` | `str` → `list[EvalResult]` | Past results. |
| `get_trend(schedule_name)` | `str` → `EvalTrend \| None` | Metric trend (improving/stable/degrading). |

### Counterfactual Bias

**`CounterfactualGenerator`** — `trust_safety/eval/counterfactual_bias.py`

| Method | Signature | Description |
|---|---|---|
| `generate(prompt)` | `str` → `list[BiasPair]` | Generate counterfactual pairs by swapping demographic attributes (gender names, ethnicity names, pronouns). |

**`BiasAnalyzer`** — `trust_safety/eval/counterfactual_bias.py`

| Method | Signature | Description |
|---|---|---|
| `analyze(pairs, output_fn, original_outputs, swapped_outputs)` | `list[BiasPair], ...` → `BiasReport` | Compare outputs for sentiment divergence, length divergence, refusal rate delta. Flags if any metric exceeds threshold. |

### Eval Suites

- `eval/suites/injection_suite.yaml` — 8 tests (5 injection + 3 benign), baseline block_rate 1.0, regression threshold 0.05.

## 3. Configuration

No module-specific env vars. Suite paths are passed at runtime. Regression thresholds are per-suite in YAML.

## 4. Data Flow

```
EvalSuite (YAML) → EvalRunner.load_suite()
                 → EvalRunner.run_suite()
                     → for each EvalTest:
                         InjectionDetector.scan(test.input_text)
                         → compare against test.expected_blocked
                 → EvalResult (passed/failed/regression)

EvalScheduler → run_due() → EvalRunner for each schedule → records trends
```

**This module does NOT:**
- Run the full pipeline (eval tests use the injection detector directly, not the guarded LLM call)
- Execute per-provider eval suites (provider-specific eval is declared in the llm-integration doc but not yet wired)

## 5. Dependencies

- **Internal**: `trust_safety.guardrails.input.injection_detector`, `trust_safety.governance.audit_log`
- **External**: `pyyaml` (suite loading)

## 6. Usage Example

```python
from trust_safety.eval.ci_runner import EvalRunner, EvalSuite, EvalTest

runner = EvalRunner()

# Load and run a suite
suite = runner.load_suite("trust_safety/eval/suites/injection_suite.yaml")
result = runner.run_suite(suite)
print(f"Suite: {result.suite_name}")
print(f"Passed: {result.passed}/{result.total_tests}")
print(f"Block rate: {result.block_rate:.1%}")
print(f"Regression: {result.regression_detected}")

# Counterfactual bias
from trust_safety.eval.counterfactual_bias import CounterfactualGenerator, BiasAnalyzer
gen = CounterfactualGenerator()
pairs = gen.generate("John is a good candidate for the engineering role.")
print(f"Generated {len(pairs)} counterfactual pairs")
# → [BiasPair(original="John is...", swapped="Jane is...", dimension="gender"), ...]

analyzer = BiasAnalyzer()
report = analyzer.analyze(
    pairs,
    original_outputs=["John is an excellent candidate."] * len(pairs),
    swapped_outputs=["I cannot help with that request."] * len(pairs),
)
print(f"Refusal divergence: {report.pairs_with_refusal_divergence} pairs")
print(f"Flagged: {report.flagged}")
```

## 7. Testing

Tests: `trust_safety/tests/test_ci_eval.py`, `test_counterfactual_bias.py`, `test_scheduler.py`
Run: `pytest trust_safety/tests/test_ci_eval.py trust_safety/tests/test_counterfactual_bias.py trust_safety/tests/test_scheduler.py -v`
Coverage: Suite loading from YAML, execution + regression detection, counterfactual pair generation (gender/ethnicity/pronouns), bias report computation, schedule creation + due detection + trend tracking.

## 8. Failure Modes

- **Suite YAML not found**: `FileNotFoundError` — caller must handle.
- **Regression detection**: FAIL-CLOSED for CI gating — `regression_detected=True` should fail the build. The threshold is per-suite and configurable.
- **Counterfactual generator**: If no demographic attributes match the prompt, returns empty list — no pairs generated, no bias report. This is a silent gap: if a prompt uses names not in the swap table, bias goes undetected for that prompt.

## 9. Related Modules

- Called by: CI pipeline (external), gateway routes (`/eval/*`)
- Calls: `trust_safety.guardrails.input.injection_detector`
- See also: [../redteam/README.md](../redteam/README.md), [../guardrails/input/README.md](../guardrails/input/README.md)
