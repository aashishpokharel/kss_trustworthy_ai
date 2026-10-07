
# 🤖 Trustworthy AI for LLMs & Agentic AI

## 🎯 KSS Session: Testing and Best Practices

**Audience:** AI/Software Engineers  
**Duration:** 3 Hours (2 hours theory + 1 hour coding)

---

## 📋 Session Structure

### Part 1: Why Trustworthy AI? (30 min)

**The Problem:**
- LLMs are non-deterministic — same input can give different outputs
- Prompt injection attacks are trivial to execute
- Agentic AI can cause real-world damage (delete files, send emails, execute commands)
- Data privacy regulations (GDPR, CCPA) apply to AI systems

**Key Principle:** Defense in Depth — multiple safety layers
```
User Input → Sanitize → Detect Injection → Check Permissions → Execute → Validate Output → Audit Log
```

### Part 2: The Anti-Patterns (30 min)

Run the demo showing what NOT to do:
```bash
python "2_agentic_ai/01_naive_agent.py"
```

**What you'll see:**
- Naive agent that executes ANY tool the LLM suggests
- No validation on arguments (path traversal, command injection)
- No permission system (any user can delete files)
- No human oversight
- No audit trail

### Part 3: The Trustworthy Way (30 min)

Run the trustworthy implementation:
```bash
python "2_agentic_ai/02_trustworthy_agent.py"
```

**What you'll see:**
- Permission manager with role-based access
- Input validation pipeline (PII, injection, sensitive topics)
- Human-in-the-loop for dangerous operations
- Complete audit trail
- Rate limiting

### Part 4: Safety Utilities Deep Dive (30 min)

Key components from `trust_safety/lessons/safety.py`:

| Component | Purpose |
|-----------|---------|
| `ContentFilter` | PII detection, sanitization, sensitive topic filtering |
| `PromptInjectionDetector` | Pattern-based injection detection, risk scoring |
| `OutputValidator` | JSON schema validation, hallucination detection |
| `AuditLogger` | Immutable audit trail for all interactions |

> These teaching utilities ship inside the canonical `trust_safety/` package as
> `trust_safety.lessons`. Production-grade equivalents — built on Pydantic v2 and
> Microsoft Presidio, with tamper-evident audit logging — live alongside them under
> `trust_safety/guardrails/` and `trust_safety/governance/`. Each teaching class is
> docstring-mapped to its production counterpart.

### Break (10 min)

### Part 5: 🏆 Coding Challenge (1 hour)

Open the challenge:
```
3_testing/CHALLENGE.md
```

**Task:** Build a safe code review agent function that:
1. Validates inputs (PII, injection, sanity)
2. Enforces role-based permissions
3. Validates outputs
4. Logs everything
5. Passes all 5 test cases

### Part 6: Review & Takeaways (15 min)

Go through the checklist:
```
4_best_practices/checklist.md
```

---

## 📁 Project Structure

```
trustworthy_ai/
├── trust_safety/                 # Canonical safety package (single source of truth)
│   ├── lessons/                  #   ↳ stdlib-only teaching layer used by the demos
│   │   ├── config.py             #     Configuration templates
│   │   └── safety.py             #     Core safety utilities
│   ├── guardrails/               #   ↳ production input/output guardrails
│   ├── orchestrator/             #   ↳ tool registry, policy gate, approval queue
│   ├── governance/               #   ↳ tamper-evident audit log
│   └── ...                       #   ↳ llm, gateway, policies, eval, redteam, tests
│
├── 1_llm_basics/
│   ├── 01_prompt_engineering.py  # Usual vs Trustworthy prompting
│   └── 02_data_privacy_rag.py    # RAG with data governance
│
├── 2_agentic_ai/
│   ├── 01_naive_agent.py         # ANTI-PATTERN demo
│   └── 02_trustworthy_agent.py   # Trustworthy agent
│
├── 3_testing/
│   ├── 01_llm_testing.py         # Test suite
│   └── CHALLENGE.md              # 1-hour coding challenge
│
├── 4_best_practices/
│   └── checklist.md              # Complete best practices guide
│
├── 5_responsible_trustworthy_ai/ # Core questions (C1–C4) + running case
│
├── questions/                    # Session, agentic and scenario question sets
│
├── learning_resources/           # Student-facing module document (Markdown + PDF)
│   └── build_pdf.py              #   ↳ renders the Markdown to a printable PDF
│
└── README.md                     # This file
```

