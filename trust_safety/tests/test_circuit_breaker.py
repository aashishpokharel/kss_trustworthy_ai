"""Tests for CircuitBreaker — out-of-band emergency stop (Section 9.2)."""

from trust_safety.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
)


class TestCircuitBreaker:
    """Circuit breaker — trip, reset, state isolation."""

    def test_initial_state_closed(self):
        breaker = CircuitBreaker()
        assert breaker.is_operational()
        assert breaker.status().state == CircuitBreakerState.CLOSED

    def test_trip_opens_breaker(self):
        breaker = CircuitBreaker()
        breaker.trip("Suspicious activity detected", "operator-alice")
        assert not breaker.is_operational()
        assert breaker.status().state == CircuitBreakerState.OPEN

    def test_reset_closes_breaker(self):
        breaker = CircuitBreaker()
        breaker.trip("Test trip", "op")
        breaker.reset("op")
        assert breaker.is_operational()
        assert breaker.status().state == CircuitBreakerState.CLOSED

    def test_trip_count_increments(self):
        breaker = CircuitBreaker()
        assert breaker.status().trip_count == 0
        breaker.trip("First", "op")
        assert breaker.status().trip_count == 1
        breaker.reset("op")
        breaker.trip("Second", "op")
        assert breaker.status().trip_count == 2

    def test_status_includes_trip_metadata(self):
        breaker = CircuitBreaker()
        breaker.trip("Emergency — injection wave", "security-team")
        status = breaker.status()
        assert status.current_trip is not None
        assert status.current_trip.reason == "Emergency — injection wave"
        assert status.current_trip.operator == "security-team"

    # -- Tool allow/deny -----------------------------------------------

    def test_readonly_tools_allowed_when_open(self):
        breaker = CircuitBreaker()
        breaker.trip("Test", "op")
        assert breaker.is_tool_allowed("read_file")
        assert breaker.is_tool_allowed("search_code")
        assert breaker.is_tool_allowed("read_directory")

    def test_dangerous_tools_blocked_when_open(self):
        breaker = CircuitBreaker()
        breaker.trip("Test", "op")
        assert not breaker.is_tool_allowed("delete_file")
        assert not breaker.is_tool_allowed("execute_command")
        assert not breaker.is_tool_allowed("send_email")

    def test_all_tools_allowed_when_closed(self):
        breaker = CircuitBreaker()
        assert breaker.is_tool_allowed("delete_file")
        assert breaker.is_tool_allowed("execute_command")

    # -- Audit logging -------------------------------------------------

    def test_trip_logs_to_audit(self, tmp_path):
        from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        breaker = CircuitBreaker(audit_logger=logger)
        breaker.trip("Test trip", "op")
        entries = list(store.read_all())
        assert len(entries) >= 1
        assert entries[-1].event_type == "circuit_breaker"
        assert "TRIPPED" in entries[-1].action

    def test_reset_logs_to_audit(self, tmp_path):
        from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
        store = AppendOnlyFileStore(tmp_path / "audit.jsonl")
        logger = AuditLogger(store)
        breaker = CircuitBreaker(audit_logger=logger)
        breaker.trip("Test", "op")
        breaker.reset("op")
        entries = list(store.read_all())
        assert len(entries) >= 2
        assert "RESET" in entries[-1].action
