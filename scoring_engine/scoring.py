"""
Scoring Logic (Section 3)
Full transformation pipeline:
  Raw Response → Direction Adjustment → Weighted Score →
  Normalization → Domain Aggregation → Construct Aggregation → Final Output

All calculations are deterministic. No rounding until final output stage.
"""

import logging
from scoring_engine.config import INTERNAL_PRECISION, DOMAIN_INDEX_WEIGHTS
from scoring_engine.item_dictionary import ITEM_DICTIONARY

logger = logging.getLogger(__name__)


def adjust_for_direction(raw_response: float, direction: str,
                         min_score: float, max_score: float) -> float:
    """
    Section 3.4: Direction Adjustment (Reverse Scoring)
    If forward → adjusted_score = raw_response
    If reverse → adjusted_score = (max_score + min_score) - raw_response
    """
    if direction == "reverse":
        return (max_score + min_score) - raw_response
    return raw_response


def apply_weight(adjusted_score: float, weight: float) -> float:
    """
    Section 3.5: Weight Application
    weighted_score = adjusted_score × weight
    """
    return adjusted_score * weight


def normalize_score(weighted_score: float, min_score: float, max_score: float) -> float:
    """
    Section 3.6: Normalization for cross-scale consistency
    normalized_score = (weighted_score - min_score) / (max_score - min_score)
    Output range: 0.0 → 1.0

    Prevents division by zero if min == max.
    """
    denominator = max_score - min_score
    if denominator == 0:
        logger.warning("Normalization: min_score == max_score, returning 0.0")
        return 0.0
    result = (weighted_score - min_score) / denominator
    # Clamp to [0, 1] as a safeguard
    return max(0.0, min(1.0, result))


def score_single_item(raw_response: float, item_def: dict) -> dict:
    """
    Process a single item through the full scoring pipeline (Section 3.12).

    Returns a traceable scoring record:
      raw → adjusted → weighted → normalized
    """
    direction = item_def["direction"]
    weight = item_def["weight"]
    min_s = item_def["min_score"]
    max_s = item_def["max_score"]

    adjusted = adjust_for_direction(raw_response, direction, min_s, max_s)
    weighted = apply_weight(adjusted, weight)
    normalized = normalize_score(weighted, min_s, max_s)

    return {
        "item_id": item_def["item_id"],
        "domain": item_def["domain"],
        "subdomain": item_def["subdomain"],
        "construct": item_def["construct"],
        "raw_response": raw_response,
        "direction": direction,
        "adjusted_score": round(adjusted, INTERNAL_PRECISION),
        "weight": weight,
        "weighted_score": round(weighted, INTERNAL_PRECISION),
        "normalized_score": round(normalized, INTERNAL_PRECISION),
    }


def score_all_items(validated_responses: list[dict],
                    items: list[dict] | None = None) -> list[dict]:
    """
    Score all validated responses through the item-level pipeline.

    Args:
        validated_responses: list of {"item_id": str, "response": number}
        items: item dictionary (defaults to ITEM_DICTIONARY)

    Returns:
        list of scored item records
    """
    if items is None:
        items = ITEM_DICTIONARY

    item_lookup = {item["item_id"]: item for item in items}
    scored_items = []

    for resp in validated_responses:
        item_id = resp["item_id"]
        raw = resp["response"]

        item_def = item_lookup.get(item_id)
        if item_def is None:
            logger.error(f"Item {item_id} not found in dictionary — skipping")
            continue

        scored = score_single_item(raw, item_def)
        scored_items.append(scored)

    logger.info(f"Scored {len(scored_items)} items")
    return scored_items


def aggregate_by_domain(scored_items: list[dict]) -> dict[str, float]:
    """
    Section 3.7 / 5.2: Domain Aggregation
    domain_score = average(normalized_scores for all items in domain)
    """
    domain_scores: dict[str, list[float]] = {}

    for item in scored_items:
        domain = item["domain"]
        if domain not in domain_scores:
            domain_scores[domain] = []
        domain_scores[domain].append(item["normalized_score"])

    result = {}
    for domain, scores in domain_scores.items():
        if len(scores) > 0:
            result[domain] = round(sum(scores) / len(scores), INTERNAL_PRECISION)
        else:
            logger.warning(f"Domain '{domain}' has 0 items — excluded")

    return result


