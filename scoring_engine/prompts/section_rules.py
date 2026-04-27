"""
Section-by-section generation rules for AI reports.
Defines the required 15-section structure for lens reports
and the 11-section structure for the Cosmic Integration report.
"""

# =============================================================================
# LENS REPORT SECTIONS (15 sections — mandatory order)
# =============================================================================

LENS_REPORT_SECTIONS = [
    {
        "number": 1,
        "key": "galaxy_snapshot",
        "title": "Galaxy Snapshot",
        "instructions": (
            "Summarize the overall PEI × BHP relationship and main performance pattern. "
            "Provide a nonjudgmental explanation. "
            "MUST include language similar to: 'This does not reflect a lack of ability. "
            "It reflects a load imbalance.' "
            "Include 1-2 key insights about the user's system."
        ),
    },
    {
        "number": 2,
        "key": "galaxy_placement",
        "title": "Galaxy Placement",
        "instructions": (
            "State the quadrant (e.g., High PEI / Moderate BHP), zone classification, "
            "and brief explanation of stability vs strain. "
            "Example format: 'Transitional Stability: stable under structure, strained under load.'"
        ),
    },
    {
        "number": 3,
        "key": "archetype_profile",
        "title": "Archetype Profile",
        "instructions": (
            "Include the archetype name, strength expression, under-load pattern, "
            "and what support helps the archetype stabilize. "
            "Frame strengths as natural capacities and under-load patterns as system responses."
        ),
    },
    {
        "number": 4,
        "key": "ef_ecosystem",
        "title": "Executive Function Ecosystem",
        "instructions": (
            "Cover all four domains: Action & Follow-Through, Focus & Drive, "
            "Emotional Regulation, and Life Load. "
            "IMPORTANT: Life Load must ALWAYS be framed as environmental pressure, NOT a strength. "
            "For each domain, describe stable-state capacity and what happens under increased load."
        ),
    },
    {
        "number": 5,
        "key": "financial_ef_profile",
        "title": "Financial Executive Functioning Profile™",
        "instructions": (
            "Must include: financial behavior pattern, PEI × BHP load interaction, "
            "financial identity under load, risk patterns (e.g., avoidance, impulsivity), "
            "and AIMS for financial stabilization. "
            "AI must NOT assume income level. No shame-based language. "
            "Focus on behavior patterns, not wealth status."
        ),
    },
    {
        "number": 6,
        "key": "health_ef_profile",
        "title": "Health & Fitness Executive Functioning Profile™",
        "instructions": (
            "Must include: health behavior pattern, regulation stability, load interaction, "
            "coping vs restoration behaviors. "
            "No medical advice. No body-shaming language. "
            "Focus on behavior + regulation patterns."
        ),
    },
    {
        "number": 7,
        "key": "pei_analysis",
        "title": "PEI Analysis",
        "instructions": (
            "Identify external demands and pressure sources relevant to the user's lens. "
            "Examples: academic deadlines, workload, financial pressure, family expectations, "
            "health-related load, role strain. "
            "Explain how these demands draw from the same executive functioning resources."
        ),
    },
    {
        "number": 8,
        "key": "bhp_analysis",
        "title": "BHP Analysis",
        "instructions": (
            "Identify internal capacity and current skill/regulation strengths. "
            "Examples: task initiation, emotional regulation, planning, follow-through, "
            "self-awareness, adaptability. "
            "Also note where strain occurs when demands exceed supports."
        ),
    },
    {
        "number": 9,
        "key": "pei_bhp_interaction",
        "title": "PEI × BHP Interaction",
        "instructions": (
            "This is the core interpretation section. "
            "Explain: What happens when external load meets internal capacity? "
            "Must avoid blaming the user. Frame as system dynamics."
        ),
    },
    {
        "number": 10,
        "key": "strength_profile",
        "title": "Strength Profile",
        "instructions": (
            "Identify stabilizers and protective capacities. "
            "Frame strengths as: 'Capacity anchors that help restore balance.' "
            "These are the user's system stabilizers."
        ),
    },
    {
        "number": 11,
        "key": "growth_edges",
        "title": "Growth Edges / Load Sensitivity Zones",
        "instructions": (
            "Must avoid deficit framing. Use 'Load Sensitivity Zones' terminology. "
            "NEVER use: weaknesses, deficits, problems, failures. "
            "Frame as: 'Points where total system load exceeds available support structures.'"
        ),
    },
    {
        "number": 12,
        "key": "aims_plan",
        "title": "AIMS for the BEST™",
        "instructions": (
            "Must follow this exact structure:\n"
            "A — Awareness & Activation\n"
            "I — Intervention & Implementation\n"
            "M — Mastery & Integration\n"
            "S — Sustain / Scaffold / Systemize\n\n"
            "AIMS interventions must: reduce load, be realistic, be behaviorally actionable, "
            "avoid overwhelm, and match the selected lens."
        ),
    },
    {
        "number": 13,
        "key": "pattern_continuity",
        "title": "Pattern Continuity Section™",
        "instructions": (
            "Explain how patterns may generalize across life domains. "
            "Required concept: 'You take yourself everywhere you go.' "
            "Can be used directly or translated softly depending on lens."
        ),
    },
    {
        "number": 14,
        "key": "expansion_pathway",
        "title": "Expansion Pathway Section™",
        "instructions": (
            "Recommend relevant additional report lenses the user has not yet purchased. "
            "Do NOT use pressure, scarcity, or fear-based upsell language. "
            "Use curiosity-based language only. "
            "Example: 'To expand your insight, consider exploring...'"
        ),
    },
    {
        "number": 15,
        "key": "cosmic_summary",
        "title": "Cosmic Summary",
        "instructions": (
            "Close with: dignity, hope, agency, and load balance framing. "
            "Must NOT overpromise outcomes. "
            "Reinforce that the user's system is capable and responsive. "
            "Goal framing: align environment with capacity, not push harder."
        ),
    },
]

