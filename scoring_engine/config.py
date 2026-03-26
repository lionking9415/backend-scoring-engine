"""
Configuration layer for the BEST Executive Function Galaxy Assessment™.
All thresholds, domain definitions, and system constants are defined here.
Changes to scoring behavior should be made HERE, not in the scoring logic.
"""

# =============================================================================
# SYSTEM CONSTANTS
# =============================================================================

SYSTEM_ID = "BEST_EF_GALAXY_V1"
SYSTEM_NAME = "BEST_EXECUTIVE_FUNCTION_GALAXY_ASSESSMENT"
DISPLAY_NAME = "The BEST Executive Function Galaxy Assessment™"

# =============================================================================
# REPORT LENSES (ENUM)
# =============================================================================

REPORT_LENSES = [
    "PERSONAL_LIFESTYLE",
    "STUDENT_SUCCESS",
    "PROFESSIONAL_LEADERSHIP",
    "FAMILY_ECOSYSTEM",
]

REPORT_DISPLAY_NAMES = {
    "PERSONAL_LIFESTYLE": "Personal Executive Function Galaxy Report",
    "STUDENT_SUCCESS": "Student Success Executive Function Galaxy Report",
    "PROFESSIONAL_LEADERSHIP": "Professional Executive Function Galaxy Report",
    "FAMILY_ECOSYSTEM": "Family Executive Function Galaxy Report",
}

# =============================================================================
# CONSTRUCTS (DO NOT CHANGE)
# =============================================================================

CONSTRUCTS = ["PEI", "BHP"]
# PEI = Probability Environment Index (External Load)
# BHP = Behavioral Health Probability (Internal Capacity)

# =============================================================================
# DOMAINS (LEVEL 1 SCORING BUCKETS)
# =============================================================================

APPROVED_DOMAINS = [
    "EXECUTIVE_FUNCTION_SKILLS",
    "ENVIRONMENTAL_DEMANDS",
    "EMOTIONAL_REGULATION",
    "BEHAVIORAL_PATTERNS",
    "COGNITIVE_CONTROL",
    "MOTIVATIONAL_SYSTEMS",
    "INTERNAL_STATE_FACTORS",
]

# =============================================================================
# SCORING DIRECTION
# =============================================================================

VALID_DIRECTIONS = ["forward", "reverse"]

# =============================================================================
# RESPONSE SCALE DEFINITIONS
# =============================================================================

RESPONSE_SCALES = {
    "ABCD_4": {"min_score": 1, "max_score": 4},
    "Likert_5": {"min_score": 1, "max_score": 5},
    "Likert_7": {"min_score": 1, "max_score": 7},
    "TeeterTotter_7": {"min_score": 1, "max_score": 7},
}

# =============================================================================
# ITEM TYPES
# =============================================================================

VALID_ITEM_TYPES = ["behavioral", "aims"]
VALID_CONTEXTS = ["preferred", "non_preferred", "coping", "function"]

# =============================================================================
# AIMS FUNCTION CATEGORIES (Every 4th question)
# =============================================================================

AIMS_FUNCTIONS = ["ATTENTION", "SENSORY", "ESCAPE", "OVERWHELM"]

# =============================================================================
# APPROVED SUBDOMAINS (13 subdomains × 4 items = 52)
# =============================================================================

APPROVED_SUBDOMAINS = [
    "TASK_INITIATION",
    "ORGANIZATION",
    "PLANNING",
    "ACTIVATION",
    "SUSTAINED_ATTENTION",
    "TASK_COMPLETION",
    "RESPONSE_ACTIVATION",
    "EMOTIONAL_REGULATION",
    "HELP_SEEKING",
    "SOCIAL_ENGAGEMENT",
    "SELF_ADVOCACY",
    "FOLLOW_THROUGH",
    "SHUTDOWN_RESPONSE",
]

# =============================================================================
# QUADRANT THRESHOLD (Section 4)
# Configurable — change this value to adjust High/Low boundary
# =============================================================================

QUADRANT_THRESHOLD = 0.50

