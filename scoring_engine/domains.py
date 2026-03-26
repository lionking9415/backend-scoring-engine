"""
Domain Aggregation Rules (Section 5)
Transforms normalized scores into interpretable behavioral patterns:
  - Domain classification (Strength / Developed / Emerging / Growth Edge)
  - Domain ranking
  - Strength & growth edge identification
  - Domain-to-AIMS mapping
"""

import logging
from scoring_engine.config import (
    DOMAIN_CLASSIFICATIONS,
    AIMS_PRIORITY_MAP,
    TOP_STRENGTHS_COUNT,
    GROWTH_EDGES_COUNT,
    INTERNAL_PRECISION,
)

logger = logging.getLogger(__name__)


def classify_domain_score(score: float) -> str:
    """
    Section 5.4: Map a domain score to a performance band.
    0.80–1.00 → Strength
    0.60–0.79 → Developed
    0.40–0.59 → Emerging
    0.00–0.39 → Growth_Edge
    """
    for band in DOMAIN_CLASSIFICATIONS:
        if band["min"] <= score <= band["max"]:
            return band["label"]
    # Fallback
    if score >= 0.80:
        return "Strength"
    return "Growth_Edge"


def get_aims_priority(classification: str) -> str:
    """
    Section 5.13: Map domain classification to AIMS intervention priority.
    """
    return AIMS_PRIORITY_MAP.get(classification, "Unknown")


def build_domain_profiles(domain_scores: dict[str, float],
                          domain_construct_balance: dict[str, dict] | None = None
                          ) -> list[dict]:
    """
    Section 5.12: Build composite domain profiles.
    Each domain produces: name, score, classification, rank, construct_balance, aims_priority

    Args:
        domain_scores: {domain_name: score}
        domain_construct_balance: {domain_name: {PEI: x, BHP: y, interpretation: str}}

    Returns:
        Sorted list of domain profile dicts (highest score first).
    """
    profiles = []

    for domain, score in domain_scores.items():
        classification = classify_domain_score(score)
        profile = {
            "name": domain,
            "score": round(score, INTERNAL_PRECISION),
            "classification": classification,
            "aims_priority": get_aims_priority(classification),
        }

        if domain_construct_balance and domain in domain_construct_balance:
            profile["construct_balance"] = domain_construct_balance[domain]

        profiles.append(profile)

    # Section 5.7: Rank domains from highest to lowest
    profiles.sort(key=lambda p: p["score"], reverse=True)
    for rank, profile in enumerate(profiles, start=1):
        profile["rank"] = rank

    return profiles


def extract_strengths(domain_profiles: list[dict],
                      count: int | None = None) -> list[str]:
    """
    Section 5.5 / 5.8: Extract top strength domains.
    Returns domain names of the top N highest-scoring domains.
    """
    if count is None:
        count = TOP_STRENGTHS_COUNT
    return [p["name"] for p in domain_profiles[:count]]


def extract_growth_edges(domain_profiles: list[dict],
                         count: int | None = None) -> list[str]:
    """
    Section 5.6 / 5.8: Extract bottom growth edge domains.
    Returns domain names of the bottom N lowest-scoring domains.
    """
    if count is None:
        count = GROWTH_EDGES_COUNT
    return [p["name"] for p in domain_profiles[-count:]]
