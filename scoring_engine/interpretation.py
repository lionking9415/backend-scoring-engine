"""
AI Interpretation Layer — Narrative & Personalization Engine (Section 7)
Translates structured scoring output into human-readable, actionable insights.

This layer does NOT change scores. It INTERPRETS them.
Scoring Engine → produces DATA
AI Layer → produces MEANING

All narratives follow the hierarchy (non-negotiable):
  1. Quadrant (identity state)
  2. Load State (pressure level)
  3. Domain Patterns (strengths + growth edges)
  4. Construct Interaction (PEI vs BHP meaning)
  5. AIMS Intervention Pathway

Tone & Ethics:
  - Non-pathologizing
  - Strength-based
  - Avoids "deficit", "disorder", "failure"
  - Emphasizes capacity, growth, alignment
"""

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# QUADRANT NARRATIVE TEMPLATES (Section 7.5)
# =============================================================================

QUADRANT_NARRATIVES = {
    "Q1_Aligned_Flow": {
        "tone": "Empowered, stable, optimized",
        "PERSONAL_LIFESTYLE": (
            "You are currently operating in a state of aligned flow. "
            "Your internal capacity is strong, and the demands in your personal "
            "environment are manageable. This is a position of strength — your "
            "executive functioning skills are well-matched to your current lifestyle demands."
        ),
        "STUDENT_SUCCESS": (
            "You are currently operating in a state of aligned flow within your academic environment. "
            "Your internal capacity is strong, and the demands of your learning environment "
            "are manageable. This is a position of academic strength — your executive functioning "
            "skills are well-matched to your current educational demands."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "You are currently operating in a state of aligned flow within your professional environment. "
            "Your internal capacity is strong, and workplace demands are within your range. "
            "This is a position of leadership strength — your executive functioning skills "
            "support effective performance and decision-making."
        ),
        "FAMILY_ECOSYSTEM": (
            "You are currently operating in a state of aligned flow within your family system. "
            "Your internal capacity is strong, and family-related demands are manageable. "
            "This is a position of family stability — your executive functioning skills "
            "support healthy engagement with your family ecosystem."
        ),
    },
    "Q2_Capacity_Strain": {
        "tone": "Capable but stretched",
        "PERSONAL_LIFESTYLE": (
            "You demonstrate strong internal capacity, yet your personal environment "
            "is placing significant demands on your system. You are capable but stretched. "
            "Your executive functioning skills are active and engaged, but the volume of "
            "external pressure may be approaching your capacity limits."
        ),
        "STUDENT_SUCCESS": (
            "You demonstrate strong internal capacity, yet your academic environment "
            "is placing significant demands on your system. You are capable but stretched. "
            "Your study skills and cognitive abilities are active, but academic pressures "
            "may be approaching your capacity limits."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "You demonstrate strong internal capacity, yet your professional environment "
            "is placing significant demands on your system. You are capable but stretched. "
            "Your leadership skills are engaged, but workplace demands may be approaching "
            "your capacity limits."
        ),
        "FAMILY_ECOSYSTEM": (
            "You demonstrate strong internal capacity, yet your family environment "
            "is placing significant demands on your system. You are capable but stretched. "
            "Your family management skills are active, but household and relational demands "
            "may be approaching your capacity limits."
        ),
    },
    "Q3_Overload": {
        "tone": "Under pressure, support needed",
        "PERSONAL_LIFESTYLE": (
            "You are currently experiencing a state where environmental demands are exceeding "
            "your available capacity. This is not a reflection of your potential — it indicates "
            "that your system is under significant pressure and would benefit from targeted support "
            "to rebuild capacity and manage external load."
        ),
        "STUDENT_SUCCESS": (
            "You are currently experiencing a state where academic demands are exceeding "
            "your available capacity. This is not a reflection of your intelligence or potential — "
            "it indicates that your learning system is under significant pressure and would benefit "
            "from targeted support to strengthen executive functioning skills."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "You are currently experiencing a state where professional demands are exceeding "
            "your available capacity. This is not a reflection of your competence — it indicates "
            "that your system is under significant pressure and would benefit from strategic support "
            "to restore balance between workload and capacity."
        ),
        "FAMILY_ECOSYSTEM": (
            "You are currently experiencing a state where family demands are exceeding "
            "your available capacity. This is not a reflection of your commitment — it indicates "
            "that your family system is under significant pressure and would benefit from support "
            "to restore balance between family responsibilities and personal capacity."
        ),
    },
    "Q4_Underutilized": {
        "tone": "Untapped potential",
        "PERSONAL_LIFESTYLE": (
            "Your current profile suggests a state of low activation — both internal capacity "
            "and external demands are operating at reduced levels. This may indicate untapped "
            "potential waiting to be activated. With the right environmental cues and skill-building, "
            "your executive functioning system has significant room for growth."
        ),
        "STUDENT_SUCCESS": (
            "Your current profile suggests a state of low activation within your academic environment. "
            "Both internal capacity and learning demands are operating at reduced levels. "
            "This may indicate untapped academic potential. With the right engagement strategies "
            "and skill-building, your executive functioning system can be activated for growth."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "Your current profile suggests a state of low activation within your professional environment. "
            "Both internal capacity and workplace demands are operating at reduced levels. "
            "This may indicate untapped leadership potential. With the right challenges and support, "
            "your executive functioning system can be activated for professional growth."
        ),
        "FAMILY_ECOSYSTEM": (
            "Your current profile suggests a state of low activation within your family system. "
            "Both internal capacity and family demands are operating at reduced levels. "
            "This may indicate an opportunity for deeper engagement. With the right approach, "
            "your executive functioning system can support richer family dynamics."
        ),
    },
}

