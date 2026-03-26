"""
Tests for the Domain Aggregation module (Section 5).
"""

import pytest
from scoring_engine.domains import (
    classify_domain_score,
    get_aims_priority,
    build_domain_profiles,
    extract_strengths,
    extract_growth_edges,
)


class TestDomainClassification:
    """Section 5.4: Domain performance band classification."""

    def test_strength(self):
        assert classify_domain_score(0.85) == "Strength"

    def test_strength_boundary(self):
        assert classify_domain_score(0.80) == "Strength"

    def test_developed(self):
        assert classify_domain_score(0.70) == "Developed"

    def test_developed_boundary(self):
        assert classify_domain_score(0.60) == "Developed"

    def test_emerging(self):
        assert classify_domain_score(0.50) == "Emerging"

    def test_emerging_boundary(self):
        assert classify_domain_score(0.40) == "Emerging"

    def test_growth_edge(self):
        assert classify_domain_score(0.30) == "Growth_Edge"

    def test_growth_edge_zero(self):
        assert classify_domain_score(0.0) == "Growth_Edge"

    def test_perfect_score(self):
        assert classify_domain_score(1.0) == "Strength"


class TestAimsPriority:
    """Section 5.13: AIMS mapping."""

    def test_strength_mapping(self):
        assert get_aims_priority("Strength") == "Sustain & Generalize"

    def test_developed_mapping(self):
        assert get_aims_priority("Developed") == "Optimize"

    def test_emerging_mapping(self):
        assert get_aims_priority("Emerging") == "Targeted Intervention"

    def test_growth_edge_mapping(self):
        assert get_aims_priority("Growth_Edge") == "Immediate Priority"


class TestDomainProfiles:
    """Section 5.12: Composite domain profiles."""

    def _sample_domain_scores(self):
        return {
            "EMOTIONAL_REGULATION": 0.82,
            "COGNITIVE_CONTROL": 0.74,
            "EXECUTIVE_FUNCTION_SKILLS": 0.55,
            "BEHAVIORAL_PATTERNS": 0.33,
        }

    def test_profiles_sorted_by_score(self):
        profiles = build_domain_profiles(self._sample_domain_scores())
        scores = [p["score"] for p in profiles]
        assert scores == sorted(scores, reverse=True)

    def test_profiles_have_ranks(self):
        profiles = build_domain_profiles(self._sample_domain_scores())
        ranks = [p["rank"] for p in profiles]
        assert ranks == [1, 2, 3, 4]

    def test_profiles_have_classification(self):
        profiles = build_domain_profiles(self._sample_domain_scores())
        profile_lookup = {p["name"]: p for p in profiles}
        assert profile_lookup["EMOTIONAL_REGULATION"]["classification"] == "Strength"
        assert profile_lookup["COGNITIVE_CONTROL"]["classification"] == "Developed"
        assert profile_lookup["EXECUTIVE_FUNCTION_SKILLS"]["classification"] == "Emerging"
        assert profile_lookup["BEHAVIORAL_PATTERNS"]["classification"] == "Growth_Edge"

    def test_profiles_have_aims_priority(self):
        profiles = build_domain_profiles(self._sample_domain_scores())
        for p in profiles:
            assert "aims_priority" in p

    def test_construct_balance_included(self):
        domain_scores = {"D1": 0.60}
        balance = {"D1": {"PEI": 0.55, "BHP": 0.65, "interpretation": "Capacity-driven pattern"}}
        profiles = build_domain_profiles(domain_scores, balance)
        assert "construct_balance" in profiles[0]
        assert profiles[0]["construct_balance"]["PEI"] == 0.55


class TestStrengthsAndGrowthEdges:
    """Section 5.5, 5.6, 5.8: Extraction of top/bottom domains."""

    def _sample_profiles(self):
        return build_domain_profiles({
            "D1": 0.90,
            "D2": 0.80,
            "D3": 0.60,
            "D4": 0.40,
            "D5": 0.20,
        })

    def test_extract_strengths_top3(self):
        profiles = self._sample_profiles()
        strengths = extract_strengths(profiles, count=3)
        assert strengths == ["D1", "D2", "D3"]

    def test_extract_growth_edges_bottom3(self):
        profiles = self._sample_profiles()
        edges = extract_growth_edges(profiles, count=3)
        assert edges == ["D3", "D4", "D5"]

    def test_extract_strengths_custom_count(self):
        profiles = self._sample_profiles()
        strengths = extract_strengths(profiles, count=2)
        assert len(strengths) == 2
