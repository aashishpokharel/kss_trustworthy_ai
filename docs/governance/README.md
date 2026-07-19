# Governance Module

## 1. Purpose

The cross-cutting governance plane. Provides the append-only audit log (SHA-256 hash-chained), metrics dashboard, incident review, policy versioning, and the system constitution. Architecture doc: Sections 12, 13.

## 2. Public Interface

### Audit Log

**`AppendOnlyFileStore`** — `trust_safety/governance/audit_log/store.py`

| Method | Signature | Description |
|---|---|---|
| `append(entry)` | `entry: AuditEntry` → `AuditEntry` | Append to JSONL file. Computes `previous_hash` + `entry_hash`. Returns entry with hashes. |
| `read_all()` | → `Generator[AuditEntry]` | Yield all entries in insertion order. |
| `count()` | → `int` | Number of entries. |
| `query(query)` | `query: AuditQuery` → `list[AuditEntry]` | Filter by event_type, user_id, time range, risk score, status. |
| `verify_integrity()` | → `(bool, list[str])` | Walk hash chain. Returns (valid, errors). |
| `get_last_entry_hash()` | → `str` | SHA-256 of the most recent entry, or "". |

**Immutability**: Only `append()` writes. No `delete()`, `update()`, `truncate()` methods exist. Opening in `"a"` mode enforces OS-level append.

**`AuditLogger`** — wraps `AppendOnlyFileStore` with `log()`, `log_async()`, `query()`, `verify_integrity()`, `count()`, `read_all()`.

**`AuditEntry`** fields: `entry_id` (UUID), `timestamp`, `event_type`, `action`, `resource`, `agent_id`, `user_id`, `session_id`, `risk_score` (0-1), `risk_tier`, `data_tier`, `provenance`, `compliance_profile`, `policy_version`, `status`, `metadata`, `previous_hash`, `entry_hash`.

### Dashboard

**`MetricsCollector`** — `trust_safety/governance/dashboard.py`

| Method | Signature | Description |
|---|---|---|
| `get_metrics(hours)` | `hours: int = 24` → `DashboardMetrics` | Aggregated stats: block rate, injection attempts, PII leaks, groundedness avg, refusal rate, HITL stats, breaker trips. |
| `get_summary()` | → `AuditSummary` | Total entries, integrity status, first/last entry times, top event types. |

### Incident Review

**`IncidentTracker`** — `trust_safety/governance/incident_review.py`

| Method | Signature | Description |
|---|---|---|
| `report(title, description, severity, source, reported_by)` | `str, str, IncidentSeverity, IncidentSource, str` → `Incident` | File a new incident. |
| `investigate(incident_id, findings)` | `str, list[str]` → `Incident` | Add findings. |
| `resolve(incident_id, remediation, golden_set_updates)` | `str, str, list[str]` → `Incident` | Resolve with remediation. Golden set updates feed new test cases back into eval suites. |
| `wont_fix(incident_id, reason)` | `str, str` → `Incident` | Mark as won't fix. |
| `list_open()` | → `list[Incident]` | Active (open + investigating) incidents. |
| `get_trends()` | → `dict[str, int]` | Incident counts by severity. |

### Policy Versioning

**`PolicyVersionTracker`** — `trust_safety/governance/policy_versioning.py`

| Method | Signature | Description |
|---|---|---|
| `register(name, path, version, changelog)` | `str, str, str, list[str]` → `PolicyVersion` | Register a new version. Auto-deactivates old versions. Content hash computed from file. |
| `get_current(name)` | `str` → `PolicyVersion \| None` | Active version. |
| `get_history(name)` | `str` → `list[PolicyVersion]` | All versions with changelogs. |
| `activate(name, version)` | `str, str` → `PolicyVersion` | Rollback to a specific version. |

## 3. Configuration

| Variable | Default | Notes |
|---|---|---|
| `TS_AUDIT_LOG_PATH` | `./data/audit_log.jsonl` | File path for the JSONL audit log |
| `TS_AUDIT_LOG_VERIFY_ON_READ` | `True` | Verify hash chain on every read |

## 4. Data Flow

```
Every action → AuditLogger.log(AuditEntry)
                    ↓
              AppendOnlyFileStore.append()
                    ↓
              JSONL line with SHA-256 hash chain

MetricsCollector reads from AuditLogger → computes stats from raw entries
IncidentTracker writes Incident events to AuditLogger
PolicyVersionTracker writes version_change events to AuditLogger
```

**This module does NOT:**
- Enforce data retention (max_retention_days is declared in policy config, not enforced)
- Rotate or archive audit logs (single file, grows indefinitely)
- Provide a database backend (local dev uses JSONL; production would need migration)

## 5. Dependencies

- **Internal**: `trust_safety.models` (DataTier, ProvenanceTag, RiskTier)
- **External**: None beyond stdlib (`hashlib`, `json`, `pathlib`). No database driver.

> **Design rationale**: JSONL + hash chaining chosen over SQLite per architecture doc — append-only by construction, no delete/update surface, cryptographic integrity verification. A future production phase can add SQLite/Postgres while keeping the same `AuditLogger` interface.

## 6. Usage Example

```python
from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from trust_safety.governance.audit_log.models import AuditEntry, AuditQuery
from pathlib import Path

store = AppendOnlyFileStore(Path("./data/audit.jsonl"))
logger = AuditLogger(store)

# Log an entry
entry = AuditEntry(event_type="llm_call", action="Generated response",
                   user_id="alice", status="allowed", risk_score=0.1)
logged = logger.log(entry)
print(logged.entry_hash)  # SHA-256 hex
print(logged.previous_hash)  # Previous entry's hash ("" for first)

# Query
results = logger.query(AuditQuery(event_type="llm_call", limit=10))
print(len(results))

# Verify integrity
report = logger.verify_integrity()
print(report.valid)  # True if hash chain intact

# Metrics
from trust_safety.governance.dashboard import MetricsCollector
collector = MetricsCollector(logger)
metrics = collector.get_metrics(hours=24)
print(f"Block rate: {metrics.block_rate:.1%}")
print(f"Injection attempts: {metrics.injection_attempts}")
```

## 7. Testing

Tests: `trust_safety/tests/test_audit_log.py`, `test_dashboard.py`, `test_incident_review.py`, `test_policy_versioning.py`

Run: `pytest trust_safety/tests/test_audit_log.py trust_safety/tests/test_dashboard.py trust_safety/tests/test_incident_review.py trust_safety/tests/test_policy_versioning.py -v`

Coverage: Hash chain correctness, tamper detection (manual JSONL corruption → verify fails), no-delete enforcement, query filtering (by type/user/time/risk/status), unicode content integrity. Dashboard metrics computation from seeded audit entries. Incident lifecycle. Policy version registration/activation/history.

## 8. Failure Modes

- **Audit log integrity**: Tampered entries are detected by `verify_integrity()` (hash mismatch or previous_hash break). In production, startup checks integrity — if it fails, the server refuses to start (fail-closed).
- **File not found**: `AppendOnlyFileStore.__init__` creates the file and parent directory automatically.
- **Disk full**: `append()` raises `OSError` — caller must handle. The guardrail pipeline catches exceptions and logs them but does NOT fail the request (the request is blocked by the guardrail, not the audit failure — this is a known risk: a full disk could allow unlogged requests through).

## 9. Related Modules

- Called by: every other module (audit log), Streamlit UI (dashboard)
- Calls: (leaf module — depends only on models)
- See also: [../orchestrator/README.md](../orchestrator/README.md) (for HITL/policy gate which also write to audit log)