# =============================================================================
# LOAD STATE NARRATIVE TEMPLATES (Section 7.6)
# =============================================================================

LOAD_STATE_NARRATIVES = {
    "Surplus_Capacity": (
        "Your system currently has surplus capacity — your internal resources "
        "significantly exceed the demands placed on you. This is an optimal position "
        "for expansion, growth, and taking on new challenges."
    ),
    "Stable_Capacity": (
        "Your system is operating with stable capacity — your internal resources "
        "are comfortably managing current demands. This is a maintenance zone where "
        "you can sustain current performance while gradually building new skills."
    ),
    "Balanced_Load": (
        "Your system is in a balanced state — internal capacity and external demands "
        "are closely matched. This is a stability zone, but one where shifts in either "
        "direction could tip the balance."
    ),
    "Emerging_Strain": (
        "Your system is showing signs of emerging strain — external demands are beginning "
        "to outpace your available capacity. This is a caution zone where proactive "
        "adjustments can prevent further imbalance."
    ),
    "Critical_Overload": (
        "Your system is experiencing critical overload — external demands significantly "
        "exceed your available capacity. Immediate support and environmental adjustments "
        "are recommended to prevent further strain on your executive functioning."
    ),
}


# =============================================================================
# LENS TEASER TEMPLATES (FREE ScoreCard — Phase 1 Final)
# =============================================================================
# 2-3 sentence teasers per lens, adapted by quadrant.
# Purpose: Create emotional resonance + curiosity without explanation.
# =============================================================================

# New AIMS-integrated lens teaser copy (universal, not quadrant-specific)
LENS_TEASER_TEMPLATES = {
    "PERSONAL_LIFESTYLE": (
        "Understand how your executive functioning shows up in your daily life—from routines and "
        "organization to energy, consistency, and self-management. This report reveals how your internal "
        "capacity interacts with everyday demands and provides insight into how to create greater balance "
        "and personal effectiveness.\n\n"
        "Your personalized AIMS for the BEST™ Plan guides you through building awareness, implementing "
        "targeted strategies, strengthening key skills, and sustaining long-term improvements in your daily functioning."
    ),
    "STUDENT_SUCCESS": (
        "Explore how your executive functioning impacts learning, focus, organization, and academic performance. "
        "This report highlights how your brain responds to academic demands and provides insight into how to "
        "improve consistency, manage workload, and optimize performance in structured environments.\n\n"
        "Your AIMS for the BEST™ Plan provides a clear pathway to increase focus, strengthen study behaviors, "
        "and develop the executive skills needed for sustained academic success."
    ),
    "PROFESSIONAL_LEADERSHIP": (
        "Discover how your executive functioning influences productivity, decision-making, leadership, and "
        "performance under pressure. This report reveals how you manage professional demands and where strategic "
        "adjustments can enhance efficiency, clarity, and long-term success.\n\n"
        "Your AIMS for the BEST™ Plan delivers targeted strategies to improve execution, manage workload demands, "
        "and strengthen leadership effectiveness in high-performance environments."
    ),
    "FAMILY_ECOSYSTEM": (
        "Gain insight into how your executive functioning operates within your relationships and family environment. "
        "This report highlights patterns of interaction, responsiveness, and consistency, and provides guidance on "
        "how to create more balance and alignment within your ecosystem.\n\n"
        "Your AIMS for the BEST™ Plan helps you apply practical strategies to improve communication, increase "
        "consistency, and support healthier, more effective interactions within your family system."
    ),
}


