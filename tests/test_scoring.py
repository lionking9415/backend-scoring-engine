"""
Tests for the Scoring module (Section 3).
"""

import pytest
from scoring_engine.scoring import (
    adjust_for_direction,
    apply_weight,
    normalize_score,
    score_single_item,
    score_all_items,
    aggregate_by_domain,
    aggregate_by_construct,
    compute_domain_construct_balance,
)


class TestDirectionAdjustment:
    """Section 3.4: Reverse scoring tests."""

    def test_forward_no_change(self):
        assert adjust_for_direction(4, "forward", 1, 5) == 4

    def test_reverse_likert5(self):
        # (5 + 1) - 4 = 2
        assert adjust_for_direction(4, "reverse", 1, 5) == 2

    def test_reverse_likert5_min(self):
        # (5 + 1) - 1 = 5
        assert adjust_for_direction(1, "reverse", 1, 5) == 5

    def test_reverse_likert5_max(self):
        # (5 + 1) - 5 = 1
        assert adjust_for_direction(5, "reverse", 1, 5) == 1

    def test_reverse_likert7(self):
        # (7 + 1) - 3 = 5
        assert adjust_for_direction(3, "reverse", 1, 7) == 5


class TestWeightApplication:
    """Section 3.5: Weight application tests."""

    def test_default_weight(self):
        assert apply_weight(4, 1.0) == 4.0

    def test_custom_weight(self):
        assert apply_weight(4, 1.5) == 6.0

    def test_zero_score(self):
        assert apply_weight(0, 1.0) == 0.0


class TestNormalization:
    """Section 3.6: Normalization to 0.0–1.0 range."""

    def test_min_value(self):
        # (1 - 1) / (5 - 1) = 0.0
        assert normalize_score(1, 1, 5) == 0.0

    def test_max_value(self):
        # (5 - 1) / (5 - 1) = 1.0
        assert normalize_score(5, 1, 5) == 1.0

    def test_mid_value(self):
        # (3 - 1) / (5 - 1) = 0.5
        assert normalize_score(3, 1, 5) == 0.5

    def test_division_by_zero_safe(self):
        """min == max should return 0.0, not crash."""
        assert normalize_score(5, 5, 5) == 0.0

    def test_likert7_normalization(self):
        # (4 - 1) / (7 - 1) = 0.5
        assert normalize_score(4, 1, 7) == 0.5


class TestScoreSingleItem:
    """Section 3.12: End-to-end single item scoring."""

    def test_forward_item(self):
        item_def = {
            "item_id": "Q01",
            "domain": "EXECUTIVE_FUNCTION_SKILLS",
            "subdomain": "TASK_INITIATION",
            "construct": "BHP",
            "direction": "forward",
            "weight": 1.0,
            "min_score": 1,
            "max_score": 5,
        }
        result = score_single_item(4, item_def)
        assert result["raw_response"] == 4
        assert result["adjusted_score"] == 4
        assert result["weighted_score"] == 4
        # (4 - 1) / (5 - 1) = 0.75
        assert result["normalized_score"] == 0.75

    def test_reverse_item(self):
        """Section 3.12 example: reverse-scored item."""
        item_def = {
            "item_id": "Q02",
            "domain": "EMOTIONAL_REGULATION",
            "subdomain": "TASK_AVOIDANCE",
            "construct": "BHP",
            "direction": "reverse",
            "weight": 1.0,
            "min_score": 1,
            "max_score": 5,
        }
        result = score_single_item(4, item_def)
        assert result["raw_response"] == 4
        # (5 + 1) - 4 = 2
        assert result["adjusted_score"] == 2
        # (2 - 1) / (5 - 1) = 0.25
        assert result["normalized_score"] == 0.25

    def test_weighted_item(self):
        item_def = {
            "item_id": "Q03",
            "domain": "COGNITIVE_CONTROL",
            "subdomain": "SUSTAINED_ATTENTION",
            "construct": "BHP",
            "direction": "forward",
            "weight": 1.5,
            "min_score": 1,
            "max_score": 5,
        }
        result = score_single_item(4, item_def)
        # adjusted = 4, weighted = 4 * 1.5 = 6.0
        assert result["weighted_score"] == 6.0


class TestAggregation:
    """Sections 3.7, 3.8: Domain and construct aggregation."""

    def _make_scored_items(self):
        return [
            {"item_id": "Q01", "domain": "D1", "subdomain": "S1",
             "construct": "BHP", "normalized_score": 0.75},
            {"item_id": "Q02", "domain": "D1", "subdomain": "S2",
             "construct": "BHP", "normalized_score": 0.50},
            {"item_id": "Q03", "domain": "D2", "subdomain": "S3",
             "construct": "PEI", "normalized_score": 0.60},
            {"item_id": "Q04", "domain": "D2", "subdomain": "S4",
             "construct": "PEI", "normalized_score": 0.40},
        ]

    def test_domain_aggregation(self):
        scored = self._make_scored_items()
        domain_scores = aggregate_by_domain(scored)
        # D1: (0.75 + 0.50) / 2 = 0.625
        assert domain_scores["D1"] == 0.625
        # D2: (0.60 + 0.40) / 2 = 0.50
        assert domain_scores["D2"] == 0.50

    def test_construct_aggregation(self):
        scored = self._make_scored_items()
        construct_scores = aggregate_by_construct(scored)
        # BHP: (0.75 + 0.50) / 2 = 0.625
        assert construct_scores["BHP_score"] == 0.625
        # PEI: (0.60 + 0.40) / 2 = 0.50
        assert construct_scores["PEI_score"] == 0.50

    def test_domain_construct_balance(self):
        scored = self._make_scored_items()
        balance = compute_domain_construct_balance(scored)
        assert balance["D1"]["BHP"] == 0.625
        assert balance["D1"]["PEI"] is None  # No PEI items in D1
        assert balance["D2"]["PEI"] == 0.50
        assert balance["D2"]["BHP"] is None  # No BHP items in D2
