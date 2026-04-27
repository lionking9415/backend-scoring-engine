"""
Lens-specific context rules for AI report generation.
Each lens changes the CONTEXT and EXAMPLES, never the scoring logic.
"""

LENS_RULES = {
    "STUDENT_SUCCESS": {
        "label": "Student Success",
        "icon": "🎓",
        "primary_goal": "academic performance",
        "context_instruction": (
            "Interpret ALL results through the primary lens goal: ACADEMIC PERFORMANCE. "
            "Apply academic context throughout. Use examples related to: "
            "studying, assignments, deadlines, school/work balance, course load, "
            "class participation, exam preparation, academic planning, "
            "campus life, and student responsibilities. "
            "Frame financial sections around student-specific pressures (tuition, "
            "part-time work, student loans). "
            "Frame health sections around student lifestyle (irregular sleep, "
            "cafeteria food, limited exercise time)."
        ),
        "expansion_suggest": ["PERSONAL_LIFESTYLE", "PROFESSIONAL_LEADERSHIP", "FAMILY_ECOSYSTEM"],
    },
    "PERSONAL_LIFESTYLE": {
        "label": "Personal / Lifestyle",
        "icon": "🧍",
        "primary_goal": "lifestyle stability",
        "context_instruction": (
            "Interpret ALL results through the primary lens goal: LIFESTYLE STABILITY. "
            "Apply lifestyle context throughout. Use examples related to: "
            "daily routines, habits, identity, self-management, personal organization, "
            "health behaviors, financial habits, life transitions, "
            "personal relationships, self-care, and daily decision-making. "
            "Financial and Health EF sections should be FULLY integrated "
            "(this is the primary lens for these domains). "
            "Frame everything around personal systems and daily life management."
        ),
        "expansion_suggest": ["STUDENT_SUCCESS", "PROFESSIONAL_LEADERSHIP", "FAMILY_ECOSYSTEM"],
    },
    "PROFESSIONAL_LEADERSHIP": {
        "label": "Professional / Leadership",
        "icon": "💼",
        "primary_goal": "execution and productivity",
        "context_instruction": (
            "Interpret ALL results through the primary lens goal: EXECUTION AND PRODUCTIVITY. "
            "Apply workplace context throughout. Use examples related to: "
            "productivity, execution, leadership, performance demands, workflow, "
            "communication, role expectations, workplace relationships, "
            "project management, meeting deadlines, and career development. "
            "Frame financial sections around workplace impact (financial stress "
            "affecting performance, burnout from financial pressure). "
            "Frame health sections around work capacity (energy, focus, "
            "burnout, work-life balance)."
        ),
        "expansion_suggest": ["PERSONAL_LIFESTYLE", "STUDENT_SUCCESS", "FAMILY_ECOSYSTEM"],
    },
    "FAMILY_ECOSYSTEM": {
        "label": "Family EF Ecosystem",
        "icon": "👨‍👩‍👧",
        "primary_goal": "relational and shared system dynamics",
        "context_instruction": (
            "Interpret ALL results through the primary lens goal: RELATIONAL AND SHARED SYSTEM DYNAMICS. "
            "Apply relational/family context throughout. Use examples related to: "
            "co-regulation, household systems, shared responsibilities, "
            "family expectations, communication, relational load, "
            "parenting dynamics, caregiving, and household management. "
            "Frame financial sections around household/family financial dynamics. "
            "Frame health sections around caregiver load, family health patterns, "
            "and how personal regulation affects family interactions. "
            "Emphasize dual-load system (individual + relational demands)."
        ),
        "expansion_suggest": ["PERSONAL_LIFESTYLE", "STUDENT_SUCCESS", "PROFESSIONAL_LEADERSHIP"],
    },
}

# Full Galaxy lens (all 4 combined) triggers the Cosmic Integration Report
COSMIC_LENS = "FULL_GALAXY"


def get_lens_context(report_type: str) -> dict:
    """Get lens configuration for the given report type."""
    return LENS_RULES.get(report_type, LENS_RULES["PERSONAL_LIFESTYLE"])