# =============================================================================
# COSMIC INTEGRATION REPORT SECTIONS (11 sections)
# =============================================================================

COSMIC_REPORT_SECTIONS = [
    {
        "number": 1,
        "key": "cosmic_snapshot",
        "title": "Cosmic Snapshot",
        "instructions": (
            "Provide a unified system description across all 4 lenses. "
            "Identify the core load pattern and key insight across all environments. "
            "Do NOT summarize individual reports — SYNTHESIZE."
        ),
    },
    {
        "number": 2,
        "key": "galaxy_convergence_map",
        "title": "Galaxy Convergence Map™",
        "instructions": (
            "This is the signature section. Describe how all 4 lenses connect, "
            "where patterns align, and where they diverge. "
            "Frame as a unified behavioral constellation."
        ),
    },
    {
        "number": 3,
        "key": "load_balance_matrix",
        "title": "Load Balance Matrix™",
        "instructions": (
            "Break down High Stability Zones, Transitional Zones, and High Strain Zones "
            "across: Personal, Academic, Professional, Family. "
            "Present as a structured comparison."
        ),
    },
    {
        "number": 4,
        "key": "cross_domain_load_transfer",
        "title": "Cross-Domain Load Transfer Analysis",
        "instructions": (
            "Explain: 'When one domain increases pressure, how does it affect others?' "
            "Examples: Financial → Emotional → Academic, Health → Focus → Work performance. "
            "Show the chain reactions in the user's system."
        ),
    },
    {
        "number": 5,
        "key": "core_system_identity",
        "title": "Core System Identity Under Load",
        "instructions": (
            "Define who the user becomes when pressure is high across all environments. "
            "This is about the consistent behavioral pattern that emerges under sustained load."
        ),
    },
    {
        "number": 6,
        "key": "global_strength_architecture",
        "title": "Global Strength Architecture",
        "instructions": (
            "Identify strengths that appear across ALL lenses. "
            "Label these as 'System Stabilizers' — capacities that support recovery and growth."
        ),
    },
    {
        "number": 7,
        "key": "system_wide_sensitivity",
        "title": "System-Wide Load Sensitivity Zones",
        "instructions": (
            "Identify patterns that break down across environments. "
            "Frame as load sensitivity points, not weaknesses."
        ),
    },
    {
        "number": 8,
        "key": "pattern_continuity_amplified",
        "title": "Pattern Continuity Amplified™",
        "instructions": (
            "Expand the 'You take yourself everywhere you go' concept — now backed by 4-lens evidence. "
            "Show how the same core pattern expresses differently in each environment."
        ),
    },
    {
        "number": 9,
        "key": "cosmic_aims",
        "title": "AIMS for the BEST™ — Cosmic Level",
        "instructions": (
            "This is DIFFERENT from single-lens AIMS.\n"
            "A — Awareness: Recognize cross-domain patterns\n"
            "I — Intervention: Focus on highest leverage domain first\n"
            "M — Mastery: Build stability in one domain → transfer to others\n"
            "S — Systemize: Create life-wide systems, not isolated habits"
        ),
    },
    {
        "number": 10,
        "key": "expansion_pathway",
        "title": "Expansion Pathway",
        "instructions": (
            "Suggest deep-dive reports: Financial only, Health only, Compatibility. "
            "Use curiosity-based language, no pressure."
        ),
    },
    {
        "number": 11,
        "key": "cosmic_summary",
        "title": "Cosmic Summary",
        "instructions": (
            "Must feel like: 'I finally understand how my whole system works.' "
            "Close with dignity, hope, agency, unified understanding."
        ),
    },
]

