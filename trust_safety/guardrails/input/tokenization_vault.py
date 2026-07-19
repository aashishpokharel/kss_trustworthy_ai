"""
Tokenization Vault — reversible PII anonymization (Section 5).

When PII must be reconstituted later (e.g., customer support needs the
real email to respond), use tokenization instead of irreversible redaction.

The vault is keyed separately from the audit log — PII tokens must never
share storage with the audit trail (security boundary).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from pydantic import BaseModel, Field


class TokenizationVault(BaseModel):
    """Reversible PII tokenization with cryptographically keyed tokens.

    Usage::

        vault = TokenizationVault(secret_key="my-secret")
        token = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        # → "TOK_a1b2c3d4..."

        original = vault.detokenize(token)
        # → "john@example.com"
    """

    secret_key: str = Field(
        description="HMAC key for token derivation.  Keep this separate "
                    "from the audit log and NEVER commit to source control."
    )
    _store: dict[str, str] = {}  # token → original_value

    def __init__(self, secret_key: str | None = None, **data: Any):
        if secret_key is None:
            secret_key = secrets.token_hex(32)
        super().__init__(secret_key=secret_key, **data)

    # ------------------------------------------------------------------
    # Tokenize / detokenize
    # ------------------------------------------------------------------

    def tokenize(self, entity_value: str, entity_type: str) -> str:
        """Replace *entity_value* with a reversible token.

        The token is derived via HMAC-SHA256 so it cannot be reversed
        without the secret key.  The mapping is stored in-memory.
        """
        token = self._derive_token(entity_value)
        self._store[token] = entity_value
        return token

    def detokenize(self, token: str) -> str | None:
        """Reverse a token back to the original value.

        Returns None if the token is unknown.
        """
        return self._store.get(token)

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def revoke(self, token: str) -> None:
        """Delete a token mapping (right-to-forget)."""
        self._store.pop(token, None)

    def clear(self) -> None:
        """Clear all token mappings."""
        self._store.clear()

    def count(self) -> int:
        """Number of tokens in the vault."""
        return len(self._store)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _derive_token(self, value: str) -> str:
        """Derive a deterministic token from *value* using HMAC-SHA256."""
        h = hmac.new(
            self.secret_key.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256,
        )
        return f"TOK_{h.hexdigest()[:24]}"
