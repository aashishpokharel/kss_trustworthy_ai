# UI Module (Streamlit)

## 1. Purpose

Operator-facing Streamlit UI for the Trust & Safety Layer. Four pages: governance dashboard (read-only), HITL approval queue (authenticated, write), provider comparison (read-only), and guardrail test console (authenticated, with/without guardrails side-by-side). Architecture doc: `llm-integration-architecture-new-ui.md` Section 8.

## 2. Pages

### 🏠 Home (`streamlit_app.py`)

Operator console landing page. Shows quick stats (environment, LLM provider, ladder rung, HITL timeout). Streamlit auto-discovers additional pages from `ui/pages/` and lists them in the sidebar.

### 📊 Dashboard (`pages/01_Dashboard.py`)

Read-only governance metrics from the shared audit log:
- **KPI row**: Total interactions, block rate, injection attempts, refusal rate, groundedness avg
- **Gauge charts**: Pass rate, groundedness, non-refusal rate (Plotly indicators)
- **Data privacy**: PII detections (input), PII leaks (output), secrets detected
- **HITL**: Approved/denied/timed out counts, breaker trips
- **Audit summary**: Total entries, integrity status, first entry time
- **Top event types**: Bar chart
- **Time window selector**: 1–168 hours (sidebar slider)
- **Manual refresh button**

### 🛡️ HITL Approval Queue (`pages/02_Approval_Queue.py`)

Authenticated (password-gated). Approve/deny high-risk tool calls:
- **Stats bar**: Pending/approved/denied/timed out counts
- **Per-request card**: Tool name, params, requester, risk tier, timeout countdown (⚠️ urgent when <60s)
- **Approve/Deny buttons**: With reviewer name and reason fields
- Calls `ApprovalQueue.approve()` / `ApprovalQueue.deny()` directly — no duplicate approval logic
- Auth: `components/auth.py`, default password `trustworthy-ai` (override via `TS_OPERATOR_PASSWORD`)

### 🔀 Provider Comparison (`pages/03_Provider_Comparison.py`)

Side-by-side Anthropic vs DeepSeek configuration:
- Per-provider settings: base URL, model, max tokens, temperature, timeout, cost ceiling, zero-retention, API key status
- **Environment ladder**: 5-rung progress bar (mock → sandbox → shadow → canary → production)
- Canary force-HITL status and routing policy display
- Eval results table (placeholder — populated after running eval suites against live providers)

### 🧪 Guardrail Test Console (`pages/04_Guardrail_Test_Console.py`)

With-guardrails vs. without-guardrails side-by-side comparison. Per `llm-integration-architecture-new-ui.md` §8.5.

**Input panel:**
- Free-text prompt box
- 15 preloaded golden-set/red-team presets (injection, PII, secrets, jailbreak, bias, benign, RAG poisoned context)
- Optional context block JSON for RAG simulation (trusted/untrusted per main doc §2)
- Provider selector (mock / anthropic / deepseek)

**Two-column output:**
- **Left (🛡️ With Guardrails)**: Full orchestrator pipeline. Per-stage KPI tiles: injection verdict, PII count, secrets flag, topic category, groundedness score, refusal type, schema status. Expandable full JSON report.
- **Right (🔓 Without Guardrails)**: Raw model response with zero guardrails applied (calls `client.generate()` directly, skipping stages [2] and [5]).

**Diff view:** Detects and highlights what changed — `guarded_blocked_unguarded_responded`, `response_text_changed`. Side-by-side code comparison when both paths return text.

**Critical restrictions (§8.5):**
- Server-side hard-blocked in production (returns HTTP 403 — not just hidden in UI)
- Requires operator authentication (same password as HITL page)
- All traffic tagged `source=test_console` in audit log, excluded from production metrics
- Warning banner: never use real PII or customer data

## 3. Components

- `components/auth.py` — Password-based operator login. Default: `trustworthy-ai`. Override via `TS_OPERATOR_PASSWORD` env var. Session-based (persists until tab closes).
- `components/audit_log_viewer.py` — Filterable table (event type + status dropdowns, max rows configurable).
- `components/metrics_charts.py` — Gauge (Plotly `go.Indicator`), line (Plotly Express), bar charts. All use `width="stretch"` (not deprecated `use_container_width`).

## 4. Configuration

| Variable | Default | Notes |
|---|---|---|
| `TS_AUDIT_LOG_PATH` | `./data/audit_log.jsonl` | Shared with the API server — both read the same file |
| `TS_OPERATOR_PASSWORD` | `trustworthy-ai` | Auth for HITL queue + test console |

