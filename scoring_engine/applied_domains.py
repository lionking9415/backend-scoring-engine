"""
Applied Executive Functioning Domains — Phase 4
Financial EF + Health & Fitness EF

These are standalone domain modules derived from the existing 52-question
assessment data. They are NOT nested under existing domains.

Each domain computes:
  - BHP (Internal Capacity)
  - PEI (External Pressure)
  - load_balance = BHP - PEI
  - domain_score = clamp(50 + load_balance, 0, 100)  (normalized 0-100)
  - status_band
  - subvariables (computed from existing scored items)
  - flags (boolean behavioral indicators)
  - aims_targets (domain-specific recommendations)

Architecture:
  - Subvariables are derived by mapping existing domain/subdomain/construct
    scores to the new financial/health subvariable definitions.
  - The mapping uses the existing scored item data to compute proxy scores
    for each subvariable on a 0-100 scale.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# STATUS BAND THRESHOLDS (same for both domains)
# =============================================================================

STATUS_BANDS = [
    {"label": "Buffered Under Load",    "min": 20,   "max": float("inf")},
    {"label": "Stable but Vulnerable",  "min": 5,    "max": 19.999},
    {"label": "Fragile Balance",        "min": -4.999, "max": 4.999},
    {"label": "Strained Under Load",    "min": -19.999, "max": -5},
    {"label": "Turbulence Zone",        "min": float("-inf"), "max": -20},
]

STATUS_BAND_COLORS = {
    "Buffered Under Load":   "#22C55E",
    "Stable but Vulnerable": "#3B82F6",
    "Fragile Balance":       "#F59E0B",
    "Strained Under Load":   "#F97316",
    "Turbulence Zone":       "#EF4444",
}


def _assign_status_band(load_balance: float) -> str:
    """Assign a status band based on load_balance value."""
    for band in STATUS_BANDS:
        if band["min"] <= load_balance <= band["max"]:
            return band["label"]
    return "Fragile Balance"


def _clamp(value: float, min_val: float = 0, max_val: float = 100) -> float:
    """Clamp a value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


# =============================================================================
# SUBVARIABLE DERIVATION MAPPINGS
# =============================================================================
# Each subvariable is derived from existing domain/subdomain/construct scores.
# The mapping defines which existing data points contribute to each subvariable.
#
# Strategy:
#   - Use domain scores (0-1 normalized) as proxies for subvariables
#   - Use construct balance (PEI vs BHP within domains) for pressure indicators
#   - Map to 0-100 scale for the applied domain formulas
# =============================================================================

# Financial BHP subvariable mappings → which existing scores inform each
FINANCIAL_BHP_SOURCES = {
    "financial_planning_consistency": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS"],
        "subdomains": ["PLANNING", "ORGANIZATION"],
        "construct": "BHP",
        "weight": 0.20,
    },
    "financial_follow_through": {
        "domains": ["BEHAVIORAL_PATTERNS", "MOTIVATIONAL_SYSTEMS"],
        "subdomains": ["TASK_COMPLETION", "FOLLOW_THROUGH"],
        "construct": "BHP",
        "weight": 0.20,
    },
    "financial_emotional_regulation": {
        "domains": ["EMOTIONAL_REGULATION"],
        "subdomains": ["EMOTIONAL_REGULATION"],
        "construct": "BHP",
        "weight": 0.20,
    },
    "financial_organization": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS"],
        "subdomains": ["ORGANIZATION"],
        "construct": "BHP",
        "weight": 0.15,
    },
    "financial_delayed_gratification": {
        "domains": ["MOTIVATIONAL_SYSTEMS", "COGNITIVE_CONTROL"],
        "subdomains": ["FOLLOW_THROUGH", "SUSTAINED_ATTENTION"],
        "construct": "BHP",
        "weight": 0.15,
    },
    "financial_decision_clarity": {
        "domains": ["COGNITIVE_CONTROL", "EXECUTIVE_FUNCTION_SKILLS"],
        "subdomains": ["SUSTAINED_ATTENTION", "PLANNING"],
        "construct": "BHP",
        "weight": 0.10,
    },
}

