"""
Sensitive Topic Classifier — keyword + pattern classification (Section 6).

Categories with pre-defined routing:
- weapons/CBRN       → hard_block
- cyberweapons/malware → hard_block
- self-harm/crisis   → safe_response (routed to crisis resources)
- extremism           → hard_block
- CSAE                → hard_block
- fraud               → hard_block
- illicit substances  → hard_block

Self-harm/crisis is special: it must route to a safe-response path
with resources, not the general refusal path (Section 6 requirement).
"""

from __future__ import annotations

import re
from typing import ClassVar

from trust_safety.guardrails.input.models import (
    RouteAction,
    SensitiveCategory,
    SensitiveTopicFinding,
    SensitiveTopicResult,
)

# ------------------------------------------------------------------
# Category definitions
# ------------------------------------------------------------------

CATEGORY_CONFIG: dict[SensitiveCategory, dict] = {
    "weapons_cbrn": {
        "route": "hard_block",
        "terms": [
            "how to make a bomb", "synthesize explosives", "build a nuclear",
            "chemical weapon", "biological weapon", "ricin", "anthrax",
            "mustard gas", "sarin", "cbrn", "dirty bomb",
            "how to manufacture", "weaponize", "detonator",
        ],
        "patterns": [
            r'(?i)\b(make|build|construct|create)\b.*\b(bomb|explosive|weapon|detonator)\b',
            r'(?i)\b(synthesize|manufacture|produce)\b.*\b(explosive|chemical\s+agent|toxin)\b',
        ],
    },
    "cyberweapons_malware": {
        "route": "hard_block",
        "terms": [
            "write ransomware", "create malware", "build a botnet",
            "ddos attack script", "how to hack into", "exploit zero-day",
            "phishing kit", "keylogger", "rootkit", "trojan",
            "sql injection attack", "xss payload", "remote access trojan",
            "credential harvester", "ransomware builder",
        ],
        "patterns": [
            r'(?i)\b(write|create|build|develop)\b.*\b(ransomware|malware|virus|worm|trojan|botnet)\b',
            r'(?i)\b(exploit|hack|breach|infiltrate)\b.*\b(system|network|server|database)\b',
        ],
    },
    "self_harm_crisis": {
        "route": "safe_response",
        "terms": [
            "want to kill myself", "end my life", "suicide method",
            "how to commit suicide", "i want to die", "no reason to live",
            "self harm", "cutting myself", "overdose on",
            "jump off a bridge", "hang myself",
        ],
        "patterns": [
            r'(?i)\b(i\s+(want|need|plan|am\s+going)\s+to\s+(die|kill\s+myself|end\s+my\s+life|commit\s+suicide))\b',
            r'(?i)\b(suicide|self[\s-]?harm|self[\s-]?injury)\b.*\b(how|method|way|best)\b',
        ],
    },
    "extremism": {
        "route": "hard_block",
        "terms": [
            "terrorist attack", "jihad", "white supremacy",
            "hate crime", "ethnic cleansing", "genocide",
            "radicalization", "extremist", "lone wolf attack",
            "mass shooting plan", "incel violence",
        ],
        "patterns": [
            r'(?i)\b(terroris[mt]|extremis[mt]|radicali[sz])\b',
            r'(?i)\b(plan|prepare|organize)\b.*\b(attack|bombing|shooting)\b',
        ],
    },
    "csae": {
        "route": "hard_block",
        "terms": [
            "child pornography", "cp ", "lolita", "pedophile",
            "underage", "child abuse material", "jailbait",
            "preteen", "child model nude",
        ],
        "patterns": [
            r'(?i)\b(child|minor|underage|teen)\b.*\b(sexual|nude|naked|explicit|porn)\b',
            r'(?i)\b(pedo|preteen|jailbait|lolita)\b',
        ],
    },
    "fraud": {
        "route": "hard_block",
        "terms": [
            "how to launder money", "credit card fraud", "identity theft",
            "ponzi scheme", "pyramid scheme", "tax evasion method",
            "fake id template", "counterfeit money", "phishing email template",
            "social engineering attack",
        ],
        "patterns": [
            r'(?i)\b(launder|fraud|scam|phish|counterfeit|fake)\b.*\b(money|credit|identity|id|passport)\b',
            r'(?i)\b(how\s+to|method|technique)\b.*\b(evade|avoid|bypass)\b.*\b(tax|law|regulation)\b',
        ],
    },
    "illicit_substances": {
        "route": "hard_block",
        "terms": [
            "how to make meth", "synthesize lsd", "cocaine production",
            "heroin recipe", "fentanyl synthesis", "mdma manufacture",
            "drug trafficking", "darknet market", "methamphetamine",
            "synthesize meth", "how to synthesize",
        ],
        "patterns": [
            r'(?i)\b(synthesize|manufacture|produce|cook)\b.*\b(meth|methamphetamine|cocaine|heroin|lsd|mdma|fentanyl)\b',
            r'(?i)\b(how\s+to|recipe|method)\b.*\b(make|produce|synthesize)\b.*\b(drug|narcotic|meth)\b',
        ],
    },
}