The UI imports backend services directly (not via HTTP to the API) — `MetricsCollector`, `ApprovalQueue`, `get_settings()`. It shares the same audit log file. Both UI and API server must run on the same machine with the same `PYTHONPATH`.

## 5. Running Locally

```powershell
cd D:\FUSE\trustworthy_ai
$env:PYTHONPATH="D:\FUSE\trustworthy_ai"

# Terminal 1 — API server (required for test console's server-side endpoint)
.\venv\Scripts\python.exe -m uvicorn trust_safety.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Streamlit UI
.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.port 8501
```

**Note:** Use `python -m streamlit`, not `streamlit.exe` directly — Windows Application Control may block the `.exe`.

Opens at:
- Home: `http://localhost:8501/`
- Dashboard: `http://localhost:8501/01_Dashboard`
- HITL Queue: `http://localhost:8501/02_Approval_Queue`
- Providers: `http://localhost:8501/03_Provider_Comparison`
- Test Console: `http://localhost:8501/04_Guardrail_Test_Console`

## 6. Auth Setup

1. Default password: `trustworthy-ai`
2. Override: `$env:TS_OPERATOR_PASSWORD = "your-secure-password"`
3. Both HITL approval queue and guardrail test console require auth
4. For production: front with an SSO/auth proxy instead of the basic password gate

## 7. Page Layout (ASCII)

```
┌──────────────────────────────────────────────────────────┐
│  🛡️ Trust & Safety                    [sidebar]          │
│  Operator Console                      ┌──────────┐     │
│                                        │ 🏠 Home   │     │
│  HOME:                                 │ 📊 Dash   │     │
│  ┌─────────┐ ┌─────────┐ ┌─────┐ ┌───┐│ 🛡️ HITL   │     │
│  │Env: dev │ │Provider │ │Ladder│ │HITL││ 🔀 Prov   │     │
│  └─────────┘ └─────────┘ └─────┘ └───┘│ 🧪 Test   │     │
│                                        └──────────┘     │
│  DASHBOARD:                                              │
│  ┌────┐┌────┐┌────┐┌────┐┌────┐                         │
│  │KPI ││KPI ││KPI ││KPI ││KPI │                         │
│  └────┘└────┘└────┘└────┘└────┘                         │
│  [Gauge: Pass Rate] [Gauge: Grounded] [Gauge: Non-Ref]  │
│  [Bar chart: Top Event Types]                            │
│                                                          │
│  TEST CONSOLE:                                           │
│  ┌─────────────────────────────────────────┐            │
│  │ Prompt: [___________________________]   │            │
│  │ Context: [{...}]               [Run 🧪] │            │
│  ├──────────────────┬──────────────────────┤            │
│  │ 🛡️ With Guards   │ 🔓 Without Guards    │            │
│  │ ✅ Passed         │ ⚠️ Raw output        │            │
│  │ Inj:✅ PII:2 Sec:✅│ "The capital is..." │            │
│  │ Ground:0.92       │                      │            │
│  ├──────────────────┴──────────────────────┤            │
│  │ 🔍 Diff: response_text_changed          │            │
│  └─────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────┘
```

## 8. Dependencies

- **Internal**: `trust_safety.governance.dashboard`, `trust_safety.governance.audit_log`, `trust_safety.orchestrator.approval_queue`, `trust_safety.config`, `trust_safety.guardrails.input`
- **External**: `streamlit>=1.40.0`, `plotly>=5.24.0`, `pandas>=2.2.0`, `httpx>=0.28.0`

## 9. Testing

No automated tests for the UI module. Streamlit apps are tested manually. The underlying services (dashboard, approval queue, guardrails) have full test coverage (439 tests). The test console's server-side endpoint (`POST /api/v1/test-console/run`) is tested via manual curl.

## 10. Failure Modes

- **Audit log not found**: Dashboard shows 0 entries (file auto-created by `AppendOnlyFileStore`).
- **API server not running**: Test console shows connection error with instructions to start the server. Dashboard and HITL pages unaffected (they import services directly).
- **Password bypass**: Basic env-var gating. For production, replace with SSO.
- **Prod hard-block**: Server-side HTTP 403 prevents any bypass attempt, even via direct API calls — the UI check is redundant defense, not the primary gate.

## 11. Related Modules

- Calls: `trust_safety.governance.dashboard`, `trust_safety.orchestrator.approval_queue`, `trust_safety.config`, `trust_safety.guardrails.input`
- Server endpoint: `POST /api/v1/test-console/run` (in `trust_safety/gateway/routes.py`)
- See also: [../gateway/README.md](../gateway/README.md), [../governance/README.md](../governance/README.md), [../llm-integration/README.md](../llm-integration/README.md)