# Financial PEI subvariable mappings
FINANCIAL_PEI_SOURCES = {
    "financial_instability": {
        "domains": ["ENVIRONMENTAL_DEMANDS", "INTERNAL_STATE_FACTORS"],
        "subdomains": ["SOCIAL_ENGAGEMENT", "SHUTDOWN_RESPONSE"],
        "construct": "PEI",
        "weight": 0.20,
    },
    "financial_debt_pressure": {
        "domains": ["ENVIRONMENTAL_DEMANDS", "INTERNAL_STATE_FACTORS"],
        "subdomains": ["SOCIAL_ENGAGEMENT", "SHUTDOWN_RESPONSE"],
        "construct": "PEI",
        "weight": 0.20,
    },
    "financial_unpredictability": {
        "domains": ["EMOTIONAL_REGULATION", "INTERNAL_STATE_FACTORS"],
        "subdomains": ["EMOTIONAL_REGULATION", "SHUTDOWN_RESPONSE"],
        "construct": "PEI",
        "weight": 0.15,
    },
    "financial_obligation_complexity": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS"],
        "subdomains": ["PLANNING", "ORGANIZATION"],
        "construct": "PEI",
        "weight": 0.15,
    },
    "financial_urgency_load": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS", "BEHAVIORAL_PATTERNS"],
        "subdomains": ["TASK_INITIATION", "RESPONSE_ACTIVATION"],
        "construct": "PEI",
        "weight": 0.15,
    },
    "financial_household_pressure": {
        "domains": ["ENVIRONMENTAL_DEMANDS", "MOTIVATIONAL_SYSTEMS"],
        "subdomains": ["SOCIAL_ENGAGEMENT", "FOLLOW_THROUGH"],
        "construct": "PEI",
        "weight": 0.15,
    },
}

# Health BHP subvariable mappings
HEALTH_BHP_SOURCES = {
    "health_routine_consistency": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS", "BEHAVIORAL_PATTERNS"],
        "subdomains": ["ORGANIZATION", "TASK_COMPLETION"],
        "construct": "BHP",
        "weight": 0.20,
    },
    "health_nourishment_regulation": {
        "domains": ["EMOTIONAL_REGULATION"],
        "subdomains": ["EMOTIONAL_REGULATION"],
        "construct": "BHP",
        "weight": 0.15,
    },
    "health_movement_follow_through": {
        "domains": ["MOTIVATIONAL_SYSTEMS", "BEHAVIORAL_PATTERNS"],
        "subdomains": ["FOLLOW_THROUGH", "TASK_COMPLETION"],
        "construct": "BHP",
        "weight": 0.15,
    },
    "health_sleep_support": {
        "domains": ["INTERNAL_STATE_FACTORS", "EMOTIONAL_REGULATION"],
        "subdomains": ["SHUTDOWN_RESPONSE", "EMOTIONAL_REGULATION"],
        "construct": "BHP",
        "weight": 0.15,
    },
    "health_self_care_initiation": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS"],
        "subdomains": ["TASK_INITIATION", "ACTIVATION"],
        "construct": "BHP",
        "weight": 0.15,
    },
    "health_coping_flexibility": {
        "domains": ["BEHAVIORAL_PATTERNS", "EMOTIONAL_REGULATION"],
        "subdomains": ["HELP_SEEKING", "EMOTIONAL_REGULATION"],
        "construct": "BHP",
        "weight": 0.10,
    },
    "health_recovery_capacity": {
        "domains": ["INTERNAL_STATE_FACTORS", "MOTIVATIONAL_SYSTEMS"],
        "subdomains": ["SHUTDOWN_RESPONSE", "FOLLOW_THROUGH"],
        "construct": "BHP",
        "weight": 0.10,
    },
}

