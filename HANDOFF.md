# Trust & Safety Layer — Agent Handoff Document

**Generated:** 2026-07-19
**For:** Continuing work with any coding agent (Claude Code, Cursor, Copilot, etc.)
**Repo:** `github.com/aashishpokharel/kss_trustworthy_ai` (branch: `master`, commit: `b8501c8`)

---

## 1. What This Is

A production-grade Trust & Safety layer for LLM/Agent systems, built from the architecture specs in this repo. Six phases, 439 tests, wired to a live DeepSeek endpoint. Streamlit operator UI with dashboard, HITL approval queue, and guardrail test console.

**Two architecture docs drive everything:**
- `ai_trust_safety_architecture.md` — the main spec (Sections 1-15, Appendix A-B)
- `llm-integration-architecture-new-ui.md` — LLM provider abstraction + Streamlit UI spec (Sections 1-9, including §8.5 Guardrail Test Console)

## 2. How To Resume Work

```powershell
cd D:\FUSE\trustworthy_ai
$env:PYTHONPATH="D:\FUSE\trustworthy_ai"

# Verify everything still works
.\venv\Scripts\python.exe -m pytest trust_safety/tests/ -q
# Expected: 439 passed

# Start API server (needed for test console + live LLM calls)
.\venv\Scripts\python.exe -m uvicorn trust_safety.main:app --host 127.0.0.1 --port 8000

# Start Streamlit UI (separate terminal)
.\venv\Scripts\python.exe -m streamlit run ui/streamlit_app.py --server.port 8501

# API docs: http://localhost:8000/docs
# Streamlit: http://localhost:8501
```

## 3. Architecture At A Glance

```
User → [1] Gateway (FastAPI) → [2] Input Guardrails → [3] Orchestrator
      → [3.5] LLMClient.generate() → [4] Real LLM (DeepSeek)
      → [5] Output Guardrails → [6] Response
                        ↑
              Governance Plane (audit log, dashboard, HITL, circuit breaker)
```

**Every module is in `trust_safety/`:**

| Module | Path | What it does |
|---|---|---|
| `models/` | `base.py`, `context.py` | DataTier, TrustLevelEnum, ContextBlock, ProvenanceTag, ContextAssembler |
| `gateway/` | `routes.py`, `dependencies.py` | FastAPI app, all 30+ endpoints, singleton wiring |
| `guardrails/input/` | 8 files | Injection detector (regex+heuristic+canary), PII (Presidio), secrets, sensitive topics, input validator, pipeline |
| `guardrails/output/` | 5 files | Schema validator (retry prompts), groundedness checker, refusal classifier (4-type), pipeline |
| `orchestrator/` | 5 files | Tool registry (risk→HITL derivation), approval queue (fail-closed), circuit breaker, policy gate, autonomy promotion |
| `governance/` | 5 files | Append-only audit log (SHA-256 hash chain), dashboard metrics, incident review, policy versioning, constitution |
| `llm/` | 8 files | LLMClient interface, Mock/Anthropic/DeepSeek clients, ProviderRouter, LLMOrchestrator, retry handling |
| `eval/` | 3 files | CI eval runner (regression gating), bias counterfactual suite, eval scheduler |
| `redteam/` | 3 files | Garak/PyRIT configs, red-team runner, threat model template |
| `policies/` | 2 files | Compliance profiles (GDPR/HIPAA/CCPA/NONE) with conservative merging |
| `config.py` | — | All settings via `TS_`-prefixed env vars (.env file) |

**Streamlit UI in `ui/`:**

| Page | File | Auth |
|---|---|---|
| Home | `streamlit_app.py` | None |
| Dashboard | `pages/01_Dashboard.py` | None |
| HITL Approval Queue | `pages/02_Approval_Queue.py` | Password (`trustworthy-ai`) |
| Provider Comparison | `pages/03_Provider_Comparison.py` | None |
| Guardrail Test Console | `pages/04_Guardrail_Test_Console.py` | Password |

