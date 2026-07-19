"""
Eval Scheduler — scheduled eval cadence with trend tracking (Section 13).

Supports daily, weekly, and monthly cadences.  Tracks metric trends over
time to detect drift even when individual runs pass.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from trust_safety.eval.ci_runner import EvalResult
from trust_safety.governance.audit_log.store import AuditLogger


class EvalCadence(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class EvalSchedule(BaseModel):
    """A scheduled eval run."""
    name: str
    cadence: EvalCadence
    suite_paths: list[str] = Field(default_factory=list)
    last_run: datetime | None = None
    next_run: datetime | None = None

    def is_due(self) -> bool:
        """Is this schedule due for execution?"""
        if self.next_run is None:
            return True
        return datetime.now(timezone.utc) >= self.next_run

    def advance(self) -> None:
        """Advance last_run/next_run after execution."""
        now = datetime.now(timezone.utc)
        self.last_run = now
        if self.cadence == EvalCadence.DAILY:
            self.next_run = now + timedelta(days=1)
        elif self.cadence == EvalCadence.WEEKLY:
            self.next_run = now + timedelta(weeks=1)
        elif self.cadence == EvalCadence.MONTHLY:
            self.next_run = now + timedelta(days=30)


class EvalTrend(BaseModel):
    """Metric trend over time."""
    metric: str
    values: list[float] = Field(default_factory=list)
    timestamps: list[datetime] = Field(default_factory=list)
    direction: str = "stable"  # improving, stable, degrading

    def add_point(self, value: float) -> None:
        self.values.append(value)
        self.timestamps.append(datetime.now(timezone.utc))
        self._update_direction()

    def _update_direction(self) -> None:
        if len(self.values) < 2:
            self.direction = "stable"
            return
        recent = self.values[-3:] if len(self.values) >= 3 else self.values
        if len(recent) >= 2 and recent[-1] > recent[0]:
            self.direction = "improving"
        elif len(recent) >= 2 and recent[-1] < recent[0]:
            self.direction = "degrading"
        else:
            self.direction = "stable"


class EvalScheduler:
    """Scheduled eval runner with trend tracking.

    Usage::

        scheduler = EvalScheduler(audit_logger=logger)
        scheduler.add_schedule("weekly_injection", EvalCadence.WEEKLY, ["suites/injection.yaml"])
        results = scheduler.run_due()
    """

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self.schedules: dict[str, EvalSchedule] = {}
        self._history: dict[str, list[EvalResult]] = {}
        self._trends: dict[str, EvalTrend] = {}
        self.audit_logger = audit_logger

    def add_schedule(
        self, name: str, cadence: EvalCadence, suite_paths: list[str]
    ) -> EvalSchedule:
        schedule = EvalSchedule(name=name, cadence=cadence, suite_paths=suite_paths)
        self.schedules[name] = schedule
        self._history[name] = []
        self._trends[name] = EvalTrend(metric="block_rate")
        return schedule

    def run_due(self) -> dict[str, list[EvalResult]]:
        """Run all schedules that are due. Returns {schedule_name: [results]}."""
        from trust_safety.eval.ci_runner import EvalRunner
        runner = EvalRunner(audit_logger=self.audit_logger)
        results: dict[str, list[EvalResult]] = {}

        for name, schedule in self.schedules.items():
            if schedule.is_due():
                suite_results: list[EvalResult] = []
                for suite_path in schedule.suite_paths:
                    try:
                        suite = runner.load_suite(suite_path)
                        result = runner.run_suite(suite)
                        suite_results.append(result)
                        # Track trend
                        self._trends[name].add_point(result.block_rate)
                    except Exception:
                        pass  # Skip failed suite loads in scheduled mode
                results[name] = suite_results
                self._history[name].extend(suite_results)
                schedule.advance()

        return results

    def get_history(self, schedule_name: str) -> list[EvalResult]:
        return self._history.get(schedule_name, [])

    def get_trend(self, schedule_name: str) -> EvalTrend | None:
        return self._trends.get(schedule_name)

    def get_next_run(self, schedule_name: str) -> datetime | None:
        schedule = self.schedules.get(schedule_name)
        return schedule.next_run if schedule else None
