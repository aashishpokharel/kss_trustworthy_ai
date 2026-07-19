# Trust & Safety Layer — Developer Documentation

**Version:** 0.1.0 | **Tests:** 439 passing | **Last updated:** 2026-07-19

## Architecture

The system is a six-stage pipeline with a cross-cutting governance plane, per
[ai-trust-safety-architecture.md](../ai_trust_safety_architecture.md), Section 1:

```
User → [1] Gateway → [2] Input Guardrails → [3] Orchestrator → [4] LLM Core → [5] Output Guardrails → [6] Action/Tool Layer → Response
                              ↑                                        ↑                       ↑
                              └──────────── Governance Plane ──────────┴───────────────────────┘
```

An LLM integration layer ([llm-integration-architecture.md](../llm-integration-architecture.md))
sits at stage 3.5, providing provider abstraction and real API call handling.

## Module Map

| Module | Path | Status | Doc |
|---|---|---|---|
| **Gateway** | `trust_safety/gateway/` | ✅ Complete | [gateway/README.md](gateway/README.md) |
| **Input Guardrails** | `trust_safety/guardrails/input/` | ✅ Complete | [guardrails/input/README.md](guardrails/input/README.md) |
| **Output Guardrails** | `trust_safety/guardrails/output/` | ✅ Complete | [guardrails/output/README.md](guardrails/output/README.md) |
| **Orchestrator** | `trust_safety/orchestrator/` | ✅ Complete | [orchestrator/README.md](orchestrator/README.md) |
| **Governance** | `trust_safety/governance/` | ✅ Complete | [governance/README.md](governance/README.md) |
| **Red Team** | `trust_safety/redteam/` | ⚠️ Config-only | [redteam/README.md](redteam/README.md) |
| **Eval** | `trust_safety/eval/` | ✅ Complete | [eval/README.md](eval/README.md) |
| **LLM Integration** | `trust_safety/llm/` | ✅ Complete | [llm-integration/README.md](llm-integration/README.md) |
| **UI** | `ui/` | ✅ Complete | [ui/README.md](ui/README.md) |
| **Models** | `trust_safety/models/` | ✅ Complete | (see gateway/README.md) |
| **Policies** | `trust_safety/policies/` | ✅ Complete | (see orchestrator/README.md) |
| **Config** | `trust_safety/config.py` | ✅ Complete | (see gateway/README.md) |

## Quick Start

```powershell
cd D:\FUSE\trustworthy_ai
$env:PYTHONPATH="D:\FUSE\trustworthy_ai"

# Run all tests
.\venv\Scripts\python.exe -m pytest trust_safety/tests/ -v

# Start API server
.\venv\Scripts\python.exe -m uvicorn trust_safety.main:app --host 127.0.0.1 --port 8000 --reload

# Start Streamlit UI
.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.port 8501
```

API docs at `http://localhost:8000/docs` (auto-generated OpenAPI).

## Key Design Principles

1. **Defense in depth** — no single component is "the" safety layer. Input and output are independently guarded.
2. **Fail-closed** — every guardrail defaults to blocking when uncertain. Timeout = denial, not auto-approval.
3. **Append-only audit** — every decision is logged immutably with SHA-256 hash chaining. No delete or update.
4. **Provider-agnostic** — guardrails run on text, not provider internals. All clients normalize to `LLMResponse`.
5. **Config-driven** — compliance profiles, provider selection, and HITL modes are set via environment variables, not code changes.

## Consolidated Implementation Status

See individual module docs for details. Notable gaps and divergences from the architecture docs:

| Item | Status |
|---|---|
| Garak/PyRIT runtime execution | **Not yet implemented** — configs exist, runner is ours, but actual Garak/PyRIT CLI not integrated |
| Streaming output guardrails (§7 of llm-integration doc) | **Not yet implemented** — all guardrails assume complete response |
| Shadow/canary traffic splitting (§5 of llm-integration doc) | **Not yet implemented** — mechanism in config, not wired to a traffic router |
| Cost ceiling auto-enforcement (§4 of llm-integration doc) | **Not yet implemented** — declared in config, not enforced at runtime |
| Two-pass verification for high-risk outputs (§2 of main doc) | **Not yet implemented** |
| Multi-turn attack state tracking (§9.1 of main doc) | **Not yet implemented** |
| DeepSeek via OpenAI-compatible endpoint (§2 of llm-integration doc) | **Diverges** — DeepSeek client built, but actual integration uses Anthropic-compatible endpoint instead |
| Red-team eval per-provider (§2.1 of llm-integration doc) | **Not yet implemented** — eval suites run, but not per-provider independently |