**Developer docs in `docs/`:** 11 markdown files, one per module + top-level index.

## 4. Key Design Decisions (What Another Agent Must Know)

1. **Fail-closed everywhere.** Defaults are always restrictive. HITL timeout = denial. Injection strictness = 0.1 (catches single-pattern attacks). Provenance trust_score defaults to 0.0.

2. **No llm-guard.** `sentencepiece` won't build on Windows. Injection detection is manual regex + heuristics + canary tokens. Same categories, zero native deps.

3. **Audit log is JSONL + SHA-256 hash chain.** `AppendOnlyFileStore` has NO delete/update methods. Tampering is detected by `verify_integrity()`. Single file, local dev only.

4. **DeepSeek via Anthropic endpoint.** In `.env`: `TS_LLM_PROVIDER=anthropic`, `TS_ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, `TS_ANTHROPIC_MODEL=deepseek-v4-pro[1m]`. The `provider_name` field says "anthropic" but it's DeepSeek — check `model_name` for the actual model.

5. **PII detection uses Presidio** but LOCATION and DATE_TIME entities are removed (false positives: "France" flagged as LOCATION, "72" as DATE_TIME).

6. **Groundedness uses keyword overlap**, not NLI. Interface allows future NLI model swap. Domain thresholds: medical/legal 0.85, financial 0.80, general 0.70, creative 0.0.

7. **Pipeline order matters.** Input: normalize → injection → PII → secrets → sensitive topics → classify. Output: schema → groundedness → PII leak → refusal. First blocker stops the pipeline (fail-fast).

8. **Page filenames start with digits** (`01_Dashboard.py`). Python can't import modules starting with digits. Streamlit handles this internally for auto-discovery but explicit `import pages.2_approval_queue` will fail. The `streamlit_app.py` was fixed to NOT explicitly import pages.

## 5. What's Built vs. What's Not

### Built and tested (439 tests)
- [x] Full input guardrail pipeline (injection, PII, secrets, sensitive topics, validation, data classification)
- [x] Full output guardrail pipeline (schema, groundedness, PII leak, refusal)
- [x] Append-only audit log with hash chaining + tamper detection
- [x] Tool registry with HITL derivation (LOW→out, MEDIUM+rev→on, HIGH/CRITICAL→in)
- [x] HITL approval queue (fail-closed timeout)
- [x] Circuit breaker (LLM-independent)
- [x] Policy registry (GDPR/HIPAA/CCPA/NONE with conservative merge)
- [x] System constitution (versioned, changelogged)
- [x] LLM provider abstraction (Mock/Anthropic/DeepSeek)
- [x] LLMOrchestrator (input→LLM→output→HITL→audit)
- [x] ProviderRouter (4 routing policies)
- [x] Retry with exponential backoff + availability breaker
- [x] CI eval engine with regression gating
- [x] Bias counterfactual suite (gender/ethnicity/pronoun swaps)
- [x] Data poisoning defenses (anomaly detection, source allowlisting, hash verification)
- [x] Eval scheduler (daily/weekly/monthly with trend tracking)
- [x] Incident review loop (report→investigate→resolve→golden set feedback)
- [x] Policy versioning (changelog, rollback)
- [x] Autonomy promotion workflow (safety case→review→promote)
- [x] Streamlit UI (4 pages: dashboard, HITL, providers, test console)
- [x] Guardrail test console with server-side prod hard-block
- [x] Live DeepSeek integration (verified: real API calls work through the full pipeline)

### Not yet implemented
- [ ] Garak/PyRIT CLI integration — configs exist, runner is ours
- [ ] Streaming guardrails — all assume complete responses
- [ ] Shadow/canary traffic splitting — mechanism in config, not wired
- [ ] Cost ceiling auto-enforcement — declared in config, not enforced
- [ ] Two-pass verification for high-risk outputs (§2 of main doc)
- [ ] Multi-turn attack state tracking
- [ ] Per-provider red-team eval suites
- [ ] API auth middleware
- [ ] Audit log rotation/archival
- [ ] Data retention enforcement

## 6. Configuration (.env)

```
TS_LLM_PROVIDER=anthropic
TS_ANTHROPIC_API_KEY=sk-...           # DeepSeek API key
TS_ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
TS_ANTHROPIC_MODEL=deepseek-v4-pro[1m]
TS_AUDIT_LOG_PATH=./data/audit_log.jsonl
TS_ENVIRONMENT=development
TS_HITL_TIMEOUT_SECONDS=300
TS_HITL_FAIL_CLOSED=true
TS_OPERATOR_PASSWORD=trustworthy-ai    # Streamlit HITL queue auth
```

## 7. Endpoint Quick Reference

```
GET  /api/v1/health
POST /api/v1/generate                    # Full pipeline with live LLM
POST /api/v1/guardrails/input/scan       # Input guardrails only
POST /api/v1/guardrails/output/scan      # Output guardrails only
POST /api/v1/test-console/run            # Guarded vs unguarded side-by-side
GET  /api/v1/llm/providers
POST /api/v1/llm/providers/{name}/test
POST /api/v1/hitl/approval/submit
POST /api/v1/hitl/approval/{id}/approve
POST /api/v1/hitl/approval/{id}/deny
GET  /api/v1/hitl/approval/pending
GET  /api/v1/circuit-breaker/status
POST /api/v1/circuit-breaker/trip
POST /api/v1/circuit-breaker/reset
GET  /api/v1/dashboard/metrics
GET  /api/v1/dashboard/summary
GET  /api/v1/policies
POST /api/v1/eval/run
GET  /api/v1/eval/schedules
POST /api/v1/incidents
POST /api/v1/autonomy/promote
```

## 8. Test Commands

```powershell
# All tests
pytest trust_safety/tests/ -v