# Health PEI subvariable mappings
HEALTH_PEI_SOURCES = {
    "health_schedule_overload": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS", "ENVIRONMENTAL_DEMANDS"],
        "subdomains": ["PLANNING", "SOCIAL_ENGAGEMENT"],
        "construct": "PEI",
        "weight": 0.20,
    },
    "health_caregiving_load": {
        "domains": ["ENVIRONMENTAL_DEMANDS", "BEHAVIORAL_PATTERNS"],
        "subdomains": ["SOCIAL_ENGAGEMENT", "HELP_SEEKING"],
        "construct": "PEI",
        "weight": 0.15,
    },
    "health_exhaustion_pressure": {
        "domains": ["INTERNAL_STATE_FACTORS", "EMOTIONAL_REGULATION"],
        "subdomains": ["SHUTDOWN_RESPONSE", "EMOTIONAL_REGULATION"],
        "construct": "PEI",
        "weight": 0.20,
    },
    "health_disruption": {
        "domains": ["EXECUTIVE_FUNCTION_SKILLS", "COGNITIVE_CONTROL"],
        "subdomains": ["ORGANIZATION", "SUSTAINED_ATTENTION"],
        "construct": "PEI",
        "weight": 0.15,
    },
    "health_stress_intensity": {
        "domains": ["EMOTIONAL_REGULATION", "INTERNAL_STATE_FACTORS"],
        "subdomains": ["EMOTIONAL_REGULATION", "SHUTDOWN_RESPONSE"],
        "construct": "PEI",
        "weight": 0.15,
    },
    "health_limited_resources": {
        "domains": ["ENVIRONMENTAL_DEMANDS"],
        "subdomains": ["SOCIAL_ENGAGEMENT"],
        "construct": "PEI",
        "weight": 0.10,
    },
    "health_instability": {
        "domains": ["ENVIRONMENTAL_DEMANDS", "INTERNAL_STATE_FACTORS"],
        "subdomains": ["SOCIAL_ENGAGEMENT", "SHUTDOWN_RESPONSE"],
        "construct": "PEI",
        "weight": 0.05,
    },
}


# =============================================================================
# SUBVARIABLE COMPUTATION
# =============================================================================

def _compute_subvariable(
    source_def: dict,
    subdomain_scores: dict[str, dict[str, float]],
    domain_construct_balance: dict[str, dict],
) -> float:
    """
    Compute a single subvariable score (0-100) from existing assessment data.

    Uses subdomain scores filtered by the target construct to derive a proxy
    score for the applied domain subvariable.
    """
    scores = []

    # Gather relevant subdomain scores
    for domain in source_def["domains"]:
        if domain in subdomain_scores:
            for sub_name in source_def["subdomains"]:
                if sub_name in subdomain_scores[domain]:
                    scores.append(subdomain_scores[domain][sub_name])

    # Also factor in construct balance from the target domains
    target_construct = source_def["construct"]
    for domain in source_def["domains"]:
        if domain in domain_construct_balance:
            cb = domain_construct_balance[domain]
            construct_val = cb.get(target_construct)
            if construct_val is not None:
                scores.append(construct_val)

    if not scores:
        return 50.0  # neutral default

    # Average and scale to 0-100
    avg = sum(scores) / len(scores)
    # Scores are 0-1 normalized, scale to 0-100
    return round(_clamp(avg * 100, 0, 100), 2)


def _compute_subvariables(
    source_map: dict,
    subdomain_scores: dict[str, dict[str, float]],
    domain_construct_balance: dict[str, dict],
) -> dict[str, float]:
    """Compute all subvariables for a BHP or PEI component."""
    result = {}
    for var_name, source_def in source_map.items():
        result[var_name] = _compute_subvariable(
            source_def, subdomain_scores, domain_construct_balance
        )
    return result


def _compute_weighted_score(subvariables: dict[str, float], source_map: dict) -> float:
    """
    Compute the weighted BHP or PEI score from subvariables.
    Uses weights defined in the source mapping.
    """
    total = 0.0
    weight_sum = 0.0
    for var_name, source_def in source_map.items():
        if var_name in subvariables:
            w = source_def["weight"]
            total += subvariables[var_name] * w
            weight_sum += w

    if weight_sum == 0:
        return 50.0
    return round(total / weight_sum, 2)


# =============================================================================
# FLAG DETECTION
# =============================================================================

