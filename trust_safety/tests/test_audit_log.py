"""Tests for AuditEntry, AuditQuery, AppendOnlyFileStore, AuditLogger.

This is the most critical test file in Phase 0.  The audit log MUST be:
1. Append-only (no delete, no update)
2. Hash-chained (every entry links to the previous)
3. Tamper-evident (any modification is detected)
"""

import json
from datetime import datetime, timezone

import pytest

from trust_safety.governance.audit_log.models import AuditEntry, AuditQuery
from trust_safety.governance.audit_log.store import (
    AppendOnlyFileStore,
    AuditLogIntegrityError,
    AuditLogger,
    IntegrityReport,
)
from trust_safety.models.base import DataTier
from trust_safety.models.context import ProvenanceTag
from trust_safety.orchestrator.tool_registry import RiskTier


# ==================================================================
# AuditEntry model tests
# ==================================================================

class TestAuditEntryModel:
    """AuditEntry Pydantic model — construction and defaults."""

    def test_minimal_construction(self):
        """Only event_type and action are required."""
        entry = AuditEntry(event_type="llm_call", action="Generated response")
        assert entry.entry_id
        assert len(entry.entry_id) == 36  # UUID v4
        assert entry.timestamp is not None
        assert entry.entry_hash == ""  # Not set by caller

    def test_full_construction(self):
        """All fields settable."""
        prov = ProvenanceTag(
            source_id="s1", source_type="user_input", origin="test"
        )
        entry = AuditEntry(
            event_type="tool_call",
            action="read file",
            agent_id="agent-1",
            user_id="alice",
            session_id="sess-1",
            resource="/tmp/test.txt",
            risk_score=0.5,
            risk_tier=RiskTier.LOW,
            data_tier=DataTier.INTERNAL,
            provenance=prov,
            compliance_profile="gdpr",
            policy_version="v1.0",
            status="allowed",
            metadata={"key": "value"},
        )
        assert entry.user_id == "alice"
        assert entry.risk_tier == RiskTier.LOW
        assert entry.provenance.source_id == "s1"

    def test_json_round_trip(self):
        """Serialization round-trip preserves all fields."""
        entry = AuditEntry(
            event_type="test", action="round trip", user_id="bob",
            risk_score=0.7, status="blocked",
        )
        json_str = entry.model_dump_json()
        data = json.loads(json_str)
        restored = AuditEntry(**data)
        assert restored.event_type == entry.event_type
        assert restored.user_id == entry.user_id
        assert restored.risk_score == 0.7

    def test_entry_hash_not_required(self):
        """entry_hash defaults to empty string (computed by store)."""
        entry = AuditEntry(event_type="test", action="test")
        assert entry.entry_hash == ""

    def test_previous_hash_empty_default(self):
        """previous_hash defaults to empty string."""
        entry = AuditEntry(event_type="test", action="test")
        assert entry.previous_hash == ""

    def test_risk_score_clamped(self):
        """risk_score must be 0.0-1.0."""
        with pytest.raises(ValueError):
            AuditEntry(event_type="test", action="test", risk_score=1.5)
        with pytest.raises(ValueError):
            AuditEntry(event_type="test", action="test", risk_score=-0.1)

    def test_default_status_allowed(self):
        """Default status is 'allowed'."""
        entry = AuditEntry(event_type="test", action="test")
        assert entry.status == "allowed"


# ==================================================================
# AuditQuery model tests
# ==================================================================

class TestAuditQuery:
    """AuditQuery — filter parameters."""

    def test_defaults(self):
        q = AuditQuery()
        assert q.limit == 100
        assert q.offset == 0


# ==================================================================
# AppendOnlyFileStore tests
# ==================================================================

