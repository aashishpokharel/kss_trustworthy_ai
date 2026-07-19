"""Tests for TokenizationVault — reversible PII anonymization."""

from trust_safety.guardrails.input.tokenization_vault import TokenizationVault


class TestTokenizationVault:
    """Tokenization vault for reversible PII anonymization."""

    def test_tokenize_returns_token(self):
        vault = TokenizationVault(secret_key="test-key")
        token = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert token.startswith("TOK_")
        assert len(token) > 4

    def test_detokenize_round_trip(self):
        vault = TokenizationVault(secret_key="test-key")
        original = "john@example.com"
        token = vault.tokenize(original, "EMAIL_ADDRESS")
        restored = vault.detokenize(token)
        assert restored == original

    def test_detokenize_unknown_returns_none(self):
        vault = TokenizationVault(secret_key="test-key")
        assert vault.detokenize("TOK_nonexistent") is None

    def test_different_keys_produce_different_tokens(self):
        vault1 = TokenizationVault(secret_key="key-alpha")
        vault2 = TokenizationVault(secret_key="key-beta")
        token1 = vault1.tokenize("john@example.com", "EMAIL_ADDRESS")
        token2 = vault2.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert token1 != token2

    def test_same_input_produces_same_token(self):
        vault = TokenizationVault(secret_key="test-key")
        token1 = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        token2 = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert token1 == token2

    def test_different_inputs_produce_different_tokens(self):
        vault = TokenizationVault(secret_key="test-key")
        token1 = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        token2 = vault.tokenize("jane@example.com", "EMAIL_ADDRESS")
        assert token1 != token2

    def test_count_tracks_entries(self):
        vault = TokenizationVault(secret_key="test-key")
        assert vault.count() == 0
        vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert vault.count() == 1
        vault.tokenize("555-1234", "PHONE_NUMBER")
        assert vault.count() == 2
        # Same input doesn't increase count (token is deterministic)
        vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert vault.count() == 2

    def test_revoke_removes_entry(self):
        vault = TokenizationVault(secret_key="test-key")
        token = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert vault.detokenize(token) is not None
        vault.revoke(token)
        assert vault.detokenize(token) is None
        assert vault.count() == 0

    def test_clear_removes_all(self):
        vault = TokenizationVault(secret_key="test-key")
        vault.tokenize("a@b.com", "EMAIL_ADDRESS")
        vault.tokenize("555-1234", "PHONE_NUMBER")
        assert vault.count() == 2
        vault.clear()
        assert vault.count() == 0

    def test_default_secret_key_generated(self):
        vault = TokenizationVault()
        assert vault.secret_key
        assert len(vault.secret_key) == 64  # 32 bytes hex

    def test_entity_type_not_in_token(self):
        """The entity type should not appear in the token."""
        vault = TokenizationVault(secret_key="test-key")
        token = vault.tokenize("john@example.com", "EMAIL_ADDRESS")
        assert "EMAIL_ADDRESS" not in token
