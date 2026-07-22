# ══════════════════════════════════════════════════════════════════════
# Part B: Failure Model + Architecture (slides 6-8)
# ══════════════════════════════════════════════════════════════════════

def s06_architecture_threat_map():
    s = S()
    TITLE(s, "The System Architecture as Threat Map",
          "Every architectural boundary is also a place things can go wrong")
    layers = [
        (0.8, "Gateway" + chr(10) + "/ Auth", NAVY,
         ["Identity spoofing", "Unauthorized caller", "Rate-limit bypass"]),
        (2.8, "Input" + chr(10) + "Guardrails", PURPLE,
         ["Prompt injection", "PII in input", "Secrets in prompt", "Jailbreak attempt"]),
        (4.8, "Orchestrator", AMBER,
         ["Over-retrieval", "Wrong context assembly", "Tool routing error", "Missing human gate"]),
        (6.8, "LLM Core", BLUE_STEEL,
         ["Hallucination", "Bias in generation", "Instruction drift", "Model regurgitation"]),
        (8.8, "Output" + chr(10) + "Guardrails", GREEN,
         ["Hallucinated claims", "PII leakage", "Invalid JSON", "Harmful content"]),
        (10.8, "Action / Tool" + chr(10) + "Layer", CORAL,
         ["Unauthorized tool call", "Excessive autonomy", "No circuit breaker", "Irreversible action"]),
    ]
    for (x, label, color, threats) in layers:
        R(s, x, 1.9, 1.7, 0.8, fill=color, radius=0.1)
        TB(s, x+0.05, 1.95, 1.6, 0.5, label, fs=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        ML(s, x+0.1, 2.45, 1.5, 1.2, threats, fs=9, color=WHITE, ls=1.35)
    # Governance cross-cutting
    R(s, 0.8, 3.95, 11.7, 0.45, fill=TEAL_LIGHT, radius=0.08)
    TB(s, 1.1, 4.0, 11.1, 0.35,
       "CROSS-CUTTING GOVERNANCE THREATS: Missing audit trail  |  Stale policy  |  No incident review  |  Unversioned constitution",
       fs=12, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER)
    # Key principle
    R(s, 0.8, 4.65, 11.7, 2.0, fill=NAVY, radius=0.12)
    TB(s, 1.2, 4.85, 10.8, 0.4, "THE DEFENSE-IN-DEPTH PRINCIPLE", fs=14, bold=True, color=TEAL)
    ML(s, 1.2, 5.3, 10.8, 1.2,
       ["No single layer is the safety layer. Safety is the property that emerges from independent,",
        "independently-testable checkpoints at every stage of the pipeline.",
        "",
        "A failure at one layer should be caught at the next:",
        "  Injection bypasses input scanner " + chr(8594) + " Caught by output validation?",
        "  Hallucination passes output check " + chr(8594) + " Caught by tool authorization?",
        "  Tool auth allows action " + chr(8594) + " Caught by audit + incident review?",
        "",
        "Treat the LLM as a powerful but imperfect component" + chr(8212) + "not as the safety authority."], fs=13, color=WHITE, ls=1.35)
    PN(s, 6)
    N(s, "This is one of the most important slides in the talk. Every architectural boundary "
       "in DocuBot's pipeline is also a place where things can go wrong. The defense-in-depth "
       "principle means no single layer is the safety layer" + chr(8212) + "safety emerges from independent "
       "checkpoints at every stage. A prompt injection that bypasses the input scanner should "
       "still be caught by output validation or tool authorization. This is also why we cannot "
       "rely on the LLM itself as the safety authority" + chr(8212) + "the model is a component, not a "
       "gatekeeper. Source: ai_trust_safety_architecture.md Section 1.")
    return s

def s07_failure_control_matrix():
    s = S()
    TITLE(s, "The Failure-to-Control Matrix", "Every failure maps to a location, a consequence, a control, and evidence")
    rows_data = [
        ["Prompt injection", "Input / context", "Unauthorized instruction", "Provenance, scanners, policy gate", "Injection test suite"],
        ["Data poisoning", "Ingestion", "Persistent behavior shift", "Integrity, provenance, anomaly detection", "Post-update eval"],
        ["PII exposure", "Input / output", "Privacy violation", "Detection, redaction, tokenization", "Synthetic PII tests"],
        ["Secret leakage", "Input / output", "Credential compromise", "Secret scanner", "Secret regression tests"],
        ["Hallucination", "Model / output", "Incorrect decision", "Grounding, verification", "Known-answer eval"],
        ["Bias", "Model / system", "Disparate treatment", "Counterfactual tests", "Group-level metrics"],
        ["Invalid output", "Output / tool boundary", "Tool failure", "Schema + semantic validation", "Schema tests"],
        ["Excessive autonomy", "Tool layer", "Real-world harm", "Risk tiers, HITL", "Safety case"],
        ["Misalignment", "Planning / action", "Scope violation", "Policy, goal-conflict eval", "Multi-turn scenarios"],
        ["Governance failure", "Lifecycle", "No accountability", "Audit + policy versioning", "Audit completeness"],
    ]
    rows = len(rows_data) + 1
    cols = 5
    tbl = s.shapes.add_table(rows, cols, Inches(0.3), Inches(1.6), Inches(12.7), Inches(5.5))
    table = tbl.table
    widths = [2.2, 2.0, 2.4, 3.3, 2.8]
    for c, w in enumerate(widths):
        table.columns[c].width = Inches(w)
    headers = ["Failure", "Location", "Consequence", "Control", "Evidence"]
    for c, h in enumerate(headers):
        cell = table.cell(0, c); cell.text = ""
        p = cell.text_frame.paragraphs[0]; p.text = h
        p.font.size = Pt(12); p.font.bold = True; p.font.color.rgb = WHITE; p.font.name = "Calibri"
        cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
        cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08)
    for r, row in enumerate(rows_data, 1):
        for c, val in enumerate(row):
            cell = table.cell(r, c); cell.text = ""
            p = cell.text_frame.paragraphs[0]; p.text = val
            p.font.size = Pt(11); p.font.color.rgb = DARK_TEXT; p.font.name = "Calibri"
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xF0, 0xF4, 0xF8) if r % 2 == 0 else WHITE
            cell.margin_left = Inches(0.08); cell.margin_right = Inches(0.08)
            cell.margin_top = Inches(0.04); cell.margin_bottom = Inches(0.04)
    TB(s, 0.5, 7.1, 12.3, 0.3,
       "This is an internal planning artifact" + chr(8212) + "the presentation does not walk through every row, "
       "but every subsequent section references the relevant row.", fs=10, color=MID_GRAY)
    PN(s, 7)
    N(s, "This matrix is the internal planning artifact from Section 10 of the presentation "
       "architecture spec. It maps every failure to its location in the pipeline, the "
       "consequence if unmitigated, the engineering control that addresses it, and the "
       "evidence that verifies the control works. We will not walk through every row" + chr(8212) + ""
       "instead, each subsequent section will reference its row. The matrix ensures we "
       "cover more than just prompt injection and hallucination. Notice the governance "
       "failure row: no audit trail means no accountability, regardless of how good the "
       "technical controls are.")
    return s

