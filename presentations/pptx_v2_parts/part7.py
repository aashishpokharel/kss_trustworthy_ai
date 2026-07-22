
# ══════════════════════════════════════════════════════════════════════
# Part F: Evidence, Provider, Codebase Mapping (slides 24-29)
# ══════════════════════════════════════════════════════════════════════

def s24_evidence_model():
    s = S()
    TITLE(s, "The Evidence Model: From Claim to Residual Risk",
          "Every significant safety claim must be converted into an evidence question with a defined threshold")
    # Bad claim vs good claim
    R(s, 0.8, 1.8, 5.5, 2.0, fill=RED_BG, radius=0.1)
    TB(s, 1.1, 1.85, 5.0, 0.3, "BAD CLAIM (absolute, unverifiable)", fs=12, bold=True, color=CORAL)
    ML(s, 1.1, 2.2, 5.0, 1.4,
       ['"The system is secure."',
        '"The model is safe."',
        '"The system cannot be hacked."',
        '"Hallucinations are solved."',
        '"Bias is eliminated."',
        '"The guardrail guarantees privacy."',
        "",
        "These claims are unfalsifiable and create false confidence."], fs=13, color=DARK_TEXT, ls=1.4)
    R(s, 7.0, 1.8, 5.8, 2.0, fill=GREEN_BG, radius=0.1)
    TB(s, 7.3, 1.85, 5.2, 0.3, "BETTER CLAIM (specific, conditioned, verifiable)", fs=12, bold=True, color=GREEN)
    ML(s, 7.3, 2.2, 5.2, 1.4,
       ['"The evaluated prompt-injection suite achieved',
        'a defined detection rate under the tested',
        'attack conditions, with the tool authorization',
        'layer preventing unauthorized side effects',
        'in the tested scenarios."',
        "",
        "This claim is specific, conditioned on the",
        "evaluation context, and verifiable by re-running",
        "the test suite."], fs=13, color=DARK_TEXT, ls=1.4)
    # Evidence chain
    R(s, 0.8, 4.1, 11.7, 1.8, fill=NAVY, radius=0.12)
    TB(s, 1.2, 4.25, 10.8, 0.35, "THE EVIDENCE CHAIN", fs=14, bold=True, color=AMBER)
    chain = ["Claim", "Threat" + chr(10) + "Model", "Test" + chr(10) + "Dataset", "Metric", "Threshold", "Decision", "Residual" + chr(10) + "Risk"]
    ecolors = [TEAL, CORAL, PURPLE, AMBER, BLUE_STEEL, GREEN, NAVY]
    for i, (step, color) in enumerate(zip(chain, ecolors)):
        x = 1.0 + i * 1.7
        R(s, x, 4.8, 1.45, 0.6, fill=color, radius=0.08)
        TB(s, x+0.05, 4.83, 1.35, 0.55, step, fs=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if i < 6:
            TB(s, x+1.45, 4.95, 0.25, 0.3, chr(8594), fs=18, bold=True, color=MID_GRAY, align=PP_ALIGN.CENTER)
    ML(s, 1.2, 5.55, 10.8, 0.4,
       ["Preferred language: 'Under the evaluated conditions...' 'The implementation currently supports...' "
        "'This control reduces the risk of...' 'Residual risk remains because...'"], fs=13, color=WHITE, ls=1.4)
    # Bottom
    R(s, 0.8, 6.2, 11.7, 0.6, fill=TEAL_LIGHT, radius=0.08)
    TB(s, 1.1, 6.25, 11.1, 0.45,
       "The evidence model is the unifying discipline across every topic in this talk. "
       "No absolute claims. Every assertion is conditioned, tested, and bounded by residual risk.",
       fs=14, bold=True, color=DARK_TEXT)
    PN(s, 24)
    N(s, "The evidence model converts safety claims into evidence questions. Bad claims "
       "are absolute and unfalsifiable: 'the system is secure.' Better claims are specific, "
       "conditioned, and verifiable: 'the evaluated suite achieved X detection rate under "
       "Y conditions.' The evidence chain: claim, threat model, test dataset, metric, "
       "threshold, decision, residual risk. Preferred language includes: 'under the "
       "evaluated conditions,' 'this control reduces the risk of,' and 'residual risk "
       "remains because.' This is the unifying discipline of the entire presentation "
       "and the architecture spec (Section 11).")
    return s

def s25_provider_abstraction():
    s = S()
    TITLE(s, "Multi-Provider Safety: Not Just Config",
          "Adding a second model is not 'swap the API key'" + chr(8212) + "it changes what the guardrail and governance layers need to track")
    R(s, 0.8, 1.8, 5.8, 3.0, fill=WHITE, border=TEAL, radius=0.1)
    R(s, 0.8, 1.8, 5.8, 0.5, fill=TEAL, radius=0.08)
    TB(s, 1.1, 1.85, 5.2, 0.4, "WHY PROVIDER ABSTRACTION MATTERS", fs=14, bold=True, color=WHITE)
    ML(s, 1.1, 2.4, 5.2, 2.3,
       ["LLMClient interface: one internal API,",
        "swappable implementations:",
        "  " + chr(8226) + " MockLLMClient (deterministic, CI)",
        "  " + chr(8226) + " AnthropicLLMClient (Claude)",
        "  " + chr(8226) + " DeepSeekLLMClient (DeepSeek)",
        "  " + chr(8226) + " FallbackLLMClient (failover pair)",
        "",
        "Guardrails must be provider-agnostic by",
        "construction. All safety checks operate on",
        "normalized text in the LLMResponse schema.",
        "",
        "Provider-specific behavior:",
        "  " + chr(8226) + " Different safety postures per provider",
        "  " + chr(8226) + " Different refusal and over-refusal rates",
        "  " + chr(8226) + " Different data-use and retention policies",
        "  " + chr(8226) + " Eval suites run per provider independently"], fs=12, color=DARK_TEXT, ls=1.32)
    R(s, 7.3, 1.8, 5.5, 3.0, fill=NAVY, radius=0.12)
    TB(s, 7.6, 1.95, 5.0, 0.35, "CRITICAL RULES", fs=14, bold=True, color=AMBER)
    ML(s, 7.6, 2.4, 5.0, 2.3,
       ["1. Run full adversarial and bias suites",
        "   against EACH provider independently.",
        "",
        "2. A new provider is not 'integrated'" + chr(8212) + "it is",
        "   'connected' until it has passed the same",
        "   safety case as the first provider.",
        "",
        "3. A provider swap or fallback should never",
        "   silently lower your effective safety bar.",
        "",
        "4. Data governance differs per provider" + chr(8212) + ""
        "   verify zero-retention/no-train settings",
        "   independently for each.",
        "",
        "5. Per-provider cost ceilings as hard",
        "   circuit breakers."], fs=12, color=WHITE, ls=1.32)
    # Provider comparison
    R(s, 0.8, 5.1, 11.7, 1.8, fill=NAVY_LIGHT, radius=0.1)
    TB(s, 1.1, 5.15, 11.1, 0.3, "PROVIDER COMPARISON: NOT 'CLAUDE IS SAFE, DEEPSEEK IS UNSAFE'", fs=13, bold=True, color=NAVY)
    ML(s, 1.1, 5.5, 11.1, 1.3,
       ["Safety is a property of the provider-system configuration under defined evaluation conditions. Provider comparison examines:",
        "safety behavior, refusal behavior, hallucination rate, groundedness, bias, latency, cost, reliability" + chr(8212) + "not a single 'safety' score.",
        "Implementation status: LLMClient interface and provider abstraction are PLANNED (llm-integration-architecture.md Sections 2-5). Not yet implemented.",
        "The Streamlit governance dashboard with provider-comparison page is architecturally specified (Section 8.4) but not yet built."], fs=12, color=DARK_TEXT, ls=1.35)
    PN(s, 25)
    N(s, "Provider abstraction is an engineering capability, not a safety guarantee. "
       "The LLMClient interface enables swappable provider implementations, but each "
       "provider must pass the same safety case independently. Five critical rules: "
       "run eval suites per provider, treat a new provider as connected until proven, "
       "never let a fallback silently lower the safety bar, verify data governance per "
       "provider, and enforce per-provider cost ceilings. Safety is not 'Claude is safe "
       "and DeepSeek is unsafe'" + chr(8212) + "it is a property of the provider-system configuration "
       "under defined conditions. Implementation status: PLANNED. Source: "
       "llm-integration-architecture.md Sections 2 and 9.")
    return s

def s26_codebase_matrix():
    s = S()
    TITLE(s, "Codebase Validation Matrix",
          "Mapping architecture claims to actual implementation evidence")
    rows_data = [
        ["Prompt injection", "Input Guardrails", "PromptInjectionDetector class", "IMPLEMENTED", "Pattern-based, regex"],
        ["PII detection", "Input/Output", "ContentFilter.detect_pii()", "IMPLEMENTED", "Regex patterns, Presidio-ready"],
        ["Output validation", "Output", "OutputValidator class", "IMPLEMENTED", "JSON schema, hallucination patterns"],
        ["Audit logging", "Governance", "AuditLogger class", "IMPLEMENTED", "Append-only, AuditEntry records"],
        ["Permission system", "Tool Layer", "PermissionManager class", "IMPLEMENTED", "Role-based, risk-tiered tools"],
        ["HITL approval", "Tool Layer", "_request_human_approval()", "PARTIALLY", "Simulated; real queue planned"],
        ["Bias detection", "Evaluation", "Counterfactual suite (design)", "PLANNED", "Architecture Section 8"],
        ["Red-teaming", "Evaluation", "Garak/PyRIT configs (design)", "PLANNED", "Architecture Section 3"],
        ["Provider abstraction", "LLM Core", "LLMClient interface (design)", "PLANNED", "Integration doc Sections 2-5"],
        ["Groundedness", "Output", "Basic hallucination check", "PARTIALLY", "Pattern-based only, not NLI"],
        ["Data poisoning", "Ingestion", "Not implemented", "NOT_IMPL", "Architecture Section 14"],
        ["Constitution/policy", "Governance", "Not implemented", "NOT_IMPL", "Architecture Section 9.1"],
    ]
    rows = len(rows_data) + 1; cols = 5
    tbl = s.shapes.add_table(rows, cols, Inches(0.4), Inches(1.55), Inches(12.5), Inches(5.6))
    table = tbl.table
    widths = [2.0, 2.0, 3.0, 2.0, 3.5]
    for c, w in enumerate(widths):
        table.columns[c].width = Inches(w)
    headers = ["Capability", "Layer", "Implementation", "Status", "Notes"]
    status_colors = {"IMPLEMENTED": GREEN, "PARTIALLY": AMBER, "PLANNED": BLUE_STEEL, "NOT_IMPL": CORAL}
    for c, h in enumerate(headers):
        cell = table.cell(0, c); cell.text = ""
        p = cell.text_frame.paragraphs[0]; p.text = h
        p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = WHITE; p.font.name = "Calibri"
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
        cell.margin_left = Inches(0.06); cell.margin_right = Inches(0.06)
    for r, row in enumerate(rows_data, 1):
        for c, val in enumerate(row):
            cell = table.cell(r, c); cell.text = ""
            p = cell.text_frame.paragraphs[0]; p.text = val
            p.font.size = Pt(11); p.font.color.rgb = DARK_TEXT; p.font.name = "Calibri"
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xF0, 0xF4, 0xF8) if r % 2 == 0 else WHITE
            if c == 3:
                p.font.bold = True
                p.font.color.rgb = status_colors.get(val, DARK_TEXT)
            cell.margin_left = Inches(0.06); cell.margin_right = Inches(0.06)
            cell.margin_top = Inches(0.03); cell.margin_bottom = Inches(0.03)
    TB(s, 0.5, 7.15, 12.3, 0.3,
       "Source: ai_trust_safety_architecture.md, llm-integration-architecture.md, shared/safety.py, "
       "2_agentic_ai/02_trustworthy_agent.py. Validated July 2026.",
       fs=10, color=MID_GRAY)
    PN(s, 26)
    N(s, "This is the codebase validation matrix (Artifact D from the presentation "
       "architecture spec). It maps every architecture claim to actual implementation "
       "evidence. Status key: IMPLEMENTED (code exists and is testable), PARTIALLY "
       "(basic implementation exists, full specification not yet built), PLANNED "
       "(architecture designed, not yet coded), NOT_IMPL (recognized gap). The matrix "
       "is the basis for the honesty slide that follows. It was generated by inspecting "
       "shared/safety.py, 2_agentic_ai/02_trustworthy_agent.py, and the architecture "
       "documents.")
    return s

