"""
Tests for the Validation module (Section 8).
"""

import pytest
from scoring_engine.validation import (
    validate_item_dictionary,
    validate_responses,
    ValidationError,
)
from scoring_engine.item_dictionary import ITEM_DICTIONARY


class TestItemDictionaryValidation:
    """Tests for validate_item_dictionary()."""

    def test_default_dictionary_passes(self):
        """The built-in 52-item dictionary should pass validation."""
        warnings = validate_item_dictionary()
        assert isinstance(warnings, list)

    def test_has_52_items(self):
        """Item dictionary must contain exactly 52 items."""
        assert len(ITEM_DICTIONARY) == 52

    def test_no_duplicate_ids(self):
        """All item_ids must be unique."""
        ids = [item["item_id"] for item in ITEM_DICTIONARY]
        assert len(ids) == len(set(ids))

    def test_all_constructs_valid(self):
        """Every item must be PEI or BHP."""
        for item in ITEM_DICTIONARY:
            assert item["construct"] in ("PEI", "BHP"), f"{item['item_id']} has invalid construct"

    def test_both_constructs_present(self):
        """Dictionary must have both PEI and BHP items."""
        constructs = {item["construct"] for item in ITEM_DICTIONARY}
        assert "PEI" in constructs
        assert "BHP" in constructs

    def test_missing_field_raises_error(self):
        """Missing required field should raise ValidationError."""
        bad_items = [{"item_id": "Q99", "item_text": "test"}]
        with pytest.raises(ValidationError, match="Missing required field"):
            validate_item_dictionary(bad_items)

    def test_duplicate_id_raises_error(self):
        """Duplicate item_id should raise ValidationError."""
        dup_items = [ITEM_DICTIONARY[0].copy(), ITEM_DICTIONARY[0].copy()]
        with pytest.raises(ValidationError, match="Duplicate item_id"):
            validate_item_dictionary(dup_items)

    def test_invalid_domain_raises_error(self):
        """Invalid domain should raise ValidationError."""
        bad = ITEM_DICTIONARY[0].copy()
        bad["item_id"] = "Q99"
        bad["domain"] = "INVALID_DOMAIN"
        with pytest.raises(ValidationError, match="not in approved list"):
            validate_item_dictionary([bad])

    def test_invalid_construct_raises_error(self):
        """Invalid construct should raise ValidationError."""
        bad = ITEM_DICTIONARY[0].copy()
        bad["item_id"] = "Q99"
        bad["construct"] = "XYZ"
        with pytest.raises(ValidationError, match="must be one of"):
            validate_item_dictionary([bad])

    def test_invalid_direction_raises_error(self):
        """Invalid direction should raise ValidationError."""
        bad = ITEM_DICTIONARY[0].copy()
        bad["item_id"] = "Q99"
        bad["direction"] = "sideways"
        with pytest.raises(ValidationError, match="must be one of"):
            validate_item_dictionary([bad])

    def test_no_pei_items_raises_error(self):
        """If no PEI items exist, should raise ValidationError."""
        bhp_only = [i.copy() for i in ITEM_DICTIONARY if i["construct"] == "BHP"]
        # Ensure unique IDs
        for idx, item in enumerate(bhp_only):
            item["item_id"] = f"BHP_{idx}"
        with pytest.raises(ValidationError, match="No PEI items"):
            validate_item_dictionary(bhp_only)


class TestResponseValidation:
    """Tests for validate_responses()."""

    def _make_full_responses(self, value=3):
        """Helper: generate a complete response set with a fixed value."""
        return [{"item_id": item["item_id"], "response": value} for item in ITEM_DICTIONARY]

    def test_full_valid_responses(self):
        """All 52 responses with valid values should pass."""
        responses = self._make_full_responses(3)
        result = validate_responses(responses)
        assert result["valid"] is True
        assert len(result["validated_responses"]) == 52
        assert result["completion_rate"] == 1.0
        assert result["low_confidence"] is False

    def test_missing_responses_flagged(self):
        """Missing items should be tracked in skipped_items."""
        responses = [{"item_id": "Q01", "response": 3}]
        result = validate_responses(responses)
        assert result["valid"] is True
        assert len(result["validated_responses"]) == 1
        assert "Q02" in result["skipped_items"]

    def test_low_confidence_flag(self):
        """Below 70% completion should flag low_confidence."""
        # 10 out of 52 = ~19%
        responses = self._make_full_responses(3)[:10]
        result = validate_responses(responses)
        assert result["low_confidence"] is True

    def test_out_of_range_rejected(self):
        """Response outside min/max range should be rejected."""
        responses = [{"item_id": "Q01", "response": 99}]
        result = validate_responses(responses)
        assert len(result["validated_responses"]) == 0
        assert "Q01" in result["skipped_items"]

    def test_null_response_rejected(self):
        """Null response should be rejected."""
        responses = [{"item_id": "Q01", "response": None}]
        result = validate_responses(responses)
        assert len(result["validated_responses"]) == 0

    def test_string_response_rejected(self):
        """Non-numeric response should be rejected."""
        responses = [{"item_id": "Q01", "response": "three"}]
        result = validate_responses(responses)
        assert len(result["validated_responses"]) == 0

    def test_empty_responses_invalid(self):
        """Empty response list should result in valid=False."""
        result = validate_responses([])
        assert result["valid"] is False