def generate_lens_teasers(quadrant: str) -> dict:
    """
    Generate all 4 lens teaser paragraphs for the FREE ScoreCard.
    Now uses universal AIMS-integrated copy (not quadrant-specific).
    """
    return {
        "PERSONAL_LIFESTYLE": LENS_TEASER_TEMPLATES["PERSONAL_LIFESTYLE"],
        "STUDENT_SUCCESS": LENS_TEASER_TEMPLATES["STUDENT_SUCCESS"],
        "PROFESSIONAL_LEADERSHIP": LENS_TEASER_TEMPLATES["PROFESSIONAL_LEADERSHIP"],
        "FAMILY_ECOSYSTEM": LENS_TEASER_TEMPLATES["FAMILY_ECOSYSTEM"],
    }


def generate_quadrant_narrative(quadrant: str, report_type: str) -> str:
    """Generate the quadrant-specific narrative for the given report lens."""
    templates = QUADRANT_NARRATIVES.get(quadrant, {})
    narrative = templates.get(report_type)
    if narrative is None:
        # Fallback to generic
        narrative = templates.get("PERSONAL_LIFESTYLE",
                                  f"Your current quadrant is {quadrant}.")
    return narrative


def generate_load_narrative(load_state: str) -> str:
    """Generate the load state narrative."""
    return LOAD_STATE_NARRATIVES.get(
        load_state, f"Your current load state is {load_state}."
    )


def generate_strengths_narrative(top_strengths: list[str],
                                 domain_profiles: list[dict]) -> str:
    """
    Section 7.7: Highlight top strengths and explain how they support EF.
    Excludes ENVIRONMENTAL_DEMANDS (external pressure, not internal capacity).
    """
    if not top_strengths:
        return "No strength domains were identified in this assessment."

    strength_details = []
    profile_lookup = {p["name"]: p for p in domain_profiles}

    for name in top_strengths:
        if name == "ENVIRONMENTAL_DEMANDS":
            continue
        profile = profile_lookup.get(name)
        if profile:
            score_pct = int(profile["score"] * 100)
            strength_details.append(
                f"Your strength in {_display_domain(name)} (score: {score_pct}%) "
                f"provides a stabilizing anchor for your executive functioning system."
            )

    return " ".join(strength_details)


def generate_growth_edges_narrative(growth_edges: list[str],
                                    domain_profiles: list[dict]) -> str:
    """
    Section 7.7: Identify growth edges and explain why breakdown occurs.
    """
    if not growth_edges:
        return "No significant growth edges were identified in this assessment."

    edge_details = []
    profile_lookup = {p["name"]: p for p in domain_profiles}

    for name in growth_edges:
        profile = profile_lookup.get(name)
        if profile:
            score_pct = int(profile["score"] * 100)
            cb = profile.get("construct_balance", {})
            interp = cb.get("interpretation", "")

            detail = (
                f"Your {_display_domain(name)} domain (score: {score_pct}%) "
                f"represents an area where your system would benefit from targeted support."
            )
            if "Environment-driven" in interp:
                detail += (
                    " This challenge appears to be driven by environmental demands "
                    "rather than a lack of internal ability."
                )
            elif "Capacity-driven" in interp:
                detail += (
                    " This area reflects an opportunity to build internal capacity "
                    "and skill development."
                )
            edge_details.append(detail)

    return " ".join(edge_details)


