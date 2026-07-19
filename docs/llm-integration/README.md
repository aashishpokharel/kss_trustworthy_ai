# LLM Integration Module

## 1. Purpose

The provider abstraction layer that sits between the Orchestrator (stage [3]) and the real LLM API call (stage [4]). Provides a swappable `LLMClient` interface with mock, Anthropic, and DeepSeek implementations, a provider router, retry/failure handling, and the `LLMOrchestrator` that wires the full input→LLM→output pipeline. Architecture doc: `llm-integration-architecture.md` (addendum).

## 2. Public Interface

### Core Models

**`LLMConfig`** — `trust_safety/llm/models.py`
| Field | Type | Default | Description |
|---|---|---|---|
| `provider` | `str` | `"mock"` | Provider identifier |
| `model` | `str` | `"claude-sonnet-5"` | Model name |
| `base_url` | `str` | `""` | API base URL override |
| `api_key` | `str` | `""` | API key (never hardcode) |
| `max_tokens` | `int` | `4096` | Max tokens per response |
| `temperature` | `float` | `0.0` | Sampling temperature |
| `timeout_seconds` | `int` | `60` | Request timeout |
| `max_retries` | `int` | `3` | Retry count for transient errors |
| `cost_ceiling_daily_usd` | `float` | `50.0` | Daily cost cap (declared, not enforced) |
| `zero_retention_enabled` | `bool` | `False` | Provider confirmed no-train/zero-retention |

**`LLMResponse`** — `trust_safety/llm/models.py`
| Field | Type | Description |
|---|---|---|
| `text` | `str` | Response text |
| `tool_calls` | `list[ToolCall]` | Extracted tool invocations |
| `stop_reason` | `str` | end_turn, max_tokens, tool_use, stop_sequence, refusal |
| `usage` | `Usage` | input_tokens, output_tokens |
| `latency_ms` | `float` | Round-trip time |
| `provider_name` | `str` | Which provider served this |
| `model_name` | `str` | Which model was used |

### Client Interface

**`LLMClient`** (ABC) — `trust_safety/llm/client.py`

| Method | Signature | Description |
|---|---|---|
| `generate(messages, tools, stream)` | `list[dict], list[dict]\|None, bool` → `LLMResponse` | Abstract — must be implemented. |
| `health_check()` | → `bool` | Quick connectivity test. Default: sends "Hi" and checks for non-empty response. |

### Implementations

**`MockLLMClient`** — `trust_safety/llm/mock_client.py`
- Pattern-matched canned responses. `add_response(pattern, text)` or `add_response(pattern, tool_call=tc)`.
- `set_default(text)` for fallback. `on_generate(callback)` for test assertions.
- `call_count` property for verifying test interactions.

**`AnthropicLLMClient`** — `trust_safety/llm/anthropic_client.py`
- Wraps `anthropic` Python SDK. Lazy-initializes the client on first call.
- **Also handles DeepSeek**: set `base_url="https://api.deepseek.com/anthropic"` and `model="deepseek-v4-pro[1m]"`.
- Fails closed: raises `ValueError` if `api_key` is empty.
- Extracts text + tool_calls from Anthropic content blocks.
- Translates common errors: 401→`RuntimeError("auth failed")`, 429→`RuntimeError("rate limited")`, timeout→`TimeoutError`.

**`DeepSeekLLMClient`** — `trust_safety/llm/deepseek_client.py`
- Wraps `openai` Python SDK pointed at DeepSeek's `https://api.deepseek.com/v1`.
- Uses OpenAI-compatible chat/completions format.
- Converts tools to OpenAI function format. Normalizes response to `LLMResponse`.

> **Divergence note**: The llm-integration doc specifies DeepSeek via OpenAI-compatible format. The current production setup uses DeepSeek via the Anthropic-compatible Messages API endpoint (`api.deepseek.com/anthropic`). Both clients exist; the Anthropic path is what's wired in `.env`.

### Provider Router

**`ProviderRouter`** — `trust_safety/llm/router.py`

| Method | Signature | Description |
|---|---|---|
| `route(task_type)` | `str\|None` → `LLMClient` | Select client per routing policy. |
| `list_clients()` | → `list[LLMClient]` | All registered clients. |

**Routing policies** (enum `RoutingPolicy`):
| Policy | Behavior |
|---|---|
| `fixed_default` | Always use the configured default_provider |
| `task_based` | Code/analysis → primary; chat → secondary |
| `cost_based` | Prefer secondary (assumed cheaper) |
| `fallback_only` | Primary always; secondary only on failure |