class TestAppendOnlyFileStore:
    """AppendOnlyFileStore — the core immutable store."""

    # -- Basic operations -----------------------------------------------

    def test_append_single(self, audit_store: AppendOnlyFileStore):
        """Appending one entry produces valid JSONL with hashes."""
        entry = AuditEntry(event_type="test", action="first")
        result = audit_store.append(entry)
        assert result.entry_hash
        assert result.previous_hash == ""
        assert audit_store.count() == 1

    def test_append_multiple_chain(self, audit_store: AppendOnlyFileStore):
        """Multiple entries form a valid hash chain."""
        e1 = audit_store.append(AuditEntry(event_type="test", action="one"))
        e2 = audit_store.append(AuditEntry(event_type="test", action="two"))
        e3 = audit_store.append(AuditEntry(event_type="test", action="three"))

        assert e2.previous_hash == e1.entry_hash
        assert e3.previous_hash == e2.entry_hash
        assert audit_store.count() == 3

    def test_read_all_returns_entries_in_order(self, audit_store: AppendOnlyFileStore):
        """read_all yields entries in insertion order."""
        actions = ["alpha", "beta", "gamma"]
        for a in actions:
            audit_store.append(AuditEntry(event_type="test", action=a))

        entries = list(audit_store.read_all())
        assert len(entries) == 3
        assert [e.action for e in entries] == actions

    def test_count(self, audit_store: AppendOnlyFileStore):
        """count returns the correct number of entries."""
        assert audit_store.count() == 0
        audit_store.append(AuditEntry(event_type="test", action="one"))
        assert audit_store.count() == 1
        audit_store.append(AuditEntry(event_type="test", action="two"))
        assert audit_store.count() == 2

    def test_get_last_entry_hash_empty(self, audit_store: AppendOnlyFileStore):
        """Empty store returns empty string."""
        assert audit_store.get_last_entry_hash() == ""

    def test_get_last_entry_hash_populated(self, audit_store: AppendOnlyFileStore):
        """After append, returns the last entry's hash."""
        e = audit_store.append(AuditEntry(event_type="test", action="last"))
        assert audit_store.get_last_entry_hash() == e.entry_hash

    def test_file_created_automatically(self, tmp_path):
        """If the file doesn't exist, it's created."""
        path = tmp_path / "new_subdir" / "audit.jsonl"
        store = AppendOnlyFileStore(path)
        assert path.exists()
        assert store.count() == 0

    def test_read_empty_file(self, audit_store: AppendOnlyFileStore):
        """Reading from an empty file returns nothing."""
        assert list(audit_store.read_all()) == []
        assert audit_store.count() == 0

    # -- Integrity verification ----------------------------------------

    def test_verify_integrity_valid(self, audit_store: AppendOnlyFileStore):
        """Untouched log passes integrity check."""
        for i in range(5):
            audit_store.append(AuditEntry(event_type="test", action=f"entry_{i}"))
        valid, errors = audit_store.verify_integrity()
        assert valid is True
        assert errors == []

    def test_verify_integrity_single_entry(self, audit_store: AppendOnlyFileStore):
        """Single-entry log passes integrity check."""
        audit_store.append(AuditEntry(event_type="test", action="only"))
        valid, errors = audit_store.verify_integrity()
        assert valid is True

    def test_verify_integrity_empty(self, audit_store: AppendOnlyFileStore):
        """Empty log passes integrity check (trivially)."""
        valid, errors = audit_store.verify_integrity()
        assert valid is True

    # -- Tamper detection -----------------------------------------------

    def test_tamper_detection_modified_content(self, audit_store: AppendOnlyFileStore):
        """Manually editing a JSONL line breaks the hash chain."""
        audit_store.append(AuditEntry(event_type="test", action="original"))

        # Read the file, modify a character
        content = audit_store._path.read_text(encoding="utf-8")
        tampered = content.replace("original", "TAMPERED")

        # Write it back directly (bypassing the append-only API)
        audit_store._path.write_text(tampered, encoding="utf-8")

        valid, errors = audit_store.verify_integrity()
        assert valid is False, f"Tampering should be detected! Errors: {errors}"
        assert len(errors) > 0

    def test_tamper_detection_injected_entry(self, audit_store: AppendOnlyFileStore):
        """Adding a fake entry directly to the file is detected."""
        audit_store.append(AuditEntry(event_type="test", action="real"))
        audit_store.append(AuditEntry(event_type="test", action="also real"))

        # Inject a fake entry directly into the file
        fake = AuditEntry(
            event_type="test", action="FAKE",
            previous_hash="0000", entry_hash="1111",
        )
        with open(audit_store._path, "a", encoding="utf-8") as f:
            f.write(fake.model_dump_json() + "\n")

        valid, errors = audit_store.verify_integrity()
        assert valid is False, f"Injected entry should break the chain! Errors: {errors}"

    def test_tamper_detection_hash_change(self, audit_store: AppendOnlyFileStore):
        """Changing just the entry_hash value is detected."""
        entry = audit_store.append(AuditEntry(event_type="test", action="hash_test"))

        # Change the stored hash
        lines = audit_store._path.read_text(encoding="utf-8").strip().split("\n")
        data = json.loads(lines[0])
        data["entry_hash"] = "0000000000000000000000000000000000000000000000000000000000000000"
        audit_store._path.write_text(json.dumps(data) + "\n", encoding="utf-8")

        valid, errors = audit_store.verify_integrity()
        assert valid is False, f"Hash modification should be detected! Errors: {errors}"

    # -- No-delete / no-update enforcement ------------------------------

    def test_no_delete_method(self, audit_store: AppendOnlyFileStore):
        """AppendOnlyFileStore must NOT have a delete method."""
        assert not hasattr(audit_store, "delete"), "Store must not have delete()"
        assert not hasattr(audit_store, "remove"), "Store must not have remove()"

    def test_no_update_method(self, audit_store: AppendOnlyFileStore):
        """AppendOnlyFileStore must NOT have an update method."""
        assert not hasattr(audit_store, "update"), "Store must not have update()"

    def test_no_truncate_method(self, audit_store: AppendOnlyFileStore):
        """AppendOnlyFileStore must NOT have a truncate method."""
        assert not hasattr(audit_store, "truncate"), "Store must not have truncate()"

    # -- Unicode support ------------------------------------------------

    def test_unicode_content(self, audit_store: AppendOnlyFileStore):
        """Entries with unicode content preserve integrity."""
        entry = AuditEntry(
            event_type="test",
            action="ユーザー入力の検証",  # Japanese
            metadata={"emoji": "🔒"},
        )
        result = audit_store.append(entry)
        valid, errors = audit_store.verify_integrity()
        assert valid is True
        # Re-read and check unicode survived
        entries = list(audit_store.read_all())
        assert entries[0].action == "ユーザー入力の検証"


