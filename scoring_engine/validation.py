"""
Data Validation & Error Handling (Section 8)
Validates all inputs before scoring begins.
Prevents undefined states and ensures data integrity.
"""

import logging
from scoring_engine.config import (
    APPROVED_DOMAINS,
    CONSTRUCTS,
    VALID_DIRECTIONS,
    RESPONSE_SCALES,
    LOW_CONFIDENCE_THRESHOLD,
)
from scoring_engine.item_dictionary import ITEM_DICTIONARY

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when a critical validation check fails and scoring must stop."""
    pass


class ValidationWarning:
    """Non-fatal validation issue that is logged but does not halt scoring."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message

    def __repr__(self):
        return f"ValidationWarning({self.code}: {self.message})"


def validate_item_dictionary(items: list[dict] | None = None) -> list[ValidationWarning]:
    """
    Validate the integrity of the item coding dictionary (Section 2.9).
    Checks:
      - All required fields present
      - No duplicate item_ids
      - Domains match approved list
      - Constructs are PEI or BHP only
      - Directions are forward or reverse only
      - Response scale aligns with min/max
    """
    if items is None:
        items = ITEM_DICTIONARY

    warnings = []
    required_fields = [
        "item_id", "item_text", "domain", "subdomain",
        "construct", "direction", "weight", "response_scale",
        "min_score", "max_score", "item_type",
    ]

    seen_ids = set()

    for idx, item in enumerate(items):
        prefix = f"Item index {idx}"

        # Check required fields
        for field in required_fields:
            if field not in item or item[field] is None:
                raise ValidationError(f"{prefix}: Missing required field '{field}'")

        item_id = item["item_id"]
        prefix = f"Item {item_id}"

        # Duplicate check
        if item_id in seen_ids:
            raise ValidationError(f"{prefix}: Duplicate item_id detected")
        seen_ids.add(item_id)

        # Domain check
        if item["domain"] not in APPROVED_DOMAINS:
            raise ValidationError(
                f"{prefix}: Domain '{item['domain']}' not in approved list: {APPROVED_DOMAINS}"
            )

        # Construct check
        if item["construct"] not in CONSTRUCTS:
            raise ValidationError(
                f"{prefix}: Construct '{item['construct']}' must be one of {CONSTRUCTS}"
            )

        # Direction check
        if item["direction"] not in VALID_DIRECTIONS:
            raise ValidationError(
                f"{prefix}: Direction '{item['direction']}' must be one of {VALID_DIRECTIONS}"
            )

        # Response scale check
        scale = item["response_scale"]
        if scale in RESPONSE_SCALES:
            expected = RESPONSE_SCALES[scale]
            if item["min_score"] != expected["min_score"]:
                warnings.append(ValidationWarning(
                    "SCALE_MISMATCH",
                    f"{prefix}: min_score {item['min_score']} doesn't match "
                    f"scale {scale} expected {expected['min_score']}"
                ))
            if item["max_score"] != expected["max_score"]:
                warnings.append(ValidationWarning(
                    "SCALE_MISMATCH",
                    f"{prefix}: max_score {item['max_score']} doesn't match "
                    f"scale {scale} expected {expected['max_score']}"
                ))

        # Weight check
        if not isinstance(item["weight"], (int, float)) or item["weight"] <= 0:
            raise ValidationError(f"{prefix}: Weight must be a positive number")

    # Construct coverage check (Section 8.7)
    pei_items = [i for i in items if i["construct"] == "PEI"]
    bhp_items = [i for i in items if i["construct"] == "BHP"]

    if len(pei_items) == 0:
        raise ValidationError("No PEI items found — system cannot compute PEI score")
    if len(bhp_items) == 0:
        raise ValidationError("No BHP items found — system cannot compute BHP score")

    logger.info(
        f"Item dictionary validated: {len(items)} items, "
        f"{len(pei_items)} PEI, {len(bhp_items)} BHP, "
        f"{len(warnings)} warnings"
    )

    return warnings


def validate_responses(responses: list[dict], items: list[dict] | None = None) -> dict:
    """
    Validate user responses before scoring (Section 8.2).

    Returns:
        {
            "valid": True/False,
            "validated_responses": [...],
            "skipped_items": [...],
            "low_confidence": True/False,
            "warnings": [...]
        }
    """
    if items is None:
        items = ITEM_DICTIONARY

    item_lookup = {item["item_id"]: item for item in items}
    warnings = []
    validated = []
    skipped_ids = []

    response_map = {}
    for resp in responses:
        if "item_id" not in resp:
            warnings.append(ValidationWarning("MISSING_ID", "Response missing item_id"))
            continue
        response_map[resp["item_id"]] = resp

    for item_id, item_def in item_lookup.items():
        if item_id not in response_map:
            skipped_ids.append(item_id)
            logger.warning(f"Item {item_id} has no response — skipped")
            continue

        resp = response_map[item_id]
        raw = resp.get("response")

        # Null check
        if raw is None:
            skipped_ids.append(item_id)
            warnings.append(ValidationWarning(
                "NULL_RESPONSE", f"Item {item_id}: response is null"
            ))
            continue

        # Type check
        if not isinstance(raw, (int, float)):
            warnings.append(ValidationWarning(
                "INVALID_TYPE", f"Item {item_id}: response must be numeric, got {type(raw).__name__}"
            ))
            skipped_ids.append(item_id)
            continue

        # Range check
        min_s = item_def["min_score"]
        max_s = item_def["max_score"]
        if raw < min_s or raw > max_s:
            warnings.append(ValidationWarning(
                "OUT_OF_RANGE",
                f"Item {item_id}: response {raw} outside valid range [{min_s}, {max_s}]"
            ))
            skipped_ids.append(item_id)
            continue

        validated.append({
            "item_id": item_id,
            "response": raw,
        })

    # Low confidence check (Section 8.4)
    total_items = len(item_lookup)
    answered = len(validated)
    completion_rate = answered / total_items if total_items > 0 else 0
    low_confidence = completion_rate < LOW_CONFIDENCE_THRESHOLD

    if low_confidence:
        logger.warning(
            f"Low confidence: {answered}/{total_items} items answered "
            f"({completion_rate:.1%} < {LOW_CONFIDENCE_THRESHOLD:.0%})"
        )

    return {
        "valid": len(validated) > 0,
        "validated_responses": validated,
        "skipped_items": skipped_ids,
        "completion_rate": round(completion_rate, 4),
        "low_confidence": low_confidence,
        "warnings": warnings,
    }