def generate_construct_narrative(construct_scores: dict) -> str:
    """
    Section 7.8: PEI vs BHP interpretation — the KEY DIFFERENTIATOR.
    Explicitly interprets whether the issue is internal, external, or a mismatch.
    """
    pei = construct_scores.get("PEI_score", 0)
    bhp = construct_scores.get("BHP_score", 0)
    diff = bhp - pei

    if diff > 0.15:
        return (
            "Your internal capacity (BHP) significantly exceeds your environmental demands (PEI). "
            "Your system has strong resources available and is well-positioned to handle "
            "current pressures or take on new challenges."
        )
    elif diff > 0.05:
        return (
            "Your internal capacity (BHP) slightly exceeds your environmental demands (PEI). "
            "Your system is managing well, with a modest buffer of available capacity."
        )
    elif diff > -0.05:
        return (
            "Your internal capacity (BHP) and environmental demands (PEI) are closely matched. "
            "Your system is in a state of balance, but shifts in either direction could "
            "impact your executive functioning performance."
        )
    elif diff > -0.15:
        return (
            "Your environmental demands (PEI) are beginning to exceed your internal capacity (BHP). "
            "Your challenges are not due to a lack of ability, but rather the level of "
            "environmental demand approaching your current capacity limits."
        )
    else:
        return (
            "Your environmental demands (PEI) significantly exceed your internal capacity (BHP). "
            "Your system is under considerable pressure. Your challenges are driven by the weight "
            "of external demands, not by a lack of capability. Targeted support to either reduce "
            "environmental load or build internal capacity is recommended."
        )


def generate_aims_plan(domain_profiles: list[dict]) -> dict:
    """
    Section 7.10–7.11: AIMS for the BEST™ Intervention Mapping.
    Maps assessment results into the four AIMS phases.
    Environmental Demands is excluded from Sustain (it represents external
    pressure, not internal capacity) and is addressed in Awareness/Intervention.
    Order: Awareness → Intervention → Mastery → Sustain.
    """
    # Separate Environmental Demands from capacity domains
    env_domains = [p for p in domain_profiles if p["name"] == "ENVIRONMENTAL_DEMANDS"]
    capacity_profiles = [p for p in domain_profiles if p["name"] != "ENVIRONMENTAL_DEMANDS"]

    growth_domains = [p for p in capacity_profiles if p["classification"] == "Growth_Edge"]
    emerging_domains = [p for p in capacity_profiles if p["classification"] == "Emerging"]
    developed_domains = [p for p in capacity_profiles if p["classification"] == "Developed"]
    strength_domains = [p for p in capacity_profiles if p["classification"] == "Strength"]

    def _domain_list(profiles):
        return ", ".join(_display_domain(p["name"]) for p in profiles) if profiles else "none identified"

    # Check if environmental load is high
    env_score = env_domains[0]["score"] if env_domains else 0
    env_note = ""
    if env_score >= 0.7:
        env_note = (
            " Recognizing where external demands are placing pressure on your system "
            "is the first step toward meaningful change and more effective self-regulation."
        )

    awareness = (
        f"Begin by building awareness of how your internal capacity is interacting "
        f"with your current level of environmental load."
        f"{env_note}"
    )

    env_intervention = ""
    if env_score >= 0.7:
        env_intervention = (
            " In addition, adjustments to your environment may be necessary to reduce "
            "excessive load and support your system more effectively."
        )

    intervention = (
        f"Targeted skill-building is recommended for: {_domain_list(emerging_domains + growth_domains)}. "
        f"These areas will benefit from structured practice to improve consistency "
        f"and cognitive flexibility."
        f"{env_intervention}"
    )

    mastery = (
        f"Continue strengthening and integrating skills in: {_domain_list(developed_domains)}. "
        f"These domains are functional and can be further optimized through consistent practice, "
        f"allowing your system to perform more efficiently under varying levels of demand."
    )

    sustain = (
        f"Sustain and generalize your strengths in: {_domain_list(strength_domains)}. "
        f"These domains serve as stabilizing anchors for your system and can help "
        f"maintain balance, especially when external pressures increase."
    )

    return {
        "awareness": awareness,
        "intervention": intervention,
        "mastery": mastery,
        "sustain": sustain,
    }


def generate_executive_summary(quadrant: str, load_state: str,
                               top_strengths: list[str],
                               growth_edges: list[str],
                               report_type: str) -> str:
    """Generate a concise executive summary combining key findings.
    Uses generic 'assessment results' language for broader applicability.
    Excludes ENVIRONMENTAL_DEMANDS from strengths display."""
    quadrant_label = quadrant.replace("_", " ").replace("Q1 ", "").replace("Q2 ", "").replace("Q3 ", "").replace("Q4 ", "")
    capacity_strengths = [s for s in top_strengths if s != "ENVIRONMENTAL_DEMANDS"]
    strengths_str = ", ".join(_display_domain(s) for s in capacity_strengths[:2]) if capacity_strengths else "none identified"
    edges_str = ", ".join(_display_domain(e) for e in growth_edges[:2]) if growth_edges else "none identified"

    return (
        f"Based on your assessment results, your executive functioning "
        f"system is currently operating in a state of {quadrant_label} with a load classification "
        f"of {load_state.replace('_', ' ')}. "
        f"Your primary strengths are in {strengths_str}, while your key areas for growth "
        f"include {edges_str}."
    )


