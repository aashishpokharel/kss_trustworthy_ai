# Threat Model — {tool_name}

**Version:** 1.0
**Date:** {date}
**Author:** {author}

---

## 1. Tool Description

- **Tool name:** {tool_name}
- **Risk tier:** {LOW|MEDIUM|HIGH|CRITICAL}
- **Reversible:** {yes|no}
- **Description:** {what does this tool do?}

## 2. Worst-Case Action

What is the single most damaging action this tool could take if:
- Prompt injection succeeded?
- The LLM hallucinated parameters?
- An unauthorized user gained access?

**Worst case:** {description}

## 3. Blast Radius

- **Scope of effect:** {single file | directory | machine | network | external system}
- **Can it affect other users?** {yes|no}
- **Can it cause financial damage?** {yes|no} — if yes, max exposure: ${amount}
- **Can it cause data loss?** {yes|no}
- **Can it send external communications?** {yes|no}

## 4. MITRE ATLAS Mapping

| ATLAS Tactic | Applicable? | Mitigation |
|---|---|---|
| **Reconnaissance** — probing system capabilities | | |
| **Resource Development** — acquiring infrastructure | | |
| **Initial Access** — prompt injection | | |
| **ML Model Access** — extracting model details | | |
| **Execution** — running tool via injection | | |
| **Persistence** — maintaining access across sessions | | |
| **Defense Evasion** — bypassing guardrails | | |
| **Impact** — real-world harm from tool execution | | |

## 5. Guardrails in Place

- [ ] Input guardrails (injection, PII, secrets, sensitive topics)
- [ ] Output guardrails (schema, groundedness, PII leak, refusal)
- [ ] HITL approval required before execution
- [ ] Circuit breaker can halt this tool
- [ ] Rate limiting applied
- [ ] Audit logged

## 6. Residual Risk

After all guardrails, what risk remains?

**Assessment:** {LOW|MEDIUM|HIGH|CRITICAL}

**Rationale:** {explanation}

## 7. Review History

| Date | Reviewer | Changes |
|---|---|---|
| | | |
