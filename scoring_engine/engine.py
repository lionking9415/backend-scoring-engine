"""
Main Orchestrator — System Integration (Section 9)
End-to-end pipeline that processes assessment responses through all layers:

  Frontend (Assessment UI)
      ↓
  Response Capture Layer
      ↓
  Validation Layer (Section 8)
      ↓
  Scoring Engine (Section 3)
      ↓
  Framework Layer (Section 4)
      ↓
  Domain Aggregation (Section 5)
      ↓
  Output Generator (Section 6)
      ↓
  AI Interpretation Layer (Section 7)
      ↓
  Report Output (UI / PDF / Dashboard)
"""

import logging
from scoring_engine.config import REPORT_LENSES
from scoring_engine.item_dictionary import ITEM_DICTIONARY
from scoring_engine.validation import (
    validate_item_dictionary,
    validate_responses,
    ValidationError,
)
from scoring_engine.scoring import (
    score_all_items,
    aggregate_by_domain,
    aggregate_by_subdomain,
    aggregate_by_construct,
    aggregate_indices_by_domain_weights,
    compute_domain_construct_balance,
)
from scoring_engine.archetypes import assign_archetype
from scoring_engine.framework import compute_framework
from scoring_engine.domains import (
    build_domain_profiles,
    extract_strengths,
    extract_growth_edges,
)
from scoring_engine.output import build_output
from scoring_engine.interpretation import generate_full_interpretation

logger = logging.getLogger(__name__)