# =============================================================================
# LENS-EXCLUSIVE SECTIONS (Addendum Phase 3, Section 4)
# Each lens gets ONE unique section not present in other lenses.
# Inserted as Section 12b (after AIMS, before Pattern Continuity).
# =============================================================================

LENS_EXCLUSIVE_SECTIONS = {
    "STUDENT_SUCCESS": {
        "key": "academic_performance_impact",
        "title": "Academic Performance Impact™",
        "instructions": (
            "This section is EXCLUSIVE to the Student Success lens.\n"
            "Analyze how the user's executive functioning profile directly impacts "
            "academic performance. MUST include:\n"
            "- Study efficiency: How EF patterns affect study habits and retention\n"
            "- Assignment initiation: Patterns around starting academic tasks\n"
            "- Deadline behavior: How the user's system responds to academic deadlines\n"
            "- Learning under pressure: Performance during exams, high-stakes situations\n\n"
            "Connect each area to the user's specific PEI × BHP profile. "
            "Frame as system behavior, not character traits."
        ),
    },
    "PERSONAL_LIFESTYLE": {
        "key": "lifestyle_stability_index",
        "title": "Lifestyle Stability Index™",
        "instructions": (
            "This section is EXCLUSIVE to the Personal / Lifestyle lens.\n"
            "Analyze how the user's executive functioning profile impacts daily life "
            "stability. MUST include:\n"
            "- Routine consistency: Ability to maintain daily rhythms and structure\n"
            "- Habit strength: How well positive habits hold under load\n"
            "- Identity alignment: Whether daily actions match personal values and goals\n"
            "- Daily structure: Overall organization of the user's personal system\n\n"
            "Connect each area to the user's specific PEI × BHP profile. "
            "Frame as lifestyle system dynamics, not personal failures."
        ),
    },
    "PROFESSIONAL_LEADERSHIP": {
        "key": "execution_productivity_profile",
        "title": "Execution & Productivity Profile™",
        "instructions": (
            "This section is EXCLUSIVE to the Professional / Leadership lens.\n"
            "Analyze how the user's executive functioning profile impacts workplace "
            "execution. MUST include:\n"
            "- Task completion patterns: How projects move from initiation to finish\n"
            "- Workflow efficiency: Ability to manage multi-step processes\n"
            "- Prioritization: How the user allocates focus across competing demands\n"
            "- Performance under pressure: Execution quality when deadlines or stakes rise\n\n"
            "Connect each area to the user's specific PEI × BHP profile. "
            "Frame as professional system dynamics, not competence judgments."
        ),
    },
    "FAMILY_ECOSYSTEM": {
        "key": "family_system_dynamics",
        "title": "Family System Dynamics™",
        "instructions": (
            "This section is EXCLUSIVE to the Family EF Ecosystem lens.\n"
            "Analyze how the user's executive functioning profile impacts family and "
            "relational systems. MUST include:\n"
            "- Role clarity: How well the user manages expectations within family roles\n"
            "- Co-regulation: Ability to regulate alongside others in shared environments\n"
            "- Communication patterns: How EF load affects relational communication\n"
            "- Engagement vs withdrawal: Patterns of connection or disconnection under load\n\n"
            "Connect each area to the user's specific PEI × BHP profile. "
            "Frame as relational system dynamics, not relationship failures."
        ),
    },
}