def aggregate_by_subdomain(scored_items: list[dict]) -> dict[str, dict[str, float]]:
    """
    Section 5.3: Subdomain Aggregation
    Subdomains roll up INTO domains.
    """
    subdomain_scores: dict[str, dict[str, list[float]]] = {}

    for item in scored_items:
        domain = item["domain"]
        subdomain = item["subdomain"]
        if domain not in subdomain_scores:
            subdomain_scores[domain] = {}
        if subdomain not in subdomain_scores[domain]:
            subdomain_scores[domain][subdomain] = []
        subdomain_scores[domain][subdomain].append(item["normalized_score"])

    result = {}
    for domain, subs in subdomain_scores.items():
        result[domain] = {}
        for sub, scores in subs.items():
            if len(scores) > 0:
                result[domain][sub] = round(sum(scores) / len(scores), INTERNAL_PRECISION)

    return result


def aggregate_by_construct(scored_items: list[dict]) -> dict[str, float]:
    """
    Section 3.8: Construct Aggregation (PEI vs BHP)
    PEI_score = average(normalized_scores of all PEI items)
    BHP_score = average(normalized_scores of all BHP items)
    """
    construct_scores: dict[str, list[float]] = {"PEI": [], "BHP": []}

    for item in scored_items:
        construct = item["construct"]
        construct_scores[construct].append(item["normalized_score"])

    result = {}
    for construct, scores in construct_scores.items():
        if len(scores) > 0:
            result[f"{construct}_score"] = round(
                sum(scores) / len(scores), INTERNAL_PRECISION
            )
        else:
            result[f"{construct}_score"] = 0.0
            logger.warning(f"Construct '{construct}' has 0 scored items")

    return result


def aggregate_indices_by_domain_weights(
    domain_scores: dict[str, float],
    weight_matrix: dict[str, dict[str, float]] | None = None,
) -> dict[str, float]:
    """
    Compute PEI and BHP index scores using the overlapping domain weight matrix.

    This is the KEY architectural feature: a single domain can contribute to
    BOTH indices with DIFFERENT weights. The weight matrix lives in config.py
    so it can be changed without touching scoring logic.

    Formula per index:
        index_score = sum(domain_score * domain_weight) / sum(domain_weight)
        (weighted average across all contributing domains)

    Args:
        domain_scores: {domain_name: normalized_score}
        weight_matrix: {domain_name: {"PEI": weight, "BHP": weight}}
                       Defaults to DOMAIN_INDEX_WEIGHTS from config.

    Returns:
        {"PEI_score": float, "BHP_score": float}
    """
    if weight_matrix is None:
        weight_matrix = DOMAIN_INDEX_WEIGHTS

    index_totals = {"PEI": 0.0, "BHP": 0.0}
    weight_totals = {"PEI": 0.0, "BHP": 0.0}

    for domain, score in domain_scores.items():
        weights = weight_matrix.get(domain, {"PEI": 0.0, "BHP": 0.0})

        for index_name in ("PEI", "BHP"):
            w = weights.get(index_name, 0.0)
            if w > 0:
                index_totals[index_name] += score * w
                weight_totals[index_name] += w

    result = {}
    for index_name in ("PEI", "BHP"):
        if weight_totals[index_name] > 0:
            result[f"{index_name}_score"] = round(
                index_totals[index_name] / weight_totals[index_name],
                INTERNAL_PRECISION,
            )
        else:
            result[f"{index_name}_score"] = 0.0
            logger.warning(f"Index '{index_name}' has 0 total weight — no contributing domains")

    return result


def compute_domain_construct_balance(scored_items: list[dict]) -> dict[str, dict]:
    """
    Section 5.9: Domain–Construct Interaction Mapping
    For each domain, compute the PEI and BHP component scores separately.
    """
    domain_construct: dict[str, dict[str, list[float]]] = {}

    for item in scored_items:
        domain = item["domain"]
        construct = item["construct"]
        if domain not in domain_construct:
            domain_construct[domain] = {"PEI": [], "BHP": []}
        domain_construct[domain][construct].append(item["normalized_score"])

    result = {}
    for domain, constructs in domain_construct.items():
        pei_scores = constructs["PEI"]
        bhp_scores = constructs["BHP"]

        pei_avg = round(sum(pei_scores) / len(pei_scores), INTERNAL_PRECISION) if pei_scores else None
        bhp_avg = round(sum(bhp_scores) / len(bhp_scores), INTERNAL_PRECISION) if bhp_scores else None

        # Section 5.10: Domain Load Interpretation
        interpretation = "N/A"
        if pei_avg is not None and bhp_avg is not None:
            if pei_avg > bhp_avg:
                interpretation = "Environment-driven strain"
            elif bhp_avg > pei_avg:
                interpretation = "Capacity-driven pattern"
            else:
                interpretation = "Balanced domain"
        elif pei_avg is not None:
            interpretation = "PEI-only domain"
        elif bhp_avg is not None:
            interpretation = "BHP-only domain"

        result[domain] = {
            "PEI": pei_avg,
            "BHP": bhp_avg,
            "interpretation": interpretation,
        }

    return result