# Financial flags: triggered by specific subvariable patterns
FINANCIAL_FLAG_RULES = {
    "financial_avoidance_flag": {
        "description": "Financial avoidance under pressure",
        "condition": lambda sv: sv.get("financial_planning_consistency", 100) < 35
                     and sv.get("financial_emotional_regulation", 100) < 40,
    },
    "financial_impulsive_spending_flag": {
        "description": "Impulsive spending under stress",
        "condition": lambda sv: sv.get("financial_delayed_gratification", 100) < 35
                     and sv.get("financial_emotional_regulation", 100) < 45,
    },
    "financial_shutdown_flag": {
        "description": "Financial shutdown patterns",
        "condition": lambda sv: sv.get("financial_planning_consistency", 100) < 30
                     and sv.get("financial_follow_through", 100) < 30,
    },
    "financial_conflict_flag": {
        "description": "Financial conflict triggers",
        "condition": lambda sv: sv.get("financial_emotional_regulation", 100) < 35
                     and sv.get("financial_decision_clarity", 100) < 40,
    },
    "financial_overcontrol_flag": {
        "description": "Financial overcontrol patterns",
        "condition": lambda sv: sv.get("financial_organization", 100) > 80
                     and sv.get("financial_emotional_regulation", 100) < 40,
    },
    "financial_inconsistent_planning_flag": {
        "description": "Inconsistent financial planning",
        "condition": lambda sv: sv.get("financial_planning_consistency", 100) < 40
                     and sv.get("financial_organization", 100) < 45,
    },
    "financial_survival_mode_flag": {
        "description": "Financial survival mode",
        "condition": lambda sv_bhp, pei=None: pei is not None and pei > 75
                     and sv_bhp.get("financial_follow_through", 100) < 35,
    },
}

HEALTH_FLAG_RULES = {
    "health_stress_eating_flag": {
        "description": "Stress eating patterns",
        "condition": lambda sv: sv.get("health_nourishment_regulation", 100) < 35
                     and sv.get("health_coping_flexibility", 100) < 45,
    },
    "health_under_eating_flag": {
        "description": "Under-eating under pressure",
        "condition": lambda sv: sv.get("health_nourishment_regulation", 100) < 30
                     and sv.get("health_self_care_initiation", 100) < 35,
    },
    "health_sleep_collapse_flag": {
        "description": "Sleep collapse under load",
        "condition": lambda sv: sv.get("health_sleep_support", 100) < 35
                     and sv.get("health_recovery_capacity", 100) < 40,
    },
    "health_self_care_avoidance_flag": {
        "description": "Self-care avoidance",
        "condition": lambda sv: sv.get("health_self_care_initiation", 100) < 35
                     and sv.get("health_routine_consistency", 100) < 40,
    },
    "health_all_or_nothing_flag": {
        "description": "All-or-nothing health cycles",
        "condition": lambda sv: sv.get("health_routine_consistency", 100) < 40
                     and sv.get("health_movement_follow_through", 100) < 35,
    },
    "health_burnout_flag": {
        "description": "Burnout indicators",
        "condition": lambda sv: sv.get("health_recovery_capacity", 100) < 30
                     and sv.get("health_coping_flexibility", 100) < 35,
    },
    "health_maladaptive_coping_flag": {
        "description": "Maladaptive coping patterns",
        "condition": lambda sv: sv.get("health_coping_flexibility", 100) < 30
                     and sv.get("health_self_care_initiation", 100) < 35,
    },
}


def _detect_flags(
    flag_rules: dict,
    all_subvariables: dict[str, float],
    pei_score: float | None = None,
) -> dict[str, Any]:
    """Detect active flags based on subvariable patterns (BHP + PEI combined)."""
    flags = {}
    for flag_name, rule in flag_rules.items():
        try:
            # Special case for survival_mode_flag which needs PEI score
            if flag_name == "financial_survival_mode_flag":
                triggered = rule["condition"](all_subvariables, pei_score)
            else:
                triggered = rule["condition"](all_subvariables)
            flags[flag_name] = {
                "triggered": triggered,
                "description": rule["description"],
            }
        except Exception:
            flags[flag_name] = {
                "triggered": False,
                "description": rule["description"],
            }
    return flags


# =============================================================================
# AIMS TARGET GENERATION
# =============================================================================

FINANCIAL_AIMS_TARGETS = {
    "low": [
        {"phase": "Awareness", "target": "Identify financial shutdown triggers and avoidance patterns"},
        {"phase": "Intervention", "target": "Create a 5-minute daily money check-in ritual"},
        {"phase": "Mastery", "target": "Build one consistent bill-paying routine"},
        {"phase": "Sustain", "target": "Develop a long-term financial stability plan"},
    ],
    "mid": [
        {"phase": "Awareness", "target": "Track spending patterns under stress"},
        {"phase": "Intervention", "target": "Set up automated financial tracking"},
        {"phase": "Mastery", "target": "Improve financial follow-through consistency"},
        {"phase": "Sustain", "target": "Maintain financial planning under rising pressure"},
    ],
    "high": [
        {"phase": "Awareness", "target": "Recognize financial strengths and optimize capacity"},
        {"phase": "Intervention", "target": "Refine financial decision-making strategies"},
        {"phase": "Mastery", "target": "Expand financial planning across life domains"},
        {"phase": "Sustain", "target": "Generalize financial executive functioning gains"},
    ],
}

