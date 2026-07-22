
# ══════════════════════════════════════════════════════════════════════
# Part D: Model and Output Safety (slides 13-17)
# ══════════════════════════════════════════════════════════════════════

def s13_llm_untrusted():
    s = S()
    TITLE(s, "The LLM as an Untrusted Component",
          "Treat the model the same way you treat any external API" + chr(8212) + "validate inputs, validate outputs")
    # Three key rules
    rules = [
        ("NEVER TRUST" + chr(10) + "MODEL OUTPUT", CORAL,
         "A fluent, confident response is not automatically valid. "
         "The model can be wrong, biased, hallucinated, or manipulated "
         "without any visible signal. Confidence " + chr(8800) + " correctness."),
        ("ALWAYS VALIDATE" + chr(10) + "BEFORE ACTING", AMBER,
         "Schema validation, semantic validation, and business-rule "
         "validation must run before any model output reaches the "
         "tool layer. 'Valid JSON' is not sufficient" + chr(8212) + "a $50,000 "
         "refund in valid JSON is still a policy violation."),
        ("FAIL CLOSED," + chr(10) + "NOT OPEN", NAVY,
         "If validation fails, the default behavior is block, retry "
         "with corrective prompting, or escalate to human. Never "
         "silently pass through unvalidated output to downstream systems."),
    ]
    for i, (label, color, desc) in enumerate(rules):
        y = 1.9 + i * 1.7
        R(s, 0.8, y, 0.55, 0.55, fill=color, radius=0.08)
        TB(s, 0.8, y+0.05, 0.55, 0.45, str(i+1), fs=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        R(s, 1.5, y, 3.5, 1.3, fill=WHITE, border=color, radius=0.1)
        TB(s, 1.65, y+0.05, 3.2, 0.8, label, fs=16, bold=True, color=color, align=PP_ALIGN.CENTER)
        TB(s, 5.3, y+0.1, 7.2, 1.1, desc, fs=14, color=DARK_TEXT, line_spacing=1.4)
    # DocuBot example
    R(s, 0.8, 6.1, 11.7, 1.05, fill=RED_BG, radius=0.08)
    TB(s, 1.1, 6.15, 11.1, 0.3, "DOCUBOT FAILURE EXAMPLE", fs=11, bold=True, color=CORAL)
    ML(s, 1.1, 6.4, 11.1, 0.65,
       ["Model output: 'Refund amount = $50,000' (valid JSON). Business rule: 'Maximum refund = $500'.",
        "Without output validation: $50,000 is processed. With validation: blocked, human escalation triggered.",
        "The model did nothing wrong by its training" + chr(8212) + "it generated a plausible number. The SYSTEM failed by executing unvalidated output."], fs=12, color=DARK_TEXT, ls=1.3)
    PN(s, 13)
    N(s, "This slide establishes a fundamental engineering principle: treat the LLM as an "
       "untrusted component. Three rules: (1) Never trust model output implicitly" + chr(8212) + ""
       "confidence and fluency do not equal correctness. (2) Always validate before acting" + chr(8212) + ""
       "schema, semantics, and business rules must pass before any output reaches the tool "
       "layer. (3) Fail closed, not open" + chr(8212) + "default to block, retry, or escalate when "
       "validation fails. The DocuBot example shows why: a model outputting a $50,000 refund "
       "in valid JSON is syntactically correct but a business-rule violation. The system "
       "fails if it executes unvalidated output. Source: ai_trust_safety_architecture.md "
       "Section 7.")
    return s

def s14_hallucination():
    s = S()
    TITLE(s, "Hallucination: Detection and Containment",
          "You cannot eliminate hallucination. You can reduce, detect, and contain it under defined conditions.")
    controls = [
        ("Retrieval" + chr(10) + "Grounding", TEAL,
         "Force the model to cite which retrieved chunk supports each claim. "
         "Unsupported claims are flagged. Works for fact-based domains with a document corpus."),
        ("Groundedness" + chr(10) + "Scoring", PURPLE,
         "NLI-based or LLM-as-judge check comparing generated claims against source context. "
         "Score 0-1 per claim. Set domain-specific thresholds (e.g., block below 0.8 for medical/legal)."),
        ("Self-Consistency" + chr(10) + "Checks", AMBER,
         "Sample the same query multiple times. High variance in factual claims is a "
         "hallucination signal. Flag for human review on high-stakes answers."),
        ("Confidence" + chr(10) + "Surfacing", BLUE_STEEL,
         "Prompt the model to explicitly flag low-confidence claims. Verify this behavior "
         "with eval" + chr(8212) + "do not just trust the instruction. Track over time as a metric."),
        ("Tool" + chr(10) + "Verification", GREEN,
         "If a fact is verifiable via a tool call (calculator, database, search), require "
         "the tool call rather than trusting parametric memory. Especially for numbers, dates, and named entities."),
    ]
    for i, (label, color, desc) in enumerate(controls):
        x = 0.5 + i * 2.5
        R(s, x, 1.8, 2.3, 1.0, fill=color, radius=0.1)
        TB(s, x+0.1, 1.85, 2.1, 0.8, label, fs=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        ML(s, x+0.1, 2.7, 2.1, 2.0, [desc], fs=10, color=DARK_TEXT, ls=1.35)
    # Honest claim
    R(s, 0.8, 5.1, 11.7, 1.5, fill=NAVY, radius=0.12)
    TB(s, 1.2, 5.25, 10.8, 0.35, "WHAT WE CAN AND CANNOT CLAIM", fs=14, bold=True, color=AMBER)
    ML(s, 1.2, 5.65, 10.8, 0.85,
       ["CANNOT claim: 'Hallucinations are solved.' 'The model never fabricates.'",
        "CAN claim: 'The system can reduce, detect, and contain hallucination under defined conditions.'",
        "CAN claim: 'Under the evaluated conditions, the groundedness checker catches X% of unsupported claims at threshold Y.'",
        "",
        "This is the bounded-claim pattern from the Evidence Model (Section 11 of the architecture spec). "
        "Every safety claim should be specific, conditioned, and verifiable."], fs=13, color=WHITE, ls=1.35)
    PN(s, 14)
    N(s, "Hallucination is a reliability problem, not a solved problem. Five controls, "
       "ordered from cheapest to most expensive: retrieval grounding, groundedness "
       "scoring, self-consistency checks, confidence surfacing, and tool verification. "
       "The key is the bounded-claim pattern: we cannot claim hallucinations are eliminated, "
       "but we can claim the system reduces, detects, and contains hallucination under "
       "defined, evaluated conditions. This is the evidence model: every safety claim "
       "should be specific, conditioned, and verifiable" + chr(8212) + "not absolute. Source: "
       "ai_trust_safety_architecture.md Section 11.")
    return s

def s15_output_validation():
    s = S()
    TITLE(s, "Output Validation: Schema, Range, Semantics",
          "Valid JSON is not enough. The output must be valid, safe, and consistent with business rules.")
    checks = [
        ("Schema" + chr(10) + "Validation", TEAL,
         "Does the output match the expected structure?",
         ["Tool-call JSON matches the actual tool signature",
          "Required fields present, types correct",
          "Tools: Pydantic, Instructor, Guardrails AI, Outlines"]),
        ("Range" + chr(10) + "Validation", AMBER,
         "Are the values within acceptable bounds?",
         ["Refund amount within policy limits",
          "Date ranges within allowed windows",
          "Numeric values within min/max constraints",
          "String lengths within system capacities"]),
        ("Semantic" + chr(10) + "Validation", PURPLE,
         "Does the output make sense in context?",
         ["Sentiment consistent with task type",
          "No protected-attribute leakage in output",
          "Groundedness: claims supported by context",
          "Business-rule conformance checks"]),
    ]
    for i, (label, color, question, items) in enumerate(checks):
        x = 0.5 + i * 4.2
        R(s, x, 1.8, 3.95, 0.5, fill=color, radius=0.1)
        TB(s, x+0.1, 1.83, 3.75, 0.44, label, fs=15, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        TB(s, x+0.1, 2.35, 3.75, 0.3, question, fs=12, bold=True, color=DARK_TEXT)
        ML(s, x+0.1, 2.65, 3.75, 1.5, items, fs=12, color=DARK_TEXT, ls=1.4)
    # Never execute rule
    R(s, 0.8, 4.8, 11.7, 1.6, fill=NAVY, radius=0.12)
    TB(s, 1.2, 4.95, 10.8, 0.35, "THE CRITICAL RULE", fs=14, bold=True, color=CORAL)
    ML(s, 1.2, 5.35, 10.8, 0.9,
       ["NEVER EXECUTE UNVALIDATED MODEL OUTPUT.",
        "",
        "On validation failure: Block, or Corrective Retry, or Human Escalation" + chr(8212) + "never silent pass-through.",
        "",
        "DocuBot example: Model outputs 'send_email(to=bob@example.com, body=Approved.)'. "
        "Schema check passes. Range check passes. Semantic check: does the email body match the task context? "
        "Does the recipient match the expected distribution list? If not, block and escalate."], fs=13, color=WHITE, ls=1.35)
    PN(s, 15)
    N(s, "Output validation has three layers: schema (structure), range (bounds), and "
       "semantics (meaning). The critical rule: never execute unvalidated model output. "
       "On validation failure, the default is block, corrective retry, or human escalation" + chr(8212) + ""
       "never silent pass-through. The DocuBot example shows semantic validation catching "
       "what schema and range checks miss: the output is perfectly formatted JSON with "
       "valid values, but the recipient is wrong and the body does not match the task "
       "context. Source: ai_trust_safety_architecture.md Section 7.")
    return s

def s16_safe_refusal():
    s = S()
    TITLE(s, "Safe Refusal: Under-Refusal and Over-Refusal Are Both Failures",
          "Refuse the unsafe part as narrowly as possible while preserving legitimate assistance")
    # Spectrum
    R(s, 0.8, 1.8, 11.7, 0.8, fill=TEAL_LIGHT, radius=0.1)
    TB(s, 1.1, 1.85, 11.1, 0.35,
       "UNDER-REFUSAL " + chr(8596) + " CORRECT REFUSAL " + chr(8596) + " OVER-REFUSAL",
       fs=16, bold=True, color=DARK_TEXT, align=PP_ALIGN.CENTER)
    TB(s, 1.1, 2.2, 11.1, 0.3,
       "System complies with harmful request  |  System declines unsafe part, fulfills rest  |  System refuses legitimate query",
       fs=12, color=BLUE_STEEL, align=PP_ALIGN.CENTER)
    # Decision tree
    R(s, 0.8, 2.85, 5.5, 3.8, fill=WHITE, border=GREEN, radius=0.1)
    R(s, 0.8, 2.85, 5.5, 0.5, fill=GREEN, radius=0.08)
    TB(s, 1.1, 2.9, 5.0, 0.4, "REFUSAL DECISION TREE", fs=14, bold=True, color=WHITE)
    ML(s, 1.1, 3.5, 5.0, 3.0,
       ["Request classified as:",
        "",
        "ALLOWED " + chr(8594) + " Process normally",
        "",
        "NEEDS CLARIFICATION " + chr(8594) + " Ask, do not refuse",
        "  (ambiguous/underspecified requests)",
        "",
        "PARTIALLY ALLOWED " + chr(8594) + " Fulfill safe part,",
        "  decline problematic part with brief reason",
        "",
        "REFUSE + SAFE ALTERNATIVE " + chr(8594) + " Decline",
        "  the request but offer a safe path forward",
        "  (e.g., 'I cannot provide that, but I can help",
        "  you understand the policy instead')",
        "",
        "HARD POLICY VIOLATION " + chr(8594) + " Decline,",
        "  no negotiation, log for audit",
        "",
        "ESCALATE " + chr(8594) + " Route to human for review"], fs=12, color=DARK_TEXT, ls=1.3)
    # Over-refusal
    R(s, 7.0, 2.85, 5.8, 3.8, fill=WHITE, border=CORAL, radius=0.1)
    R(s, 7.0, 2.85, 5.8, 0.5, fill=CORAL, radius=0.08)
    TB(s, 7.3, 2.9, 5.2, 0.4, "OVER-REFUSAL: THE OFTEN-IGNORED FAILURE", fs=14, bold=True, color=WHITE)
    ML(s, 7.3, 3.5, 5.2, 3.0,
       ["Over-refusal is also a system failure: an",
        "agent that refuses too much is failing its",
        "purpose.",
        "",
        "Examples of over-refusal on legitimate queries:",
        "  " + chr(8226) + " Medical questions asked by doctors",
        "  " + chr(8226) + " Legal topics asked by lawyers",
        "  " + chr(8226) + " Security research in good faith",
        "  " + chr(8226) + " Creative fiction with dark themes",
        "",
        "Track over-refusal as a first-class metric:",
        "  " + chr(8226) + " Build a 'golden set' of borderline-but-",
        "    legitimate prompts",
        "  " + chr(8226) + " Track refusal rate on this set over time",
        "  " + chr(8226) + " A spike signals over-refusal regression",
        "",
        "Principles:",
        "  " + chr(8226) + " Refuse the narrowest thing possible",
        "  " + chr(8226) + " Avoid moralizing or lecturing",
        "  " + chr(8226) + " Distinguish policy violation from",
        "    capability limitation from ambiguity"], fs=12, color=DARK_TEXT, ls=1.28)
    PN(s, 16)
    N(s, "Safe refusal is a spectrum: under-refusal (complying with harmful requests) and "
       "over-refusal (refusing legitimate queries) are both system failures. The decision "
       "tree distinguishes: allowed, needs clarification, partially allowed, refuse with "
       "safe alternative, hard policy violation, and escalate. Over-refusal is often "
       "ignored but its a first-class safety metric: track refusal rate on a golden set "
       "of borderline-but-legitimate prompts and treat a spike as a regression. The "
       "principles: refuse the narrowest thing possible, avoid moralizing, and distinguish "
       "policy violations from capability limitations. Source: ai_trust_safety_architecture.md "
       "Section 10.")
    return s

def s17_bias_detection():
    s = S()
    TITLE(s, "Bias Detection: Counterfactual Evaluation",
          "Bias is often a distributional property" + chr(8212) + "it requires aggregate evaluation, not single-message classification")
    # Counterfactual method
    R(s, 0.8, 1.8, 5.5, 3.0, fill=WHITE, border=TEAL, radius=0.1)
    R(s, 0.8, 1.8, 5.5, 0.5, fill=TEAL, radius=0.08)
    TB(s, 1.1, 1.85, 5.0, 0.4, "COUNTERFACTUAL TESTING METHOD", fs=14, bold=True, color=WHITE)
    ML(s, 1.1, 2.45, 5.0, 2.2,
       ["1. Take a test input (e.g., employee review).",
        "2. Create a counterfactual pair by changing",
        "   only one sensitive attribute (name, gender,",
        "   ethnicity marker).",
        "3. Run both through the system.",
        "4. Compare outputs on:",
        "   " + chr(8226) + " Refusal rate difference",
        "   " + chr(8226) + " Sentiment difference",
        "   " + chr(8226) + " Recommendation difference",
        "   " + chr(8226) + " Quality difference",
        "   " + chr(8226) + " Output length disparity",
        "5. Measure aggregate divergence across many pairs.",
        "",
        "DocuBot example: Swap 'John Smith' with 'Jane Smith'",
        "in identical performance reviews. Measure whether",
        "compensation recommendations differ systematically."], fs=12, color=DARK_TEXT, ls=1.32)
    # Metrics and monitoring
    R(s, 7.0, 1.8, 5.8, 3.0, fill=WHITE, border=PURPLE, radius=0.1)
    R(s, 7.0, 1.8, 5.8, 0.5, fill=PURPLE, radius=0.08)
    TB(s, 7.3, 1.85, 5.2, 0.4, "AGGREGATE MONITORING APPROACH", fs=14, bold=True, color=WHITE)
    ML(s, 7.3, 2.45, 5.2, 2.2,
       ["Individual-message bias classifiers provide",
        "signals, but bias is best caught statistically",
        "across many interactions.",
        "",
        "Monitoring signals:",
        "  " + chr(8226) + " Refusal rate by demographic group",
        "  " + chr(8226) + " Sentiment variance across groups",
        "  " + chr(8226) + " Recommendation distribution by group",
        "  " + chr(8226) + " Output quality metrics by group",
        "",
        "Key insight: Bias is a distributional property.",
        "You need aggregate evaluation over many samples,",
        "not a single-message pass/fail classifier.",
        "",
        "CI integration: Run counterfactual suite on every",
        "model or prompt change. Drift can occur silently.",
        "Track bias metrics as a time series, not a gate."], fs=12, color=DARK_TEXT, ls=1.32)
    R(s, 0.8, 5.1, 11.7, 1.5, fill=NAVY, radius=0.12)
    TB(s, 1.2, 5.25, 10.8, 0.35, "IMPLEMENTATION STATUS", fs=14, bold=True, color=AMBER)
    ML(s, 1.2, 5.65, 10.8, 0.8,
       ["The architecture specifies a counterfactual test suite (Section 8 of ai_trust_safety_architecture.md).",
        "Current status: PLANNED. The test generator, CI gating, and dashboard panel are designed but not yet built.",
        "What exists: the conceptual framework, test-generation logic, and metric definitions are specified.",
        "Next step: implement counterfactual pair generation and wire into the CI eval suite as a scheduled job."], fs=13, color=WHITE, ls=1.35)
    PN(s, 17)
    N(s, "Bias detection uses counterfactual evaluation: create pairs of inputs differing "
       "only in a sensitive attribute, measure divergence across multiple dimensions. "
       "Bias is a distributional property" + chr(8212) + "it requires aggregate evaluation, not "
       "single-message classification. The monitoring signals include refusal rate by "
       "group, sentiment variance, recommendation distribution, and quality metrics. "
       "Implementation status: PLANNED in our architecture but not yet built. The "
       "counterfactual test suite design exists; the generation and CI integration are "
       "the next engineering steps. Source: ai_trust_safety_architecture.md Section 8.")
    return s

