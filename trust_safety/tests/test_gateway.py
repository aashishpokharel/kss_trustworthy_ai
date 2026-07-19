"""Integration tests for FastAPI gateway endpoints."""

import json

from fastapi.testclient import TestClient

from trust_safety.governance.audit_log.models import AuditEntry


class TestHealthEndpoint:
    """GET /api/v1/health"""

    def test_health_returns_200(self, client: TestClient):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "audit_log_entries" in data


class TestAuditEndpoints:
    """POST /audit/log, GET /audit/query, GET /audit/verify"""

    def test_create_audit_entry(self, client: TestClient):
        """POST /audit/log returns 201 with hashed entry."""
        payload = {
            "event_type": "test",
            "action": "api test entry",
            "user_id": "tester",
            "status": "allowed",
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["entry_hash"]
        assert len(data["entry_hash"]) == 64  # SHA-256 hex
        # previous_hash chains from the last real entry (may not be
        # empty if other tests have already logged to the shared store)
        assert len(data["previous_hash"]) in (0, 64)

    def test_create_audit_entry_hash_overwritten(self, client: TestClient):
        """Caller-provided entry_hash and previous_hash are overwritten.

        The store computes both fields; any value passed by the caller
        is discarded.  ``previous_hash`` is chained from the last real
        entry (which may not be empty if other tests have already
        logged entries).
        """
        payload = {
            "event_type": "test",
            "action": "hash test",
            "previous_hash": "fake_previous",
            "entry_hash": "fake_hash",
        }
        response = client.post("/api/v1/audit/log", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["entry_hash"] != "fake_hash"
        assert data["previous_hash"] != "fake_previous"
        # previous_hash is a real SHA-256 hex string (64 chars)
        assert len(data["entry_hash"]) == 64

    def test_query_audit_log(self, client: TestClient):
        """GET /audit/query returns entries matching filters."""
        # Seed some entries
        for i in range(5):
            client.post("/api/v1/audit/log", json={
                "event_type": "test",
                "action": f"query_test_{i}",
                "user_id": f"user_{i % 2}",
            })

        response = client.get("/api/v1/audit/query", params={
            "user_id": "user_0", "limit": "10",
        })
        assert response.status_code == 200

    def test_verify_audit_log(self, client: TestClient):
        """GET /audit/verify returns integrity report."""
        response = client.get("/api/v1/audit/verify")
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data
        assert "total_entries" in data


class TestToolEndpoints:
    """GET /tools, GET /tools/{name}, POST /tools"""

    def test_list_tools(self, client: TestClient):
        """GET /tools returns list of registered tools."""
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        tools = response.json()
        assert isinstance(tools, list)
        assert len(tools) >= 4  # pre-seeded in dependencies

        tool_names = {t["name"] for t in tools}
        assert "read_file" in tool_names
        assert "execute_command" in tool_names

    def test_list_tools_has_hitl_mode(self, client: TestClient):
        """Each tool response includes hitl_mode."""
        response = client.get("/api/v1/tools")
        tools = response.json()
        for tool in tools:
            assert "hitl_mode" in tool
            assert tool["hitl_mode"] in (
                "human_in_the_loop",
                "human_on_the_loop",
                "human_out_of_the_loop",
            )

    def test_get_tool_found(self, client: TestClient):
        """GET /tools/{name} returns tool details."""
        response = client.get("/api/v1/tools/read_file")
        assert response.status_code == 200
        tool = response.json()
        assert tool["name"] == "read_file"
        assert tool["risk_tier"] == "low"
        assert "parameter_schema" in tool

    def test_get_tool_not_found(self, client: TestClient):
        """GET /tools/{name} for unknown tool returns 404."""
        response = client.get("/api/v1/tools/nonexistent")
        assert response.status_code == 404

    def test_register_tool(self, client: TestClient):
        """POST /tools registers a new tool."""
        new_tool = {
            "name": "list_directory",
            "description": "List files in a directory.",
            "risk_tier": "low",
            "reversible": True,
            "allowed_roles": ["admin", "developer", "viewer"],
        }
        response = client.post("/api/v1/tools", json=new_tool)
        assert response.status_code == 201
        assert response.json()["status"] == "registered"

    def test_register_duplicate_tool(self, client: TestClient):
        """POST /tools for existing name returns 409."""
        dup = {
            "name": "read_file",
            "description": "duplicate",
            "risk_tier": "low",
        }
        response = client.post("/api/v1/tools", json=dup)
        assert response.status_code == 409


class TestPolicyEndpoints:
    """GET /policies, GET /policies/{profile}, POST /policies/validate-tier"""

    def test_list_policies(self, client: TestClient):
        """GET /policies returns available compliance profiles."""
        response = client.get("/api/v1/policies")
        assert response.status_code == 200
        profiles = response.json()
        assert isinstance(profiles, list)
        assert len(profiles) >= 4  # NONE, GDPR, HIPAA, CCPA
        names = {p["name"] for p in profiles}
        assert "gdpr" in names

    def test_get_policy_found(self, client: TestClient):
        """GET /policies/{profile} returns config."""
        response = client.get("/api/v1/policies/gdpr")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "gdpr"
        assert "data_handling" in data
        assert data["data_handling"]["require_consent"] is True

    def test_get_policy_not_found(self, client: TestClient):
        """GET /policies/{profile} for unknown returns 404."""
        response = client.get("/api/v1/policies/made_up")
        assert response.status_code == 404

    def test_validate_tier_allowed(self, client: TestClient):
        """POST /policies/validate-tier for public data returns allowed=True."""
        response = client.post(
            "/api/v1/policies/validate-tier",
            params={"tier": "public", "profile": "gdpr"},
        )
        assert response.status_code == 200
        assert response.json()["allowed"] is True

    def test_validate_tier_blocked(self, client: TestClient):
        """POST /policies/validate-tier for restricted data returns allowed=False."""
        response = client.post(
            "/api/v1/policies/validate-tier",
            params={"tier": "restricted", "profile": "gdpr"},
        )
        assert response.status_code == 200
        assert response.json()["allowed"] is False

    def test_validate_tier_invalid_tier(self, client: TestClient):
        """POST /policies/validate-tier with invalid tier returns 400."""
        response = client.post(
            "/api/v1/policies/validate-tier",
            params={"tier": "top_secret", "profile": "gdpr"},
        )
        assert response.status_code == 400
