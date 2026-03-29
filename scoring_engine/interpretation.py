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

LENS_TEASER_TEMPLATES = {
    "Q1_Aligned_Flow": {
        "PERSONAL_LIFESTYLE": (
            "You show moments of clarity and intention in your daily life, especially "
            "when your environment supports your natural rhythm. There is a deeper pattern "
            "in how your internal energy and external expectations interact\u2014one that reveals "
            "where your greatest stability can be built."
        ),
        "STUDENT_SUCCESS": (
            "Your learning patterns suggest that you are capable of strong engagement "
            "when the material aligns with your processing style. Your full profile reveals "
            "how your brain responds to academic demand\u2014and how to optimize it."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "In professional environments, you bring a unique way of thinking, organizing, "
            "and responding to expectations. There is a deeper leadership pattern within your "
            "results that highlights how you operate under pressure\u2014and where your highest "
            "performance can emerge."
        ),
        "FAMILY_ECOSYSTEM": (
            "Within your family or relational environment, your executive functioning interacts "
            "dynamically with others\u2019 needs, emotions, and expectations. Your full profile "
            "uncovers how these interactions shape your behavior\u2014and how to create more balance "
            "within your ecosystem."
        ),
    },
    "Q2_Capacity_Strain": {
        "PERSONAL_LIFESTYLE": (
            "You show real capacity in your daily life, but there are moments when the weight "
            "of your environment begins to press against your internal resources. Your full "
            "profile reveals the specific pattern of demand that is stretching your system\u2014and "
            "what can be done about it."
        ),
        "STUDENT_SUCCESS": (
            "Your academic abilities are real, but certain demands may place an invisible strain "
            "on your executive functioning, especially in areas requiring sustained effort or "
            "rapid organization. Your full profile reveals how your brain responds to academic "
            "pressure\u2014and how to optimize it."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "You excel in areas that align with your natural strengths, while other professional "
            "demands create friction beneath the surface. There is a deeper pattern in your results "
            "that shows where targeted adjustments can unlock your next level of performance."
        ),
        "FAMILY_ECOSYSTEM": (
            "You may find yourself adapting, responding, or compensating in ways that impact your "
            "consistency and energy within your family. Your full profile uncovers how these "
            "interactions shape your behavior\u2014and how to create more balance within your ecosystem."
        ),
    },
    "Q3_Overload": {
        "PERSONAL_LIFESTYLE": (
            "Your daily environment is asking more of you than your current system can comfortably "
            "sustain. This is not about ability\u2014it is about the weight of demand on your capacity. "
            "Your full profile reveals exactly where the pressure points are and what support looks like."
        ),
        "STUDENT_SUCCESS": (
            "Your learning environment is placing demands that exceed what your executive functioning "
            "can comfortably manage right now. This is not about intelligence\u2014your full profile "
            "reveals the specific pressure points and how to address them."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "Your professional environment is asking more of your system than it can currently sustain. "
            "This is not a reflection of your competence\u2014your full profile shows the exact pattern "
            "of overload and the path to restoring balance."
        ),
        "FAMILY_ECOSYSTEM": (
            "Your family dynamics are placing significant demands on your executive functioning. "
            "You may be compensating in ways you don\u2019t fully see yet. Your full profile reveals "
            "how to create more sustainable patterns within your family ecosystem."
        ),
    },
    "Q4_Underutilized": {
        "PERSONAL_LIFESTYLE": (
            "Your current patterns suggest untapped potential\u2014there is capacity within you that "
            "hasn\u2019t been fully activated by your environment. Your full profile reveals what\u2019s "
            "holding that potential in place and how to unlock it."
        ),
        "STUDENT_SUCCESS": (
            "Your academic engagement may be operating below its natural potential. There are "
            "signals in your results that suggest stronger capacity than what is currently being "
            "activated. Your full profile reveals how to ignite that engagement."
        ),
        "PROFESSIONAL_LEADERSHIP": (
            "Your professional profile suggests capacity that isn\u2019t being fully engaged by your "
            "current environment. There is a pattern in your results pointing to untapped leadership "
            "potential\u2014your full report reveals how to activate it."
        ),
        "FAMILY_ECOSYSTEM": (
            "Within your family system, there may be an opportunity for deeper engagement that "
            "hasn\u2019t yet been activated. Your full profile reveals how your executive functioning "
            "can support richer, more balanced family dynamics."
        ),
    },
}