### Retry & Failure Handling

**`with_retry(call, max_retries, backoff_base)`** — `trust_safety/llm/retry.py`
- Exponential backoff with jitter. Retries on `TimeoutError` and rate-limit errors.
- Does NOT retry on auth errors (401) or bad requests (400).
- Raises the last exception if all retries exhausted.

**`AvailabilityBreaker`** — `trust_safety/llm/retry.py`
- Separate from the safety circuit breaker in orchestrator.
- Trips after N consecutive failures. Allows one probe request in HALF_OPEN state.

### LLM Orchestrator

**`LLMOrchestrator`** — `trust_safety/llm/orchestrator.py`

| Method | Signature | Description |
|---|---|---|
| `generate(user_input, source_context, expected_schema, tools)` | `str, str\|None, dict\|None, list[dict]\|None` → `OrchestratorResult` | **The full pipeline**: input guardrails → system prompt assembly (Constitution + Canary + ContextBlocks) → LLM call with retry → canary verification → output guardrails → retry on schema failure → HITL routing → audit log. |

**`OrchestratorResult`**: `success`, `response_text`, `tool_calls[]`, `input_guardrail`, `output_guardrail`, `llm_response`, `block_reason`, `retry_count`, `hitl_required`, `hitl_request_ids[]`, `total_latency_ms`.

## 3. Configuration

| Variable | Default | Notes |
|---|---|---|
| `TS_LLM_PROVIDER` | `mock` | `mock`, `anthropic`, or `deepseek` |
| `TS_LLM_ROUTING_POLICY` | `fixed_default` | Routing policy for the ProviderRouter |
| `TS_ANTHROPIC_API_KEY` | (empty) | **Required** for Anthropic client. Set to DeepSeek API key when using `api.deepseek.com/anthropic`. |
| `TS_ANTHROPIC_BASE_URL` | (empty) | Override for non-Anthropic endpoints. Set to `https://api.deepseek.com/anthropic` for DeepSeek. |
| `TS_ANTHROPIC_MODEL` | `claude-sonnet-5` | Model name. Set to `deepseek-v4-pro[1m]` for DeepSeek. |
| `TS_ANTHROPIC_MAX_TOKENS` | `4096` | |
| `TS_ANTHROPIC_TEMPERATURE` | `0.0` | |
| `TS_ANTHROPIC_TIMEOUT_SECONDS` | `60` | |
| `TS_ANTHROPIC_MAX_RETRIES` | `3` | |
| `TS_ANTHROPIC_COST_CEILING_DAILY_USD` | `50.0` | Declared, not enforced. |
| `TS_ANTHROPIC_ZERO_RETENTION` | `False` | Must be True before RESTRICTED-tier data is routed. |
| `TS_DEEPSEEK_API_KEY` | (empty) | For OpenAI-compatible endpoint. |
| `TS_DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | |
| `TS_DEEPSEEK_MODEL` | `deepseek-chat` | |
| (additional TS_DEEPSEEK_* settings) | | Same pattern as Anthropic above |

## 4. Data Flow

```
user_input → InputGuardrailPipeline.run()
           → blocked? → return OrchestratorResult(success=False)

           → ContextAssembler: system prompt = Constitution + CanaryToken + ContextBlocks
           → ProviderRouter.route() → selects LLMClient
           → with_retry(client.generate(messages, tools))
           → verify_output_canary(response.text)
           → OutputGuardrailPipeline.run(response.text, source_context)
           → schema failure? → retry with corrective prompt (up to N=3)
           → tool_calls? → ApprovalQueue.submit() for each
           → AuditLogger.log()
           → OrchestratorResult(success=True, response_text=..., ...)