HEALTH_AIMS_TARGETS = {
    "low": [
        {"phase": "Awareness", "target": "Notice when exhaustion triggers self-care shutdown"},
        {"phase": "Intervention", "target": "Implement a 10-minute minimum viable self-care routine"},
        {"phase": "Mastery", "target": "Protect one non-negotiable health anchor daily"},
        {"phase": "Sustain", "target": "Build sustainable health routines under real-world load"},
    ],
    "mid": [
        {"phase": "Awareness", "target": "Track health behavior consistency under varying load"},
        {"phase": "Intervention", "target": "Stabilize sleep and eating routines under pressure"},
        {"phase": "Mastery", "target": "Increase movement follow-through consistency"},
        {"phase": "Sustain", "target": "Maintain health routines during high-demand periods"},
    ],
    "high": [
        {"phase": "Awareness", "target": "Recognize health routine strengths and capacity reserves"},
        {"phase": "Intervention", "target": "Optimize self-care strategies for peak performance"},
        {"phase": "Mastery", "target": "Expand health routines to support all life domains"},
        {"phase": "Sustain", "target": "Generalize health executive functioning gains"},
    ],
}


def _select_aims_targets(domain_score: float, targets_map: dict) -> list[dict]:
    """Select appropriate AIMS targets based on domain score."""
    if domain_score < 35:
        return targets_map["low"]
    elif domain_score < 65:
        return targets_map["mid"]
    else:
        return targets_map["high"]


# =============================================================================
# INTERPRETATION GENERATION
# =============================================================================

