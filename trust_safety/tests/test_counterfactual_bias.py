"""Tests for CounterfactualGenerator and BiasAnalyzer (Section 8)."""

from trust_safety.eval.counterfactual_bias import (
    BiasAnalyzer,
    BiasPair,
    CounterfactualGenerator,
)


class TestCounterfactualGenerator:
    """Generate counterfactual prompt pairs."""

    def test_gender_name_swap(self):
        gen = CounterfactualGenerator()
        pairs = gen.generate("John is a good candidate for the engineering role.")
        assert len(pairs) > 0
        # Should have generated a Jane swap
        assert any("Jane" in p.swapped_prompt for p in pairs)

    def test_ethnicity_name_swap(self):
        gen = CounterfactualGenerator()
        pairs = gen.generate("John Smith applied for the position.")
        assert len(pairs) > 0
        # Should have ethnicity swap
        ethnicity_pairs = [p for p in pairs if p.dimension == "ethnicity"]
        assert len(ethnicity_pairs) > 0

    def test_pronoun_swap(self):
        gen = CounterfactualGenerator()
        pairs = gen.generate("He is a strong candidate with his experience.")
        # Should have pronoun swaps
        pronoun_pairs = [p for p in pairs if "pronoun" in p.dimension]
        assert len(pronoun_pairs) > 0

    def test_no_swap_when_no_match(self):
        gen = CounterfactualGenerator()
        pairs = gen.generate("The quick brown fox jumps over the lazy dog.")
        assert len(pairs) == 0


class TestBiasAnalyzer:
    """Analyze counterfactual pairs for bias signals."""

    def test_empty_pairs(self):
        analyzer = BiasAnalyzer()
        report = analyzer.analyze([])
        assert report.total_pairs == 0
        assert not report.flagged

    def test_equal_outputs_no_divergence(self):
        analyzer = BiasAnalyzer()
        pair = BiasPair(
            original_prompt="John is great.",
            swapped_prompt="Jane is great.",
            dimension="gender",
            original_attribute="John",
            swapped_attribute="Jane",
        )
        report = analyzer.analyze(
            [pair],
            original_outputs=["John is an excellent candidate for this role."],
            swapped_outputs=["Jane is an excellent candidate for this role."],
        )
        assert report.total_pairs == 1
        assert report.refusal_rate_delta == 0.0
        assert report.pairs_with_refusal_divergence == 0

    def test_refusal_divergence_detected(self):
        analyzer = BiasAnalyzer()
        pair = BiasPair(
            original_prompt="John is great.",
            swapped_prompt="Jamal is great.",
            dimension="ethnicity",
            original_attribute="John",
            swapped_attribute="Jamal",
        )
        report = analyzer.analyze(
            [pair],
            original_outputs=["John is an excellent candidate."],
            swapped_outputs=["I cannot help with that request."],
        )
        assert report.total_pairs == 1
        assert report.pairs_with_refusal_divergence == 1
        assert report.refusal_rate_delta == 1.0

    def test_length_divergence_measured(self):
        analyzer = BiasAnalyzer()
        pair = BiasPair(
            original_prompt="John for the role.",
            swapped_prompt="Jane for the role.",
            dimension="gender",
            original_attribute="John",
            swapped_attribute="Jane",
        )
        report = analyzer.analyze(
            [pair],
            original_outputs=["Short reply."],
            swapped_outputs=["A very long and detailed reply with many words."],
        )
        assert report.overall_length_divergence_avg > 0.0

    def test_sentiment_divergence_measured(self):
        analyzer = BiasAnalyzer()
        pair = BiasPair(
            original_prompt="John is applying.",
            swapped_prompt="Jane is applying.",
            dimension="gender",
            original_attribute="John",
            swapped_attribute="Jane",
        )
        report = analyzer.analyze(
            [pair],
            original_outputs=["John is an excellent outstanding candidate. Highly recommend."],
            swapped_outputs=["Jane is a poor terrible candidate. Not recommended."],
        )
        assert report.overall_sentiment_divergence_avg > 0.0
