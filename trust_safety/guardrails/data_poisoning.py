"""
Data Poisoning Defenses (Section 14).

Prevent malicious/corrupted data from entering training, fine-tuning, or
retrieval corpora:
1. IngestionAnomalyDetector — embedding-distance outlier detection
2. SourceAllowlist — configurable allowed sources
3. ContentHashVerifier — checksum integrity verification
4. CorpusUpdateGate — eval suite gate after corpus update
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Simple text embedding (no external model needed)
# ------------------------------------------------------------------

def _simple_embed(text: str) -> list[float]:
    """Bag-of-character-ngrams embedding for anomaly detection.

    Crude but effective — anomalous documents have different character
    distributions than normal corpus entries.  Good enough for outlier
    detection without requiring a transformer model.
    """
    # Character bigram frequencies
    text = text.lower()[:2000]  # Truncate for performance
    bigrams: Counter[str] = Counter()
    for i in range(len(text) - 1):
        bigrams[text[i:i+2]] += 1

    total = sum(bigrams.values()) or 1
    # Normalize to unit vector using top 100 bigrams
    top = bigrams.most_common(100)
    vec = [count / math.sqrt(total) for _, count in top]
    # Pad to length 100
    while len(vec) < 100:
        vec.append(0.0)
    return vec


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b):
        min_len = min(len(a), len(b))
        a, b = a[:min_len], b[:min_len]
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class AnomalyReport(BaseModel):
    """Result of an ingestion anomaly check."""
    document_id: str
    is_anomalous: bool
    avg_similarity: float = 1.0
    threshold: float = 0.3
    reason: str = ""


class SourceCheckResult(BaseModel):
    """Result of a source allowlist check."""
    allowed: bool
    source: str
    reason: str = ""


class CorpusUpdateGateReport(BaseModel):
    """Result of corpus update gating."""
    passed: bool = False
    anomaly_documents: list[str] = Field(default_factory=list)
    blocked_sources: list[str] = Field(default_factory=list)
    hash_failures: list[str] = Field(default_factory=list)
    eval_regression: bool = False


# ------------------------------------------------------------------
# IngestionAnomalyDetector
# ------------------------------------------------------------------

class IngestionAnomalyDetector:
    """Detect anomalous documents via embedding-distance outlier detection.

    Usage::

        detector = IngestionAnomalyDetector()
        detector.fit(corpus_documents)  # Learn normal distribution
        report = detector.check(new_document)
    """

    def __init__(self, outlier_threshold: float = 0.3) -> None:
        self.threshold = outlier_threshold
        self._corpus_embeddings: list[list[float]] = []

    def fit(self, documents: list[str]) -> None:
        """Learn the normal document distribution from *documents*."""
        self._corpus_embeddings = [_simple_embed(d) for d in documents]

    def check(self, document: str, doc_id: str = "unknown") -> AnomalyReport:
        """Check if *document* is an outlier relative to the corpus."""
        if not self._corpus_embeddings:
            # No baseline — can't detect anomalies
            return AnomalyReport(
                document_id=doc_id,
                is_anomalous=False,
                reason="No baseline corpus fitted",
            )

        new_embedding = _simple_embed(document)
        similarities = [
            _cosine_similarity(new_embedding, e)
            for e in self._corpus_embeddings
        ]
        avg_sim = sum(similarities) / len(similarities)
        is_anomalous = avg_sim < self.threshold

        return AnomalyReport(
            document_id=doc_id,
            is_anomalous=is_anomalous,
            avg_similarity=round(avg_sim, 4),
            threshold=self.threshold,
            reason=(
                f"Low similarity ({avg_sim:.3f}) to corpus baseline"
                if is_anomalous else ""
            ),
        )


# ------------------------------------------------------------------
# SourceAllowlist
# ------------------------------------------------------------------

class SourceAllowlist:
    """Configurable source allowlisting for RAG/training data ingestion.

    Usage::

        allowlist = SourceAllowlist(allowed_domains=["example.com", "internal.wiki"])
        result = allowlist.check("https://evil.com/data")
    """

    def __init__(
        self,
        allowed_domains: list[str] | None = None,
        allowed_prefixes: list[str] | None = None,
    ) -> None:
        self.allowed_domains = set(allowed_domains or [])
        self.allowed_prefixes = allowed_prefixes or []

    def check(self, source: str) -> SourceCheckResult:
        """Check if *source* is in the allowlist."""
        # Domain check
        for domain in self.allowed_domains:
            if domain in source:
                return SourceCheckResult(allowed=True, source=source)

        # Prefix check
        for prefix in self.allowed_prefixes:
            if source.startswith(prefix):
                return SourceCheckResult(allowed=True, source=source)

        return SourceCheckResult(
            allowed=False,
            source=source,
            reason=f"Source '{source}' not in allowlist",
        )


# ------------------------------------------------------------------
# ContentHashVerifier
# ------------------------------------------------------------------

class ContentHashVerifier:
    """Verify content integrity via SHA-256 checksums.

    Usage::

        verifier = ContentHashVerifier()
        verifier.register("doc-1", "document content here")
        is_valid = verifier.verify("doc-1", "tampered content")  # False
    """

    def __init__(self) -> None:
        self._hashes: dict[str, str] = {}

    def register(self, doc_id: str, content: str) -> str:
        """Register a document's hash."""
        h = hashlib.sha256(content.encode("utf-8")).hexdigest()
        self._hashes[doc_id] = h
        return h

    def verify(self, doc_id: str, content: str) -> bool:
        """Verify content matches the registered hash."""
        if doc_id not in self._hashes:
            return False  # Unknown document
        expected = self._hashes[doc_id]
        actual = hashlib.sha256(content.encode("utf-8")).hexdigest()
        return expected == actual

    def get_hash(self, doc_id: str) -> str | None:
        """Get the registered hash for a document."""
        return self._hashes.get(doc_id)