def process_assessment(
    user_id: str,
    report_type: str,
    responses: list[dict],
    items: list[dict] | None = None,
    demographics: dict | None = None,
    threshold: float | None = None,
    include_interpretation: bool = True,
    use_ai: bool = False,
    user_email: str | None = None,
) -> dict:
    """
    Process a complete assessment from raw responses to final output.

    Args:
        user_id: Unique user identifier (anonymizable)
        report_type: One of REPORT_LENSES (determines interpretation lens)
        responses: List of {"item_id": str, "response": int/float}
        items: Custom item dictionary (defaults to ITEM_DICTIONARY)
        demographics: Optional demographic metadata (does not affect scoring)
        threshold: Custom quadrant threshold (defaults to config)
        include_interpretation: Whether to generate AI narrative layer
        use_ai: Whether to use OpenAI for interpretation (Phase 2)

    Returns:
        Complete output JSON per Section 6 schema, optionally with
        Section 7 interpretation attached.

    Raises:
        ValidationError: If critical validation checks fail.
        ValueError: If report_type is invalid.
    """

    # -------------------------------------------------------------------------
    # Step 0: Validate report type
    # -------------------------------------------------------------------------
    if report_type not in REPORT_LENSES:
        raise ValueError(
            f"Invalid report_type '{report_type}'. Must be one of: {REPORT_LENSES}"
        )

    if items is None:
        items = ITEM_DICTIONARY

    logger.info(f"Processing assessment for user={user_id}, lens={report_type}")

    # -------------------------------------------------------------------------
    # Step 1: Validate item dictionary (Section 2.9 / 8.3)
    # -------------------------------------------------------------------------
    dict_warnings = validate_item_dictionary(items)
    if dict_warnings:
        for w in dict_warnings:
            logger.warning(f"Item dictionary: {w}")

    # -------------------------------------------------------------------------
    # Step 2: Validate responses (Section 8.2)
    # -------------------------------------------------------------------------
    validation_result = validate_responses(responses, items)

    if not validation_result["valid"]:
        raise ValidationError("No valid responses — cannot proceed with scoring")

    validated_responses = validation_result["validated_responses"]
    completion_rate = validation_result["completion_rate"]
    low_confidence = validation_result["low_confidence"]

    if validation_result["warnings"]:
        for w in validation_result["warnings"]:
            logger.warning(f"Response validation: {w}")

    logger.info(
        f"Validation complete: {len(validated_responses)} valid responses, "
        f"completion={completion_rate:.1%}, low_confidence={low_confidence}"
    )

    # -------------------------------------------------------------------------
    # Step 3: Score all items (Section 3)
    # -------------------------------------------------------------------------
    scored_items = score_all_items(validated_responses, items)

    # -------------------------------------------------------------------------
    # Step 4a: Aggregate by domain (needed before index computation)
    # -------------------------------------------------------------------------
    domain_scores = aggregate_by_domain(scored_items)

    # -------------------------------------------------------------------------
    # Step 4b: Compute PEI & BHP indices via overlapping domain weight matrix
    # This is the key architectural feature: domains contribute to BOTH
    # indices with DIFFERENT configurable weights.
    # -------------------------------------------------------------------------
    construct_scores = aggregate_indices_by_domain_weights(domain_scores)

    # Also compute per-item construct aggregation (legacy / transparency)
    construct_scores_by_item = aggregate_by_construct(scored_items)
    construct_scores["PEI_score_by_item"] = construct_scores_by_item.get("PEI_score", 0.0)
    construct_scores["BHP_score_by_item"] = construct_scores_by_item.get("BHP_score", 0.0)

    pei_score = construct_scores.get("PEI_score", 0.0)
    bhp_score = construct_scores.get("BHP_score", 0.0)

    # -------------------------------------------------------------------------
    # Step 5: Compute PEI × BHP framework (Section 4)
    # -------------------------------------------------------------------------
    load_framework = compute_framework(pei_score, bhp_score, threshold)

    # -------------------------------------------------------------------------
    # Step 6: Domain construct balance (Section 5)
    # -------------------------------------------------------------------------
    domain_construct_balance = compute_domain_construct_balance(scored_items)

    # -------------------------------------------------------------------------
    # Step 7: Build domain profiles (Section 5.12)
    # -------------------------------------------------------------------------
    domain_profiles = build_domain_profiles(domain_scores, domain_construct_balance)
    top_strengths = extract_strengths(domain_profiles)
    growth_edges = extract_growth_edges(domain_profiles)

    # -------------------------------------------------------------------------
    # Step 8: Build output JSON (Section 6)
    # -------------------------------------------------------------------------
    output = build_output(
        user_id=user_id,
        report_type=report_type,
        construct_scores=construct_scores,
        load_framework=load_framework,
        domain_profiles=domain_profiles,
        top_strengths=top_strengths,
        growth_edges=growth_edges,
        scored_items=scored_items,
        completion_rate=completion_rate,
        low_confidence=low_confidence,
        demographics=demographics,
        user_email=user_email,
    )

    # -------------------------------------------------------------------------
    # Step 9: Assign archetype
    # -------------------------------------------------------------------------
    archetype = assign_archetype(
        quadrant=load_framework["quadrant"],
        load_state=load_framework["load_state"],
        domain_profiles=domain_profiles,
    )
    output["archetype"] = archetype

    # -------------------------------------------------------------------------
    # Step 10: Generate AI interpretation (Section 7)
    # -------------------------------------------------------------------------
    if include_interpretation:
        if use_ai:
            # Phase 2: Use OpenAI for interpretation
            from scoring_engine.ai_service import generate_full_ai_interpretation
            interpretation = generate_full_ai_interpretation(output)
        else:
            # Phase 1: Use template-based interpretation
            interpretation = generate_full_interpretation(output)
        output["interpretation"] = interpretation

    logger.info(
        f"Assessment complete: quadrant={load_framework['quadrant']}, "
        f"load_state={load_framework['load_state']}, "
        f"PEI={pei_score:.3f}, BHP={bhp_score:.3f}"
    )

    return output


def process_multi_lens(
    user_id: str,
    responses: list[dict],
    lenses: list[str] | None = None,
    items: list[dict] | None = None,
    demographics: dict | None = None,
    threshold: float | None = None,
) -> dict:
    """
    Process the same assessment data through multiple report lenses.
    Scoring is done ONCE — only interpretation changes per lens.

    Args:
        user_id: Unique user identifier
        responses: Raw responses
        lenses: List of report types (defaults to all 4 lenses)
        items: Custom item dictionary
        demographics: Optional demographic metadata
        threshold: Custom quadrant threshold

    Returns:
        {"reports": {lens: output_json, ...}}
    """
    if lenses is None:
        lenses = REPORT_LENSES

    results = {}
    for lens in lenses:
        results[lens] = process_assessment(
            user_id=user_id,
            report_type=lens,
            responses=responses,
            items=items,
            demographics=demographics,
            threshold=threshold,
            include_interpretation=True,
        )

    return {"reports": results}
