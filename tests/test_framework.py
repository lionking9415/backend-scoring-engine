"""
Tests for the PEI × BHP Framework module (Section 4).
"""

import pytest
from scoring_engine.framework import (
    assign_quadrant,
    compute_load_balance,
    compute_load_ratio,
    assign_load_state,
    compute_framework,
)


class TestQuadrantAssignment:
    """Section 4.6: Quadrant assignment logic."""

    def test_q1_aligned_flow(self):
        """High BHP, Low PEI → Q1."""
        assert assign_quadrant(0.30, 0.70) == "Q1_Aligned_Flow"

    def test_q2_capacity_strain(self):
        """High BHP, High PEI → Q2."""
        assert assign_quadrant(0.60, 0.70) == "Q2_Capacity_Strain"

    def test_q3_overload(self):
        """Low BHP, High PEI → Q3."""
        assert assign_quadrant(0.62, 0.48) == "Q3_Overload"

    def test_q4_underutilized(self):
        """Low BHP, Low PEI → Q4."""
        assert assign_quadrant(0.30, 0.30) == "Q4_Underutilized"

    def test_boundary_high_high(self):
        """Both exactly at threshold → Q2 (>= 0.50)."""
        assert assign_quadrant(0.50, 0.50) == "Q2_Capacity_Strain"

    def test_custom_threshold(self):
        """Custom threshold should change classification."""
        # With threshold 0.60: PEI=0.55 is Low, BHP=0.55 is Low → Q4
        assert assign_quadrant(0.55, 0.55, threshold=0.60) == "Q4_Underutilized"


class TestLoadBalance:
    """Section 3.9 / 4.7: Load balance calculation."""

    def test_positive_balance(self):
        """BHP > PEI → positive."""
        result = compute_load_balance(0.40, 0.60)
        assert result == 0.20

    def test_negative_balance(self):
        """PEI > BHP → negative."""
        result = compute_load_balance(0.62, 0.48)
        assert result == -0.14

    def test_zero_balance(self):
        """Equal → zero."""
        result = compute_load_balance(0.50, 0.50)
        assert result == 0.0


class TestLoadRatio:
    """Section 3.10: Load ratio."""

    def test_normal_ratio(self):
        result = compute_load_ratio(0.50, 0.75)
        assert result == 1.5

    def test_zero_pei_returns_none(self):
        """Division by zero protection."""
        result = compute_load_ratio(0.0, 0.5)
        assert result is None


class TestLoadState:
    """Section 4.8: Load state classification."""

    def test_surplus_capacity(self):
        assert assign_load_state(0.25) == "Surplus_Capacity"

    def test_stable_capacity(self):
        assert assign_load_state(0.10) == "Stable_Capacity"

    def test_balanced_load(self):
        assert assign_load_state(0.0) == "Balanced_Load"

    def test_emerging_strain(self):
        assert assign_load_state(-0.14) == "Emerging_Strain"

    def test_critical_overload(self):
        assert assign_load_state(-0.30) == "Critical_Overload"

    def test_boundary_surplus(self):
        assert assign_load_state(0.20) == "Surplus_Capacity"

    def test_boundary_critical(self):
        assert assign_load_state(-0.20) == "Critical_Overload"


class TestComputeFramework:
    """Section 4.14: Full framework output."""

    def test_example_from_spec(self):
        """Match the example from Section 4.14."""
        result = compute_framework(0.62, 0.48)
        assert result["PEI_score"] == 0.62
        assert result["BHP_score"] == 0.48
        assert result["quadrant"] == "Q3_Overload"
        assert result["load_balance"] == -0.14
        assert result["load_state"] == "Emerging_Strain"
        assert result["coordinates"]["x"] == 0.62
        assert result["coordinates"]["y"] == 0.48

    def test_all_fields_present(self):
        result = compute_framework(0.50, 0.50)
        required_keys = ["PEI_score", "BHP_score", "quadrant",
                         "load_balance", "load_state", "load_ratio", "coordinates"]
        for key in required_keys:
            assert key in result
