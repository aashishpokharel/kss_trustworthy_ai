# LLM Integration Layer — Addendum to ai-trust-safety-architecture.md

**Purpose:** The original architecture doc describes stages [3] Orchestrator and [4] LLM Core but assumes "the model call itself" as a black box. This addendum specifies *how that call actually gets wired to a real provider*, safely, with a clean path from mock → staging → production. Read alongside Section 1 (pipeline) and Section 9 (autonomy) of the main doc.

---

## 1. Why this is usually the last thing to get real

Mocking the LLM call is the correct default during Phases 0–4 — it makes the guardrail logic testable in isolation, deterministically, for free. The risk is that "mock-shaped" code quietly assumes things a real provider won't guarantee: instant responses, no rate limits, no partial/streamed output, no malformed responses, no auth failures, no cost. This layer exists to close that gap deliberately rather than discover it in production.

---

## 2. Provider Abstraction Layer

**Objective:** Stage [4] should call one internal interface, not a specific vendor SDK — so mock, staging, and production are swappable without touching guardrail code.

```
LLMClient (interface)
 ├── MockLLMClient        — canned/deterministic responses, used in unit tests & CI
 ├── AnthropicLLMClient    — wraps the real Anthropic SDK (Claude)
 ├── DeepSeekLLMClient     — wraps DeepSeek's API (OpenAI-compatible REST format)
 ├── OpenAILLMClient       — (optional, if a third provider is added later)
 └── FallbackLLMClient     — wraps a primary+secondary pair for failover
```

Every implementation exposes the same method signature: `generate(context_blocks, tools, stream=False) -> LLMResponse`. Guardrail code, the orchestrator, and tests all depend on `LLMClient`, never on a vendor SDK directly.

