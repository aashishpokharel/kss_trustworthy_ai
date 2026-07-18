"""
Trustworthy AI Safety Utilities
Content filtering, prompt injection detection, output validation
"""
import re
import hashlib
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ============================================================
# 1. CONTENT FILTERING
# ============================================================

class ContentFilter:
    """
    Filter sensitive content in prompts and outputs.
    
    === USUAL WAY ===
    # No filtering at all - trust user input completely
    
    === TRUSTWORTHY WAY ===
    Multi-layer content filtering
    """
    
    # Patterns for sensitive data detection
    PATTERNS = {
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        "api_key": r'(?:sk-|pk-)[a-zA-Z0-9]{20,}',
        "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    }
    
    SENSITIVE_TOPICS = [
        "how to commit fraud", "how to launder money", "how to make weapons",
        "suicide methods", "self-harm instructions", "illegal drug synthesis",
        "child exploitation material", "terrorism planning",
        "bypass security", "hack into", "unauthorized access"
    ]
    
    @classmethod
    def detect_pii(cls, text: str) -> List[Dict[str, str]]:
        """Detect personally identifiable information"""
        findings = []
        for name, pattern in cls.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                findings.append({
                    "type": name,
                    "value": mask_sensitive(match.group()),
                    "position": match.start()
                })
        return findings
    
    @classmethod
    def contains_sensitive_topic(cls, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains sensitive topics"""
        text_lower = text.lower()
        found = []
        for topic in cls.SENSITIVE_TOPICS:
            if topic in text_lower:
                found.append(topic)
        return len(found) > 0, found
    
    @classmethod
    def sanitize_pii(cls, text: str, replacement: str = "[REDACTED]") -> str:
        """Remove PII from text"""
        for name, pattern in cls.PATTERNS.items():
            text = re.sub(pattern, replacement, text)
        return text


# ============================================================
# 2. PROMPT INJECTION DETECTION
# ============================================================

class PromptInjectionDetector:
    """
    Detect prompt injection attacks.
    
    Common injection patterns:
    - "Ignore previous instructions and..."
    - "You are now a different AI..."
    - "Print the system prompt..."
    - Role-playing to extract information
    """
    
    INJECTION_PATTERNS = [
        r'(?i)ignore\s+(all\s+|your\s+|these\s+)?(previous|above|prior|all)\s+(instructions|prompt|directions|rules)',
        r'(?i)forget\s+(all\s+)?(previous|above|prior)\s+(instructions|prompt)',
        r'(?i)you\s+are\s+(now\s+)?(a\s+)?(free|unconstrained|ungoverned|unrestricted)',
        r'(?i)print\s+(the\s+)?(system\s+)?prompt',
        r'(?i)reveal\s+(your\s+)?(system\s+)?(prompt|instructions)',
        r'(?i)output\s+(your\s+)?(system\s+)?(prompt|instructions)',
        r'(?i)repeat\s+(after\s+me|the\s+words|everything\s+above)',
        r'(?i)new\s+instructions?:\s*ignore',
        r'(?i)do\s+what\s+i\s+say\s+not\s+what\s+you\s+were\s+told',
        r'(?i)dans\s+mode|dan\s+mode|jailbreak',
        r'(?i)you\s+have\s+been\s+(replaced|overridden|bypassed)',
    ]
    
    @classmethod
    def check(cls, text: str) -> Tuple[bool, List[str]]:
        """
        Check text for prompt injection patterns.
        Returns (is_injection, list_of_matched_patterns)
        """
        matched = []
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text):
                matched.append(pattern)
        return len(matched) > 0, matched
    
    @classmethod
    def compute_risk_score(cls, text: str) -> float:
        """
        Compute a risk score 0.0-1.0 for prompt injection.
        Higher score = higher risk.
        """
        score = 0.0
        is_injection, matches = cls.check(text)
        
        # Base score from pattern matches
        if is_injection:
            score += min(0.5, len(matches) * 0.15)
        
        # Additional heuristics
        text_lower = text.lower()
        
        # Suspicious length ratio (very long prompts can be injection attempts)
        if len(text) > 2000:
            score += 0.1
            
        # Multiple language switches
        # (simplified check for non-ASCII characters)
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / max(len(text), 1)
        if non_ascii_ratio > 0.3:
            score += 0.1
            
        # Excessive escaping/encoding
        escape_count = text.count('\\') + text.count('%') + text.count('0x')
        if escape_count > 10:
            score += 0.1
            
        # Suspicious system command patterns
        if re.search(r'(?i)(cmd|powershell|bash|exec|eval|system\(|subprocess)', text):
            score += 0.2
            
        return min(1.0, score)


# ============================================================
# 3. OUTPUT VALIDATION
# ============================================================

@dataclass
class ValidationResult:
    """Result of output validation"""
    passed: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def is_safe(self) -> bool:
        return self.passed and len(self.errors) == 0


class OutputValidator:
    """
    Validate LLM outputs for safety and correctness.
    
    === USUAL WAY ===
    response = openai.ChatCompletion.create(...)
    print(response.choices[0].message.content)
    # No validation at all!
    
    === TRUSTWORTHY WAY ===
    validator = OutputValidator()
    result = validator.validate(response)
    if result.is_safe:
        use_response(response)
    else:
        log_and_reject(result.errors)
    """
    
    HALLUCINATION_INDICATORS = [
        r'(?i)i\s+don\'?t\s+(have\s+)?(access\s+to\s+)?(real\s+)?(time|data)',
        r'(?i)i\s+don\'?t\s+have\s+(enough\s+)?information',
        r'(?i)i\s+(cannot|cannot)\s+(confirm|verify|guarantee)',
        r'(?i)as\s+(an\s+)?(AI|assistant)',
    ]
    
    CONFIDENCE_PATTERNS = {
        "high": [r'(?i)(always|definitely|certainly|absolutely|guaranteed)'],
        "medium": [r'(?i)(likely|probably|may|might|could|typically)'],
        "low": [r'(?i)(maybe|perhaps|possibly|unclear|uncertain|unsure|not sure)'],
    }
    
    @classmethod
    def check_hallucination_risk(cls, text: str) -> float:
        """
        Check if output shows signs of hallucination.
        Returns risk score 0.0-1.0
        """
        matches = 0
        for pattern in cls.HALLUCINATION_INDICATORS:
            if re.search(pattern, text):
                matches += 1
        return min(1.0, matches * 0.25)
    
    @classmethod
    def validate_json_output(cls, text: str, expected_schema: Optional[Dict] = None) -> ValidationResult:
        """Validate that output is valid JSON and matches expected schema"""
        warnings = []
        errors = []
        
        try:
            # Try to find JSON in the output
            json_match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
            if not json_match:
                errors.append("No JSON structure found in output")
                return ValidationResult(passed=False, errors=errors)
            
            data = json.loads(json_match.group())
            
            if expected_schema:
                for key, expected_type in expected_schema.items():
                    if key not in data:
                        warnings.append(f"Missing expected key: {key}")
                    elif not isinstance(data[key], expected_type):
                        errors.append(
                            f"Key '{key}' expected {expected_type.__name__}, "
                            f"got {type(data[key]).__name__}"
                        )
            
            return ValidationResult(
                passed=len(errors) == 0,
                warnings=warnings,
                errors=errors
            )
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
            return ValidationResult(passed=False, errors=errors)
    
    @classmethod
    def check_confidence(cls, text: str) -> Dict[str, float]:
        """
        Analyze confidence level of response.
        Returns dict of confidence categories and their presence count
        """
        result = {"high": 0, "medium": 0, "low": 0}
        for level, patterns in cls.CONFIDENCE_PATTERNS.items():
            count = sum(1 for p in patterns if re.search(p, text))
            result[level] = count
        return result


# ============================================================
# 4. AUDIT LOGGING
# ============================================================

@dataclass
class AuditEntry:
    """Single audit log entry"""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    user_id: str = ""
    request_hash: str = ""
    prompt_preview: str = ""
    response_preview: str = ""
    risk_score: float = 0.0
    validation_passed: bool = True
    issues: List[str] = field(default_factory=list)
    cost: float = 0.0
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "request_hash": self.request_hash,
            "prompt_length": len(self.prompt_preview),
            "response_length": len(self.response_preview),
            "risk_score": self.risk_score,
            "validation_passed": self.validation_passed,
            "issues": self.issues,
            "cost": self.cost,
            "latency_ms": self.latency_ms,
        }


class AuditLogger:
    """
    Immutable audit logging for AI interactions.
    
    === USUAL WAY ===
    # No logging at all - can't debug issues or detect abuse
    
    === TRUSTWORTHY WAY ===
    Log every interaction with full traceability
    """
    
    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._read_only = False
    
    def log(self, entry: AuditEntry) -> None:
        """Log an audit entry (append-only)"""
        self._entries.append(entry)
    
    def get_recent(self, count: int = 10) -> List[AuditEntry]:
        """Get most recent log entries"""
        return self._entries[-count:]
    
    def export_to_json(self) -> str:
        """Export all entries as JSON for analysis"""
        return json.dumps(
            [e.to_dict() for e in self._entries],
            indent=2
        )


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def mask_sensitive(value: str) -> str:
    """Mask sensitive data showing only last 4 chars"""
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]


def compute_hash(text: str) -> str:
    """Compute hash of text for audit logging"""
    return hashlib.sha256(text.encode()).hexdigest()[:16]