# =============================================================================
# QUADRANT DEFINITIONS (Section 4.4)
# =============================================================================

QUADRANTS = {
    "Q1_Aligned_Flow": {
        "condition": "BHP >= threshold AND PEI < threshold",
        "interpretation": "Strong capacity, manageable demand",
    },
    "Q2_Capacity_Strain": {
        "condition": "BHP >= threshold AND PEI >= threshold",
        "interpretation": "Strong capacity under heavy demand",
    },
    "Q3_Overload": {
        "condition": "BHP < threshold AND PEI >= threshold",
        "interpretation": "Demand exceeds capacity",
    },
    "Q4_Underutilized": {
        "condition": "BHP < threshold AND PEI < threshold",
        "interpretation": "Low demand, low activation",
    },
}

# =============================================================================
# LOAD STATE RANGES (Section 4.8)
# =============================================================================

LOAD_STATES = [
    {"label": "Surplus_Capacity", "min": 0.20, "max": float("inf")},
    {"label": "Stable_Capacity", "min": 0.05, "max": 0.19},
    {"label": "Balanced_Load", "min": -0.04, "max": 0.04},
    {"label": "Emerging_Strain", "min": -0.19, "max": -0.05},
    {"label": "Critical_Overload", "min": float("-inf"), "max": -0.20},
]

# =============================================================================
# DOMAIN CLASSIFICATION THRESHOLDS (Section 5.4)
# =============================================================================

DOMAIN_CLASSIFICATIONS = [
    {"label": "Strength", "min": 0.80, "max": 1.00},
    {"label": "Developed", "min": 0.60, "max": 0.79},
    {"label": "Emerging", "min": 0.40, "max": 0.59},
    {"label": "Growth_Edge", "min": 0.00, "max": 0.39},
]

# =============================================================================
# AIMS MAPPING (Section 5.13 / 7.10)
# =============================================================================

AIMS_PRIORITY_MAP = {
    "Strength": "Sustain & Generalize",
    "Developed": "Optimize",
    "Emerging": "Targeted Intervention",
    "Growth_Edge": "Immediate Priority",
}

# =============================================================================
# MISSING DATA HANDLING (Section 8 — LOCKED)
# =============================================================================

MISSING_DATA_RULE = "compute_available"  # Option A: Compute using available items only
LOW_CONFIDENCE_THRESHOLD = 0.70  # Flag if < 70% items answered

# =============================================================================
# SUMMARY EXTRACTION
# =============================================================================

TOP_STRENGTHS_COUNT = 3
GROWTH_EDGES_COUNT = 3

# =============================================================================
# PRECISION
# =============================================================================

INTERNAL_PRECISION = 4  # Decimal places for internal calculations
OUTPUT_PRECISION = 3    # Decimal places for final output

# =============================================================================
# DOMAIN-TO-INDEX WEIGHT MATRIX (Overlapping Domain Contributions)
# =============================================================================
# Key architectural feature: domains can contribute to BOTH PEI and BHP
# indices with DIFFERENT weights. This is the configurable weight matrix.
#
# Format: { domain: { "PEI": weight, "BHP": weight } }
# - A weight of 0.0 means the domain does NOT contribute to that index
# - A domain can have non-zero weights for BOTH indices (overlapping)
# - Weights are applied AFTER item-level normalization, during index aggregation
# - Change weights here without touching scoring logic
# =============================================================================

DOMAIN_INDEX_WEIGHTS = {
    "EXECUTIVE_FUNCTION_SKILLS": {"PEI": 0.0, "BHP": 1.0},
    "ENVIRONMENTAL_DEMANDS":     {"PEI": 1.0, "BHP": 0.0},
    "EMOTIONAL_REGULATION":      {"PEI": 0.3, "BHP": 1.0},  # overlapping
    "BEHAVIORAL_PATTERNS":       {"PEI": 0.0, "BHP": 1.0},
    "COGNITIVE_CONTROL":         {"PEI": 0.0, "BHP": 1.0},
    "MOTIVATIONAL_SYSTEMS":      {"PEI": 0.4, "BHP": 0.8},  # overlapping
    "INTERNAL_STATE_FACTORS":    {"PEI": 0.6, "BHP": 0.7},  # overlapping
}