**Build tasks:**
1. Define the `LLMClient` interface and `LLMResponse` schema (text, tool_calls, stop_reason, usage/tokens, latency_ms, **provider name**).
2. Move the existing mock into `MockLLMClient` implementing this interface (if it doesn't already).
3. Implement `AnthropicLLMClient` using the real Anthropic SDK, reading model/params from config (§4), not hardcoded.
4. Implement `DeepSeekLLMClient` using DeepSeek's API (OpenAI-compatible chat-completions format — the same request/response shape as OpenAI's SDK, pointed at DeepSeek's base URL). Normalize its response into the same `LLMResponse` schema so downstream guardrail code cannot tell which provider answered.
5. Config-driven selection: an environment variable or per-request parameter (`LLM_PROVIDER=mock|anthropic|deepseek`) picks the implementation — no code changes to switch providers or environments.

### 2.1 Why running two providers changes the architecture, not just the config

Adding a second model is not "swap the API key" — it changes what the guardrail and governance layers need to track:

- **Guardrails must be provider-agnostic by construction.** Injection/PII/groundedness/bias checks (Sections 2, 5, 8, 11 of the main doc) run on *text*, not on provider-specific internals — so they should already work unmodified across providers, as long as every client normalizes into the shared `LLMResponse` schema (build task 4 above). Treat any guardrail that silently assumes Anthropic-specific response fields as a bug to fix now, before it causes a DeepSeek response to skip a check.
- **Different providers can have materially different safety postures.** Don't assume both models pass the same golden sets / red-team suite (§3, §13 of the main doc) at the same rate — run the full adversarial and bias suites against *each* provider independently, and track results per-provider on the governance dashboard (§9 below). A provider swap or fallback should never be allowed to silently lower your effective safety bar.
- **Data governance differs per provider.** Section 4 of the main doc (data classification tiers) and the zero-retention/no-train check in §4 of this addendum must be configured and verified *per provider* — confirm DeepSeek's data retention/training policy independently; don't assume it matches Anthropic's.
- **Routing logic is a first-class decision, not an afterthought.** Decide explicitly (config, not ad hoc code) what determines which provider handles a given request: user/task selection, cost optimization, automatic failover, A/B comparison, or a fixed default with the other as fallback only. Document the chosen policy in the governance policy docs (§12 of the main doc).

**Build tasks (routing):**
1. Add a `ProviderRouter` that selects the `LLMClient` implementation per request based on the configured policy (fixed default / task-based / cost-based / fallback-only).
2. Tag every logged request/response with which provider served it, so audit logs, cost tracking, and eval results can be filtered per-provider.
3. Run Sections 3, 8, 11, and 13 of the main doc's eval suites against **each** provider before enabling it for real traffic — a new provider is not "integrated," it's "connected," until it has passed the same safety case as the first.

---

## 3. Where This Sits in the Pipeline

```
[3] Orchestrator ──▶ [3.5] LLMClient.generate() ──▶ [4] Real model API call
        │                        │
        │                        ├── on success ──▶ [5] Output Guardrails
        │                        ├── on timeout/error ──▶ Retry/Fallback (§6)
        │                        └── on stream ──▶ Streaming Guardrail Mode (§7)
        └── injects: system prompt (from your constitution doc, §9.1 of main doc),
                     provenance-tagged context blocks, tool schemas, canary token
```

The Orchestrator's job doesn't change — it still assembles `ContextBlock`s and enforces the `PolicyGate`. What's new is that `[3.5]` is a real network call with real failure modes, and `[5]` now runs against genuinely unpredictable model output instead of scripted mock text.

---

## 4. Configuration & Secrets

**Objective:** API keys and provider config are the single highest-value target if this system is compromised — treat them accordingly.

- **Secrets manager, not env files in the repo** — AWS Secrets Manager / GCP Secret Manager / Vault, injected at runtime. Never commit keys, never log full request/response bodies containing them.
- **Per-environment, per-provider config** (`config/mock.yaml`, `config/staging.yaml`, `config/prod.yaml`), each with a section per provider: model name, max tokens, temperature, timeout, retry policy, rate limit, cost ceiling per request and per day. Anthropic and DeepSeek get independent entries — don't share one block of "the model" settings across both.
- **Zero-retention/no-train settings, checked per provider** — confirm and set each provider's data-handling flags explicitly in config, tying back to Section 4 (Data Privacy governance) of the main doc. Do not assume Anthropic and DeepSeek have equivalent default policies — verify DeepSeek's terms independently before routing any Confidential/Restricted-tier data (per the classification table in Section 4 of the main doc) to it.
- **Key scoping** — separate, narrowly-scoped API keys per provider, each stored under its own secrets-manager entry (e.g. `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`), never a shared key or a single "LLM_API_KEY" catch-all.

**Build tasks:**
1. Wire secrets retrieval into `AnthropicLLMClient` and `DeepSeekLLMClient` startup independently — fail closed (refuse to start) if either provider's required secret is missing and that provider is enabled in config for the current environment.
2. Add a startup config validator: reject prod startup if `LLM_PROVIDER=mock`, or if either enabled provider is missing explicit zero-retention flags.
3. Add cost-ceiling enforcement per provider as a hard circuit breaker (ties to the kill switch in §9 of the main doc) — auto-halt a provider individually if its daily spend crosses its configured threshold, without necessarily halting the other provider.

---

## 5. Going Live Safely — Environment Ladder

Don't flip straight from mock to prod. Use a staged rollout, each gated by evidence, mirroring the proportional-autonomy principle in Section 13/15 of the main doc:

1. **Mock (current state)** — guardrail logic tests, deterministic CI.
2. **Live-in-sandbox** — real API calls, but only from a dev/test account, against the golden sets and red-team suite (§3, §13 of main doc) run live instead of mocked. Goal: confirm guardrails still catch real jailbreak/injection attempts against a real model (mocks can't produce a real jailbroken response, so this is the first time you actually validate stage [5]'s output guardrails against genuine adversarial model output).
3. **Shadow mode in staging** — real traffic mirrored to the live LLM path, but its output is logged/compared, not served to users; production traffic still served by the previous path (or mock, if this is a new build).
4. **Canary in production** — small % of real traffic served by the live LLM path, human-in-the-loop mode forced on for all tool calls regardless of their declared risk tier, tight monitoring.
5. **Full production** — normal HITL tiers apply (per Section 9.2 of the main doc), cost/rate monitoring steady-state.

**Build tasks:**
1. Add an environment flag/feature-gate for shadow/canary traffic splitting.
2. Re-run the full red-team and golden-set suites at each rung (§13 of main doc) — a passing suite against mock output does not guarantee a passing suite against real output.
3. Force HITL-in-loop for all actions during canary regardless of tool risk tier; only relax to the tool's declared tier after canary evidence is reviewed and signed off.

---

## 6. Failure Handling — Real Networks Fail

Mock clients don't time out, get rate-limited, or return malformed JSON. A real client will. This is new surface area the guardrail layer needs to handle explicitly:

- **Timeouts** — bounded, configurable; on timeout, fail closed for high-risk actions (no silent retry-with-side-effects), fail-safe-message for conversational responses.
- **Rate limits (429s)** — exponential backoff with jitter; queue depth alerting so a burst doesn't silently degrade UX.
- **Malformed/partial responses** — the output schema validation from Section 7 of the main doc now does real work — a real model can return a tool call that doesn't match the declared schema; that's not hypothetical anymore.
- **Provider outage** — `FallbackLLMClient` can failover to a secondary provider/model *only* if that fallback has been through the same guardrail validation and safety-case review as the primary — don't let an outage be the reason a less-vetted model quietly starts serving traffic.

**Build tasks:**
1. Implement retry-with-backoff and circuit-breaking around `AnthropicLLMClient` calls, distinct from the safety circuit breaker in the main doc (this one is about availability, that one is about safety) — but both should be visible on the same governance dashboard.
2. Add explicit tests that simulate timeout, 429, and malformed-response conditions (inject via a faulty test client, not by hoping the real API fails on demand).

---

## 7. Streaming Considerations

If the UI streams tokens as they generate, guardrails that assumed a complete response (groundedness check, PII leakage scan, schema validation) need a strategy:

- **Buffer-then-check for high-risk domains** — don't stream to the user until output guardrails have cleared the full response, for any action-triggering or high-stakes-content response.
- **Stream-with-trailing-validation for low-risk conversational text** — stream immediately, run guardrails on the completed text in parallel, and retract/append a correction if a violation is caught after the fact (rare, but needs a defined UX — e.g., a "message removed" state).
- **Tool calls are never streamed partially into execution** — a tool call must be fully formed and schema-validated before the Action/Tool Layer (stage 6) touches it, regardless of streaming mode for the conversational text alongside it.

**Build tasks:**
1. Decide streaming policy per domain/risk tier (reuse the tiering from Section 9.2 of the main doc) and implement buffer-vs-stream branching in the Output Guardrails stage.
2. Ensure tool-call assembly is always non-streamed/atomic even when surrounding text streams.

---

## 8. Governance & HITL UI (Streamlit)

**Objective:** Give the two UI-shaped gaps identified earlier — the governance dashboard (Section 12 of the main doc) and the HITL approval queue (Section 9.2) — an actual screen, not just API endpoints. Streamlit is the right choice here: it's Python-native, so it can import the same `LLMClient`, `ToolRegistry`, and audit-log models the backend already uses instead of re-implementing a client against the API, and it's fast to stand up for an internal/operator-facing tool (this is not meant to be the end-user chat UI, if one exists separately).

### 8.1 Structure — two Streamlit apps (or one app, two pages)

```
/ui/
  streamlit_app.py          # entry point, page router
  /pages/
    1_dashboard.py           # governance metrics (read-only)
    2_approval_queue.py       # HITL approve/reject (write — gated by auth)
    3_provider_comparison.py  # Claude vs DeepSeek eval/cost/latency side-by-side
  /components/
    audit_log_viewer.py
    metrics_charts.py
    auth.py                   # operator login — this UI touches approval actions, it needs its own auth
```

### 8.2 Page 1 — Governance Dashboard (read-only)

Pulls directly from the audit log and eval results described in Sections 12–13 of the main doc:
- Refusal rate over time, broken out by category (§10 of the main doc) and **by provider**
- Groundedness/hallucination scores over time, by domain and by provider
- Bias counterfactual deltas (§8 of the main doc), by provider
- Injection-attempt count and block rate (§2 of the main doc)
- Cost and latency, split Claude vs. DeepSeek, with the per-provider ceilings from §4 of this addendum visualized against actual spend
- Live vs. mock traffic split (ties to §5's environment ladder) and current environment/canary status

**Build tasks:**
1. Build read-only data-access functions against the audit log/metrics store (no direct DB writes from this page).
2. Use Streamlit's native charting (`st.line_chart`, `st.bar_chart`) or `plotly`/`altair` for the drift-over-time views — drift is the metric that matters most, not point-in-time snapshots.
3. Auto-refresh on an interval (`st.rerun` on a timer, or a manual refresh button) rather than requiring redeploys to see new data.

### 8.3 Page 2 — HITL Approval Queue (write, authenticated)

This is the actual UI implementation of the "human-in-the-loop" approval queue from Section 9.2 of the main doc — the piece most likely to still be API-only right now.

- List pending high-risk actions (from the `ToolRegistry`'s risk-tier flagging), each showing: the tool call, the reasoning/plan the model stated before the call (§9.1's reasoning-vs-action divergence log), which provider generated it, and the timeout deadline.
- Approve / Reject / Escalate buttons per item, writing back to the orchestrator's approval queue via the same internal service the API uses — **do not duplicate approval logic in the UI**, the UI should call the same `PolicyGate`/approval service as everything else, only render it.
- Surface the reasoning/action divergence flag (§9.2 of main doc) prominently if present — that's the strongest single signal an operator should see before approving.
- Require operator authentication (§8.1's `auth.py`) — this page can execute real actions, it is not read-only, and it needs the same access-control seriousness as the tool layer itself.

**Build tasks:**
1. Build the approval-queue page against the *existing* approval-queue API/service from Phase 3 of the main doc — this UI should be a thin client, not a second implementation of approval logic.
2. Add operator auth (even basic — Streamlit supports session-based auth patterns, or front it with your existing SSO/auth proxy) before allowing any approve/reject action.
3. Add a visible timeout countdown per pending item, matching the fail-closed timeout behavior specified in Section 9.2 of the main doc.

### 8.4 Page 3 — Provider Comparison (Claude vs. DeepSeek)

Useful once both providers are live (§2.1): a side-by-side view for deciding routing policy with evidence instead of guesswork.
- Eval suite pass rates per provider (red-team, bias, groundedness, golden refusal set — §3, §8, §11, §13 of main doc)
- Cost per 1K requests and average latency per provider
- Refusal-rate and over-refusal-rate comparison on the same golden set

**Build tasks:**
1. Run the shared eval suites (not provider-specific ones) against both providers and store results taggable by provider, then render side-by-side in this page.
2. Treat this page as the evidence artifact for any future `ProviderRouter` policy change — a routing-policy change should reference a comparison run, not be made informally.

### 8.5 Page 4 — Guardrail Test Console (with-guardrails vs. without)

**Objective:** Let a developer/operator send the same prompt through the pipeline twice — once through the full guardrail stack, once bypassing it — and see exactly what each stage caught, blocked, redacted, or changed. This is the difference between "the test suite passes" and "I can see with my own eyes what this guardrail actually does to this input."

**Layout:**
- **Input panel:** free-text prompt box, optional context blocks (paste a document to simulate RAG content, mark it trusted/untrusted per §2 of the main doc), provider selector (Claude / DeepSeek / mock), a toggle for "include a known test payload" (pre-loaded injection/PII/jailbreak samples from the golden sets in §13, so a user doesn't have to hand-craft an attack to see the system work).
- **Two-column output:**
  - Left: **with guardrails** — final response, plus a per-stage breakdown (injection scanner verdict, PII entities found + redacted, secrets scanner result, groundedness score, bias-classifier flag, schema validation result, refusal category if refused) so the user sees *which specific check* did what, not just a pass/fail badge.
  - Right: **without guardrails** — the raw model response with nothing intercepted, for comparison.
- **Diff view:** highlight what changed between the two columns (redacted spans, blocked-vs-allowed, refused-vs-answered) so the value of each guardrail is visible at a glance.

**Critical restriction — this is a bypass switch, treat it like one:**
- "Without guardrails" mode is **disabled entirely when `ENVIRONMENT=prod`** — hard-blocked in code, not just hidden in the UI, so it can't be re-enabled by editing a config the UI reads.
- Requires the same operator authentication as the approval-queue page (§8.3); log who ran it and when.
- Every run through this console — both columns — is tagged `source=test_console` in the audit log, kept clearly separate from real production traffic in the governance dashboard's metrics (§8.2), so bypass-mode test runs never get counted as "traffic that skipped guardrails" in a way that looks like a real incident.
- Never accepts real user PII/Confidential-tier data as input — this console should only ever run against synthetic test data or the golden-set samples, never against a live customer's real request replayed through it.

**Build tasks:**
1. Build a `run_with_guardrails()` and `run_without_guardrails()` pair of internal service calls, where the "without" path literally skips stages [2] and [5] of the main pipeline rather than being a separately-written response.
2. Wire per-stage results (not just the end response) into the "with guardrails" output — this requires each guardrail component to return a structured verdict object, not just allow/block, so the UI has something to render per stage.
3. Preload the golden-set/red-team samples from §13 of the main doc as one-click test payloads, categorized (injection, PII, jailbreak, bias-probe).
4. Enforce the environment check for bypass mode server-side (in the service layer the UI calls), not client-side in Streamlit — a UI-only restriction is not a real restriction.
5. Tag and route test-console traffic separately in the audit log from build task 3 of §8.2.

### 8.6 What NOT to build in Streamlit

- Not the end-user-facing chat interface, if this system serves external users — Streamlit is an operator/internal tool here, not a production customer-facing frontend.
- Not a second source of truth — every number on the dashboard and every approval action should trace back to the same audit log and services the backend already writes to; the UI renders, it doesn't own data.

---

## 9. What to Verify Before Calling This "Integrated"

Concrete checklist for the agent to report back on:

- [ ] `LLMClient` interface exists; mock, Anthropic, and DeepSeek implementations all conform to it and normalize into the same `LLMResponse` schema
- [ ] Both providers read config/secrets from a secrets manager independently, not hardcoded/env-committed, and neither shares a key with the other
- [ ] Full red-team + golden-set suite has been run against **both live models** independently (not just mock), and per-provider results are logged and comparable
- [ ] `ProviderRouter` routing policy is explicit and documented (fixed default / task-based / cost-based / fallback-only), not implicit in code
- [ ] Cost ceiling and rate-limit handling are implemented per provider and tested (simulate, don't wait for a real breach)
- [ ] Streaming policy is implemented per risk tier, if streaming is in scope
- [ ] Canary rollout plan exists with forced HITL-in-loop, even if not yet executed
- [ ] Streamlit governance dashboard is live, shows metrics broken out **by provider**, and reads only from the shared audit log/metrics store
- [ ] Streamlit HITL approval queue is live, authenticated, calls the existing approval service (not a duplicate implementation), and shows the reasoning/action divergence flag
- [ ] Provider-comparison page exists and reflects actual eval-suite runs, not placeholder numbers
- [ ] Guardrail test console shows per-stage verdicts (not just pass/fail) for the "with guardrails" path, side-by-side against the raw "without guardrails" response
- [ ] "Without guardrails" mode is hard-blocked server-side in prod (not just hidden in the UI), authenticated, and its traffic is tagged and excluded from real production metrics on the dashboard

---

*Pair this with the Phase 5 follow-up (scheduled eval cadence, incident review loop) — going live and closing Phase 5 should happen together, since live traffic is exactly what the scheduled eval cadence needs to be monitoring.*