# ==================================================================
# AuditLogger tests
# ==================================================================

class TestAuditLogger:
    """AuditLogger — high-level interface over AppendOnlyFileStore."""

    def test_log_returns_hashed_entry(self, audit_logger: AuditLogger):
        """log() returns entry with hashes populated."""
        entry = AuditEntry(event_type="test", action="logged")
        result = audit_logger.log(entry)
        assert result.entry_hash
        assert result.previous_hash == ""

    def test_query_by_event_type(self, audit_logger: AuditLogger):
        """Query filters by event_type."""
        audit_logger.log(AuditEntry(event_type="llm_call", action="call 1"))
        audit_logger.log(AuditEntry(event_type="tool_call", action="tool 1"))
        audit_logger.log(AuditEntry(event_type="llm_call", action="call 2"))

        q = AuditQuery(event_type="llm_call", limit=100)
        results = audit_logger.query(q)
        assert len(results) == 2
        assert all(r.event_type == "llm_call" for r in results)

    def test_query_by_user_id(self, audit_logger: AuditLogger):
        """Query filters by user_id."""
        audit_logger.log(AuditEntry(event_type="test", action="a", user_id="alice"))
        audit_logger.log(AuditEntry(event_type="test", action="b", user_id="bob"))
        audit_logger.log(AuditEntry(event_type="test", action="c", user_id="alice"))

        q = AuditQuery(user_id="alice", limit=100)
        results = audit_logger.query(q)
        assert len(results) == 2

    def test_query_limit_offset(self, audit_logger: AuditLogger):
        """Query respects limit and offset."""
        for i in range(10):
            audit_logger.log(AuditEntry(event_type="test", action=f"entry_{i}"))

        q = AuditQuery(limit=3, offset=2)
        results = audit_logger.query(q)
        assert len(results) == 3
        assert results[0].action == "entry_2"

    def test_query_by_time_range(self, audit_logger: AuditLogger):
        """Query filters by time range."""
        t1 = datetime(2025, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2025, 6, 1, tzinfo=timezone.utc)
        t3 = datetime(2025, 12, 1, tzinfo=timezone.utc)

        # Entry with known timestamp
        audit_logger.log(AuditEntry(
            event_type="test", action="old", timestamp=t1,
        ))
        audit_logger.log(AuditEntry(
            event_type="test", action="mid", timestamp=t2,
        ))
        audit_logger.log(AuditEntry(
            event_type="test", action="new", timestamp=t3,
        ))

        q = AuditQuery(
            start_time=datetime(2025, 3, 1, tzinfo=timezone.utc),
            end_time=datetime(2025, 9, 1, tzinfo=timezone.utc),
            limit=100,
        )
        results = audit_logger.query(q)
        assert len(results) == 1
        assert results[0].action == "mid"

    def test_query_by_risk_score(self, audit_logger: AuditLogger):
        """Query filters by minimum risk score."""
        audit_logger.log(AuditEntry(event_type="test", action="low", risk_score=0.2))
        audit_logger.log(AuditEntry(event_type="test", action="high", risk_score=0.9))

        q = AuditQuery(risk_score_min=0.5, limit=100)
        results = audit_logger.query(q)
        assert len(results) == 1
        assert results[0].action == "high"

    def test_query_by_status(self, audit_logger: AuditLogger):
        """Query filters by status."""
        audit_logger.log(AuditEntry(event_type="test", action="ok", status="allowed"))
        audit_logger.log(AuditEntry(event_type="test", action="no", status="blocked"))

        q = AuditQuery(status="blocked", limit=100)
        results = audit_logger.query(q)
        assert len(results) == 1
        assert results[0].action == "no"

    def test_verify_integrity_delegates(self, audit_logger: AuditLogger):
        """verify_integrity returns an IntegrityReport."""
        audit_logger.log(AuditEntry(event_type="test", action="verify_me"))
        report = audit_logger.verify_integrity()
        assert isinstance(report, IntegrityReport)
        assert report.valid is True
        assert report.total_entries == 1

    def test_count(self, audit_logger: AuditLogger):
        """count returns correct number."""
        assert audit_logger.count() == 0
        audit_logger.log(AuditEntry(event_type="test", action="one"))
        audit_logger.log(AuditEntry(event_type="test", action="two"))
        assert audit_logger.count() == 2

    def test_read_all(self, audit_logger: AuditLogger):
        """read_all returns all entries as a list."""
        for i in range(3):
            audit_logger.log(AuditEntry(event_type="test", action=f"item_{i}"))
        all_entries = audit_logger.read_all()
        assert len(all_entries) == 3
