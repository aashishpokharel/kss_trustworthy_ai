"""
CI Eval Runner — Promptfoo-style eval-as-code for regression gating (Section 13).

Runs eval suites (golden injection sets, benign sets, refusal sets, bias sets)
and compares against baselines.  Fails the build on regression past defined
thresholds.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import yaml
from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.models import AuditEntry
from trust_safety.governance.audit_log.store import AuditLogger


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class EvalTest(BaseModel):
    """A single test case in an eval suite."""
    name: str
    input_text: str
    expected_blocked: bool | None = None  # None = informational only
    expected_category: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvalSuite(BaseModel):
    """A named eval suite with tests and regression thresholds."""
    name: str
    description: str = ""
    tests: list[EvalTest] = Field(default_factory=list)
    baseline_block_rate: float = 0.0
    regression_threshold: float = Field(
        default=0.05,
        description="Max allowed drop in block rate before failing (5%)."
    )


class EvalResult(BaseModel):
    """Result of running an eval suite."""
    suite_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    block_rate: float = 0.0
    regression_detected: bool = False
    regression_delta: float = 0.0
    failures: list[dict[str, Any]] = Field(default_factory=list)


# ------------------------------------------------------------------
# EvalRunner
# ------------------------------------------------------------------

class EvalRunner:
    """Run eval suites and check for regression.

    Usage::

        runner = EvalRunner(audit_logger=logger)
        suite = runner.load_suite("eval/suites/injection_suite.yaml")
        result = runner.run_suite(suite)
        if result.regression_detected:
            raise SystemExit("CI gate: regression detected")
    """

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self.audit_logger = audit_logger

    # ------------------------------------------------------------------
    # Suite loading
    # ------------------------------------------------------------------

    def load_suite(self, path: str | Path) -> EvalSuite:
        """Load an eval suite from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        tests = [
            EvalTest(**t) for t in data.get("tests", [])
        ]
        return EvalSuite(
            name=data.get("name", Path(path).stem),
            description=data.get("description", ""),
            tests=tests,
            baseline_block_rate=data.get("baseline_block_rate", 0.0),
            regression_threshold=data.get("regression_threshold", 0.05),
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_suite(self, suite: EvalSuite) -> EvalResult:
        """Run every test in *suite* and return results."""
        from trust_safety.guardrails.input.injection_detector import InjectionDetector

        detector = InjectionDetector(strictness=0.1)
        result = EvalResult(suite_name=suite.name, total_tests=len(suite.tests))
        blocked_count = 0

        for test in suite.tests:
            scan_result = detector.scan(test.input_text)
            blocked = scan_result.is_injection

            if blocked:
                blocked_count += 1

            # Check expectations
            if test.expected_blocked is True and not blocked:
                result.failed += 1
                result.failures.append({
                    "test": test.name,
                    "reason": f"Expected blocked, but passed (risk={scan_result.risk_score:.2f})",
                    "input": test.input_text[:80],
                })
            elif test.expected_blocked is False and blocked:
                result.failed += 1
                result.failures.append({
                    "test": test.name,
                    "reason": f"Expected to pass, but was blocked (risk={scan_result.risk_score:.2f})",
                    "input": test.input_text[:80],
                })
            else:
                result.passed += 1

        # Compute block rate
        if result.total_tests > 0:
            result.block_rate = blocked_count / result.total_tests

        # Check regression
        delta = suite.baseline_block_rate - result.block_rate
        if delta > suite.regression_threshold:
            result.regression_detected = True
            result.regression_delta = delta

        # Audit log
        self._audit_result(result)

        return result

    def check_regression(self, result: EvalResult, baseline: float, threshold: float = 0.05) -> bool:
        """Return True if *result* shows regression past *threshold*."""
        return (baseline - result.block_rate) > threshold

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def _audit_result(self, result: EvalResult) -> None:
        """Log eval run results."""
        if not self.audit_logger:
            return

        entry = AuditEntry(
            event_type="ci_eval_run",
            action=f"Eval suite: {result.suite_name}",
            risk_score=1.0 - result.block_rate,
            status="blocked" if result.regression_detected else "allowed",
            metadata={
                "suite": result.suite_name,
                "total": result.total_tests,
                "passed": result.passed,
                "failed": result.failed,
                "block_rate": result.block_rate,
                "regression": result.regression_detected,
                "regression_delta": result.regression_delta,
            },
        )
        self.audit_logger.log(entry)