# ------------------------------------------------------------------
# Safe response for crisis content
# ------------------------------------------------------------------

CRISIS_SAFE_RESPONSE = (
    "I recognize this may be a difficult moment. If you're experiencing "
    "a mental health crisis or having thoughts of self-harm, please reach "
    "out to a professional who can help:\n\n"
    "• 988 Suicide & Crisis Lifeline (US): Call or text 988\n"
    "• Crisis Text Line: Text HOME to 741741\n"
    "• Samaritans (UK): Call 116 123\n"
    "• Lifeline (AU): Call 13 11 14\n\n"
    "You are not alone, and there are people who want to help."
)


# ------------------------------------------------------------------
# SensitiveTopicClassifier
# ------------------------------------------------------------------

class SensitiveTopicClassifier:
    """Keyword + pattern classifier for sensitive content.

    Usage::

        classifier = SensitiveTopicClassifier()
        result = classifier.classify(user_text)
        if result.topics_detected:
            for finding in result.findings:
                action = finding.route_action  # hard_block / safe_response / escalate
    """

    # Compiled regex patterns per category (built once at class level)
    _compiled_patterns: ClassVar[dict[SensitiveCategory, list[re.Pattern]]] = {}

    def __init__(self) -> None:
        if not SensitiveTopicClassifier._compiled_patterns:
            self._build_patterns()

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify(self, text: str) -> SensitiveTopicResult:
        """Classify *text* against all sensitive topic categories.

        Returns a SensitiveTopicResult with findings and the strictest
        route action across all matches.
        """
        if not text or not text.strip():
            return SensitiveTopicResult(topics_detected=False)

        text_lower = text.lower()
        findings: list[SensitiveTopicFinding] = []

        for category, config in CATEGORY_CONFIG.items():
            matched_terms: list[str] = []

            # Keyword matching
            for term in config["terms"]:
                if term in text_lower:
                    matched_terms.append(term)

            # Pattern matching
            for pattern in self._compiled_patterns.get(category, []):
                for match in pattern.finditer(text):
                    matched_terms.append(match.group()[:80])

            if matched_terms:
                # Deduplicate terms
                unique_terms = list(set(matched_terms))
                confidence = min(1.0, 0.5 + len(unique_terms) * 0.15)

                route: RouteAction = config["route"]  # type: ignore[assignment]

                findings.append(SensitiveTopicFinding(
                    category=category,
                    confidence=round(confidence, 2),
                    matched_terms=unique_terms[:10],  # Cap at 10
                    route_action=route,
                ))

        # Determine strictest action
        action_order: dict[RouteAction, int] = {
            "hard_block": 2,
            "escalate": 1,
            "safe_response": 0,
        }
        strictest: RouteAction = "safe_response"
        if findings:
            strictest = max(
                findings, key=lambda f: action_order[f.route_action]
            ).route_action

        return SensitiveTopicResult(
            topics_detected=len(findings) > 0,
            findings=findings,
            strictest_action=strictest,
        )

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    @staticmethod
    def route_action(category: SensitiveCategory) -> RouteAction:
        """Return the routing action for a given category."""
        config = CATEGORY_CONFIG.get(category)
        if config:
            return config["route"]  # type: ignore[return-value]
        return "hard_block"

    @staticmethod
    def safe_response_for(category: str) -> str:
        """Return the appropriate safe response template."""
        if category == "self_harm_crisis":
            return CRISIS_SAFE_RESPONSE
        return "I cannot assist with that request."

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @classmethod
    def _build_patterns(cls) -> None:
        """Compile all regex patterns once."""
        for category, config in CATEGORY_CONFIG.items():
            cls._compiled_patterns[category] = [
                re.compile(p) for p in config.get("patterns", [])
            ]