def s27_what_we_built():
    s = S()
    TITLE(s, "What We Built: Architecture Walkthrough",
          "A tour through the implemented components, mapped to the defense-in-depth pipeline")
    pipeline = [
        ("Gateway" + chr(10) + "/ Auth", NAVY, "NOT IMPLEMENTED" + chr(10) + "(architecture" + chr(10) + "specified)"),
        ("Input" + chr(10) + "Guardrails", PURPLE, "IMPLEMENTED:" + chr(10) + "PromptInjectionDetector" + chr(10) + "ContentFilter (PII)" + chr(10) + "SENSITIVE_TOPICS list"),
        ("Orchestrator", AMBER, "IMPLEMENTED:" + chr(10) + "PermissionManager" + chr(10) + "ToolRegistry (risk tiers)" + chr(10) + "process_message() pipeline"),
        ("LLM" + chr(10) + "Core", BLUE_STEEL, "PARTIALLY:" + chr(10) + "Simulated LLM calls" + chr(10) + "(LLMClient design" + chr(10) + "exists, not built)"),
        ("Output" + chr(10) + "Guardrails", GREEN, "IMPLEMENTED:" + chr(10) + "OutputValidator" + chr(10) + "check_hallucination_risk()" + chr(10) + "validate_json_output()"),
        ("Action /" + chr(10) + "Tool Layer", CORAL, "IMPLEMENTED:" + chr(10) + "PermissionManager" + chr(10) + "Tool risk levels" + chr(10) + "Arg validators"),
    ]
    for i, (label, color, status) in enumerate(pipeline):
        x = 0.5 + i * 2.15
        R(s, x, 1.8, 1.9, 0.7, fill=color, radius=0.1)
        TB(s, x+0.05, 1.85, 1.8, 0.4, label, fs=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        ML(s, x+0.05, 2.25, 1.8, 0.55, [status], fs=9, color=WHITE, align=PP_ALIGN.CENTER, ls=1.25)
        if i < 5:
            TB(s, x+1.9, 2.0, 0.25, 0.3, chr(8594), fs=16, bold=True, color=MID_GRAY, align=PP_ALIGN.CENTER)
    # Code details
    R(s, 0.5, 3.2, 6.0, 3.5, fill=WHITE, border=TEAL, radius=0.1)
    R(s, 0.5, 3.2, 6.0, 0.45, fill=TEAL, radius=0.08)
    TB(s, 0.8, 3.23, 5.4, 0.4, "WHAT EXISTS IN shared/safety.py", fs=14, bold=True, color=WHITE)
    ML(s, 0.8, 3.8, 5.4, 2.8,
       ["ContentFilter: detect_pii(), sanitize_pii(),",
        "contains_sensitive_topic() with 10 topic patterns",
        "",
        "PromptInjectionDetector: check() with 11 regex",
        "patterns, compute_risk_score() with heuristics",
        "",
        "OutputValidator: check_hallucination_risk(),",
        "validate_json_output() with schema checking,",
        "check_confidence() with 3-level analysis",
        "",
        "AuditLogger: append-only log, AuditEntry records",
        "with timestamp, user_id, request_hash, risk_score,",
        "validation status, cost, latency",
        "",
        "All pure Python standard library" + chr(8212) + "zero external",
        "dependencies. Intentionally minimal and auditable."], fs=12, color=DARK_TEXT, ls=1.3)
    R(s, 7.0, 3.2, 5.8, 3.5, fill=WHITE, border=AMBER, radius=0.1)
    R(s, 7.0, 3.2, 5.8, 0.45, fill=AMBER, radius=0.08)
    TB(s, 7.3, 3.23, 5.2, 0.4, "WHAT EXISTS IN trustworthy_agent.py", fs=14, bold=True, color=WHITE)
    ML(s, 7.3, 3.8, 5.2, 2.8,
       ["PermissionManager: 8 registered tools, each with",
        "risk_level, allowed_args, arg_validators, rate limits",
        "",
        "ToolRiskLevel enum: SAFE, LOW_RISK, MEDIUM_RISK,",
        "HIGH_RISK, CRITICAL" + chr(8212) + "mapped to role permissions",
        "",
        "Role-based access: viewer, developer, admin",
        "with per-role tool allowlists and risk ceilings",
        "",
        "TrustworthyAgent.process_message(): 10-step",
        "pipeline from input validation through audit logging",
        "",
        "Tool implementations with path traversal prevention,",
        "PII detection on write, command injection blocking,",
        "regex validation, output size/pattern checks"], fs=12, color=DARK_TEXT, ls=1.3)
    PN(s, 27)
    N(s, "This slide walks through the actual implemented components mapped to each "
       "architecture layer. The shared/safety.py module provides ContentFilter, "
       "PromptInjectionDetector, OutputValidator, and AuditLogger" + chr(8212) + "all pure Python "
       "standard library with zero external dependencies. The 02_trustworthy_agent.py "
       "module provides PermissionManager with role-based access and risk-tiered tools, "
       "and TrustworthyAgent with a 10-step safety pipeline. What is NOT yet implemented: "
       "the Gateway/Auth layer, LLMClient provider abstraction, full groundedness scoring, "
       "bias counterfactual suite, and red-teaming harness.")
    return s

def s28_honesty():
    s = S()
    TITLE(s, "What We Have Not Built (Yet)",
          "Being explicit about gaps is more credible than overclaiming" + chr(8212) + "and it tells the team where to invest next")
    gaps = [
        ("No Red-Teaming Infrastructure", CORAL,
         "Garak, PyRIT, and CI gating are designed in the architecture (Section 3) but no /redteam/ directory "
         "exists in the repo. We have the threat model and the tool selection, but adversarial testing is not yet "
         "automated. This means we cannot currently answer 'has this prompt/guardrail change introduced a regression "
         "in our injection defenses.'"),
        ("No Counterfactual Bias Evaluation", PURPLE,
         "The counterfactual test suite design exists (Section 8), but the test generator, CI integration, and "
         "dashboard panel are not built. We can detect PII and injection patterns per-message, but we cannot "
         "currently measure disparate impact across demographic groups."),
        ("No Formal Groundedness Scoring", AMBER,
         "OutputValidator.check_hallucination_risk() uses basic pattern matching. The architecture specifies "
         "NLI-based or LLM-as-judge groundedness scoring with domain-specific thresholds" + chr(8212) + "this is designed "
         "but not implemented. Pattern matching catches obvious cases but cannot verify factual claims."),
        ("No Written Constitution / Policy Document", BLUE_STEEL,
         "The architecture (Section 9.1) specifies a written behavioral specification as a first-class, versioned "
         "artifact that both the system prompt and the classifiers derive from. The current system prompt is "
         "embedded in code. Policy versioning, as specified in Section 13, is not implemented."),
        ("HITL Queue is Simulated", TEAL,
         "The _request_human_approval() method auto-approves for demo purposes. A real approval queue with "
         "timeout, escalation, and audit trail exists in the Streamlit UI design (llm-integration-architecture.md "
         "Section 8.3) but has not been built. The reasoning-action divergence monitor is also not implemented."),
    ]
    for i, (title, color, desc) in enumerate(gaps):
        y = 1.7 + i * 1.1
        R(s, 0.8, y, 0.08, 0.8, fill=color)
        TB(s, 1.1, y, 3.8, 0.3, title, fs=14, bold=True, color=color)
        TB(s, 1.1, y+0.32, 11.4, 0.6, desc, fs=11, color=BLUE_STEEL, line_spacing=1.35)
    PN(s, 28)
    N(s, "This is the honesty slide. Five explicitly identified gaps between the architecture "
       "specification and the current implementation. Each gap is a legitimate, scoped area "
       "for future investment. The gaps are prioritized by the architecture doc's execution "
       "plan: Phase 4 (adversarial hardening) requires the red-team harness; Phase 5 "
       "(continuous operation) requires the bias suite and governance dashboard. Being "
       "explicit about what we have not built serves three purposes: it prevents anyone "
       "from walking away with an inflated sense of what the codebase does, it gives the "
       "team a concrete roadmap for what to build next, and it demonstrates the engineering "
       "discipline of distinguishing specification from implementation.")
    return s

def s29_integrated_walkthrough():
    s = S()
    TITLE(s, "Integrated Walkthrough: One Request Through the Full Architecture",
          "Watching the defense-in-depth system operate as a single, coherent pipeline")
    steps = [
        ("1. Request" + chr(10) + "Arrives", TEAL, "Employee asks DocuBot:" + chr(10) + "'Review the Acme contract" + chr(10) + "and send the summary" + chr(10) + "to legal@client.com'"),
        ("2. Gateway" + chr(10) + "Auth", NAVY, "Identity verified." + chr(10) + "Rate limit checked." + chr(10) + "Caller provenance" + chr(10) + "tagged: human, employee."),
        ("3. Input" + chr(10) + "Guardrails", PURPLE, "Prompt injection scan:" + chr(10) + "clean. PII detection:" + chr(10) + "found email address" + chr(10) + "" + chr(8594) + " tokenized."),
        ("4. Context" + chr(10) + "Assembly", AMBER, "Orchestrator retrieves" + chr(10) + "Acme contract. Tags it:" + chr(10) + "{source: internal_doc," + chr(10) + "trust: high}."),
        ("5. LLM" + chr(10) + "Inference", BLUE_STEEL, "Model analyzes contract." + chr(10) + "Generates summary." + chr(10) + "Proposes action:" + chr(10) + "send_email()."),
        ("6. Output" + chr(10) + "Guardrails", GREEN, "Hallucination check:" + chr(10) + "claims verified against" + chr(10) + "source contract. PII" + chr(10) + "leakage scan: clean."),
        ("7. Policy" + chr(10) + "Gate", CORAL, "send_email to external" + chr(10) + "recipient = HIGH risk." + chr(10) + "HITL approval required." + chr(10) + "Queued for human review."),
        ("8. Action +" + chr(10) + "Audit", NAVY, "Human approves. Email sent." + chr(10) + "Audit entry written:" + chr(10) + "who, what, when, which" + chr(10) + "policy, which model."),
    ]
    for i, (label, color, desc) in enumerate(steps):
        x = 0.3 + i * 1.62
        R(s, x, 1.7, 1.45, 1.35, fill=color, radius=0.1)
        TB(s, x+0.05, 1.75, 1.35, 0.55, label, fs=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        ML(s, x+0.05, 2.2, 1.35, 0.8, [desc], fs=8, color=WHITE, align=PP_ALIGN.CENTER, ls=1.2)
        if i < 7:
            TB(s, x+1.45, 2.15, 0.17, 0.3, chr(8594), fs=16, bold=True, color=MID_GRAY, align=PP_ALIGN.CENTER)
    # Governance cross-cut
    R(s, 0.5, 3.3, 12.3, 0.45, fill=TEAL_LIGHT, radius=0.08)
    TB(s, 0.8, 3.35, 11.7, 0.35,
       "GOVERNANCE PLANE: Every step writes to the append-only audit log. Policy version v2.3 active. Metrics updated in real time.",
       fs=12, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER)
    # What the walkthrough demonstrates
    R(s, 0.5, 4.0, 12.3, 2.8, fill=NAVY, radius=0.12)
    TB(s, 0.9, 4.15, 11.5, 0.35, "WHAT THIS WALKTHROUGH DEMONSTRATES", fs=14, bold=True, color=TEAL)
    ML(s, 0.9, 4.6, 11.5, 2.0,
       ["1. The controls are not isolated concepts. They form a system. A failure at any layer has downstream layers that can catch it.",
        "2. The LLM is one component among many. The model proposes; the system validates, authorizes, and audits.",
        "3. The human decision point (HITL approval) is integrated into the pipeline, not bolted on after the fact.",
        "4. Every action leaves an audit trail. You can answer: who did what, when, under which policy, with which model.",
        "5. The architecture is defense-in-depth: input scanning, output validation, tool authorization, and governance are independent, testable checkpoints.",
        "",
        "Trustworthy AI is engineered through architecture, controlled through guardrails and authorization, evaluated through evidence, and maintained through governance."], fs=13, color=WHITE, ls=1.35)
    PN(s, 29)
    N(s, "This is the final integrated walkthrough. One request through all eight stages "
       "of the architecture, from user request to audited action. The walkthrough "
       "demonstrates five things: (1) controls are a system, not isolated concepts; "
       "(2) the LLM proposes but the system validates; (3) HITL is integrated into the "
       "pipeline; (4) every action leaves an audit trail; (5) defense-in-depth means "
       "independent, testable checkpoints at every stage. This is the closing visual "
       "that makes the architecture concrete. The concluding statement is the thesis "
       "of the entire presentation.")
    return s

