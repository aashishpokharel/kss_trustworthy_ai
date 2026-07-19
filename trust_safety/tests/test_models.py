"""Tests for DataTier, TrustLevelEnum, ProvenanceTag, ContextBlock, ContextAssembler."""

import pytest

from trust_safety.models.base import DataTier, TrustLevelEnum
from trust_safety.models.context import (
    ContextAssembler,
    ContextBlock,
    ProvenanceTag,
)


class TestDataTier:
    """DataTier enum — Section 4 classification tiers."""

    def test_values(self):
        """All four tiers must exist."""
        assert DataTier.PUBLIC.value == "public"
        assert DataTier.INTERNAL.value == "internal"
        assert DataTier.CONFIDENTIAL.value == "confidential"
        assert DataTier.RESTRICTED.value == "restricted"

    def test_value_access(self):
        """DataTier values are accessible via .value."""
        assert DataTier.PUBLIC.value == "public"
        assert DataTier.PUBLIC == "public"  # str Enum equality


class TestTrustLevelEnum:
    """TrustLevelEnum — how trusted is a piece of content."""

    def test_values(self):
        """All five levels must exist, from least to most trusted."""
        assert TrustLevelEnum.UNTRUSTED.value == "untrusted"
        assert TrustLevelEnum.LOW.value == "low"
        assert TrustLevelEnum.MEDIUM.value == "medium"
        assert TrustLevelEnum.HIGH.value == "high"
        assert TrustLevelEnum.CRITICAL.value == "critical"


class TestProvenanceTag:
    """ProvenanceTag — metadata about where content came from."""

    def test_minimal_construction(self):
        """Only required fields are source_id, source_type, origin."""
        tag = ProvenanceTag(
            source_id="abc", source_type="user_input", origin="human_input"
        )
        assert tag.source_id == "abc"
        assert tag.trust_score == 0.0  # fail-closed default

    def test_full_construction(self):
        """All fields settable."""
        tag = ProvenanceTag(
            source_id="doc-1",
            source_type="rag_chunk",
            trust_score=0.9,
            origin="internal_db",
            data_tier=DataTier.INTERNAL,
            canary_token="canary-abc",
        )
        assert tag.trust_score == 0.9
        assert tag.canary_token == "canary-abc"
        assert tag.data_tier == DataTier.INTERNAL

    def test_trust_score_clamped(self):
        """trust_score must be 0.0-1.0."""
        with pytest.raises(ValueError):
            ProvenanceTag(
                source_id="x", source_type="test", origin="test", trust_score=1.5
            )
        with pytest.raises(ValueError):
            ProvenanceTag(
                source_id="x", source_type="test", origin="test", trust_score=-0.1
            )

    def test_default_data_tier(self):
        """Unspecified data_tier defaults to INTERNAL."""
        tag = ProvenanceTag(
            source_id="x", source_type="test", origin="test"
        )
        assert tag.data_tier == DataTier.INTERNAL


class TestContextBlock:
    """ContextBlock — the core unit of prompt assembly."""

    def test_is_trusted_high(self):
        """HIGH trust → is_trusted() returns True."""
        block = ContextBlock(
            content="x", source="test", trust_level=TrustLevelEnum.HIGH
        )
        assert block.is_trusted()

    def test_is_trusted_critical(self):
        """CRITICAL trust → is_trusted() returns True."""
        block = ContextBlock(
            content="x", source="test", trust_level=TrustLevelEnum.CRITICAL
        )
        assert block.is_trusted()

    def test_is_trusted_untrusted(self):
        """UNTRUSTED → is_trusted() returns False."""
        block = ContextBlock(
            content="x", source="test", trust_level=TrustLevelEnum.UNTRUSTED
        )
        assert not block.is_trusted()

    def test_is_trusted_low(self):
        """LOW trust → is_trusted() returns False (conservative)."""
        block = ContextBlock(
            content="x", source="test", trust_level=TrustLevelEnum.LOW
        )
        assert not block.is_trusted()

    def test_is_trusted_medium(self):
        """MEDIUM trust → is_trusted() returns False (conservative)."""
        block = ContextBlock(
            content="x", source="test", trust_level=TrustLevelEnum.MEDIUM
        )
        assert not block.is_trusted()

    def test_to_prompt_block_trusted(self):
        """Trusted blocks get <trusted> wrapper."""
        block = ContextBlock(
            content="System instruction",
            source="system",
            trust_level=TrustLevelEnum.HIGH,
        )
        result = block.to_prompt_block()
        assert "<trusted>" in result
        assert "System instruction" in result

    def test_to_prompt_block_untrusted(self):
        """Untrusted blocks get <untrusted> wrapper with source attr."""
        block = ContextBlock(
            content="User input here",
            source="chat-window",
            trust_level=TrustLevelEnum.UNTRUSTED,
        )
        result = block.to_prompt_block()
        assert "<untrusted" in result
        assert 'source="chat-window"' in result
        assert "User input here" in result

    def test_to_prompt_block_untrusted_with_provenance(self):
        """Untrusted blocks include data_tier when provenance is present."""
        prov = ProvenanceTag(
            source_id="x", source_type="user_input",
            origin="test", data_tier=DataTier.CONFIDENTIAL,
        )
        block = ContextBlock(
            content="secret", source="db", trust_level=TrustLevelEnum.UNTRUSTED,
            provenance=prov,
        )
        result = block.to_prompt_block()
        assert 'data_tier="confidential"' in result

    def test_to_prompt_block_custom_template(self):
        """Custom template replaces the default wrapper."""
        block = ContextBlock(
            content="hello", source="test", trust_level=TrustLevelEnum.HIGH,
        )
        result = block.to_prompt_block(template="[CUSTOM]{content}[/CUSTOM]")
        assert result == "[CUSTOM]hello[/CUSTOM]"

    def test_context_id_auto_generated(self):
        """context_id is auto-generated as a UUID string."""
        block = ContextBlock(content="x", source="test")
        assert block.context_id
        assert len(block.context_id) == 36  # UUID length

    def test_default_trust_level_is_untrusted(self):
        """Fail-closed: unspecified trust → UNTRUSTED."""
        block = ContextBlock(content="x", source="test")
        assert block.trust_level == TrustLevelEnum.UNTRUSTED