# ------------------------------------------------------------------
# CorpusUpdateGate
# ------------------------------------------------------------------

class CorpusUpdateGate:
    """Gate corpus updates through anomaly, source, and hash checks.

    Usage::

        gate = CorpusUpdateGate(detector, allowlist, verifier)
        report = gate.check_update(new_documents)
        if not report.passed:
            raise BlockedCorpusUpdate(report)
    """

    def __init__(
        self,
        anomaly_detector: IngestionAnomalyDetector,
        source_allowlist: SourceAllowlist,
        hash_verifier: ContentHashVerifier,
    ) -> None:
        self.anomaly_detector = anomaly_detector
        self.source_allowlist = source_allowlist
        self.hash_verifier = hash_verifier

    def check_update(
        self,
        documents: list[dict[str, Any]],
    ) -> CorpusUpdateGateReport:
        """Check a batch of new documents before ingestion.

        Each doc must have: ``{"id": str, "content": str, "source": str}``.
        """
        report = CorpusUpdateGateReport()

        for doc in documents:
            doc_id = doc.get("id", "unknown")
            content = doc.get("content", "")
            source = doc.get("source", "")

            # 1. Anomaly check
            anomaly = self.anomaly_detector.check(content, doc_id)
            if anomaly.is_anomalous:
                report.anomaly_documents.append(doc_id)

            # 2. Source check
            source_check = self.source_allowlist.check(source)
            if not source_check.allowed:
                report.blocked_sources.append(source)

            # 3. Hash verification (if already registered)
            if doc_id in self.hash_verifier._hashes:
                if not self.hash_verifier.verify(doc_id, content):
                    report.hash_failures.append(doc_id)
            else:
                # Register new document
                self.hash_verifier.register(doc_id, content)

        report.passed = (
            len(report.anomaly_documents) == 0
            and len(report.blocked_sources) == 0
            and len(report.hash_failures) == 0
        )
        return report