def s08_explainability_limits():
    s = S()
    TITLE(s, "Explainability and Its Limits",
          "Explainability is evidence that may contribute to a trust judgment" + chr(8212) + "it is not the judgment itself")
    # Two-column: what XAI gives vs what it does not
    BOX(s, 0.8, 1.8, 5.5, 2.8, "What XAI (SHAP, LIME, Attention) Gives You",
         ["Local, correlational attribution:",
          "'Feature X was associated with output Y'",
          "",
          "Useful for: debugging individual predictions,",
          "identifying spurious correlations in training",
          "data, surfacing data quality issues.",
          "",
          "Limitation: post-hoc, not causal. A SHAP",
          "value tells you about THIS prediction, not",
          "about overall model safety, fairness, or",
          "robustness under distribution shift."], fs=13, tfs=15)
    BOX(s, 7.0, 1.8, 5.5, 2.8, "What Explainability Does NOT Guarantee",
         ["Explainability does not guarantee fairness.",
          "Explainability does not guarantee privacy.",
          "Explainability does not guarantee robustness.",
          "Explainability does not protect against prompt injection.",
          "Explainability does not authorize external actions.",
          "Explainability does not provide evidence that a",
          "control works under adversarial conditions.",
          "",
          "Explainability is one of NIST's seven characteristics" + chr(8212),
          "not a synonym for trustworthiness."], title_color=CORAL, fs=13, tfs=15)
    # Bottom: LLM-specific problem
    R(s, 0.8, 4.85, 11.7, 1.6, fill=NAVY, radius=0.12)
    TB(s, 1.2, 5.0, 10.8, 0.35, "THE LLM-SPECIFIC PROBLEM", fs=14, bold=True, color=AMBER)
    ML(s, 1.2, 5.4, 10.8, 0.9,
       ["LLMs can hallucinate their own explanations. A model asked 'why did you say that' generates",
        "plausible-sounding rationale that may not reflect its actual internal process at all.",
        "This is a known, current interpretability research problem" + chr(8212) + "not a hypothetical.",
        "Practical implication: treat model self-reported reasoning as a useful signal, not ground truth.",
        "Corroborate with behavioral testing: counterfactuals, adversarial probes, known-answer evaluation."], fs=13, color=WHITE, ls=1.35)
    # Reframe
    R(s, 0.8, 6.7, 11.7, 0.45, fill=TEAL_LIGHT, radius=0.08)
    TB(s, 1.1, 6.73, 11.1, 0.38,
       "Explainability is an INPUT to a trust judgment. Trust is the OUTPUT of system-level verification across ALL seven NIST characteristics.",
       fs=14, bold=True, color=DARK_TEXT)
    PN(s, 8)
    N(s, "This slide integrates the explainability material from the original slide plan into "
       "the broader system-safety narrative. The key reframe: explainability is evidence "
       "that MAY contribute to a trust judgment" + chr(8212) + "it is not the trust judgment itself. "
       "XAI methods like SHAP and LIME give local, correlational attributions. They do not "
       "guarantee fairness, privacy, robustness, or security. The LLM-specific problem is "
       "critical: models can hallucinate their own explanations, generating plausible-sounding "
       "rationale that does not reflect actual internal processing. Practical takeaway: treat "
       "self-reported reasoning as a signal, corroborate with behavioral testing. This connects "
       "to NIST: explainability is one of seven characteristics, not a synonym for trustworthiness. "
       "Sources: NIST AI RMF; Molnar, Interpretable Machine Learning; Samek et al., Explainable AI.")
    return s

