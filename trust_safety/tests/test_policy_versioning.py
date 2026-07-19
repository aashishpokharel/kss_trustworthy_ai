"""Tests for PolicyVersionTracker — versioned policy documents."""

from trust_safety.governance.audit_log.store import AppendOnlyFileStore, AuditLogger
from trust_safety.governance.policy_versioning import PolicyVersionTracker


class TestPolicyVersionTracker:
    """Policy versioning with changelogs."""

    def test_register_first_version(self):
        tracker = PolicyVersionTracker()
        pv = tracker.register("constitution", "policy_docs/constitution.md", "1.0.0",
                              changelog=["Initial version"])
        assert pv.version == "1.0.0"
        assert pv.active
        assert "Initial version" in pv.changelog

    def test_register_new_version_deactivates_old(self):
        tracker = PolicyVersionTracker()
        tracker.register("constitution", "policy_docs/constitution.md", "1.0.0")
        tracker.register("constitution", "policy_docs/constitution.md", "1.1.0",
                         changelog=["Added circuit breaker section"])

        current = tracker.get_current("constitution")
        assert current.version == "1.1.0"

    def test_get_history(self):
        tracker = PolicyVersionTracker()
        tracker.register("data_policy", "policies/data.yaml", "1.0.0")
        tracker.register("data_policy", "policies/data.yaml", "2.0.0")
        history = tracker.get_history("data_policy")
        assert len(history) == 2

    def test_activate_rollback(self):
        tracker = PolicyVersionTracker()
        tracker.register("test_policy", "test.md", "1.0.0")
        tracker.register("test_policy", "test.md", "2.0.0")
        tracker.activate("test_policy", "1.0.0")
        current = tracker.get_current("test_policy")
        assert current.version == "1.0.0"

    def test_get_current_unknown(self):
        tracker = PolicyVersionTracker()
        assert tracker.get_current("nonexistent") is None

    def test_list_documents(self):
        tracker = PolicyVersionTracker()
        tracker.register("doc_a", "a.md", "1.0.0")
        tracker.register("doc_b", "b.md", "1.0.0")
        docs = tracker.list_documents()
        assert len(docs) == 2

    def test_content_hash_computed(self):
        tracker = PolicyVersionTracker()
        pv = tracker.register("constitution", "trust_safety/governance/policy_docs/constitution.md", "1.0.0")
        assert len(pv.content_hash) == 16  # SHA-256 truncated to 16 chars