def generate_lens_teasers(quadrant: str) -> dict:
    """
    Generate all 4 lens teaser paragraphs for the FREE ScoreCard.
    Returns dict with lens keys and teaser strings.
    """
    templates = LENS_TEASER_TEMPLATES.get(quadrant, LENS_TEASER_TEMPLATES["Q1_Aligned_Flow"])
    return {
        "PERSONAL_LIFESTYLE": templates["PERSONAL_LIFESTYLE"],
        "STUDENT_SUCCESS": templates["STUDENT_SUCCESS"],
        "PROFESSIONAL_LEADERSHIP": templates["PROFESSIONAL_LEADERSHIP"],
        "FAMILY_ECOSYSTEM": templates["FAMILY_ECOSYSTEM"],
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
    """
    if not top_strengths:
        return "No strength domains were identified in this assessment."

    strength_details = []
    profile_lookup = {p["name"]: p for p in domain_profiles}

    for name in top_strengths:
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
    """
    growth_domains = [p for p in domain_profiles if p["classification"] == "Growth_Edge"]
    emerging_domains = [p for p in domain_profiles if p["classification"] == "Emerging"]
    developed_domains = [p for p in domain_profiles if p["classification"] == "Developed"]
    strength_domains = [p for p in domain_profiles if p["classification"] == "Strength"]

    def _domain_list(profiles):
        return ", ".join(_display_domain(p["name"]) for p in profiles) if profiles else "none identified"

    awareness = (
        f"Begin by building awareness of your executive functioning patterns. "
        f"Your immediate priority areas are: {_domain_list(growth_domains)}. "
        f"Recognition of these patterns is the first step toward meaningful change."
    )

    intervention = (
        f"Targeted skill-building is recommended for: {_domain_list(emerging_domains + growth_domains)}. "
        f"These areas will benefit from structured practice and environmental adjustments."
    )

    mastery = (
        f"Continue strengthening and integrating skills in: {_domain_list(developed_domains)}. "
        f"These domains are functional but can be optimized through consistent practice."
    )

    sustain = (
        f"Sustain and generalize your strengths in: {_domain_list(strength_domains)}. "
        f"These are your capacity anchors — use them to support growth in other areas."
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
    """Generate a concise executive summary combining key findings."""
    quadrant_label = quadrant.replace("_", " ").replace("Q1 ", "").replace("Q2 ", "").replace("Q3 ", "").replace("Q4 ", "")
    strengths_str = ", ".join(_display_domain(s) for s in top_strengths[:2]) if top_strengths else "none identified"
    edges_str = ", ".join(_display_domain(e) for e in growth_edges[:2]) if growth_edges else "none identified"

    return (
        f"Based on your {_display_report_type(report_type)} assessment, your executive functioning "
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
    """
    archetype_label = _display_domain(archetype) if archetype else "your unique profile"
    strengths_str = " and ".join(_display_domain(s) for s in top_strengths[:2]) if top_strengths else "your core capacities"
    edges_str = " and ".join(_display_domain(e) for e in growth_edges[:2]) if growth_edges else "emerging areas"

    return (
        f"As a {archetype_label}, your executive function galaxy is uniquely yours — "
        f"shaped by the gravitational pull of {strengths_str} and the expanding frontier of {edges_str}. "
        f"Every constellation in your galaxy tells a story of how you navigate the world, "
        f"and the brightest stars are already lighting the way forward. "
        f"Growth is not about fixing what is broken; it is about aligning what already shines "
        f"with what is ready to emerge. Your galaxy is expanding — and the best is yet to come."
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