def _generate_interpretation(
    domain_type: str,
    domain_score: float,
    bhp: float,
    pei: float,
    status_band: str,
    flags: dict,
) -> dict:
    """Generate 'When Stable' and 'When Loaded' interpretations."""

    active_flags = [f["description"] for f in flags.values() if f.get("triggered")]

    if domain_type == "financial":
        if domain_score >= 65:
            when_stable = (
                "Your financial planning capacity is strong. You can organize bills, "
                "maintain budgets, and make clear financial decisions when pressure is manageable."
            )
            when_loaded = (
                "Under rising financial demand, you may need extra structure to maintain "
                "consistency, but your core financial executive functions remain accessible."
            )
        elif domain_score >= 35:
            when_stable = (
                "Your financial system shows usable planning capacity, but external financial "
                "pressure may reduce consistency under rising load."
            )
            when_loaded = (
                "When financial demands increase, planning consistency and follow-through "
                "may weaken. Decision clarity can become compromised under pressure."
            )
        else:
            when_stable = (
                "Your financial executive functioning is under significant strain. "
                "Basic financial planning may feel overwhelming even during calm periods."
            )
            when_loaded = (
                "Financial stress triggers shutdown and avoidance. Planning capacity "
                "collapses under the weight of debt pressure, unpredictability, and urgent demands."
            )
    else:  # health
        if domain_score >= 65:
            when_stable = (
                "Your health-supportive routines are strong. You maintain consistent eating, "
                "movement, and sleep patterns when life demands are manageable."
            )
            when_loaded = (
                "Under rising load, you may need intentional effort to protect health routines, "
                "but your self-care capacity remains accessible."
            )
        elif domain_score >= 35:
            when_stable = (
                "You have moderate capacity to maintain basic health routines and make "
                "nourishing choices when external demands are manageable."
            )
            when_loaded = (
                "Health-supportive routines may weaken when stress, fatigue, or schedule "
                "demands increase. Consistency becomes harder to maintain."
            )
        else:
            when_stable = (
                "Your health executive functioning is under significant strain. "
                "Self-care routines may feel impossible even during calmer periods."
            )
            when_loaded = (
                "Schedule overload and exhaustion crush health-supportive behaviors. "
                "Sleep collapses, eating becomes irregular, and self-care feels impossible."
            )

    # Block 5: Domain Interpretation narrative — likely pattern, source of strain,
    # whether issue is mostly capacity, load, or mismatch
    if bhp > pei + 10:
        strain_source = "capacity-driven"
        if domain_type == "financial":
            domain_narrative = (
                f"Your financial executive functioning is primarily supported by strong internal capacity "
                f"(BHP: {bhp:.0f}) that currently exceeds external demand (PEI: {pei:.0f}). "
                f"Your planning, regulation, and follow-through systems are functioning well relative "
                f"to financial pressures. The main pattern here is one of maintained capacity — "
                f"your system has enough internal resource to manage current financial demands."
            )
        else:
            domain_narrative = (
                f"Your health executive functioning benefits from solid internal capacity "
                f"(BHP: {bhp:.0f}) that outpaces current external demands (PEI: {pei:.0f}). "
                f"Your routines around eating, movement, sleep, and self-care are holding steady "
                f"under current load. The primary pattern is one of sustainable health behavior — "
                f"your system can maintain health-supportive routines under present conditions."
            )
    elif pei > bhp + 10:
        strain_source = "load-driven"
        if domain_type == "financial":
            domain_narrative = (
                f"Your financial executive functioning is under strain primarily from external pressure "
                f"(PEI: {pei:.0f}) that exceeds your internal capacity (BHP: {bhp:.0f}). "
                f"The source of difficulty is not a lack of financial skill, but the weight of financial "
                f"demands — debt pressure, instability, or obligation complexity — overwhelming your "
                f"planning and regulation systems. Reducing external load is likely to be more effective "
                f"than building new skills alone."
            )
        else:
            domain_narrative = (
                f"Your health executive functioning is strained primarily by external demands "
                f"(PEI: {pei:.0f}) outweighing your internal capacity (BHP: {bhp:.0f}). "
                f"The difficulty is not a lack of health knowledge or intention, but the pressure of "
                f"schedule overload, exhaustion, or caregiving demands disrupting your ability to "
                f"maintain routines. Addressing the external load is likely more impactful than "
                f"willpower-based strategies alone."
            )
    else:
        strain_source = "mismatch"
        if domain_type == "financial":
            domain_narrative = (
                f"Your financial executive functioning shows a close balance between internal capacity "
                f"(BHP: {bhp:.0f}) and external demand (PEI: {pei:.0f}). This mismatch pattern means "
                f"your system can function adequately in calm periods but becomes vulnerable when either "
                f"capacity dips or demands spike. Small changes in either direction — building one "
                f"planning habit or reducing one source of financial pressure — could shift the balance "
                f"meaningfully."
            )
        else:
            domain_narrative = (
                f"Your health executive functioning shows a close balance between internal capacity "
                f"(BHP: {bhp:.0f}) and external pressure (PEI: {pei:.0f}). This mismatch pattern means "
                f"your health routines hold during stable periods but break down when demands rise. "
                f"Small adjustments — anchoring one non-negotiable routine or reducing one source of "
                f"schedule pressure — could meaningfully improve consistency."
            )

    return {
        "when_stable": when_stable,
        "when_loaded": when_loaded,
        "domain_narrative": domain_narrative,
        "strain_source": strain_source,
        "primary_risk_flags": active_flags[:4],
    }


# =============================================================================
# MAIN COMPUTATION FUNCTIONS
# =============================================================================

