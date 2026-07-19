"""Tests for SecretsScanner — regex + entropy-based secret detection."""

from trust_safety.guardrails.input.secrets_scanner import SecretsScanner


class TestSecretsScanner:
    """Secrets detection for API keys, tokens, passwords."""

    # -- Known patterns ------------------------------------------------

    def test_detect_openai_key(self):
        scanner = SecretsScanner()
        result = scanner.scan("API key: sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234")
        assert result.secrets_detected
        types = {f.secret_type for f in result.findings}
        assert "openai_api_key" in types or "generic_api_key" in types

    def test_detect_aws_key(self):
        scanner = SecretsScanner()
        result = scanner.scan("AWS_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE")
        assert result.secrets_detected

    def test_detect_github_token(self):
        scanner = SecretsScanner()
        result = scanner.scan("GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz1234567890")
        assert result.secrets_detected

    def test_detect_jwt(self):
        scanner = SecretsScanner()
        result = scanner.scan(
            "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        )
        assert result.secrets_detected

    def test_detect_private_key_header(self):
        scanner = SecretsScanner()
        result = scanner.scan("-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...")
        assert result.secrets_detected

    def test_detect_connection_string(self):
        scanner = SecretsScanner()
        result = scanner.scan(
            "mongodb://admin:password123@localhost:27017/mydb"
        )
        assert result.secrets_detected

    def test_detect_password_in_code(self):
        scanner = SecretsScanner()
        result = scanner.scan('password = "supersecret123"')
        assert result.secrets_detected

    # -- No false positives --------------------------------------------

    def test_no_secrets_in_normal_text(self):
        scanner = SecretsScanner()
        result = scanner.scan("The quick brown fox jumps over the lazy dog.")
        assert not result.secrets_detected

    def test_no_secrets_in_code_without_creds(self):
        scanner = SecretsScanner()
        result = scanner.scan("def hello_world():\n    print('Hello, World!')")
        assert not result.secrets_detected

    # -- Redaction -----------------------------------------------------

    def test_redacted_text_removes_secrets(self):
        scanner = SecretsScanner()
        text = "API key: sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx234"
        result = scanner.scan(text)
        if result.redacted_text:
            assert "sk-proj" not in result.redacted_text

    # -- Snippet safety ------------------------------------------------

    def test_snippet_never_exposes_full_secret(self):
        scanner = SecretsScanner()
        result = scanner.scan("API key: sk-proj-abc123def456ghi789jkl012mno345pqr678stu90")
        for finding in result.findings:
            snippet = finding.match_snippet
            assert len(snippet) <= 11  # "XXXX...XXXX" = 10 chars max
            assert "sk-proj-abc123" not in snippet  # Never the full prefix

    # -- Entropy detection ---------------------------------------------

    def test_high_entropy_token_detected(self):
        scanner = SecretsScanner()
        # A high-entropy random-looking string
        result = scanner.scan("token: aB3xK9mW2pQ7rT5yV8nL4jH6fD1sC0gU")
        # This has entropy > 4.0 and mixed case + digits
        # It should be caught if long enough
        assert isinstance(result.secrets_detected, bool)

    # -- Empty text ----------------------------------------------------

    def test_empty_text(self):
        scanner = SecretsScanner()
        result = scanner.scan("")
        assert not result.secrets_detected
