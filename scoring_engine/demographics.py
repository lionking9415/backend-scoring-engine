"""
Demographics Intake Module — Collects and stores demographic context data.

This module handles:
- Demographic intake schema definition
- Storage and retrieval of demographic data
- Validation of demographic fields
- Mapping demographics to AI interpretation context

CRITICAL RULE: Demographics MUST NOT alter scoring outputs.
Demographics MAY influence AI interpretation, tone, and AIMS recommendations.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# =============================================================================
# DEMOGRAPHIC FIELD DEFINITIONS
# =============================================================================

AGE_RANGES = ["13-17", "18-24", "25-34", "35-44", "45-54", "55+"]

GENDER_OPTIONS = ["Female", "Male", "Non-binary", "Prefer to self-describe", "Prefer not to say"]

RACE_ETHNICITY_OPTIONS = [
    "Black / African American",
    "Hispanic / Latino",
    "White",
    "Asian",
    "Native American / Indigenous",
    "Middle Eastern / North African",
    "Pacific Islander",
    "Other",
    "Prefer not to say",
]

ROLE_OPTIONS = [
    "Student",
    "Full-time employee",
    "Part-time employee",
    "Entrepreneur / Business owner",
    "Parent / Caregiver",
    "Unemployed / Between roles",
    "Other",
]

LOAD_SOURCE_OPTIONS = [
    "School / Academics",
    "Work / Career",
    "Parenting / Caregiving",
    "Finances",
    "Health / Physical well-being",
    "Relationships",
    "Major life transition",
]

PERCEIVED_LOAD_OPTIONS = ["Light", "Manageable", "Heavy", "Overwhelming"]

SUPPORT_LEVEL_OPTIONS = [
    "Strong and consistent",
    "Available but inconsistent",
    "Limited",
    "No support",
]

FINANCIAL_STABILITY_OPTIONS = ["Stable", "Somewhat stable", "Uncertain", "High financial stress"]

FINANCIAL_PRESSURE_OPTIONS = ["Rarely", "Sometimes", "Often", "Constantly"]

HEALTH_CONSISTENCY_OPTIONS = ["Very consistent", "Somewhat consistent", "Inconsistent", "Highly irregular"]

HEALTH_NUTRITION_OPTIONS = ["Consistent and balanced", "Somewhat consistent", "Inconsistent", "Highly irregular"]

EXERCISE_OPTIONS = ["Regularly", "Occasionally", "Rarely", "Not at all"]

EMOTIONAL_REG_OPTIONS = ["Strong and consistent", "Moderate", "Inconsistent", "Difficult"]

OVERWHELM_RESPONSE_OPTIONS = [
    "Break tasks into smaller steps",
    "Delay or avoid",
    "Jump between tasks",
    "Seek help",
    "Push through with stress",
]

PLANNING_STYLE_OPTIONS = ["Structured and consistent", "Somewhat structured", "Inconsistent", "Avoid planning"]

# Tag mapping: which fields are used for AI interpretation vs research only
# [R] = Research only, [AI] = AI interpretation, [R+AI] = Both
FIELD_USAGE = {
    "age_range": "R+AI",
    "gender_identity": "R",          # ❌ NOT used in AI interpretation
    "race_ethnicity": "R",           # ❌ NOT used in AI interpretation
    "roles": "R+AI",
    "primary_load_sources": "R+AI",
    "perceived_load": "R+AI",
    "support_level": "R+AI",
    "financial_stability": "R+AI",
    "financial_pressure_frequency": "R+AI",
    "health_sleep": "R+AI",
    "health_nutrition": "R+AI",
    "health_exercise": "R+AI",
    "health_emotional_regulation": "R+AI",
    "overwhelm_response": "R+AI",
    "planning_style": "R+AI",
    "cultural_context": "R+AI",
}


# =============================================================================
# DEMOGRAPHIC QUESTIONS (for frontend rendering)
# =============================================================================

DEMOGRAPHIC_QUESTIONS = [
    {
        "id": "age_range",
        "section": "Age & Developmental Stage",
        "question": "What is your age range?",
        "type": "single_select",
        "options": AGE_RANGES,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Life-stage framing (student vs adult vs midlife load)",
    },
    {
        "id": "gender_identity",
        "section": "Gender Identity",
        "question": "How do you identify?",
        "type": "single_select_with_other",
        "options": GENDER_OPTIONS,
        "required": False,
        "tag": "R",
        "ai_use": None,
    },
    {
        "id": "race_ethnicity",
        "section": "Race / Ethnicity",
        "question": "Please select all that apply:",
        "type": "multi_select_with_other",
        "options": RACE_ETHNICITY_OPTIONS,
        "required": False,
        "tag": "R",
        "ai_use": None,
    },
    {
        "id": "roles",
        "section": "Primary Role Identity",
        "question": "Which roles currently describe you? (Select all that apply)",
        "type": "multi_select_with_other",
        "options": ROLE_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Determines lens-relevant examples + AIMS context",
    },
    {
        "id": "primary_load_sources",
        "section": "Primary Environmental Load Source",
        "question": "What areas place the MOST demand on your daily life? (Select up to 3)",
        "type": "multi_select",
        "options": LOAD_SOURCE_OPTIONS,
        "max_selections": 3,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Direct PEI context shaping",
    },
    {
        "id": "perceived_load",
        "section": "Perceived Life Load",
        "question": "How would you describe your current life load?",
        "type": "single_select",
        "options": PERCEIVED_LOAD_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Validates PEI perception vs score",
    },
    {
        "id": "support_level",
        "section": "Support System",
        "question": "How would you describe your current support system?",
        "type": "single_select",
        "options": SUPPORT_LEVEL_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Adjusts AIMS recommendations (external scaffolding)",
    },
    {
        "id": "financial_stability",
        "section": "Financial Context",
        "question": "How would you describe your current financial stability?",
        "type": "single_select",
        "options": FINANCIAL_STABILITY_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Financial PEI modifier",
    },
    {
        "id": "financial_pressure_frequency",
        "section": "Financial Context",
        "question": "How often do financial concerns impact your daily decisions?",
        "type": "single_select",
        "options": FINANCIAL_PRESSURE_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Financial load intensity",
    },
    {
        "id": "health_sleep",
        "section": "Health & Regulation Context",
        "question": "How consistent is your sleep routine?",
        "type": "single_select",
        "options": HEALTH_CONSISTENCY_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Health regulation layer + AIMS targeting",
    },
    {
        "id": "health_nutrition",
        "section": "Health & Regulation Context",
        "question": "How would you describe your nutrition habits?",
        "type": "single_select",
        "options": HEALTH_NUTRITION_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Health regulation layer + AIMS targeting",
    },
    {
        "id": "health_exercise",
        "section": "Health & Regulation Context",
        "question": "How often do you engage in physical movement or exercise?",
        "type": "single_select",
        "options": EXERCISE_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Health regulation layer + AIMS targeting",
    },
    {
        "id": "health_emotional_regulation",
        "section": "Health & Regulation Context",
        "question": "How would you describe your ability to emotionally regulate under stress?",
        "type": "single_select",
        "options": EMOTIONAL_REG_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Health regulation layer + AIMS targeting",
    },
    {
        "id": "overwhelm_response",
        "section": "Executive Function Context",
        "question": "When tasks become overwhelming, what is your most common response?",
        "type": "single_select",
        "options": OVERWHELM_RESPONSE_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Behavior pattern confirmation",
    },
    {
        "id": "planning_style",
        "section": "Executive Function Context",
        "question": "How do you typically approach planning and organization?",
        "type": "single_select",
        "options": PLANNING_STYLE_OPTIONS,
        "required": True,
        "tag": "R+AI",
        "ai_use": "Behavior pattern confirmation",
    },
    {
        "id": "cultural_context",
        "section": "Cultural & Contextual Lens",
        "question": "Are there any cultural, community, or personal values that shape how you approach work, school, or daily life?",
        "type": "open_text",
        "required": False,
        "tag": "R+AI",
        "ai_use": "Tone sensitivity + contextual respect",
    },
]


# =============================================================================
# DEMOGRAPHIC OUTPUT BUILDER
# =============================================================================

def build_demographic_output(raw_demographics: dict) -> dict:
    """
    Build the standardized demographic output object from raw intake responses.

    The output preserves research-only fields (gender_identity, race_ethnicity)
    under a separate `research_only` namespace so they are stored for analysis
    but kept structurally distinct from AI-context fields. The AI pipeline
    consumes this object via filter_ai_safe_demographics() which strips the
    research_only block before any prompt assembly.
    """
    if not raw_demographics:
        return {}

    return {
        "age_range": raw_demographics.get("age_range", ""),
        "roles": raw_demographics.get("roles", []),
        "primary_load_sources": raw_demographics.get("primary_load_sources", []),
        "perceived_load": raw_demographics.get("perceived_load", ""),
        "support_level": raw_demographics.get("support_level", ""),
        "financial_stability": raw_demographics.get("financial_stability", ""),
        "financial_pressure_frequency": raw_demographics.get("financial_pressure_frequency", ""),
        "health": {
            "sleep": raw_demographics.get("health_sleep", ""),
            "nutrition": raw_demographics.get("health_nutrition", ""),
            "exercise": raw_demographics.get("health_exercise", ""),
            "emotional_regulation": raw_demographics.get("health_emotional_regulation", ""),
        },
        "behavior_patterns": {
            "overwhelm_response": raw_demographics.get("overwhelm_response", ""),
            "planning_style": raw_demographics.get("planning_style", ""),
        },
        "cultural_context": raw_demographics.get("cultural_context", ""),
        # Research-only fields — preserved for analysis, MUST NOT be passed
        # to the AI prompt. filter_ai_safe_demographics() strips this block.
        "research_only": {
            "gender_identity": raw_demographics.get("gender_identity", ""),
            "race_ethnicity": raw_demographics.get("race_ethnicity", []),
        },
    }


def filter_ai_safe_demographics(demographics: dict) -> dict:
    """
    Filter demographics to only include fields safe for AI interpretation.
    Strips out research-only fields (gender, race/ethnicity) that must not
    influence AI output to prevent bias.
    """
    if not demographics:
        return {}

    # Defensive: ensure research_only block is never carried forward, even if
    # callers passed in raw stored demographics that contain it.
    demographics = {k: v for k, v in demographics.items() if k != "research_only"}

    # Only pass fields tagged as AI-safe
    ai_safe = {}
    for field_id, usage in FIELD_USAGE.items():
        if "AI" in usage:
            # Map nested health fields
            if field_id.startswith("health_"):
                sub_key = field_id.replace("health_", "")
                if "health" not in ai_safe:
                    ai_safe["health"] = {}
                health_data = demographics.get("health", {})
                if isinstance(health_data, dict):
                    ai_safe["health"][sub_key] = health_data.get(sub_key, "")
                else:
                    ai_safe["health"][sub_key] = demographics.get(field_id, "")
            elif field_id in ("overwhelm_response", "planning_style"):
                if "behavior_patterns" not in ai_safe:
                    ai_safe["behavior_patterns"] = {}
                bp = demographics.get("behavior_patterns", {})
                if isinstance(bp, dict):
                    ai_safe["behavior_patterns"][field_id] = bp.get(field_id, "")
                else:
                    ai_safe["behavior_patterns"][field_id] = demographics.get(field_id, "")
            else:
                ai_safe[field_id] = demographics.get(field_id, "")

    return ai_safe


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def store_demographics(user_id: str, assessment_id: str, demographics: dict) -> Optional[str]:
    """Store demographic intake data in the database."""
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()

        record_id = str(uuid.uuid4())
        record = {
            "id": record_id,
            "user_id": user_id,
            "assessment_id": assessment_id,
            "demographics": demographics,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        client.table("demographic_intakes").insert(record).execute()
        logger.info(f"Demographics stored: id={record_id}, user={user_id}, assessment={assessment_id}")
        return record_id
    except Exception as e:
        logger.error(f"Failed to store demographics: {e}")
        return None


def get_demographics(user_id: str, assessment_id: Optional[str] = None) -> Optional[dict]:
    """Retrieve demographic data for a user, optionally filtered by assessment."""
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()

        query = client.table("demographic_intakes").select("*").eq("user_id", user_id)
        if assessment_id:
            query = query.eq("assessment_id", assessment_id)
        query = query.order("created_at", desc=True).limit(1)

        response = query.maybe_single().execute()
        if response.data:
            return response.data.get("demographics")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve demographics: {e}")
        return None
