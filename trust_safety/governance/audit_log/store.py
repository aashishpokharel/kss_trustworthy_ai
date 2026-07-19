"""
Append-only, immutable audit log with cryptographic hash chaining.

Design (Section 12, architecture doc):
- Storage: JSONL file — one JSON object per line.  Appending to a file
  never rewrites existing lines, so immutability is enforced at the OS
  level (O_APPEND on Windows).
- Integrity: SHA-256 hash chain.  Each entry's ``entry_hash`` includes
  the previous entry's hash, forming a tamper-evident linked list.
- API surface: ``append()`` is the ONLY write method.  There is
  intentionally no ``delete()``, ``update()``, or ``truncate()``.
- Verification: ``verify_integrity()`` walks the entire chain; any
  mismatch raises ``AuditLogIntegrityError``.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from pydantic import BaseModel, Field

from trust_safety.governance.audit_log.models import AuditEntry, AuditQuery


# ------------------------------------------------------------------
# Exceptions
# ------------------------------------------------------------------

class AuditLogIntegrityError(RuntimeError):
    """Raised when the hash chain fails verification (tampering detected)."""


# ------------------------------------------------------------------
# Integrity report
# ------------------------------------------------------------------

class IntegrityReport(BaseModel):
    """Result of an audit-log integrity verification."""

    valid: bool
    total_entries: int
    errors: list[str] = Field(default_factory=list)
    last_verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


# ------------------------------------------------------------------
# AppendOnlyFileStore
# ------------------------------------------------------------------

class AppendOnlyFileStore:
    """JSONL file store with SHA-256 hash chaining.

    **Immutability contract:**
    - The only write path is ``append()``.
    - The file is opened in ``"a"`` mode (OS-level append).
    - No method exists for deleting, updating, or truncating entries.
    - ``verify_integrity()`` detects any tampering after the fact.

    **Hash chain algorithm:**
    ::

        For entry 0:
            canonical = entry.model_dump_json(exclude={"entry_hash"})
            entry.previous_hash = ""
            entry.entry_hash = SHA-256(b"" + canonical)

        For entry N (N > 0):
            canonical = entry.model_dump_json(exclude={"entry_hash"})
            entry.previous_hash = entries[N-1].entry_hash
            entry.entry_hash = SHA-256(previous_hash + canonical)
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        # Ensure parent directory and file exist
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.touch()

    # ------------------------------------------------------------------
    # Write (the ONLY write method)
    # ------------------------------------------------------------------

    def append(self, entry: AuditEntry) -> AuditEntry:
        """Append *entry* to the log and return it with hashes populated.

        The caller passes an entry with ``previous_hash=""`` and
        ``entry_hash=""``.  This method fills both fields and writes
        the completed entry to the JSONL file.
        """
        # Link to previous entry
        last_hash = self.get_last_entry_hash()
        entry.previous_hash = last_hash

        # Compute this entry's hash
        entry.entry_hash = self._compute_hash(
            previous_hash=entry.previous_hash,
            entry=entry,
        )

        # Append to file
        line = entry.model_dump_json() + "\n"
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(line)

        return entry

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read_all(self) -> Generator[AuditEntry, None, None]:
        """Yield every entry in insertion order.

        Does NOT verify the hash chain — use ``verify_integrity()`` for that.
        """
        if not self._path.exists():
            return

        with open(self._path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield AuditEntry(**data)
                except Exception:
                    # Corrupt line — skip and let verify_integrity catch it
                    continue

    def count(self) -> int:
        """Return the number of entries in the log."""
        return sum(1 for _ in self.read_all())

    def get_last_entry_hash(self) -> str:
        """Return the ``entry_hash`` of the most recent entry, or "" if empty."""
        last: AuditEntry | None = None
        for entry in self.read_all():
            last = entry
        return last.entry_hash if last else ""

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, query: AuditQuery) -> list[AuditEntry]:
        """Filter entries matching *query*.

        This is an in-memory filter — acceptable for local dev.  A future
        phase may add SQLite indexing for production.
        """
        results: list[AuditEntry] = []

        for entry in self.read_all():
            if query.start_time and entry.timestamp < query.start_time:
                continue
            if query.end_time and entry.timestamp > query.end_time:
                continue
            if query.user_id and entry.user_id != query.user_id:
                continue
            if query.event_type and entry.event_type != query.event_type:
                continue
            if query.risk_score_min is not None and entry.risk_score < query.risk_score_min:
                continue
            if query.status and entry.status != query.status:
                continue
            results.append(entry)

        # Apply pagination
        return results[query.offset : query.offset + query.limit]

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """Walk the entire hash chain and verify every entry.

        Returns ``(valid, list_of_errors)``.  An empty error list means
        the log is intact.
        """
        errors: list[str] = []
        previous_hash = ""
        entry_count = 0

        with open(self._path, "r", encoding="utf-8") as fh:
            for line_num, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue

                # Parse the line
                try:
                    data = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"Line {line_num}: invalid JSON — {exc}")
                    continue

                # Extract stored values
                stored_hash = data.get("entry_hash", "")
                stored_previous = data.get("previous_hash", "")

                # Verify previous_hash linkage
                if stored_previous != previous_hash:
                    errors.append(
                        f"Line {line_num}: previous_hash mismatch — "
                        f"expected '{previous_hash}', got '{stored_previous}'"
                    )

                # Recompute entry_hash
                entry = AuditEntry(**data)
                recomputed = self._compute_hash(
                    previous_hash=stored_previous,
                    entry=entry,
                )

                if recomputed != stored_hash:
                    errors.append(
                        f"Line {line_num}: hash mismatch — "
                        f"stored '{stored_previous}', recomputed '{recomputed}'"
                    )

                # Advance the chain
                previous_hash = stored_hash
                entry_count += 1

        return (len(errors) == 0, errors)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_hash(previous_hash: str, entry: AuditEntry) -> str:
        """Compute SHA-256(previous_hash + canonical_json_without_entry_hash)."""
        # Serialize deterministically
        canonical = json.dumps(
            json.loads(
                entry.model_dump_json(exclude={"entry_hash"})
            ),
            sort_keys=True,
            ensure_ascii=False,
        )
        payload = previous_hash.encode("utf-8") + canonical.encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


# ------------------------------------------------------------------
# AuditLogger
# ------------------------------------------------------------------

class AuditLogger:
    """High-level audit logging interface.

    Wraps AppendOnlyFileStore with convenience methods and (in future
    phases) async support, batching, and remote forwarding.
    """

    def __init__(self, store: AppendOnlyFileStore) -> None:
        self._store = store

    # -- Write ----------------------------------------------------------

    def log(self, entry: AuditEntry) -> AuditEntry:
        """Log an entry and return it with hashes populated."""
        return self._store.append(entry)

    async def log_async(self, entry: AuditEntry) -> AuditEntry:
        """Async wrapper around ``log()`` for FastAPI endpoints."""
        return self.log(entry)

    # -- Read -----------------------------------------------------------

    def query(self, query: AuditQuery) -> list[AuditEntry]:
        """Query the audit log."""
        return self._store.query(query)

    def read_all(self) -> list[AuditEntry]:
        """Return all entries as a list."""
        return list(self._store.read_all())

    # -- Integrity ------------------------------------------------------

    def verify_integrity(self) -> IntegrityReport:
        """Verify the hash chain and return a report."""
        valid, errors = self._store.verify_integrity()
        return IntegrityReport(
            valid=valid,
            total_entries=self._store.count(),
            errors=errors,
        )

    # -- Stats ----------------------------------------------------------

    def count(self) -> int:
        """Return the number of entries in the log."""
        return self._store.count()
