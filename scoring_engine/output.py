"""
Output Structure — JSON Schema for Scoring & Reporting (Section 6)
Produces the standardized output that serves as the SINGLE SOURCE OF TRUTH
for all downstream systems: reports, visualization, AI interpretation, storage.

This is the CONTRACT LAYER of the system.
All upstream logic resolves INTO this structure.
All downstream systems READ from this structure.
"""

import logging
from datetime import datetime, timezone
from scoring_engine.config import (
    SYSTEM_ID,
    OUTPUT_PRECISION,
)
from scoring_engine.framework import get_load_balance_status
from scoring_engine.interpretation import generate_lens_teasers

logger = logging.getLogger(__name__)


def build_output(
    user_id: str,
    report_type: str,
    construct_scores: dict,
    load_framework: dict,
    domain_profiles: list[dict],
    top_strengths: list[str],
    growth_edges: list[str],
    scored_items: list[dict],
    completion_rate: float,
    low_confidence: bool,
    demographics: dict | None = None,
    user_email: str | None = None,
) -> dict:
    """
    Section 6.3: Build the complete Master Output JSON.

    Six core layers:
      1. Metadata
      2. Construct Scores (PEI & BHP)
      3. Load Framework (Quadrant + State)
      4. Domain Profiles
      5. Summary Indicators (Strengths, Growth Edges)
      6. Item-Level Data (recommended for debugging / analytics)
    """

    # Round all numeric values at final output stage (Section 3.14 / 6.10)
    rounded_construct = {
        "PEI_score": round(construct_scores.get("PEI_score", 0), OUTPUT_PRECISION),
        "BHP_score": round(construct_scores.get("BHP_score", 0), OUTPUT_PRECISION),
    }
    # Include legacy per-item construct scores for transparency
    if "PEI_score_by_item" in construct_scores:
        rounded_construct["PEI_score_by_item"] = round(
            construct_scores["PEI_score_by_item"], OUTPUT_PRECISION
        )
    if "BHP_score_by_item" in construct_scores:
        rounded_construct["BHP_score_by_item"] = round(
            construct_scores["BHP_score_by_item"], OUTPUT_PRECISION
        )

    rounded_framework = {
        "quadrant": load_framework["quadrant"],
        "load_balance": round(load_framework["load_balance"], OUTPUT_PRECISION),
        "load_state": load_framework["load_state"],
        "load_ratio": (
            round(load_framework["load_ratio"], OUTPUT_PRECISION)
            if load_framework.get("load_ratio") is not None
            else None
        ),
        "coordinates": {
            "x": round(load_framework["coordinates"]["x"], OUTPUT_PRECISION),
            "y": round(load_framework["coordinates"]["y"], OUTPUT_PRECISION),
        },
    }

    rounded_domains = []
    for dp in domain_profiles:
        entry = {
            "name": dp["name"],
            "score": round(dp["score"], OUTPUT_PRECISION),
            "classification": dp["classification"],
            "rank": dp["rank"],
            "aims_priority": dp["aims_priority"],
        }
        if "construct_balance" in dp:
            cb = dp["construct_balance"]
            entry["construct_balance"] = {
                "PEI": round(cb["PEI"], OUTPUT_PRECISION) if cb.get("PEI") is not None else None,
                "BHP": round(cb["BHP"], OUTPUT_PRECISION) if cb.get("BHP") is not None else None,
                "interpretation": cb.get("interpretation", "N/A"),
            }
        rounded_domains.append(entry)

    rounded_items = []
    for item in scored_items:
        rounded_items.append({
            "item_id": item["item_id"],
            "domain": item["domain"],
            "subdomain": item["subdomain"],
            "construct": item["construct"],
            "raw_response": item["raw_response"],
            "direction": item["direction"],
            "adjusted_score": round(item["adjusted_score"], OUTPUT_PRECISION),
            "weighted_score": round(item["weighted_score"], OUTPUT_PRECISION),
            "normalized_score": round(item["normalized_score"], OUTPUT_PRECISION),
        })

    output = {
        "metadata": {
            "assessment_id": SYSTEM_ID,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report_type": report_type,
            "completion_rate": round(completion_rate, OUTPUT_PRECISION),
            "low_confidence": low_confidence,
        },
        "construct_scores": rounded_construct,
        "load_framework": rounded_framework,
        "domains": rounded_domains,
        "summary": {
            "top_strengths": top_strengths,
            "growth_edges": growth_edges,
        },
        "items": rounded_items,
    }

    if user_email is not None:
        output["metadata"]["user_email"] = user_email
    
    if demographics is not None:
        output["metadata"]["demographics"] = demographics

    logger.info(
        f"Output generated: user={user_id}, report_type={report_type}, "
        f"quadrant={rounded_framework['quadrant']}, "
        f"domains={len(rounded_domains)}, items={len(rounded_items)}"
    )

    return output