# =============================================================================
# LENS-SPECIFIC AIMS FOCUS (Addendum Phase 3, Section 5)
# Injected into the AIMS section instructions per lens.
# =============================================================================

LENS_AIMS_FOCUS = {
    "STUDENT_SUCCESS": (
        "AIMS interventions for the Student lens MUST prioritize:\n"
        "- Study planning and scheduling\n"
        "- Assignment breakdown strategies\n"
        "- Academic scheduling and time blocking\n"
        "Frame all interventions around academic performance and student life demands."
    ),
    "PERSONAL_LIFESTYLE": (
        "AIMS interventions for the Personal lens MUST prioritize:\n"
        "- Habit building and reinforcement\n"
        "- Routine anchors for daily stability\n"
        "- Lifestyle consistency strategies\n"
        "Frame all interventions around personal systems and daily life management."
    ),
    "PROFESSIONAL_LEADERSHIP": (
        "AIMS interventions for the Professional lens MUST prioritize:\n"
        "- Workflow systems and process design\n"
        "- Task prioritization frameworks\n"
        "- Execution consistency under workload\n"
        "Frame all interventions around workplace productivity and professional demands."
    ),
    "FAMILY_ECOSYSTEM": (
        "AIMS interventions for the Family lens MUST prioritize:\n"
        "- Communication strategies within family systems\n"
        "- Boundary setting and role clarity\n"
        "- Shared expectations and co-regulation\n"
        "Frame all interventions around relational dynamics and shared household systems."
    ),
}


def get_lens_sections(report_type: str) -> list[dict]:
    """
    Build the complete section list for a lens report.
    Includes the standard 15 sections PLUS the lens-exclusive section
    inserted after AIMS (Section 12) as Section 12b.
    Also enhances AIMS instructions with lens-specific focus.
    """
    sections = []
    for s in LENS_REPORT_SECTIONS:
        entry = dict(s)
        # Enhance AIMS section with lens-specific focus
        if entry["key"] == "aims_plan" and report_type in LENS_AIMS_FOCUS:
            entry["instructions"] = entry["instructions"] + "\n\n" + LENS_AIMS_FOCUS[report_type]
        sections.append(entry)

        # Insert exclusive section right after AIMS (section 12)
        if entry["key"] == "aims_plan" and report_type in LENS_EXCLUSIVE_SECTIONS:
            exclusive = LENS_EXCLUSIVE_SECTIONS[report_type]
            sections.append({
                "number": "12b",
                "key": exclusive["key"],
                "title": exclusive["title"],
                "instructions": exclusive["instructions"],
            })

    return sections


# Quick lookup maps
LENS_SECTION_KEYS = [s["key"] for s in LENS_REPORT_SECTIONS]
COSMIC_SECTION_KEYS = [s["key"] for s in COSMIC_REPORT_SECTIONS]
EXCLUSIVE_SECTION_KEYS = [v["key"] for v in LENS_EXCLUSIVE_SECTIONS.values()]