# By module
pytest trust_safety/tests/test_injection_detector.py -v     # Input guardrails
pytest trust_safety/tests/test_audit_log.py -v              # Audit log + tamper
pytest trust_safety/tests/test_orchestrator.py -v           # LLM integration
pytest trust_safety/tests/test_approval_queue.py -v         # HITL queue
pytest trust_safety/tests/test_circuit_breaker.py -v        # Circuit breaker
pytest trust_safety/tests/test_llm_client.py -v             # Provider clients
pytest trust_safety/tests/test_output_pipeline.py -v        # Output guardrails
pytest trust_safety/tests/test_gateway.py -v                # API endpoints
```

## 9. Known Quirks

- **Streamlit must be run as `python -m streamlit`**, not `streamlit.exe` (Windows Application Control policy).
- **`use_container_width` is deprecated** — use `width="stretch"` in Streamlit components.
- **Presidio logs warnings** on startup about unsupported language recognizers — harmless.
- **The `.env` file is gitignored** — never commit API keys. `.env.local` is also gitignored.
- **`data/` directory is gitignored** — contains runtime audit log.
- **`.claude/` and `.pytest_cache/` are gitignored** — Claude Code internal files.

## 10. If You Need The Full Conversation

This HANDOFF.md captures every decision, file, and architectural choice. For the raw turn-by-turn transcript, export from Claude Code using `/export` or copy from the session history. The key phases were:

1. **Phase 0**: Repo scaffold, audit log, ContextBlock, tool registry
2. **Phase 1**: Input guardrails (injection, PII, secrets, sensitive topics, validation)
3. **Phase 2**: Output guardrails (schema, groundedness, refusal)
4. **Phase 3**: Autonomy & governance (HITL queue, circuit breaker, constitution, dashboard)
5. **Phase 4**: Adversarial hardening (red-team, CI eval, bias, data poisoning)
6. **Phase 5**: Continuous operation (scheduler, incidents, policy versioning, autonomy promotion)
7. **Phase 6**: LLM integration (provider abstraction, orchestrator, DeepSeek wiring, Streamlit UI)
8. **Docs + Commit**: Developer documentation, .gitignore hardening, git commit + push