# =============================================================================
# SCORECARD OUTPUT (FREE Tier — Phase 1 Final)
# =============================================================================
# Maps 7 backend domains into 4 visual "constellation" groups for the ScoreCard.
# =============================================================================

SCORECARD_DOMAIN_GROUPS = {
    "Executive Skills & Behavior": [
        "EXECUTIVE_FUNCTION_SKILLS",
        "BEHAVIORAL_PATTERNS",
    ],
    "Cognitive & Motivational Systems": [
        "COGNITIVE_CONTROL",
        "MOTIVATIONAL_SYSTEMS",
    ],
    "Emotional & Internal State": [
        "EMOTIONAL_REGULATION",
        "INTERNAL_STATE_FACTORS",
    ],
    "Environmental Demands": [
        "ENVIRONMENTAL_DEMANDS",
    ],
}


def _group_domain_scores(domain_profiles: list[dict]) -> list[dict]:
    """
    Consolidate 7 domains into 4 core groups for the ScoreCard constellation.
    Returns a list of 4 groups with averaged scores.
    """
    profile_lookup = {p["name"]: p["score"] for p in domain_profiles}
    groups = []
    for group_name, domains in SCORECARD_DOMAIN_GROUPS.items():
        scores = [profile_lookup[d] for d in domains if d in profile_lookup]
        avg_score = round(sum(scores) / len(scores), OUTPUT_PRECISION) if scores else 0.0
        groups.append({
            "name": group_name,
            "score": avg_score,
            "percentage": int(avg_score * 100),
        })
    return groups


def build_scorecard_output(full_output: dict) -> dict:
    """
    Build the FREE ScoreCard output from the full assessment output.
    
    Includes:
      1. Galaxy Snapshot Header (archetype name + tagline)
      2. EF Constellation (4 core domain groups)
      3. Load Balance Snapshot (simple status)
      4. Top 2 Strengths + Top 2 Growth Edges
      5. Four Lens Teaser Paragraphs
      6. Locked feature list
    
    Excludes: Full domain breakdown, item scores, AIMS plan, AI narratives.
    """
    quadrant = full_output["load_framework"]["quadrant"]
    load_balance = full_output["load_framework"]["load_balance"]
    archetype = full_output.get("archetype", {})
    domain_profiles = full_output["domains"]
    top_strengths = full_output["summary"]["top_strengths"]
    growth_edges = full_output["summary"]["growth_edges"]

    # 1. Galaxy Snapshot Header
    archetype_name = archetype.get("archetype_id", "Unknown").replace("_", " ")
    archetype_desc = archetype.get("description", "")

    # 2. EF Constellation (4 core groups)
    constellation = _group_domain_scores(domain_profiles)

    # 3. Load Balance Snapshot
    load_status = get_load_balance_status(load_balance)

    # 4. Top 2 strengths + Top 2 growth edges (names only)
    display_strengths = [s.replace("_", " ").title() for s in top_strengths[:2]]
    display_edges = [e.replace("_", " ").title() for e in growth_edges[:2]]

    # 5. Four Lens Teasers
    lens_teasers = generate_lens_teasers(quadrant)

    # 6. Locked features list
    locked_features = [
        {
            "name": "Full Archetype Profile",
            "message": "Your full pattern is ready to be revealed.",
        },
        {
            "name": "Deep Load Analysis",
            "message": "Your PEI × BHP breakdown has been calculated.",
        },
        {
            "name": "Domain-by-Domain Scoring",
            "message": "Your 7-domain detailed analysis is prepared.",
        },
        {
            "name": "AIMS for the BEST™ Intervention Plan",
            "message": "Your AIMS plan is prepared based on your responses.",
        },
        {
            "name": "AI Narrative Report",
            "message": "Unlock your full Galaxy Report to see how everything connects.",
        },
    ]

    return {
        "tier": "free",
        "metadata": full_output["metadata"],
        "galaxy_snapshot": {
            "archetype_name": archetype_name,
            "tagline": archetype_desc,
        },
        "constellation": constellation,
        "load_balance": {
            "status": load_status,
            "message": "Your environment and internal capacity are interacting in important ways...",
        },
        "strengths": display_strengths,
        "growth_edges": display_edges,
        "lens_teasers": {
            "PERSONAL_LIFESTYLE": {
                "title": "Personal / Lifestyle",
                "teaser": lens_teasers["PERSONAL_LIFESTYLE"],
            },
            "STUDENT_SUCCESS": {
                "title": "Student Success",
                "teaser": lens_teasers["STUDENT_SUCCESS"],
            },
            "PROFESSIONAL_LEADERSHIP": {
                "title": "Professional / Leadership",
                "teaser": lens_teasers["PROFESSIONAL_LEADERSHIP"],
            },
            "FAMILY_ECOSYSTEM": {
                "title": "Family / Ecosystem",
                "teaser": lens_teasers["FAMILY_ECOSYSTEM"],
            },
        },
        "locked_features": locked_features,
    }
