"""
Policy Versioning — versioned, changelogged policy documents (Section 13).

Every policy document (constitution, data classification, HITL policy) is
version-controlled with changelogs.  Audit entries reference the active
policy version at decision time, enabling full traceability.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.store import AuditLogger


class PolicyVersion(BaseModel):
    """A specific version of a policy document."""
    version: str
    changelog: list[str] = Field(default_factory=list)
    content_hash: str = ""
    active: bool = False
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PolicyDocument(BaseModel):
    """A versioned policy document."""
    name: str
    path: str
    versions: list[PolicyVersion] = Field(default_factory=list)
    current_version: str = ""


class PolicyVersionTracker:
    """Track policy document versions with changelogs.

    Usage::

        tracker = PolicyVersionTracker(audit_logger=logger)
        tracker.register("constitution", "policy_docs/constitution.md", "1.0.0",
                         changelog=["Initial ratified version"])
    """

    def __init__(self, audit_logger: AuditLogger | None = None) -> None:
        self._documents: dict[str, PolicyDocument] = {}
        self.audit_logger = audit_logger

    def register(
        self,
        name: str,
        path: str,
        version: str,
        changelog: list[str] | None = None,
    ) -> PolicyVersion:
        """Register a new policy version."""
        if name not in self._documents:
            self._documents[name] = PolicyDocument(name=name, path=path)

        doc = self._documents[name]

        # Compute content hash if file exists
        content_hash = ""
        file_path = Path(path)
        if file_path.exists():
            content_hash = hashlib.sha256(
                file_path.read_text(encoding="utf-8").encode()
            ).hexdigest()[:16]

        # Deactivate all existing versions
        for v in doc.versions:
            v.active = False

        pv = PolicyVersion(
            version=version,
            changelog=changelog or [],
            content_hash=content_hash,
            active=True,
        )
        doc.versions.append(pv)
        doc.current_version = version

        self._audit(f"Policy '{name}' version {version} registered")
        return pv

    def get_current(self, name: str) -> PolicyVersion | None:
        doc = self._documents.get(name)
        if not doc:
            return None
        for v in doc.versions:
            if v.active:
                return v
        return None

    def get_history(self, name: str) -> list[PolicyVersion]:
        doc = self._documents.get(name)
        return doc.versions if doc else []

    def activate(self, name: str, version: str) -> PolicyVersion:
        """Activate a specific version (rollback support)."""
        doc = self._documents.get(name)
        if not doc:
            raise ValueError(f"Unknown policy: '{name}'")

        for v in doc.versions:
            v.active = (v.version == version)

        doc.current_version = version
        target = next(v for v in doc.versions if v.version == version)
        self._audit(f"Policy '{name}' activated version {version}")
        return target

    def list_documents(self) -> list[PolicyDocument]:
        return list(self._documents.values())

    def _audit(self, message: str) -> None:
        if not self.audit_logger:
            return
        from trust_safety.governance.audit_log.models import AuditEntry
        entry = AuditEntry(
            event_type="policy_version_change",
            action=message,
            status="allowed",
        )
        self.audit_logger.log(entry)
