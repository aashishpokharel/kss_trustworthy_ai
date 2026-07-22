
# ══════════════════════════════════════════════════════════════════════
# Part G: Closing (slides 30-31)
# ══════════════════════════════════════════════════════════════════════

def s30_discussion():
    s = S()
    R(s, 0, 0, 13.333, 7.5, fill=NAVY)
    R(s, 0.8, 2.0, 0.08, 2.5, fill=TEAL)
    TB(s, 1.3, 2.0, 11.0, 0.5, "DISCUSSION", fs=16, color=TEAL, bold=True)
    TB(s, 1.3, 2.55, 11.0, 1.4,
       "You have seen the full architecture." + chr(10) + "Where in your own systems would you" + chr(10) + "place your first additional control" + chr(10) + "" + chr(8212) + " and how would you verify it works?",
       fs=30, bold=True, color=WHITE, line_spacing=1.25)
    TB(s, 1.3, 4.4, 11.0, 0.7,
       "(The question is deliberately scoped to one control with one verification method." + chr(10) + ""
       "Engineering trustworthy AI is incremental. Pick one layer. Build the evidence.)",
       fs=15, color=RGBColor(0xAA, 0xB5, 0xC5))
    # Reference architecture layers
    layers = ["Gateway" + chr(10) + "Auth", "Input" + chr(10) + "Guardrails", "Orchestrator",
              "LLM" + chr(10) + "Core", "Output" + chr(10) + "Guardrails", "Action" + chr(10) + "Layer", "Governance" + chr(10) + "Plane"]
    lcolors = [NAVY, PURPLE, AMBER, BLUE_STEEL, GREEN, CORAL, TEAL]
    for i, (label, color) in enumerate(zip(layers, lcolors)):
        x = 1.3 + i * 1.7
        R(s, x, 5.4, 1.5, 0.7, fill=RGBColor(0x2D, 0x3A, 0x55), border=color, radius=0.08)
        TB(s, x+0.05, 5.43, 1.4, 0.65, label, fs=10, color=RGBColor(0xCC, 0xD5, 0xE0), align=PP_ALIGN.CENTER)
    TB(s, 1.3, 6.5, 11.0, 0.4,
       "Thank you. Questions, challenges, and pushback welcome.",
       fs=14, color=MID_GRAY)
    N(s, "This is the closing discussion slide. The question is deliberately scoped: "
       "'where would you place your first additional control and how would you verify it "
       "works?' It is not 'tell me everything you would change'" + chr(8212) + "it is an engineering "
       "question that asks the audience to apply the Capability-Failure-Control-Evidence "
       "chain to their own systems. The seven architecture layers are shown as reference. "
       "Give people a moment to think, then open the floor. If nobody volunteers, offer "
       "your own answer first: 'For DocuBot, I would add groundedness scoring before the "
       "output guardrails, and I would verify it with a known-answer test set of 50 "
       "contract-analysis queries with verified ground truth.' This models the kind of "
       "answer the question is looking for.")
    return s