```

**This module does NOT:**
- Stream tokens (all calls are synchronous in terms of response completeness)
- Enforce cost ceilings at runtime (declared in config, not enforced)
- Handle multi-turn conversation state beyond what ContextBlocks provide
- Run two-pass verification for high-risk outputs

## 5. Dependencies

- **Internal**: `trust_safety.guardrails.input`, `trust_safety.guardrails.output`, `trust_safety.orchestrator`, `trust_safety.governance.audit_log`, `trust_safety.models`, `trust_safety.config`
- **External**: `anthropic` (optional, for AnthropicClient), `openai` (optional, for DeepSeekClient via OpenAI-compatible endpoint)

## 6. Per-Provider Setup

### DeepSeek via Anthropic-compatible endpoint (current production path)

```powershell
$env:TS_LLM_PROVIDER = "anthropic"
$env:TS_ANTHROPIC_API_KEY = "sk-..."  # Your DeepSeek API key
$env:TS_ANTHROPIC_BASE_URL = "https://api.deepseek.com/anthropic"
$env:TS_ANTHROPIC_MODEL = "deepseek-v4-pro[1m]"
```

Verify:
```bash
curl -X POST 'http://localhost:8000/api/v1/llm/providers/anthropic/test'
# → {"provider":"anthropic","healthy":true}
```

### Native Anthropic

```powershell
$env:TS_LLM_PROVIDER = "anthropic"
$env:TS_ANTHROPIC_API_KEY = "sk-ant-..."  # Your Anthropic API key
$env:TS_ANTHROPIC_MODEL = "claude-sonnet-5"
# (base_url defaults to api.anthropic.com)
```

### DeepSeek via OpenAI-compatible endpoint (alternative)

```powershell
$env:TS_LLM_PROVIDER = "deepseek"
$env:TS_DEEPSEEK_API_KEY = "sk-..."  # Your DeepSeek API key
$env:TS_DEEPSEEK_MODEL = "deepseek-chat"
```

## 7. Adding a Third Provider

1. Create a new class implementing `LLMClient` (ABC):
   - `__init__(config: LLMConfig)` — store config, validate credentials
   - `async generate(messages, tools, stream) -> LLMResponse` — call the API, normalize response
   - `provider_name` property → unique string
2. Add config fields to `Settings` (with `providername_` prefix)
3. Register in `_build_llm_router()` in `gateway/dependencies.py`
4. Add routing policy if needed in `router.py`
5. The guardrail code needs NO changes — it only depends on `LLMClient`, never on a specific implementation.

## 8. Usage Example

```python
# Minimal: call DeepSeek through the orchestrator
from trust_safety.llm.orchestrator import LLMOrchestrator
# (orchestrator is typically created via dependency injection)
# See gateway/dependencies.py for the full setup

# Direct client usage (bypassing orchestrator):
from trust_safety.llm import AnthropicLLMClient, LLMConfig

config = LLMConfig(
    provider="anthropic",
    api_key="sk-...",
    base_url="https://api.deepseek.com/anthropic",
    model="deepseek-v4-pro[1m]",
)
client = AnthropicLLMClient(config)
resp = await client.generate([
    {"role": "user", "content": "What is the capital of France?"}
])
print(resp.text)  # "The capital of France is Paris."
print(resp.provider_name)  # "anthropic"
print(resp.model_name)  # "deepseek-v4-pro[1m]"
```

## 9. Testing

Tests: `trust_safety/tests/test_llm_client.py`, `test_orchestrator.py`, `test_router.py`, `test_retry.py`
Run: `pytest trust_safety/tests/test_llm_client.py trust_safety/tests/test_orchestrator.py trust_safety/tests/test_router.py trust_safety/tests/test_retry.py -v`
Coverage: Mock client (pattern matching, tool calls, callbacks), interface conformance, orchestrator full pipeline (benign/injection/secrets/canary), routing policy selection, retry with backoff, availability breaker state transitions.

**Known gap**: No tests with live API keys — all LLM tests use MockLLMClient. Live API testing is manual via the gateway endpoints.

## 10. Failure Modes

- **Missing API key**: `AnthropicLLMClient` and `DeepSeekLLMClient` raise `ValueError` at construction time. FAIL-CLOSED.
- **API timeout/error**: `with_retry()` retries up to `max_retries` with exponential backoff. Auth errors (401) are NOT retried. After all retries exhausted, the orchestrator returns `success=False` with the error in `block_reason`.
- **Malformed response**: Caught by the output schema validator in the orchestrator. If schema validation fails, the orchestrator retries with a corrective re-prompt (up to 3 times). After max retries, returns `success=False`.
- **Canary token in output**: Detected by `verify_output_canary()`. Returns `success=False` with `block_reason="CRITICAL: Canary token detected..."`. This is a FAIL-CLOSED security event — the response is never returned to the user.
- **Availability breaker**: Separate from safety breaker. Trips after N consecutive API failures. Resets after `reset_timeout_seconds`. Does NOT block safety-critical actions — that's the safety breaker's job.

## 11. Related Modules

- Called by: gateway routes (`/generate`, `/llm/*`)
- Calls: `trust_safety.guardrails.input`, `trust_safety.guardrails.output`, `trust_safety.orchestrator`, `trust_safety.governance.audit_log`, `trust_safety.models`, `trust_safety.config`
- See also: [../orchestrator/README.md](../orchestrator/README.md), [../gateway/README.md](../gateway/README.md)
