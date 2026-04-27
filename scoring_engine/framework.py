"""
PEI × BHP Framework — Load Interaction Model (Section 4)
Translates aggregated construct scores into:
  - Quadrant classification
  - Load balance
  - Load state
  - Coordinates for visualization
"""

import logging
from scoring_engine.config import (
    QUADRANT_THRESHOLD,
    LOAD_STATES,
    INTERNAL_PRECISION,
)

logger = logging.getLogger(__name__)


def assign_quadrant(pei_score: float, bhp_score: float,
                    threshold: float | None = None) -> str:
    """
    Section 4.6: Quadrant Assignment Logic
    Uses configurable threshold (default 0.50).

    Q1: Aligned Flow      — High BHP, Low PEI
    Q2: Capacity Strain   — High BHP, High PEI
    Q3: Overload          — Low BHP, High PEI
    Q4: Underutilized     — Low BHP, Low PEI
    """
    if threshold is None:
        threshold = QUADRANT_THRESHOLD

    bhp_high = bhp_score >= threshold
    pei_high = pei_score >= threshold

    if bhp_high and not pei_high:
        return "Q1_Aligned_Flow"
    elif bhp_high and pei_high:
        return "Q2_Capacity_Strain"
    elif not bhp_high and pei_high:
        return "Q3_Overload"
    else:
        return "Q4_Underutilized"


def compute_load_balance(pei_score: float, bhp_score: float) -> float:
    """
    Section 3.9 / 4.7: Load Difference
    load_balance = BHP_score - PEI_score

    Positive → Capacity exceeds demand
    Negative → Demand exceeds capacity
    Near zero → Balanced
    """
    return round(bhp_score - pei_score, INTERNAL_PRECISION)


def compute_load_ratio(pei_score: float, bhp_score: float) -> float | None:
    """
    Section 3.10: Optional Load Ratio (Advanced Insight)
    load_ratio = BHP_score / PEI_score
    Returns None if PEI is zero (prevent division by zero).
    """
    if pei_score == 0:
        logger.warning("PEI_score is 0 — cannot compute load ratio")
        return None
    return round(bhp_score / pei_score, INTERNAL_PRECISION)


def assign_load_state(load_balance: float) -> str:
    """
    Section 4.8: Load State Classification (Secondary Layer)
    Maps load_balance to a severity/intensity label.

    +0.20 or higher  → Surplus_Capacity
    +0.05 to +0.19   → Stable_Capacity
    -0.04 to +0.04   → Balanced_Load
    -0.05 to -0.19   → Emerging_Strain
    -0.20 or lower   → Critical_Overload
    """
    for state in LOAD_STATES:
        if state["min"] <= load_balance <= state["max"]:
            return state["label"]

    # Fallback (should never reach here with proper config)
    logger.error(f"Could not classify load_balance={load_balance} into any state")
    return "Unknown"


def get_load_balance_status(load_balance: float) -> str:
    """
    Simplified load balance label for the FREE ScoreCard.

    Maps the technical 5-band load_state to plain-language labels per
    `docs/🌌 Phase 1-Final Steps.md` §Load Balance Snapshot. We preserve the
    Surplus signal as a separate label (rather than collapsing it into
    "Balanced") so users with strong capacity reserves see a positive
    descriptor instead of a neutral one.

    Bands (load_balance = BHP - PEI):
      ≥ +0.20            → "Surplus Capacity"
      +0.05 .. +0.19      → "Balanced"
      -0.04 ..  +0.04     → "Balanced"
      -0.19 ..  -0.05     → "Slightly Imbalanced"
      ≤ -0.20            → "High Load Strain"
    """
    if load_balance >= 0.20:
        return "Surplus Capacity"
    if load_balance >= -0.04:
        # Covers Stable_Capacity (+0.05..+0.19) and Balanced_Load (-0.04..+0.04)
        return "Balanced"
    if load_balance >= -0.19:
        return "Slightly Imbalanced"
    return "High Load Strain"


def compute_framework(pei_score: float, bhp_score: float,
                      threshold: float | None = None) -> dict:
    """
    Full PEI × BHP framework computation (Section 4.14).
    Returns the complete framework output object.
    """
    quadrant = assign_quadrant(pei_score, bhp_score, threshold)
    load_balance = compute_load_balance(pei_score, bhp_score)
    load_state = assign_load_state(load_balance)
    load_ratio = compute_load_ratio(pei_score, bhp_score)

    return {
        "PEI_score": round(pei_score, INTERNAL_PRECISION),
        "BHP_score": round(bhp_score, INTERNAL_PRECISION),
        "quadrant": quadrant,
        "load_balance": load_balance,
        "load_state": load_state,
        "load_ratio": load_ratio,
        "coordinates": {
            "x": round(pei_score, INTERNAL_PRECISION),
            "y": round(bhp_score, INTERNAL_PRECISION),
        },
    }
