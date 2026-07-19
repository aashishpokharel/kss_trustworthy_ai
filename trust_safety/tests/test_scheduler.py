"""Tests for EvalScheduler — scheduled eval cadence."""

from trust_safety.eval.scheduler import (
    EvalCadence,
    EvalSchedule,
    EvalScheduler,
    EvalTrend,
)


class TestEvalSchedule:
    """Schedule model — due detection, advancement."""

    def test_new_schedule_is_due(self):
        schedule = EvalSchedule(name="test", cadence=EvalCadence.DAILY)
        assert schedule.is_due()

    def test_advance_sets_next_run(self):
        schedule = EvalSchedule(name="test", cadence=EvalCadence.DAILY)
        schedule.advance()
        assert schedule.last_run is not None
        assert schedule.next_run is not None
        assert schedule.next_run > schedule.last_run


class TestEvalTrend:
    """Trend tracking for metrics over time."""

    def test_single_point_stable(self):
        trend = EvalTrend(metric="block_rate")
        trend.add_point(0.95)
        assert trend.direction == "stable"

    def test_improving_detected(self):
        trend = EvalTrend(metric="block_rate")
        trend.add_point(0.80)
        trend.add_point(0.90)
        trend.add_point(0.95)
        assert trend.direction == "improving"

    def test_degrading_detected(self):
        trend = EvalTrend(metric="block_rate")
        trend.add_point(0.95)
        trend.add_point(0.85)
        trend.add_point(0.75)
        assert trend.direction == "degrading"


class TestEvalScheduler:
    """Scheduled eval runner."""

    def test_add_schedule(self):
        scheduler = EvalScheduler()
        schedule = scheduler.add_schedule("daily_injection", EvalCadence.DAILY, [])
        assert schedule.name == "daily_injection"
        assert schedule in scheduler.schedules.values()

    def test_run_due_executes_due_schedules(self):
        scheduler = EvalScheduler()
        scheduler.add_schedule("test_schedule", EvalCadence.DAILY, [])
        results = scheduler.run_due()
        assert "test_schedule" in results

    def test_advances_after_run(self):
        scheduler = EvalScheduler()
        schedule = scheduler.add_schedule("test", EvalCadence.DAILY, [])
        assert schedule.is_due()
        scheduler.run_due()
        assert not schedule.is_due()

    def test_trend_tracking(self):
        scheduler = EvalScheduler()
        scheduler.add_schedule("trend_test", EvalCadence.DAILY, [])
        scheduler.run_due()
        trend = scheduler.get_trend("trend_test")
        assert trend is not None
        assert trend.metric == "block_rate"

    def test_get_next_run(self):
        scheduler = EvalScheduler()
        scheduler.add_schedule("test", EvalCadence.WEEKLY, [])
        scheduler.run_due()
        next_run = scheduler.get_next_run("test")
        assert next_run is not None
