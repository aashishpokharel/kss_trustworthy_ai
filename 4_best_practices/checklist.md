# ✅ Trustworthy AI for LLMs & Agentic AI — Best Practices Checklist

## 1. Prompt Engineering

### ❌ Never Do This
```
- ❌ Direct string interpolation: f"Answer: {user_input}"
- ❌ No input validation/sanitization
- ❌ No prompt injection detection
- ❌ No separation between instructions and data
- ❌ Using eval() or exec() on LLM output
```

### ✅ Always Do This
```
- [ ] 1.1 Sanitize all user inputs before constructing prompts
- [ ] 1.2 Run prompt injection detection on every user input
- [ ] 1.3 Use clear delimiters between instructions and user data
- [ ] 1.4 Validate LLM output structure (JSON schema, etc.)
- [ ] 1.5 Check output for PII leakage
- [ ] 1.6 Check for hallucination indicators in output
- [ ] 1.7 Never execute code from LLM output
- [ ] 1.8 Implement rate limiting per user/session
- [ ] 1.9 Audit log every prompt-response pair
```

## 2. Data Privacy & RAG

### ❌ Never Do This
```
- ❌ Ingesting documents without PII scanning
- ❌ No access control on document retrieval
- ❌ Returning raw documents to users
- ❌ No ability to delete specific documents
- ❌ No tracking of which data was used
```

### ✅ Always Do This
```
- [ ] 2.1 Scan all documents for PII before embedding
- [ ] 2.2 Implement role-based access control per document
- [ ] 2.3 Sanitize retrieved context before LLM prompt
- [ ] 2.4 Support right-to-forget (document deletion)
- [ ] 2.5 Track data lineage (who accessed what, when)
- [ ] 2.6 Audit log every retrieval operation
- [ ] 2.7 Limit context size to prevent prompt overflow
- [ ] 2.8 Filter sensitive topics before retrieval
```

## 3. Agentic AI Safety

### ❌ Never Do This
```
- ❌ Letting LLM decide tool calls without validation
- ❌ No permission system for tools
- ❌ shell=True in subprocess calls
- ❌ No human approval for dangerous operations
- ❌ Unrestricted file system access
- ❌ No session/context boundaries
- ❌ No rate limiting on tool execution
```

### ✅ Always Do This
```
- [ ] 3.1 Define risk levels for every tool
- [ ] 3.2 Implement role-based tool permissions
- [ ] 3.3 Validate all arguments before tool execution
- [ ] 3.4 Require human approval for high-risk tools
- [ ] 3.5 Never use shell=True (use subprocess with list args)
- [ ] 3.6 Path traversal protection on all file operations
- [ ] 3.7 Rate limiting per tool per user role
- [ ] 3.8 Sandbox dangerous tool execution
- [ ] 3.9 Set max tools per request (e.g., 3 per message)
- [ ] 3.10 Implement session timeouts and boundaries
```

## 4. Testing Requirements

### Minimum Test Coverage
```
- [ ] 4.1 Unit tests for content filtering
- [ ] 4.2 Unit tests for injection detection
- [ ] 4.3 Unit tests for output validation
- [ ] 4.4 Property-based tests (idempotency, invariants)
- [ ] 4.5 Integration tests for permission enforcement
- [ ] 4.6 Load tests for rate limiting
- [ ] 4.7 Edge case tests (empty input, special chars, unicode)
```

### Test Scenarios to Cover
```
- [ ] 4.8 Normal operation works correctly
- [ ] 4.9 PII is detected and sanitized
- [ ] 4.10 Prompt injection is blocked
- [ ] 4.11 Unauthorized tool access is rejected
- [ ] 4.12 Rate limits are enforced
- [ ] 4.13 Audit logs are correctly populated
- [ ] 4.14 Hallucination indicators are flagged
```

## 5. Monitoring & Observability

### Required
```
- [ ] 5.1 Audit log every LLM interaction
- [ ] 5.2 Track cost per user/session
- [ ] 5.3 Monitor latency for anomaly detection
- [ ] 5.4 Alert on high-risk score inputs
- [ ] 5.5 Track rate limit violations
- [ ] 5.6 Monitor tool usage patterns
- [ ] 5.7 Log permission denied events
```

### Recommended
```
- [ ] 5.8 Dashboard for real-time monitoring
- [ ] 5.9 Automated alerts on abuse patterns
- [ ] 5.10 Regular audit log review process
- [ ] 5.11 Cost anomaly detection
- [ ] 5.12 Periodic security testing schedule
```

## 6. Deployment Checklist

### Pre-Production
```
- [ ] 6.1 All security tests pass
- [ ] 6.2 Rate limiting configured per environment
- [ ] 6.3 Audit logging enabled and log storage confirmed
- [ ] 6.4 Human approval workflows tested
- [ ] 6.5 Role-based access control verified
- [ ] 6.6 Prompt injection detection tested with known patterns
- [ ] 6.7 PII scanning patterns reviewed and updated
- [ ] 6.8 Environment variables used (no hardcoded secrets)
```

### Production
```
- [ ] 6.9 Gradual rollout with monitoring
- [ ] 6.10 Incident response plan for AI safety breaches
- [ ] 6.11 Regular security reviews scheduled
- [ ] 6.12 Dependency updates monitored for CVEs
- [ ] 6.13 Model versioning and rollback capability
- [ ] 6.14 User feedback mechanism for safety issues
```

## 7. Architecture Decision Records

### Key Decisions to Document
```
- [ ] 7.1 Chosen safety framework and rationale
- [ ] 7.2 Tool risk level classifications
- [ ] 7.3 User role definitions and permissions
- [ ] 7.4 Human approval workflow design
- [ ] 7.5 Audit log retention policy
- [ ] 7.6 Rate limiting strategy
- [ ] 7.7 Content filtering approach
- [ ] 7.8 Model selection criteria (safety features)
```

---

## Quick Reference: Usual vs Trustworthy

| Aspect | ❌ Usual Way | ✅ Trustworthy Way |
|--------|------------|-------------------|
| **Prompt Construction** | `f"Answer: {input}"` | Sanitize + Inject detection + Delimiters |
| **Tool Execution** | LLM decides everything | Permission system + Human approval |
| **Data Access** | All documents to all users | Role-based access control |
| **Command Execution** | `subprocess.run(cmd, shell=True)` | Sandboxed, validated, no shell=True |
| **Output Handling** | Use response directly | Validate + Sanitize + Check hallucinations |
| **Testing** | Manual testing | Automated tests + Property-based tests |
| **Monitoring** | Nothing | Full audit trail + Cost tracking + Alerts |
| **Configuration** | Hardcoded values | Env vars + Config validation |

---

**Remember:** Trustworthy AI is not about building perfect models. It's about building robust systems that handle failure gracefully, respect user privacy, and operate within defined safety boundaries. The goal is **defense in depth** — multiple layers of protection so that if one layer fails, others catch it.