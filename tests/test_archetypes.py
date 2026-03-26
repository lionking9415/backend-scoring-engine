"""
Tests for the Archetype Assignment Engine (G4).
"""

import pytest
from scoring_engine.archetypes import (
    assign_archetype,
    get_archetype_by_id,
    list_archetypes_for_quadrant,
)
from scoring_engine.config import ARCHETYPE_DEFINITIONS


class TestArchetypeAssignment:
    """Archetype assignment logic tests."""

    def test_exact_match(self):
        """Exact quadrant + load_state match returns correct archetype."""
        result = assign_archetype("Q1_Aligned_Flow", "Surplus_Capacity")
        assert result["archetype_id"] == "THE_NAVIGATOR"
        assert result["confidence"] == "exact"

    def test_q2_exact(self):
        result = assign_archetype("Q2_Capacity_Strain", "Emerging_Strain")
        assert result["archetype_id"] == "THE_STRETCHER"
        assert result["confidence"] == "exact"

    def test_q3_overload_critical(self):
        result = assign_archetype("Q3_Overload", "Critical_Overload")
        assert result["archetype_id"] == "THE_OVERWHELMED"
        assert result["confidence"] == "exact"

    def test_q4_balanced(self):
        result = assign_archetype("Q4_Underutilized", "Balanced_Load")
        assert result["archetype_id"] == "THE_SEEKER"
        assert result["confidence"] == "exact"

    def test_quadrant_fallback(self):
        """When no exact match, falls back to quadrant-only match."""
        result = assign_archetype("Q1_Aligned_Flow", "Critical_Overload")
        assert result["confidence"] == "quadrant_match"
        assert result["quadrant"] == "Q1_Aligned_Flow"

    def test_complete_fallback(self):
        """Unknown quadrant returns UNASSIGNED."""
        result = assign_archetype("Q99_Unknown", "Unknown_State")
        assert result["archetype_id"] == "UNASSIGNED"
        assert result["confidence"] == "fallback"

    def test_result_structure(self):
        """Result always has required keys."""
        result = assign_archetype("Q1_Aligned_Flow", "Surplus_Capacity")
        assert "archetype_id" in result
        assert "description" in result
        assert "quadrant" in result
        assert "load_state" in result
        assert "confidence" in result

    def test_all_quadrants_have_archetypes(self):
        """Every quadrant has at least one archetype defined."""
        quadrants = ["Q1_Aligned_Flow", "Q2_Capacity_Strain",
                     "Q3_Overload", "Q4_Underutilized"]
        for q in quadrants:
            archetypes = list_archetypes_for_quadrant(q)
            assert len(archetypes) >= 1, f"Quadrant {q} has no archetypes"


class TestArchetypeConfig:
    """Tests for archetype configuration."""

    def test_16_archetypes_defined(self):
        """Config must have exactly 16 archetypes."""
        assert len(ARCHETYPE_DEFINITIONS) == 16

    def test_all_have_required_fields(self):
        """Each archetype must have quadrant, load_state, description."""
        for arch_id, arch_def in ARCHETYPE_DEFINITIONS.items():
            assert "quadrant" in arch_def, f"{arch_id} missing quadrant"
            assert "load_state" in arch_def, f"{arch_id} missing load_state"
            assert "description" in arch_def, f"{arch_id} missing description"

    def test_get_by_id(self):
        result = get_archetype_by_id("THE_NAVIGATOR")
        assert result is not None
        assert result["quadrant"] == "Q1_Aligned_Flow"

    def test_get_by_id_missing(self):
        result = get_archetype_by_id("NONEXISTENT")
        assert result is None

    def test_list_for_quadrant(self):
        q1_archs = list_archetypes_for_quadrant("Q1_Aligned_Flow")
        assert len(q1_archs) >= 2
        for a in q1_archs:
            assert a["quadrant"] == "Q1_Aligned_Flow"
