
# ══════════════════════════════════════════════════════════════════════
# Part E: Alignment, Autonomy, and Vulnerability Testing (slides 18-23)
# ══════════════════════════════════════════════════════════════════════

def s18_alignment():
    s = S()
    TITLE(s, "Alignment as an Engineering Problem",
          "Alignment is about whether the system pursues the intended goal within its constraints")
    # Goal-to-action chain
    chain_items = [
        ("User" + chr(10) + "Objective", TEAL, "What the user asked for"),
        ("Agent" + chr(10) + "Plan", PURPLE, "How the agent decides to pursue it"),
        ("Policy" + chr(10) + "Constraints", AMBER, "What the constitution/policy allows"),
        ("Tool" + chr(10) + "Permissions", BLUE_STEEL, "What the tool registry permits"),
        ("Actual" + chr(10) + "Action", GREEN, "What actually executes"),
    ]
    for i, (label, color, desc) in enumerate(chain_items):
        x = 0.5 + i * 2.5
        R(s, x, 1.8, 2.3, 0.7, fill=color, radius=0.1)
        TB(s, x+0.05, 1.85, 2.2, 0.4, label, fs=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        TB(s, x+0.05, 2.25, 2.2, 0.2, desc, fs=10, color=WHITE, align=PP_ALIGN.CENTER)
        if i < 4:
            TB(s, x+2.3, 2.0, 0.2, 0.3, chr(8594), fs=20, bold=True, color=MID_GRAY, align=PP_ALIGN.CENTER)
    TB(s, 0.8, 2.7, 11.7, 0.35,
       "An alignment failure occurs when the agent's behavior diverges from the intended objective and constraints.",
       fs=14, bold=True, color=DARK_TEXT)
    # Goal conflict
    R(s, 0.8, 3.25, 5.5, 2.5, fill=WHITE, border=CORAL, radius=0.1)
    R(s, 0.8, 3.25, 5.5, 0.5, fill=CORAL, radius=0.08)
    TB(s, 1.1, 3.3, 5.0, 0.4, "GOAL CONFLICT SCENARIO", fs=14, bold=True, color=WHITE)
    ML(s, 1.1, 3.85, 5.0, 1.8,
       ["Goal: 'Complete the task at all costs.'",
        "Constraint: 'Do not access restricted data.'",
        "",
        "Conflict: The fastest route requires",
        "restricted data.",
        "",
        "Wrong behavior: Access restricted data",
        "anyway because the goal was 'at all costs.'",
        "",
        "Correct behavior: Stop, explain the",
        "conflict, and escalate to a human.",
        "",
        "Test for this explicitly in multi-turn",
        "agentic scenarios."], fs=12, color=DARK_TEXT, ls=1.35)
    # Reasoning/action divergence
    R(s, 7.0, 3.25, 5.8, 2.5, fill=NAVY, radius=0.12)
    TB(s, 7.3, 3.4, 5.2, 0.35, "REASONING-ACTION DIVERGENCE", fs=14, bold=True, color=TEAL)
    ML(s, 7.3, 3.85, 5.2, 1.8,
       ["Log the model's stated reasoning/plan",
        "separately from its final action.",
        "",
        "If stated plan and actual tool call diverge:",
        "  " + chr(8594) + " Red flag worth auto-escalating",
        "  " + chr(8594) + " Possible alignment faking attempt",
        "  " + chr(8594) + " Possible injection influence",
        "",
        "This is the buildable analogue of",
        "interpretability research: you cannot peer",
        "inside the model's weights, but you CAN",
        "diff its stated reasoning against its",
        "actual behavior and alert on divergence."], fs=12, color=WHITE, ls=1.35)
    R(s, 0.8, 6.05, 11.7, 1.1, fill=NAVY_LIGHT, radius=0.08)
    TB(s, 1.1, 6.1, 11.1, 0.3, "WHAT ALIGNMENT IS NOT", fs=13, bold=True, color=NAVY)
    ML(s, 1.1, 6.4, 11.1, 0.65,
       ["Alignment is not solved by a system prompt. It is engineered through: written policy " + chr(8594) + " behavioral priorities " + chr(8594) + ""
        "runtime controls " + chr(8594) + " adversarial evaluation " + chr(8594) + " deployment gating. Our project analogue: "
        "constitution document " + chr(8594) + " system instructions " + chr(8594) + " classifiers/guardrails " + chr(8594) + " goal-conflict tests " + chr(8594) + " tool authorization."], fs=13, color=DARK_TEXT, ls=1.35)
    PN(s, 18)
    N(s, "Alignment is presented as an engineering problem, not a philosophical one. The "
       "chain: user objective, agent plan, policy constraints, tool permissions, actual "
       "action. An alignment failure occurs when behavior diverges from intended objective "
       "and constraints. Goal-conflict testing is critical: put the agent in a situation "
       "where the fastest path violates policy and verify it escalates rather than "
       "reinterpreting scope. Reasoning-action divergence monitoring is the buildable "
       "analogue of interpretability research: diff the model's stated plan against its "
       "actual tool calls and alert on divergence. Source: ai_trust_safety_architecture.md "
       "Section 9.")
    return s

def s19_anthropic_reference():
    s = S()
    TITLE(s, "Anthropic's Alignment Stack as a Reference Model",
          "Engineering principles we can adopt, clearly distinguished from Anthropic's own implementation")
    stack = [
        ("Written Behavioral" + chr(10) + "Specification", TEAL,
         ["Claude's Constitution (Jan 2026): priority",
          "hierarchy" + chr(8212) + "safety > ethics > compliance >",
          "helpfulness. Explains reasoning behind",
          "principles so models generalize to novel",
          "situations rather than pattern-matching.",
          "BUILD TAKEAWAY: Write your own agent's",
          "constitution as a first-class, versioned",
          "artifact" + chr(8212) + "not just a system prompt."]),
        ("Constitutional AI /" + chr(10) + "Constitutional Classifiers", PURPLE,
         ["Training and runtime classifiers derived",
          "from the same constitution. Next-gen",
          "Constitutional Classifiers (Jan 2026).",
          "BUILD TAKEAWAY: Derive runtime input/",
          "output classifiers from the same policy",
          "document the system prompt uses, so the",
          "two layers cannot drift apart."]),
        ("Responsible Scaling" + chr(10) + "Policy (RSP v3.1)", AMBER,
         ["Tiered risk framework (AI Safety Levels)",
          "gating increasingly capable deployment",
          "behind proportional security requirements.",
          "BUILD TAKEAWAY: Gate agent autonomy behind",
          "a documented safety case. Define tiers for",
          "YOUR agent and require evidence before",
          "promoting to higher autonomy."]),
        ("Alignment Auditing /" + chr(10) + "Interpretability", BLUE_STEEL,
         ["Internal auditing agents probe deployed",
          "models for hidden misaligned behavior under",
          "adversarial multi-turn pressure. Studies",
          "agentic misalignment and alignment faking.",
          "BUILD TAKEAWAY: Build multi-turn, agentic",
          "scenario tests with goal conflicts. Test",
          "whether the agent escalates rather than",
          "acting unilaterally or being deceptive."]),
    ]
    for i, (label, color, lines) in enumerate(stack):
        x = 0.5 + i * 3.15
        R(s, x, 1.8, 2.95, 0.6, fill=color, radius=0.1)
        TB(s, x+0.08, 1.85, 2.8, 0.5, label, fs=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        ML(s, x+0.08, 2.5, 2.8, 2.5, lines, fs=11, color=DARK_TEXT, ls=1.3)
    # Clear distinction
    R(s, 0.8, 5.4, 11.7, 0.65, fill=AMBER_LIGHT, radius=0.08)
    TB(s, 1.1, 5.45, 11.1, 0.5,
       "CRITICAL DISTINCTION: Anthropic's research and deployment approach " + chr(8800) + " This project's implementation. "
       "We reference Anthropic's work as an engineering reference model, not as evidence that we implement their systems.",
       fs=14, bold=True, color=DARK_TEXT)
    # Project mapping
    R(s, 0.8, 6.3, 11.7, 0.9, fill=NAVY, radius=0.1)
    TB(s, 1.2, 6.35, 11.0, 0.3, "OUR PROJECT ANALOGUE", fs=14, bold=True, color=TEAL)
    ML(s, 1.2, 6.65, 11.0, 0.5,
       ["Constitution/Policy " + chr(8594) + " System Instructions " + chr(8594) + " Classifiers and Guardrails " + chr(8594) + " Goal-Conflict Tests " + chr(8594) + ""
        "Tool Authorization " + chr(8594) + " Autonomy Promotion Criteria. This is the engineering translation, not Anthropic's stack."], fs=13, color=WHITE, ls=1.3)
    PN(s, 19)
    N(s, "Anthropic's alignment work is used as an external reference model. Four layers: "
       "Written Behavioral Specification (Claude's Constitution), Constitutional AI/Classifiers, "
       "Responsible Scaling Policy (RSP), and Alignment Auditing/Interpretability. For each, "
       "we extract the engineering takeaway relevant to our project. The critical distinction: "
       "Anthropic's implementation is not our implementation. We reference their approach "
       "for engineering principles, not as evidence that we have built Anthropic's stack. "
       "The project analogue maps: constitution to system instructions, classifiers to "
       "guardrails, RSP to autonomy promotion criteria. Sources: Claude's Constitution "
       "(Jan 2026), Anthropic RSP, Anthropic Alignment Science blog.")
    return s

def s20_autonomy():
    s = S()
    TITLE(s, "Autonomy Control: Human-in/on/out-of-the-Loop",
          "Autonomy is a property of actions, not agents" + chr(8212) + "and the LLM should not be the ultimate authority over its own permissions")
    modes = [
        ("HUMAN-IN-THE-LOOP", CORAL,
         "Human approves BEFORE" + chr(10) + "the action executes",
         ["Irreversible or high-blast-radius actions:",
          "sending external communications,",
          "financial transactions, deleting data,",
          "deploying code.",
          "DocuBot: sending contract summary to",
          "external legal team requires approval."]),
        ("HUMAN-ON-THE-LOOP", AMBER,
         "Action executes, human" + chr(10) + "can observe and interrupt",
         ["Medium-risk, reversible actions:",
          "draft creation, internal updates,",
          "low-value transactions under a cap.",
          "DocuBot: drafting an internal summary",
          "for review, with easy rollback."]),
        ("HUMAN-OUT-OF-THE-LOOP", TEAL,
         "Fully autonomous," + chr(10) + "periodic audit only",
         ["Low-risk, easily reversible, well-tested:",
          "read-only queries, internal search,",
          "drafting for the user's own review.",
          "DocuBot: searching internal documents",
          "for references to a specific clause."]),
    ]
    for i, (label, color, defn, examples) in enumerate(modes):
        x = 0.5 + i * 4.2
        R(s, x, 1.8, 3.95, 0.55, fill=color, radius=0.1)
        TB(s, x+0.1, 1.83, 3.75, 0.49, label, fs=14, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        TB(s, x+0.1, 2.4, 3.75, 0.4, defn, fs=11, color=DARK_TEXT, align=PP_ALIGN.CENTER)
        ML(s, x+0.1, 2.85, 3.75, 1.8, examples, fs=12, color=DARK_TEXT, ls=1.4)
    # Safety mechanisms
    R(s, 0.8, 5.1, 11.7, 1.5, fill=NAVY_LIGHT, radius=0.1)
    TB(s, 1.1, 5.15, 11.1, 0.3, "ADDITIONAL SAFETY MECHANISMS", fs=13, bold=True, color=NAVY)
    ML(s, 1.1, 5.5, 5.2, 1.0,
       ["Action-risk scoring at tool-registration level:",
        "every tool declares risk_tier and reversible flag.",
        "The orchestrator derives HITL mode automatically.",
        "",
        "Circuit breaker / kill switch: hard, out-of-band",
        "stop mechanism enforced at infrastructure layer" + chr(8212),
        "does not depend on model cooperation."], fs=12, color=DARK_TEXT, ls=1.35)
    ML(s, 7.0, 5.5, 5.2, 1.0,
       ["Escalation on goal conflict: if completing a task",
        "requires exceeding declared scope, stop and ask.",
        "Test for this explicitly in eval suite.",
        "",
        "Timeout and fail-closed: if human approval does",
        "not arrive within the deadline, fail closed" + chr(8212),
        "never default to auto-approval on timeout."], fs=12, color=DARK_TEXT, ls=1.35)
    PN(s, 20)
    N(s, "Autonomy is a property of actions, not agents. Three modes: human-in-the-loop "
       "(approval before execution), human-on-the-loop (supervised with interrupt capability), "
       "human-out-of-the-loop (autonomous under predefined controls). The mode is derived "
       "from the action's risk tier and reversibility, not from a global agent setting. "
       "Additional mechanisms: action-risk scoring at tool-registration, circuit breakers "
       "enforced at infrastructure level, escalation on goal conflict, and fail-closed "
       "timeouts. The LLM should not be the ultimate authority over its own permissions. "
       "Source: ai_trust_safety_architecture.md Section 9.2.")
    return s

def s21_red_teaming():
    s = S()
    TITLE(s, "Prompt Injection Prevention " + chr(8800) + " Red Teaming",
          "Runtime defense and adversarial testing are distinct disciplines with different objectives")
    # Comparison
    R(s, 0.8, 1.8, 5.5, 2.2, fill=WHITE, border=TEAL, radius=0.1)
    R(s, 0.8, 1.8, 5.5, 0.5, fill=TEAL, radius=0.08)
    TB(s, 1.1, 1.85, 5.0, 0.4, "PROMPT INJECTION PREVENTION", fs=15, bold=True, color=WHITE)
    TB(s, 1.1, 2.35, 5.0, 0.25, "= Runtime Defense", fs=14, bold=True, color=TEAL)
    ML(s, 1.1, 2.7, 5.0, 1.2,
       ["Operates at inference time.",
        "Objective: block or neutralize",
        "malicious inputs before they influence",
        "model behavior.",
        "Tools: LLM Guard, NeMo Guardrails,",
        "provenance tagging, instruction/data",
        "separation, PolicyGate."], fs=13, color=DARK_TEXT, ls=1.4)
    R(s, 7.0, 1.8, 5.5, 2.2, fill=WHITE, border=CORAL, radius=0.1)
    R(s, 7.0, 1.8, 5.5, 0.5, fill=CORAL, radius=0.08)
    TB(s, 7.3, 1.85, 5.0, 0.4, "RED TEAMING", fs=15, bold=True, color=WHITE)
    TB(s, 7.3, 2.35, 5.0, 0.25, "= Testing Discipline", fs=14, bold=True, color=CORAL)
    ML(s, 7.3, 2.7, 5.0, 1.2,
       ["Operates at evaluation time (CI, scheduled).",
        "Objective: systematically find",
        "vulnerabilities before adversaries do.",
        "Tools: Garak, PyRIT, DeepTeam,",
        "Promptfoo. Not runtime tools.",
        "Tests: jailbreaks, multi-turn attacks,",
        "encoding attacks, data leakage probes."], fs=13, color=DARK_TEXT, ls=1.4)
    # The feedback loop
    R(s, 0.8, 4.3, 11.7, 2.5, fill=NAVY, radius=0.12)
    TB(s, 1.2, 4.45, 10.8, 0.35, "THE RED-TEAM FEEDBACK LOOP", fs=14, bold=True, color=AMBER)
    loop_steps = ["Threat" + chr(10) + "Model", "Attack" + chr(10) + "Suite", "Evaluation", "Regression" + chr(10) + "Gate",
                  "Incident" + chr(10) + "Review", "Updated" + chr(10) + "Test Set"]
    loop_colors = [CORAL, AMBER, PURPLE, BLUE_STEEL, TEAL, GREEN]
    for i, (step, color) in enumerate(zip(loop_steps, loop_colors)):
        x = 1.5 + i * 1.9
        R(s, x, 5.0, 1.6, 0.7, fill=color, radius=0.08)
        TB(s, x+0.05, 5.05, 1.5, 0.6, step, fs=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if i < 5:
            TB(s, x+1.6, 5.2, 0.3, 0.3, chr(8594), fs=20, bold=True, color=MID_GRAY, align=PP_ALIGN.CENTER)
    ML(s, 1.2, 5.9, 10.8, 0.8,
       ["No single red-team run proves security. The stronger model is continuous: threat model, attack suite, evaluation, regression gate, incident review, updated test set.",
        "Current implementation status: Architecture specified (Sections 3, 13). NOT YET IMPLEMENTED in the repo. Garak/PyRIT configs and CI gating are designed but not built."], fs=13, color=WHITE, ls=1.35)
    PN(s, 21)
    N(s, "This slide distinguishes two concepts that are often conflated. Prompt injection "
       "prevention is runtime defense" + chr(8212) + "it operates at inference time to block malicious "
       "inputs. Red teaming is a testing discipline" + chr(8212) + "it operates at evaluation time to "
       "find vulnerabilities before adversaries do. The feedback loop is critical: threat "
       "model, attack suite, evaluation, regression gate, incident review, updated test set. "
       "No single red-team run proves security. Implementation status: architecture "
       "specified, not yet implemented. The /redteam/ directory, Garak/PyRIT configs, "
       "and CI gating are designed but not built. Source: ai_trust_safety_architecture.md "
       "Section 3.")
    return s

def s22_data_poisoning():
    s = S()
    TITLE(s, "Data Poisoning " + chr(8800) + " Prompt Injection",
          "Poisoning corrupts the data supply chain; injection exploits the inference-time interface. Different controls.")
    # Comparison
    R(s, 0.8, 1.8, 5.5, 2.5, fill=WHITE, border=CORAL, radius=0.1)
    R(s, 0.8, 1.8, 5.5, 0.5, fill=CORAL, radius=0.08)
    TB(s, 1.1, 1.85, 5.0, 0.4, "PROMPT INJECTION", fs=15, bold=True, color=WHITE)
    ML(s, 1.1, 2.45, 5.0, 1.7,
       ["Occurs at inference time in the prompt/context.",
        "Malicious content " + chr(8594) + " Prompt/Context " + chr(8594) + " Model.",
        "Mitigated by: input scanners, provenance",
        "tagging, instruction/data separation,",
        "tool authorization backstop.",
        "Timeline: immediate, per-request."], fs=13, color=DARK_TEXT, ls=1.45)
    R(s, 7.0, 1.8, 5.5, 2.5, fill=WHITE, border=AMBER, radius=0.1)
    R(s, 7.0, 1.8, 5.5, 0.5, fill=AMBER, radius=0.08)
    TB(s, 7.3, 1.85, 5.0, 0.4, "DATA POISONING", fs=15, bold=True, color=WHITE)
    ML(s, 7.3, 2.45, 5.0, 1.7,
       ["Occurs when malicious data enters training,",
        "fine-tuning, or retrieval corpora.",
        "Malicious Data " + chr(8594) + " Ingestion " + chr(8594) + " Corpus/Model " + chr(8594) + " Future Behavior.",
        "Mitigated by: source allowlisting, provenance,",
        "content hashing, anomaly detection,",
        "held-out canary evaluation.",
        "Timeline: persistent, affects future behavior."], fs=13, color=DARK_TEXT, ls=1.45)
    # Controls
    R(s, 0.8, 4.55, 11.7, 1.7, fill=NAVY_LIGHT, radius=0.1)
    TB(s, 1.1, 4.6, 11.1, 0.3, "POISONING CONTROLS", fs=13, bold=True, color=NAVY)
    ML(s, 1.1, 4.95, 11.1, 1.2,
       ["1. Provenance and integrity checks on all ingestion sources " + chr(8212) + " checksums, source allowlists, diff-based anomaly detection.",
        "2. Outlier/anomaly detection on new data before ingestion (statistical or embedding-space outlier detection).",
        "3. Held-out canary evaluation after every fine-tune or corpus update " + chr(8212) + " run full eval suite and compare against baseline.",
        "4. Segregated, access-controlled ingestion pipeline " + chr(8212) + " least-privilege principle applied to who/what can write into a corpus.",
        "",
        "Key principle: Runtime guardrails cannot fully solve a poisoned data source. Poisoning must be caught at ingestion time."], fs=12, color=DARK_TEXT, ls=1.35)
    PN(s, 22)
    N(s, "Data poisoning and prompt injection are distinct problems requiring distinct "
       "controls. Prompt injection exploits the inference-time interface; data poisoning "
       "corrupts the data supply chain and affects future behavior persistently. The key "
       "principle: runtime guardrails cannot fully solve a poisoned data source. Poisoning "
       "must be caught at ingestion time through provenance checks, anomaly detection, "
       "and held-out canary evaluation after corpus updates. Implementation status: NOT "
       "IMPLEMENTED. The architecture specifies ingestion-time controls but they have "
       "not been built. Source: ai_trust_safety_architecture.md Section 14.")
    return s

def s23_governance():
    s = S()
    TITLE(s, "Governance as Operational Control",
          "Governance is not documentation" + chr(8212) + "it is the operational system that answers: what happened, who approved it, and what evidence supports it")
    # Governance questions
    questions = ["What happened?", "Which model?", "Which provider?", "Which policy version?",
                 "Which data?", "Which guardrails triggered?", "Was a human involved?",
                 "What action occurred?", "What evidence?"]
    for i, q in enumerate(questions):
        col = i % 3; row = i // 3
        x = 0.8 + col * 4.1; y = 1.8 + row * 0.6
        R(s, x, y, 3.8, 0.45, fill=TEAL_LIGHT, radius=0.06)
        TB(s, x+0.15, y+0.05, 3.5, 0.35, q, fs=13, bold=True, color=DARK_TEXT)
    # Governance loop
    R(s, 0.8, 3.7, 11.7, 2.5, fill=NAVY, radius=0.12)
    TB(s, 1.2, 3.85, 10.8, 0.35, "THE GOVERNANCE LOOP", fs=14, bold=True, color=TEAL)
    loop = ["System" + chr(10) + "Behavior", "Audit" + chr(10) + "Evidence", "Evaluation", "Incident" + chr(10) + "Review",
            "Policy / Code" + chr(10) + "Change", "New" + chr(10) + "Evaluation"]
    lcolors = [TEAL, PURPLE, AMBER, CORAL, BLUE_STEEL, GREEN]
    for i, (step, color) in enumerate(zip(loop, lcolors)):
        x = 1.2 + i * 2.0
        R(s, x, 4.4, 1.7, 0.65, fill=color, radius=0.08)
        TB(s, x+0.05, 4.43, 1.6, 0.6, step, fs=11, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        if i < 5:
            TB(s, x+1.7, 4.55, 0.3, 0.3, chr(8594), fs=20, bold=True, color=MID_GRAY, align=PP_ALIGN.CENTER)
    ML(s, 1.2, 5.2, 10.8, 0.8,
       ["Governance plane components: Append-only audit log  |  Policy versioning  |  Metrics dashboard  |  "
        "HITL approval queue  |  Red-team findings log  |  Incident review workflow  |  Evaluation history  |  "
        "Autonomy promotion evidence.",
        "Implementation status: AuditLogger class IMPLEMENTED. Policy versioning, metrics dashboard, "
        "incident review loop are architecturally specified (Sections 9, 12, 13) but NOT YET IMPLEMENTED."], fs=13, color=WHITE, ls=1.35)
    PN(s, 23)
    N(s, "Governance is presented as an operational control system, not documentation. "
       "It answers nine questions about every system interaction. The governance loop is: "
       "system behavior, audit evidence, evaluation, incident review, policy/code change, "
       "new evaluation. The governance plane includes audit log, policy versioning, metrics, "
       "HITL queue, red-team findings, incident review, evaluation history, and autonomy "
       "promotion evidence. Implementation status: the AuditLogger class (append-only, "
       "with AuditEntry records) is implemented in shared/safety.py. Policy versioning, "
       "the metrics dashboard, and the incident review workflow are architecturally "
       "specified but not yet built. Source: ai_trust_safety_architecture.md Sections 12, 13.")
    return s