> 📚 **Learning resources:** the student-facing module companion — learning
> objectives, the Northline Bank running case, sessions, labs, assessment and a
> repository map — lives in [`learning_resources/`](learning_resources/).
> Edit the Markdown source and rebuild the PDF with
> `python3 learning_resources/build_pdf.py`.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- No external dependencies required (pure Python standard library only)

> **Optional:** the production guardrail stack under `trust_safety/` (everything
> except `trust_safety/lessons/`) additionally requires **Python 3.10+** and the
> packages in `trust_safety/requirements.txt` (Pydantic v2, Microsoft Presidio).
> The session lessons do not need it — they import only `trust_safety.lessons`.

### Environment Setup

```bash
# Clone or navigate to the project
cd d:\FUSE\trustworthy_ai

# Create virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows Command Prompt:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# No pip install needed! All dependencies are Python standard library.
```

> **Why no external dependencies?** This is intentional — zero external packages means zero supply chain risk. Safety/security code should be minimal and fully auditable. Students can run everything immediately without `pip install`.

### Run Demos

```bash
# 1. Prompt Engineering Demo
python "1_llm_basics/01_prompt_engineering.py"

# 2. Data Privacy & RAG Demo
python "1_llm_basics/02_data_privacy_rag.py"

# 3. Naive Agent (Anti-pattern)
python "2_agentic_ai/01_naive_agent.py"

# 4. Trustworthy Agent
python "2_agentic_ai/02_trustworthy_agent.py"

# 5. Run Test Suite
python "3_testing/01_llm_testing.py"
```

### Deactivating the Environment

When you're done:
```bash
deactivate
```

### For the Coding Challenge
```bash
# Open the challenge
code "3_testing/CHALLENGE.md"

# Create your solution file
# Implement safe_code_review() function
# Run tests to verify
python -c "import sys; sys.path.insert(0, '.'); exec(open('path/to/your/solution.py').read()); run_challenge_tests()"
```

---

## 🔑 Key Takeaways

### The Trustworthy AI Mindset

| Instead of... | Think... |
|--------------|----------|
| "Will the LLM do what I want?" | "How will the system fail safely?" |
| "Let the LLM figure it out" | "Validate everything, trust nothing" |
| "It works in testing" | "What happens with adversarial input?" |
| "Add features quickly" | "Add safety guards proportionally" |

### The 3 Pillars of Trustworthy AI Agents

1. **Permissions** — Least privilege principle for every tool
2. **Validation** — Input, output, and argument validation at every step  
3. **Observability** — Full audit trail, monitoring, and alerting

### The Golden Rule

> **Never trust LLM output implicitly. Always validate and sanitize.**

---

## 📚 Further Reading

- [OWASP LLM Security](https://owasp.org/www-project-top-10-for-llm-applications/)
- [Prompt Injection Research](https://arxiv.org/abs/2302.12173)
- [Agent Safety](https://www.anthropic.com/research/alignment)
- [GDPR for AI Systems](https://gdpr.eu/ai/)

---

## 🤝 Contributing

This is a KSS session resource. Feel free to extend:
- Add more injection patterns to `PromptInjectionDetector`
- Add more PII patterns to `ContentFilter`
- Add more tool implementations to the agent
- Create additional coding challenges

When a teaching utility gains a production counterpart, keep the two in sync and
update the mapping table in the docstring of `trust_safety/lessons/safety.py`.

---
<!-- # Resume this session with:
# claude --resume 97b64e4b-e9b4-4a88-a98d-f2dbb4f4d9c0
 -->