class TestContextAssembler:
    """ContextAssembler — safe prompt construction with sandwiching."""

    def test_empty_assemble(self):
        """An empty assembler returns an empty string."""
        asm = ContextAssembler()
        assert asm.assemble() == ""

    def test_system_prompt_only(self):
        """System prompt is prepended even with no blocks."""
        asm = ContextAssembler(system_prompt="Be helpful.")
        result = asm.assemble()
        assert "Be helpful." in result

    def test_sandwiching_untrusted(self):
        """Untrusted blocks are sandwich-wrapped with re-assertion."""
        block = ContextBlock(
            content="UNTRUSTED DATA", source="web",
            trust_level=TrustLevelEnum.UNTRUSTED,
        )
        asm = ContextAssembler()
        asm.add_block(block)
        result = asm.assemble()
        assert "RE-ASSERTION" in result
        assert "UNTRUSTED DATA" in result
        assert "END UNTRUSTED CONTENT" in result
        # Re-assertion must appear BEFORE the untrusted content
        reassert_pos = result.index("RE-ASSERTION")
        data_pos = result.index("UNTRUSTED DATA")
        end_pos = result.index("END UNTRUSTED CONTENT")
        assert reassert_pos < data_pos < end_pos

    def test_trusted_not_sandwiched(self):
        """Trusted blocks are NOT sandwiched."""
        block = ContextBlock(
            content="TRUSTED", source="system",
            trust_level=TrustLevelEnum.HIGH,
        )
        asm = ContextAssembler()
        asm.add_block(block)
        result = asm.assemble()
        assert "RE-ASSERTION" not in result
        assert "<trusted>" in result

    def test_filter_by_tier_public(self):
        """filter_by_tier(PUBLIC) returns all blocks."""
        prov_public = ProvenanceTag(
            source_id="a", source_type="test", origin="test",
            data_tier=DataTier.PUBLIC,
        )
        prov_conf = ProvenanceTag(
            source_id="b", source_type="test", origin="test",
            data_tier=DataTier.CONFIDENTIAL,
        )
        asm = ContextAssembler()
        asm.add_block(ContextBlock(content="a", source="t", provenance=prov_public))
        asm.add_block(ContextBlock(content="b", source="t", provenance=prov_conf))
        filtered = asm.filter_by_tier(DataTier.PUBLIC)
        assert len(filtered) == 2

    def test_filter_by_tier_confidential(self):
        """filter_by_tier(CONFIDENTIAL) drops PUBLIC and INTERNAL."""
        prov_public = ProvenanceTag(
            source_id="a", source_type="test", origin="test",
            data_tier=DataTier.PUBLIC,
        )
        prov_conf = ProvenanceTag(
            source_id="b", source_type="test", origin="test",
            data_tier=DataTier.CONFIDENTIAL,
        )
        asm = ContextAssembler()
        asm.add_block(ContextBlock(content="a", source="t", provenance=prov_public))
        asm.add_block(ContextBlock(content="b", source="t", provenance=prov_conf))
        filtered = asm.filter_by_tier(DataTier.CONFIDENTIAL)
        assert len(filtered) == 1
        assert filtered[0].content == "b"

    def test_add_block(self):
        """add_block appends to the assembler."""
        asm = ContextAssembler()
        block = ContextBlock(content="hello", source="test")
        asm.add_block(block)
        assert len(asm.blocks) == 1