def generate_full_interpretation(output_json: dict) -> dict:
    """
    Section 7.14: Generate the complete AI interpretation output.
    Takes the Section 6 JSON output and produces structured narrative blocks.

    Returns:
        {
            "executive_summary": str,
            "quadrant_interpretation": str,
            "load_interpretation": str,
            "strengths_analysis": str,
            "growth_edges_analysis": str,
            "pei_bhp_interpretation": str,
            "aims_plan": {
                "awareness": str,
                "intervention": str,
                "mastery": str,
                "sustain": str
            }
        }
    """
    report_type = output_json["metadata"]["report_type"]
    quadrant = output_json["load_framework"]["quadrant"]
    load_state = output_json["load_framework"]["load_state"]
    construct_scores = output_json["construct_scores"]
    domain_profiles = output_json["domains"]
    top_strengths = output_json["summary"]["top_strengths"]
    growth_edges = output_json["summary"]["growth_edges"]

    archetype = output_json.get("archetype", {}).get("archetype_id", "")

    return {
        "executive_summary": generate_executive_summary(
            quadrant, load_state, top_strengths, growth_edges, report_type
        ),
        "quadrant_interpretation": generate_quadrant_narrative(quadrant, report_type),
        "load_interpretation": generate_load_narrative(load_state),
        "strengths_analysis": generate_strengths_narrative(top_strengths, domain_profiles),
        "growth_edges_analysis": generate_growth_edges_narrative(growth_edges, domain_profiles),
        "pei_bhp_interpretation": generate_construct_narrative(construct_scores),
        "aims_plan": generate_aims_plan(domain_profiles),
        "cosmic_summary": generate_cosmic_summary(archetype, top_strengths, growth_edges),
    }


def generate_cosmic_summary(archetype: str, top_strengths: list[str],
                            growth_edges: list[str]) -> str:
    """
    Generate an inspiring closing Cosmic Summary that ties together
    the individual's archetype, strengths, and growth trajectory.
    Environmental Demands are reframed as external pressure/challenges,
    not as a stabilizing strength.
    """
    archetype_label = _display_domain(archetype) if archetype else "your unique profile"
    # Separate Environmental from capacity strengths
    capacity_strengths = [s for s in top_strengths if s != "ENVIRONMENTAL_DEMANDS"]
    strengths_str = " and ".join(_display_domain(s) for s in capacity_strengths[:2]) if capacity_strengths else "your core capacities"
    edges_str = " and ".join(_display_domain(e) for e in growth_edges[:2]) if growth_edges else "emerging areas"

    return (
        f"As {archetype_label}, your executive function galaxy is uniquely yours — "
        f"shaped by the stabilizing strength of your {strengths_str} and the demands of your "
        f"environment that continuously challenge your system. At the same time, your {edges_str} "
        f"represent areas of expansion, where growth is actively emerging. "
        f"Every constellation in your galaxy reflects how you navigate pressure, adapt to demand, "
        f"and sustain performance. Your strongest capacities are already helping you remain steady, "
        f"even as external forces increase. Growth is not about fixing what is broken; it is about "
        f"strengthening what supports you while recalibrating what places strain on your system. "
        f"Your galaxy is not static — it is actively adjusting, evolving, and expanding. "
        f"And the best is still ahead."
    )


# =============================================================================
# HELPERS
# =============================================================================

def _display_domain(domain_key: str) -> str:
    """Convert backend domain key to human-readable label."""
    return domain_key.replace("_", " ").title()


def _display_report_type(report_type: str) -> str:
    """Convert report type key to readable label."""
    mapping = {
        "PERSONAL_LIFESTYLE": "Personal/Lifestyle",
        "STUDENT_SUCCESS": "Student Success",
        "PROFESSIONAL_LEADERSHIP": "Professional/Leadership",
        "FAMILY_ECOSYSTEM": "Family Ecosystem",
    }
    return mapping.get(report_type, report_type)
