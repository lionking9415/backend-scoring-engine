"""
Tests for the overlapping domain-to-index weight matrix (G1).
Verifies that domains can contribute to BOTH PEI and BHP with different weights.
"""

import pytest
from scoring_engine.scoring import aggregate_indices_by_domain_weights


class TestOverlappingDomainWeights:
    """Core tests for the domain weight matrix aggregation."""

    def test_exclusive_domains(self):
        """Domains with weight on only one index contribute only to that index."""
        domain_scores = {
            "D_PEI_ONLY": 0.80,
            "D_BHP_ONLY": 0.60,
        }
        weights = {
            "D_PEI_ONLY": {"PEI": 1.0, "BHP": 0.0},
            "D_BHP_ONLY": {"PEI": 0.0, "BHP": 1.0},
        }
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        assert result["PEI_score"] == 0.80
        assert result["BHP_score"] == 0.60

    def test_overlapping_domain(self):
        """A domain with weights on BOTH indices contributes to both."""
        domain_scores = {
            "D_SHARED": 0.70,
        }
        weights = {
            "D_SHARED": {"PEI": 0.5, "BHP": 1.0},
        }
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        # PEI: (0.70 * 0.5) / 0.5 = 0.70
        assert result["PEI_score"] == 0.70
        # BHP: (0.70 * 1.0) / 1.0 = 0.70
        assert result["BHP_score"] == 0.70

    def test_overlapping_with_different_weights(self):
        """Multiple domains, one overlapping, produce weighted averages."""
        domain_scores = {
            "D1": 0.80,  # PEI only
            "D2": 0.40,  # BHP only
            "D3": 0.60,  # overlapping — PEI weight 0.3, BHP weight 1.0
        }
        weights = {
            "D1": {"PEI": 1.0, "BHP": 0.0},
            "D2": {"PEI": 0.0, "BHP": 1.0},
            "D3": {"PEI": 0.3, "BHP": 1.0},
        }
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        # PEI: (0.80*1.0 + 0.60*0.3) / (1.0 + 0.3) = (0.80 + 0.18) / 1.3 = 0.7538...
        assert round(result["PEI_score"], 3) == 0.754
        # BHP: (0.40*1.0 + 0.60*1.0) / (1.0 + 1.0) = 1.0 / 2.0 = 0.50
        assert result["BHP_score"] == 0.50

    def test_zero_weight_excluded(self):
        """Domains with weight 0.0 for an index don't contribute."""
        domain_scores = {"D1": 0.90}
        weights = {"D1": {"PEI": 0.0, "BHP": 1.0}}
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        assert result["BHP_score"] == 0.90
        # PEI has no contributing domains → 0.0
        assert result["PEI_score"] == 0.0

    def test_missing_domain_in_matrix_ignored(self):
        """A domain not in the weight matrix defaults to 0/0 (excluded)."""
        domain_scores = {"UNKNOWN_DOMAIN": 0.75, "D1": 0.50}
        weights = {"D1": {"PEI": 1.0, "BHP": 1.0}}
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        assert result["PEI_score"] == 0.50
        assert result["BHP_score"] == 0.50

    def test_all_domains_overlap(self):
        """All domains contribute to both indices with equal weight."""
        domain_scores = {"D1": 0.80, "D2": 0.40}
        weights = {
            "D1": {"PEI": 1.0, "BHP": 1.0},
            "D2": {"PEI": 1.0, "BHP": 1.0},
        }
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        # Both indices get same average: (0.80 + 0.40) / 2 = 0.60
        assert result["PEI_score"] == 0.60
        assert result["BHP_score"] == 0.60

    def test_uses_default_config_weights(self):
        """When no weight_matrix is passed, uses DOMAIN_INDEX_WEIGHTS from config."""
        from scoring_engine.config import DOMAIN_INDEX_WEIGHTS, APPROVED_DOMAINS
        domain_scores = {d: 0.50 for d in APPROVED_DOMAINS}
        result = aggregate_indices_by_domain_weights(domain_scores)
        # Should produce valid scores using default config
        assert 0.0 <= result["PEI_score"] <= 1.0
        assert 0.0 <= result["BHP_score"] <= 1.0

    def test_config_has_overlapping_domains(self):
        """Verify the default config actually has overlapping domain contributions."""
        from scoring_engine.config import DOMAIN_INDEX_WEIGHTS
        overlapping = [
            d for d, w in DOMAIN_INDEX_WEIGHTS.items()
            if w.get("PEI", 0) > 0 and w.get("BHP", 0) > 0
        ]
        assert len(overlapping) >= 2, "Config should have at least 2 overlapping domains"

    def test_weighted_average_not_simple_sum(self):
        """Confirm the formula uses weighted average, not sum."""
        domain_scores = {"D1": 0.80, "D2": 0.20}
        weights = {
            "D1": {"PEI": 2.0, "BHP": 0.0},  # heavy weight
            "D2": {"PEI": 1.0, "BHP": 0.0},   # light weight
        }
        result = aggregate_indices_by_domain_weights(domain_scores, weights)
        # PEI: (0.80*2.0 + 0.20*1.0) / (2.0 + 1.0) = 1.80 / 3.0 = 0.60
        assert result["PEI_score"] == 0.60