# =============================================================================
# ARCHETYPE DEFINITIONS (16 Archetypes — Phase 1 Stubs)
# =============================================================================
# Full archetype assignment logic will be refined in Phase 2.
# This config defines the structure so the engine can route into it.
# Each archetype maps to a quadrant + load_state + domain pattern.
# =============================================================================

ARCHETYPE_DEFINITIONS = {
    "THE_NAVIGATOR": {
        "quadrant": "Q1_Aligned_Flow",
        "load_state": "Surplus_Capacity",
        "description": "High capacity, low demand — strategically positioned and self-directed.",
    },
    "THE_OPTIMIZER": {
        "quadrant": "Q1_Aligned_Flow",
        "load_state": "Stable_Capacity",
        "description": "Strong internal systems with room for refinement and growth.",
    },
    "THE_ACHIEVER": {
        "quadrant": "Q1_Aligned_Flow",
        "load_state": "Balanced_Load",
        "description": "Well-calibrated system performing at a sustainable pace.",
    },
    "THE_ADAPTER": {
        "quadrant": "Q2_Capacity_Strain",
        "load_state": "Stable_Capacity",
        "description": "Strong capacity actively managing high environmental demand.",
    },
    "THE_PERFORMER": {
        "quadrant": "Q2_Capacity_Strain",
        "load_state": "Balanced_Load",
        "description": "Capable under pressure but approaching sustainable limits.",
    },
    "THE_STRETCHER": {
        "quadrant": "Q2_Capacity_Strain",
        "load_state": "Emerging_Strain",
        "description": "Capacity is being tested — proactive support recommended.",
    },
    "THE_ENDURER": {
        "quadrant": "Q2_Capacity_Strain",
        "load_state": "Surplus_Capacity",
        "description": "High capacity absorbing sustained heavy demand.",
    },
    "THE_SURVIVOR": {
        "quadrant": "Q3_Overload",
        "load_state": "Emerging_Strain",
        "description": "Demand is exceeding capacity — early intervention needed.",
    },
    "THE_OVERWHELMED": {
        "quadrant": "Q3_Overload",
        "load_state": "Critical_Overload",
        "description": "System under critical pressure — immediate support required.",
    },
    "THE_REACTOR": {
        "quadrant": "Q3_Overload",
        "load_state": "Balanced_Load",
        "description": "Operating reactively under environmental pressure.",
    },
    "THE_SEEKER": {
        "quadrant": "Q4_Underutilized",
        "load_state": "Balanced_Load",
        "description": "Untapped potential awaiting activation and direction.",
    },
    "THE_DRIFTER": {
        "quadrant": "Q4_Underutilized",
        "load_state": "Stable_Capacity",
        "description": "Low activation — system is coasting without clear engagement.",
    },
    "THE_WITHDRAWN": {
        "quadrant": "Q4_Underutilized",
        "load_state": "Emerging_Strain",
        "description": "Low activation with emerging internal strain signals.",
    },
    "THE_DORMANT": {
        "quadrant": "Q4_Underutilized",
        "load_state": "Surplus_Capacity",
        "description": "Capacity exists but is not being engaged or challenged.",
    },
    "THE_BUILDER": {
        "quadrant": "Q1_Aligned_Flow",
        "load_state": "Emerging_Strain",
        "description": "Strong foundation with emerging growth challenges.",
    },
    "THE_GRINDER": {
        "quadrant": "Q3_Overload",
        "load_state": "Stable_Capacity",
        "description": "Pushing through demand with limited but stable capacity.",
    },
}

# =============================================================================
# DATABASE CONFIGURATION (Supabase)
# =============================================================================
# Credentials are loaded from .env file via scoring_engine/supabase_client.py
# See .env.example for required variables:
#   SUPABASE_URL, SUPABASE_ANON_KEY
# =============================================================================
