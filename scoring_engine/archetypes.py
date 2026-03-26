"""
Archetype Assignment Engine (Phase 1 Stub — Full logic in Phase 2)
Maps assessment results to one of 16 predefined archetypes based on:
  - Quadrant placement (primary)
  - Load state (secondary)
  - Domain patterns (tertiary — Phase 2 refinement)

Dr. Crump's system defines 16 archetypes generated from assessment answers.
This module provides the structural foundation for assignment.
"""

import logging
from scoring_engine.config import ARCHETYPE_DEFINITIONS

logger = logging.getLogger(__name__)


def assign_archetype(
    quadrant: str,
    load_state: str,
    domain_profiles: list[dict] | None = None,
    archetype_defs: dict | None = None,
) -> dict:
    """
    Assign an archetype based on quadrant and load state.

    Phase 1: Matches on quadrant + load_state.
    Phase 2: Will incorporate domain pattern matching for finer resolution.

    Args:
        quadrant: e.g. "Q1_Aligned_Flow"
        load_state: e.g. "Surplus_Capacity"
        domain_profiles: Sorted domain profiles (for future Phase 2 refinement)
        archetype_defs: Custom archetype definitions (defaults to config)

    Returns:
        {
            "archetype_id": str,
            "description": str,
            "quadrant": str,
            "load_state": str,
            "confidence": str  # "exact" | "quadrant_match" | "fallback"
        }
    """
    if archetype_defs is None:
        archetype_defs = ARCHETYPE_DEFINITIONS

    # Phase 1: Exact match on quadrant + load_state
    for arch_id, arch_def in archetype_defs.items():
        if arch_def["quadrant"] == quadrant and arch_def["load_state"] == load_state:
            logger.info(f"Archetype assigned (exact): {arch_id}")
            return {
                "archetype_id": arch_id,
                "description": arch_def["description"],
                "quadrant": arch_def["quadrant"],
                "load_state": arch_def["load_state"],
                "confidence": "exact",
            }

    # Fallback: Match on quadrant only, pick first match
    for arch_id, arch_def in archetype_defs.items():
        if arch_def["quadrant"] == quadrant:
            logger.info(f"Archetype assigned (quadrant_match): {arch_id}")
            return {
                "archetype_id": arch_id,
                "description": arch_def["description"],
                "quadrant": arch_def["quadrant"],
                "load_state": arch_def["load_state"],
                "confidence": "quadrant_match",
            }

    # Final fallback — should never happen with complete config
    logger.warning(f"No archetype found for quadrant={quadrant}, load_state={load_state}")
    return {
        "archetype_id": "UNASSIGNED",
        "description": "Archetype could not be determined from current scores.",
        "quadrant": quadrant,
        "load_state": load_state,
        "confidence": "fallback",
    }


def get_archetype_by_id(archetype_id: str,
                        archetype_defs: dict | None = None) -> dict | None:
    """Look up an archetype definition by its ID."""
    if archetype_defs is None:
        archetype_defs = ARCHETYPE_DEFINITIONS
    return archetype_defs.get(archetype_id)


def list_archetypes_for_quadrant(quadrant: str,
                                 archetype_defs: dict | None = None) -> list[dict]:
    """Return all archetypes that belong to a given quadrant."""
    if archetype_defs is None:
        archetype_defs = ARCHETYPE_DEFINITIONS
    return [
        {"archetype_id": k, **v}
        for k, v in archetype_defs.items()
        if v["quadrant"] == quadrant
    ]
