"""
End-to-end integration tests for the scoring engine (Section 9).
Tests the full pipeline from raw responses to final output + interpretation.
"""

import pytest
import json
from scoring_engine.engine import process_assessment, process_multi_lens
from scoring_engine.item_dictionary import ITEM_DICTIONARY
from scoring_engine.config import REPORT_LENSES
from scoring_engine.validation import ValidationError


def _make_responses(value=3):
    """Generate a complete 52-item response set with a uniform value."""
    return [{"item_id": item["item_id"], "response": value} for item in ITEM_DICTIONARY]


def _make_varied_responses():
    """Generate realistic varied responses across all 52 items."""
    import random
    random.seed(42)
    return [
        {"item_id": item["item_id"], "response": random.randint(1, 4)}
        for item in ITEM_DICTIONARY
    ]


class TestEndToEndPipeline:
    """Full pipeline integration tests."""

    def test_basic_processing(self):
        """System correctly processes a complete sample assessment."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user_001",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        assert result is not None
        assert "metadata" in result
        assert "construct_scores" in result
        assert "load_framework" in result
        assert "domains" in result
        assert "summary" in result
        assert "items" in result

    def test_metadata_correct(self):
        """Metadata fields are properly populated."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user_002",
            report_type="PERSONAL_LIFESTYLE",
            responses=responses,
        )
        meta = result["metadata"]
        assert meta["assessment_id"] == "BEST_EF_GALAXY_V1"
        assert meta["user_id"] == "test_user_002"
        assert meta["report_type"] == "PERSONAL_LIFESTYLE"
        assert "timestamp" in meta
        assert meta["completion_rate"] == 1.0
        assert meta["low_confidence"] is False

    def test_construct_scores_range(self):
        """PEI and BHP scores must be between 0.0 and 1.0."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        cs = result["construct_scores"]
        assert 0.0 <= cs["PEI_score"] <= 1.0
        assert 0.0 <= cs["BHP_score"] <= 1.0

    def test_load_framework_complete(self):
        """Load framework must include quadrant, load_balance, load_state, coordinates."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        lf = result["load_framework"]
        assert lf["quadrant"] in [
            "Q1_Aligned_Flow", "Q2_Capacity_Strain",
            "Q3_Overload", "Q4_Underutilized",
        ]
        assert isinstance(lf["load_balance"], float)
        assert lf["load_state"] in [
            "Surplus_Capacity", "Stable_Capacity",
            "Balanced_Load", "Emerging_Strain", "Critical_Overload",
        ]
        assert "x" in lf["coordinates"]
        assert "y" in lf["coordinates"]

    def test_domain_profiles_populated(self):
        """All 7 domains should produce profiles."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        assert len(result["domains"]) == 7
        for domain in result["domains"]:
            assert "name" in domain
            assert "score" in domain
            assert "classification" in domain
            assert "rank" in domain
            assert "aims_priority" in domain

    def test_summary_populated(self):
        """Summary must include top_strengths and growth_edges."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        summary = result["summary"]
        assert isinstance(summary["top_strengths"], list)
        assert isinstance(summary["growth_edges"], list)
        assert len(summary["top_strengths"]) > 0
        assert len(summary["growth_edges"]) > 0

    def test_items_traced(self):
        """Item-level data should preserve scoring trace."""
        responses = _make_responses(4)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        assert len(result["items"]) == 52
        for item in result["items"]:
            assert "item_id" in item
            assert "raw_response" in item
            assert "adjusted_score" in item
            assert "weighted_score" in item
            assert "normalized_score" in item
            assert 0.0 <= item["normalized_score"] <= 1.0

    def test_interpretation_generated(self):
        """AI interpretation layer should be attached."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
            include_interpretation=True,
        )
        assert "interpretation" in result
        interp = result["interpretation"]
        assert "executive_summary" in interp
        assert "quadrant_interpretation" in interp
        assert "load_interpretation" in interp
        assert "strengths_analysis" in interp
        assert "growth_edges_analysis" in interp
        assert "pei_bhp_interpretation" in interp
        assert "aims_plan" in interp
        aims = interp["aims_plan"]
        assert "awareness" in aims
        assert "intervention" in aims
        assert "mastery" in aims
        assert "sustain" in aims

    def test_interpretation_excluded(self):
        """Interpretation can be turned off."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
            include_interpretation=False,
        )
        assert "interpretation" not in result

    def test_demographics_passthrough(self):
        """Demographics should be stored in metadata without affecting scoring."""
        responses = _make_responses(3)
        demographics = {"age": 22, "role": "student", "environment": "university"}
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
            demographics=demographics,
        )
        assert result["metadata"]["demographics"] == demographics

    def test_invalid_report_type_raises(self):
        """Invalid report_type should raise ValueError."""
        responses = _make_responses(3)
        with pytest.raises(ValueError, match="Invalid report_type"):
            process_assessment(
                user_id="test_user",
                report_type="INVALID_LENS",
                responses=responses,
            )

    def test_empty_responses_raises(self):
        """No valid responses should raise ValidationError."""
        with pytest.raises(ValidationError):
            process_assessment(
                user_id="test_user",
                report_type="STUDENT_SUCCESS",
                responses=[],
            )

    def test_varied_responses_produce_differentiated_scores(self):
        """Non-uniform responses should produce varied domain scores."""
        responses = _make_varied_responses()
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        domain_scores = [d["score"] for d in result["domains"]]
        # Not all domains should have the exact same score
        assert len(set(domain_scores)) > 1

    def test_output_is_json_serializable(self):
        """Entire output must be JSON-serializable."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        serialized = json.dumps(result)
        assert isinstance(serialized, str)
        # Round-trip
        deserialized = json.loads(serialized)
        assert deserialized["metadata"]["user_id"] == "test_user"

    def test_config_driven_threshold(self):
        """Custom threshold should change quadrant classification."""
        responses = _make_responses(3)
        result_default = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        result_custom = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
            threshold=0.90,
        )
        # With a very high threshold, both PEI and BHP should be "Low" → Q4
        assert result_custom["load_framework"]["quadrant"] == "Q4_Underutilized"


class TestMultiLens:
    """Test multi-lens processing (same data, different interpretations)."""

    def test_all_four_lenses(self):
        """Same data should produce 4 reports with same scores but different narratives."""
        responses = _make_responses(3)
        result = process_multi_lens(
            user_id="test_user",
            responses=responses,
        )
        assert "reports" in result
        assert len(result["reports"]) == 4

        # All 4 lenses present
        for lens in REPORT_LENSES:
            assert lens in result["reports"]

        # Scores should be identical across lenses
        scores = [
            result["reports"][lens]["construct_scores"]
            for lens in REPORT_LENSES
        ]
        for s in scores[1:]:
            assert s == scores[0], "Construct scores must be identical across lenses"

        # Interpretations should differ
        narratives = [
            result["reports"][lens]["interpretation"]["quadrant_interpretation"]
            for lens in REPORT_LENSES
        ]
        # At least some should differ (different lens language)
        assert len(set(narratives)) > 1, "Narratives should differ by lens"

    def test_selective_lenses(self):
        """Can process only selected lenses."""
        responses = _make_responses(3)
        result = process_multi_lens(
            user_id="test_user",
            responses=responses,
            lenses=["STUDENT_SUCCESS", "PERSONAL_LIFESTYLE"],
        )
        assert len(result["reports"]) == 2
        assert "STUDENT_SUCCESS" in result["reports"]
        assert "PERSONAL_LIFESTYLE" in result["reports"]


class TestScoringAccuracy:
    """Verify deterministic scoring with known inputs."""

    def test_all_ones_scoring(self):
        """All responses = 1: forward items get min, reverse items get max."""
        responses = _make_responses(1)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        # For forward items: normalized = (1-1)/(4-1) = 0.0
        # For reverse items: adjusted = (4+1)-1 = 4, normalized = (4-1)/(4-1) = 1.0
        for item in result["items"]:
            if item["direction"] == "forward":
                assert item["normalized_score"] == 0.0
            else:
                assert item["normalized_score"] == 1.0

    def test_all_fours_scoring(self):
        """All responses = 4 (max): forward items get max, reverse items get min."""
        responses = _make_responses(4)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        for item in result["items"]:
            if item["direction"] == "forward":
                assert item["normalized_score"] == 1.0
            else:
                assert item["normalized_score"] == 0.0

    def test_all_threes_scoring(self):
        """All responses = 3 on ABCD_4 scale: normalized = (3-1)/(4-1) = 0.6667."""
        responses = _make_responses(3)
        result = process_assessment(
            user_id="test_user",
            report_type="STUDENT_SUCCESS",
            responses=responses,
        )
        for item in result["items"]:
            if item["direction"] == "forward":
                # Output rounds to OUTPUT_PRECISION=3: round(0.6667, 3) = 0.667
                assert item["normalized_score"] == round(2/3, 3)
            else:
                # reverse: adjusted = (4+1)-3 = 2, normalized = (2-1)/3 = 0.333
                assert item["normalized_score"] == round(1/3, 3)

    def test_deterministic(self):
        """Same input must produce same output (deterministic)."""
        responses = _make_varied_responses()
        r1 = process_assessment("u1", "STUDENT_SUCCESS", responses, include_interpretation=False)
        r2 = process_assessment("u1", "STUDENT_SUCCESS", responses, include_interpretation=False)
        # Compare scores (not timestamps)
        assert r1["construct_scores"] == r2["construct_scores"]
        assert r1["load_framework"]["quadrant"] == r2["load_framework"]["quadrant"]
        assert r1["domains"] == r2["domains"]