def s31_resources():
    s = S()
    TITLE(s, "References and Further Reading",
          "Primary sources and key references cited throughout this presentation")
    refs = [
        ("NIST AI Risk Management Framework (AI RMF 1.0) and Generative AI Profile (NIST AI 600-1)",
         "The four-function core (Govern/Map/Measure/Manage) and LLM/agentic-specific risk guidance. nist.gov/itl/ai-risk-management-framework"),
        ("Christoph Molnar " + chr(8212) + " Interpretable Machine Learning",
         "Standard reference for XAI mechanics (LIME, SHAP, permutation importance, counterfactual explanations). Free online: christophm.github.io/interpretable-ml-book"),
        ("Samek, Montavon, Vedaldi, Hansen, Muller (eds.) " + chr(8212) + " Explainable AI: Interpreting, Explaining and Visualizing Deep Learning",
         "Deeper technical/academic grounding on XAI methods specifically for deep learning. Springer LNCS vol. 11700, 2019."),
        ("EU AI Act (Regulation 2024/1689) " + chr(8212) + " Official Text",
         "Binding EU law with four risk tiers. Most rules effective August 2026. artificialintelligenceact.eu"),
        ("Anthropic " + chr(8212) + " Claude's Constitution (Jan 2026)",
         "Priority hierarchy: safety > ethics > compliance > helpfulness. anthropic.com/news/claude-constitution"),
        ("Anthropic " + chr(8212) + " Responsible Scaling Policy (current version)",
         "Tiered risk framework gating deployment behind proportional security requirements. anthropic.com/responsible-scaling-policy"),
        ("Anthropic " + chr(8212) + " Alignment Science (agentic misalignment, alignment faking, auditing research)",
         "alignment.anthropic.com / anthropic.com/research/team/alignment"),
        ("Microsoft Presidio",
         "De facto open-source standard for PII detection: NER + regex + checksum recognizers. microsoft.github.io/presidio/"),
        ("OWASP Top 10 for LLM Applications",
         "Industry-standard taxonomy of LLM-specific vulnerabilities. owasp.org/www-project-top-10-for-llm-applications/"),
        ("Dwork and Roth " + chr(8212) + " The Algorithmic Foundations of Differential Privacy",
         "Foundational text on formal privacy guarantees. Foundations and Trends in Theoretical Computer Science, 2014."),
    ]
    for i, (title, desc) in enumerate(refs):
        y = 1.65 + i * 0.54
        TB(s, 0.8, y, 11.7, 0.22, title, fs=12, bold=True, color=DARK_TEXT)
        TB(s, 0.8, y+0.22, 11.7, 0.22, desc, fs=10, color=BLUE_STEEL)
    TB(s, 0.8, 7.05, 11.7, 0.3,
       "Designed for screenshotting/copying by attendees. All sources publicly available.",
       fs=10, color=MID_GRAY)
    PN(s, 31)
    N(s, "Reference slide for screenshotting. All primary sources cited in the presentation "
       "are listed in one place with full citations and URLs where available. Key calls: "
       "NIST AI RMF for the framework, Molnar for XAI mechanics, Samek et al. for deep "
       "learning XAI, EU AI Act for regulatory obligations, Anthropic's Constitution and "
       "RSP for the alignment reference model, Presidio for PII detection, and OWASP for "
       "LLM vulnerability taxonomy.")
    return s

# ══════════════════════════════════════════════════════════════════════
# BUILD SEQUENCE
# ══════════════════════════════════════════════════════════════════════

print("Building slides v2...")

# Part 1: Foundations (4 slides)
s01_title()           # 1
s02_agenda()          # 2
s03_thesis()          # 3
s04_docubot()         # 4

# Part 2: Failure and Threat Model (3 slides)
s05_failure_taxonomy()         # 5
s06_architecture_threat_map()  # 6
s07_failure_control_matrix()   # 7

# Part 3: Explainability (1 slide)
s08_explainability_limits()    # 8

# Part 4: Input Safety (4 slides)
s09_input_guardrails()         # 9
s10_prompt_injection()         # 10
s11_pii_handling()             # 11
s12_sensitive_beyond_pii()     # 12

# Part 5: Model and Output Safety (5 slides)
s13_llm_untrusted()            # 13
s14_hallucination()            # 14
s15_output_validation()        # 15
s16_safe_refusal()             # 16
s17_bias_detection()           # 17

# Part 6: Alignment and Autonomy (3 slides)
s18_alignment()                # 18
s19_anthropic_reference()      # 19
s20_autonomy()                 # 20

# Part 7: Vulnerability Testing (2 slides)
s21_red_teaming()              # 21
s22_data_poisoning()           # 22

# Part 8: Governance and Evidence (2 slides)
s23_governance()               # 23
s24_evidence_model()           # 24

# Part 9: Provider Abstraction (1 slide)
s25_provider_abstraction()     # 25

# Part 10: Codebase Mapping (3 slides)
s26_codebase_matrix()          # 26
s27_what_we_built()            # 27
s28_honesty()                  # 28

# Part 11: Closing (3 slides)
s29_integrated_walkthrough()   # 29
s30_discussion()               # 30
s31_resources()                # 31

output = "Trustworthy_AI_KSS_v2.pptx"
prs.save(output)
print(f"Done! Saved to {output}")
print(f"Total slides: {len(prs.slides)}")