def compute_financial_ef(
    subdomain_scores: dict[str, dict[str, float]],
    domain_construct_balance: dict[str, dict],
) -> dict:
    """
    Compute the Financial Executive Functioning Profile™.

    Returns the complete financial_ef domain object.
    """
    # Compute BHP subvariables
    bhp_subvars = _compute_subvariables(
        FINANCIAL_BHP_SOURCES, subdomain_scores, domain_construct_balance
    )
    bhp = _compute_weighted_score(bhp_subvars, FINANCIAL_BHP_SOURCES)

    # Compute PEI subvariables
    pei_subvars = _compute_subvariables(
        FINANCIAL_PEI_SOURCES, subdomain_scores, domain_construct_balance
    )
    pei = _compute_weighted_score(pei_subvars, FINANCIAL_PEI_SOURCES)

    # Compute load balance and domain score
    load_balance = round(bhp - pei, 2)
    domain_score = round(_clamp(50 + load_balance, 0, 100), 2)
    status_band = _assign_status_band(load_balance)

    # Detect flags (pass all subvariables so flags can reference BHP or PEI subvars)
    all_subvars = {**bhp_subvars, **pei_subvars}
    flags = _detect_flags(FINANCIAL_FLAG_RULES, all_subvars, pei)

    # Generate AIMS targets
    aims_targets = _select_aims_targets(domain_score, FINANCIAL_AIMS_TARGETS)

    # Generate interpretation
    interpretation = _generate_interpretation(
        "financial", domain_score, bhp, pei, status_band, flags
    )

    logger.info(
        f"Financial EF computed: bhp={bhp}, pei={pei}, "
        f"load_balance={load_balance}, domain_score={domain_score}, "
        f"status_band={status_band}"
    )

    return {
        "domain_name": "Financial Executive Functioning Profile™",
        "domain_key": "financial_ef",
        "bhp": bhp,
        "pei": pei,
        "load_balance": load_balance,
        "domain_score": domain_score,
        "status_band": status_band,
        "status_band_color": STATUS_BAND_COLORS.get(status_band, "#6B7280"),
        "subvariables": {**bhp_subvars, **pei_subvars},
        "flags": flags,
        "aims_targets": aims_targets,
        "interpretation": interpretation,
    }


def compute_health_ef(
    subdomain_scores: dict[str, dict[str, float]],
    domain_construct_balance: dict[str, dict],
) -> dict:
    """
    Compute the Health & Fitness Executive Functioning Profile™.

    Returns the complete health_ef domain object.
    """
    # Compute BHP subvariables
    bhp_subvars = _compute_subvariables(
        HEALTH_BHP_SOURCES, subdomain_scores, domain_construct_balance
    )
    bhp = _compute_weighted_score(bhp_subvars, HEALTH_BHP_SOURCES)

    # Compute PEI subvariables
    pei_subvars = _compute_subvariables(
        HEALTH_PEI_SOURCES, subdomain_scores, domain_construct_balance
    )
    pei = _compute_weighted_score(pei_subvars, HEALTH_PEI_SOURCES)

    # Compute load balance and domain score
    load_balance = round(bhp - pei, 2)
    domain_score = round(_clamp(50 + load_balance, 0, 100), 2)
    status_band = _assign_status_band(load_balance)

    # Detect flags (pass all subvariables so flags can reference BHP or PEI subvars)
    all_subvars = {**bhp_subvars, **pei_subvars}
    flags = _detect_flags(HEALTH_FLAG_RULES, all_subvars, pei)

    # Generate AIMS targets
    aims_targets = _select_aims_targets(domain_score, HEALTH_AIMS_TARGETS)

    # Generate interpretation
    interpretation = _generate_interpretation(
        "health", domain_score, bhp, pei, status_band, flags
    )

    logger.info(
        f"Health EF computed: bhp={bhp}, pei={pei}, "
        f"load_balance={load_balance}, domain_score={domain_score}, "
        f"status_band={status_band}"
    )

    return {
        "domain_name": "Health & Fitness Executive Functioning Profile™",
        "domain_key": "health_ef",
        "bhp": bhp,
        "pei": pei,
        "load_balance": load_balance,
        "domain_score": domain_score,
        "status_band": status_band,
        "status_band_color": STATUS_BAND_COLORS.get(status_band, "#6B7280"),
        "subvariables": {**bhp_subvars, **pei_subvars},
        "flags": flags,
        "aims_targets": aims_targets,
        "interpretation": interpretation,
    }


def compute_applied_domains(
    subdomain_scores: dict[str, dict[str, float]],
    domain_construct_balance: dict[str, dict],
) -> dict:
    """
    Compute both applied EF domains.

    Args:
        subdomain_scores: From scoring.aggregate_by_subdomain()
        domain_construct_balance: From scoring.compute_domain_construct_balance()

    Returns:
        {
            "financial_ef": {...},
            "health_ef": {...},
        }
    """
    return {
        "financial_ef": compute_financial_ef(subdomain_scores, domain_construct_balance),
        "health_ef": compute_health_ef(subdomain_scores, domain_construct_balance),
    }
