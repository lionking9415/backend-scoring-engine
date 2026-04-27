"""
Cross-Domain Pattern Engine — Phase 4.5

Computes the structured analytical layer the Cosmic Integration Report™
requires (per docs/Cosmic-Integration/Cosmic Integrat Bundle Logic&System.md):

  1. Pattern Convergence — domains showing the same load signature
  2. Domain Interdependence — which domain pressure transfers to which
  3. Cross-Lens Strain Correlations — load_balance gaps across lenses
  4. Compensation Patterns — strong domain offsetting weak one
  5. System-Wide Sensitivity Mapping — vulnerabilities present everywhere

Inputs are the same scoring artifacts already computed by scoring_engine:
  - domain_profiles (BHP/PEI per core domain)
  - applied_domains.financial_ef / health_ef (with subvariables + flags)
  - construct_scores (PEI, BHP)

Outputs are deterministic, JSON-friendly structures consumed by:
  - The AI report-generation prompt
  - The frontend Galaxy Convergence Map™ and Load Flow visuals
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# CORE DOMAIN -> LENS MAPPING
# Used to estimate per-lens stability/load when only a single assessment
# is available. Derived from docs/Universal Prompt Rules.md domain semantics.
# =============================================================================

LENS_DOMAIN_AFFINITY = {
    "STUDENT_SUCCESS": {
        "primary": ["COGNITIVE_CONTROL", "EXECUTIVE_FUNCTION_SKILLS"],
        "secondary": ["MOTIVATIONAL_SYSTEMS", "BEHAVIORAL_PATTERNS"],
        "load_drivers": ["ENVIRONMENTAL_DEMANDS"],
    },
    "PERSONAL_LIFESTYLE": {
        "primary": ["INTERNAL_STATE_FACTORS", "EMOTIONAL_REGULATION"],
        "secondary": ["BEHAVIORAL_PATTERNS", "EXECUTIVE_FUNCTION_SKILLS"],
        "load_drivers": ["ENVIRONMENTAL_DEMANDS"],
    },
    "PROFESSIONAL_LEADERSHIP": {
        "primary": ["EXECUTIVE_FUNCTION_SKILLS", "BEHAVIORAL_PATTERNS"],
        "secondary": ["COGNITIVE_CONTROL", "MOTIVATIONAL_SYSTEMS"],
        "load_drivers": ["ENVIRONMENTAL_DEMANDS"],
    },
    "FAMILY_ECOSYSTEM": {
        "primary": ["EMOTIONAL_REGULATION", "BEHAVIORAL_PATTERNS"],
        "secondary": ["INTERNAL_STATE_FACTORS", "MOTIVATIONAL_SYSTEMS"],
        "load_drivers": ["ENVIRONMENTAL_DEMANDS"],
    },
}


# =============================================================================
# FLOW DEFINITIONS (which-domain-affects-which)
# Strength is computed dynamically from the user's actual scores + flags.
# =============================================================================

# Each entry: (from, to, base_weight, condition_keys)
# condition_keys reference subvariables / flags that AMPLIFY the flow strength.
FLOW_PAIRS = [
    # Financial chain
    ("financial", "emotional", 0.40, {"flags": ["financial_avoidance_flag",
                                                  "financial_conflict_flag",
                                                  "financial_shutdown_flag"]}),
    ("financial", "academic", 0.30, {"flags": ["financial_inconsistent_planning_flag"]}),
    ("financial", "health", 0.25, {"flags": ["financial_survival_mode_flag"]}),
    ("financial", "family", 0.30, {"flags": ["financial_household_pressure_flag",
                                              "financial_conflict_flag"]}),

    # Health chain
    ("health", "emotional", 0.40, {"flags": ["health_burnout_flag",
                                              "health_sleep_collapse_flag"]}),
    ("health", "work", 0.45, {"flags": ["health_burnout_flag",
                                         "health_self_care_avoidance_flag"]}),
    ("health", "academic", 0.30, {"flags": ["health_sleep_collapse_flag"]}),
    ("health", "family", 0.25, {"flags": ["health_maladaptive_coping_flag"]}),

    # Emotional chain (regulation feeds everything)
    ("emotional", "academic", 0.30, {"domains": ["EMOTIONAL_REGULATION"]}),
    ("emotional", "work", 0.30, {"domains": ["EMOTIONAL_REGULATION"]}),
    ("emotional", "family", 0.40, {"domains": ["EMOTIONAL_REGULATION"]}),

    # Work / Academic ↔ Family
    ("work", "family", 0.30, {"domains": ["ENVIRONMENTAL_DEMANDS"]}),
    ("academic", "family", 0.20, {"domains": ["ENVIRONMENTAL_DEMANDS"]}),
]


# =============================================================================
# UTILITIES
# =============================================================================

def _domain_score_map(domains: list[dict]) -> dict[str, float]:
    """Build a {DOMAIN_NAME: 0..1 score} lookup from output.domains list."""
    return {d["name"]: d.get("score", 0.5) for d in (domains or []) if d.get("name")}


def _domain_construct_balance(domains: list[dict]) -> dict[str, dict]:
    """Build a {DOMAIN_NAME: {PEI, BHP}} lookup from output.domains list."""
    out: dict[str, dict] = {}
    for d in domains or []:
        cb = d.get("construct_balance") or {}
        out[d["name"]] = {
            "PEI": cb.get("PEI"),
            "BHP": cb.get("BHP"),
        }
    return out


def _active_flag_keys(applied_domain: dict) -> set[str]:
    """Extract triggered flag keys from a single applied_domain dict."""
    flags = applied_domain.get("flags", {}) or {}
    return {
        name for name, info in flags.items()
        if isinstance(info, dict) and info.get("triggered")
    }


# =============================================================================
# 1. PER-LENS PROFILE ESTIMATION
# =============================================================================

def estimate_lens_profiles(
    construct_scores: dict,
    domains: list[dict],
    applied_domains: dict,
) -> dict[str, dict]:
    """
    Estimate per-lens (PEI, BHP, stability) using lens-domain affinity.

    Returns {lens_key: {pei, bhp, stability, load_balance, status}}.
    """
    base_pei = float(construct_scores.get("PEI_score", 0.5) or 0.5)
    base_bhp = float(construct_scores.get("BHP_score", 0.5) or 0.5)
    domain_map = _domain_score_map(domains)
    fin_score = applied_domains.get("financial_ef", {}).get("domain_score", 50) / 100.0
    health_score = applied_domains.get("health_ef", {}).get("domain_score", 50) / 100.0

    profiles: dict[str, dict] = {}
    for lens_key, affinity in LENS_DOMAIN_AFFINITY.items():
        primary_scores = [domain_map[d] for d in affinity["primary"] if d in domain_map]
        secondary_scores = [domain_map[d] for d in affinity["secondary"] if d in domain_map]
        load_scores = [domain_map[d] for d in affinity["load_drivers"] if d in domain_map]

        # BHP per lens: weighted blend of primary (60%) + secondary (25%) + base (15%)
        primary_avg = sum(primary_scores) / len(primary_scores) if primary_scores else base_bhp
        secondary_avg = sum(secondary_scores) / len(secondary_scores) if secondary_scores else base_bhp
        bhp = 0.60 * primary_avg + 0.25 * secondary_avg + 0.15 * base_bhp

        # PEI per lens: load_drivers (60%) + base (40%)
        load_avg = sum(load_scores) / len(load_scores) if load_scores else base_pei
        pei = 0.60 * load_avg + 0.40 * base_pei

        # Lens-specific flavoring
        if lens_key == "PERSONAL_LIFESTYLE":
            # Lifestyle stability is heavily affected by financial + health EF
            bhp = 0.7 * bhp + 0.15 * fin_score + 0.15 * health_score
        elif lens_key == "FAMILY_ECOSYSTEM":
            # Family load is amplified by financial pressure
            pei = min(1.0, pei + 0.08 * (1 - fin_score))
        elif lens_key == "PROFESSIONAL_LEADERSHIP":
            # Work capacity is reduced by health strain
            bhp = 0.85 * bhp + 0.15 * health_score
        elif lens_key == "STUDENT_SUCCESS":
            bhp = 0.85 * bhp + 0.15 * health_score

        bhp = round(max(0.0, min(1.0, bhp)), 3)
        pei = round(max(0.0, min(1.0, pei)), 3)
        load_balance = round(bhp - pei, 3)

        if load_balance >= 0.15:
            status = "stable"
        elif load_balance >= -0.05:
            status = "transitional"
        elif load_balance >= -0.20:
            status = "strained"
        else:
            status = "saturated"

        profiles[lens_key] = {
            "pei": pei,
            "bhp": bhp,
            "load_balance": load_balance,
            "stability": bhp,
            "status": status,
        }
    return profiles


# =============================================================================
# 2. CROSS-DOMAIN LOAD-TRANSFER FLOWS
# =============================================================================

def compute_flows(
    construct_scores: dict,
    domains: list[dict],
    applied_domains: dict,
) -> list[dict]:
    """
    Compute strength-weighted load transfer flows for the LoadFlow visual
    and the Cross-Domain Load Transfer Analysis section of the cosmic report.
    """
    base_pei = float(construct_scores.get("PEI_score", 0.5) or 0.5)
    domain_map = _domain_score_map(domains)
    fin_active = _active_flag_keys(applied_domains.get("financial_ef", {}))
    health_active = _active_flag_keys(applied_domains.get("health_ef", {}))

    fin_score = applied_domains.get("financial_ef", {}).get("domain_score", 50) / 100.0
    health_score = applied_domains.get("health_ef", {}).get("domain_score", 50) / 100.0

    # Domain-level pressure signals (low score = high pressure / strain)
    pressure_signals = {
        "financial": 1.0 - fin_score,
        "health": 1.0 - health_score,
        "emotional": 1.0 - domain_map.get("EMOTIONAL_REGULATION", 0.5),
        "academic": base_pei,
        "work": base_pei,
        "family": 1.0 - domain_map.get("BEHAVIORAL_PATTERNS", 0.5),
    }

    flows = []
    for src, dst, base_w, conditions in FLOW_PAIRS:
        amplifier = 0.0
        rationale_parts = []

        # Flag-based amplification
        for flag in conditions.get("flags", []):
            if flag in fin_active or flag in health_active:
                amplifier += 0.15
                rationale_parts.append(flag.replace("_", " "))

        # Domain-based amplification
        for dom in conditions.get("domains", []):
            score = domain_map.get(dom, 0.5)
            if score < 0.4:  # weak domain → stronger flow
                amplifier += 0.10
                rationale_parts.append(f"weak {dom.lower()}")

        # Source-pressure amplification
        src_pressure = pressure_signals.get(src, base_pei)
        amplifier += src_pressure * 0.20

        strength = round(min(1.0, base_w + amplifier), 3)
        rationale = "; ".join(rationale_parts) or "baseline cross-domain coupling"
        flows.append({
            "from": src,
            "to": dst,
            "strength": strength,
            "rationale": rationale,
        })

    # Sort strongest-first for visual prioritization
    flows.sort(key=lambda f: f["strength"], reverse=True)
    return flows


# =============================================================================
# 3. COMPENSATION PATTERNS
# =============================================================================

def compute_compensation_patterns(
    domains: list[dict],
    applied_domains: dict,
) -> list[dict]:
    """
    Identify domains where a strong area is offsetting a weaker one
    (BHP > PEI within the same domain, or one domain's BHP > 0.6 while
    a coupled domain's BHP < 0.4).
    """
    domain_map = _domain_score_map(domains)
    cb_map = _domain_construct_balance(domains)
    patterns = []

    # Within-domain compensation (BHP outpaces PEI clearly)
    for d_name, cb in cb_map.items():
        pei = cb.get("PEI")
        bhp = cb.get("BHP")
        if pei is None or bhp is None:
            continue
        gap = bhp - pei
        if gap >= 0.20:
            patterns.append({
                "stabilizer": d_name,
                "vulnerability": f"{d_name} (load)",
                "gap": round(gap, 3),
                "type": "within_domain",
                "narrative": (
                    f"{d_name.replace('_', ' ').title()} capacity exceeds its load "
                    f"by {gap:.2f} — internal capacity is currently absorbing demand."
                ),
            })

    # Cross-domain pairs (executive function compensating for emotional, etc.)
    coupling_pairs = [
        ("EXECUTIVE_FUNCTION_SKILLS", "EMOTIONAL_REGULATION"),
        ("COGNITIVE_CONTROL", "INTERNAL_STATE_FACTORS"),
        ("MOTIVATIONAL_SYSTEMS", "BEHAVIORAL_PATTERNS"),
        ("EMOTIONAL_REGULATION", "INTERNAL_STATE_FACTORS"),
    ]
    for stabilizer, vuln in coupling_pairs:
        s_score = domain_map.get(stabilizer)
        v_score = domain_map.get(vuln)
        if s_score is None or v_score is None:
            continue
        gap = s_score - v_score
        if s_score >= 0.6 and v_score <= 0.45:
            patterns.append({
                "stabilizer": stabilizer,
                "vulnerability": vuln,
                "gap": round(gap, 3),
                "type": "cross_domain",
                "narrative": (
                    f"Strong {stabilizer.replace('_', ' ').lower()} is currently "
                    f"compensating for weaker {vuln.replace('_', ' ').lower()}."
                ),
            })

    # Applied domain compensation
    fin_score = applied_domains.get("financial_ef", {}).get("domain_score", 50)
    health_score = applied_domains.get("health_ef", {}).get("domain_score", 50)
    if fin_score >= 65 and health_score <= 40:
        patterns.append({
            "stabilizer": "Financial Executive Functioning",
            "vulnerability": "Health & Fitness Executive Functioning",
            "gap": round((fin_score - health_score) / 100.0, 3),
            "type": "applied_domain",
            "narrative": (
                "Strong financial regulation is helping maintain stability while "
                "health routines are under strain."
            ),
        })
    elif health_score >= 65 and fin_score <= 40:
        patterns.append({
            "stabilizer": "Health & Fitness Executive Functioning",
            "vulnerability": "Financial Executive Functioning",
            "gap": round((health_score - fin_score) / 100.0, 3),
            "type": "applied_domain",
            "narrative": (
                "Strong health-supportive routines are buffering financial-pressure load."
            ),
        })

    patterns.sort(key=lambda p: p["gap"], reverse=True)
    return patterns


# =============================================================================
# 4. SYSTEM-WIDE SENSITIVITIES
# =============================================================================

def compute_system_wide_sensitivities(
    domains: list[dict],
    applied_domains: dict,
) -> list[dict]:
    """
    Identify domains/subvariables that are vulnerable across multiple
    contexts — i.e. low score AND elevated PEI within the domain, or
    triggered flags spanning multiple applied domains.
    """
    domain_map = _domain_score_map(domains)
    cb_map = _domain_construct_balance(domains)
    sensitivities = []

    for d_name, score in domain_map.items():
        cb = cb_map.get(d_name, {})
        pei = cb.get("PEI") or 0
        bhp = cb.get("BHP") or 0
        if score < 0.40 and (pei or 0) > (bhp or 0):
            sensitivities.append({
                "domain": d_name,
                "score": score,
                "pattern": "Low capacity meeting elevated demand — strain emerges across environments.",
            })

    # Applied domain sensitivities
    fin = applied_domains.get("financial_ef", {})
    health = applied_domains.get("health_ef", {})
    if fin.get("domain_score", 100) < 35:
        sensitivities.append({
            "domain": "financial_ef",
            "score": fin.get("domain_score", 0) / 100.0,
            "pattern": "Financial executive functioning under significant strain.",
        })
    if health.get("domain_score", 100) < 35:
        sensitivities.append({
            "domain": "health_ef",
            "score": health.get("domain_score", 0) / 100.0,
            "pattern": "Health-supportive routines collapsing under load.",
        })

    # Triggered flags shared across financial + health → systemic burnout
    fin_active = _active_flag_keys(fin)
    health_active = _active_flag_keys(health)
    if "health_burnout_flag" in health_active and "financial_survival_mode_flag" in fin_active:
        sensitivities.append({
            "domain": "system",
            "score": 0,
            "pattern": (
                "Concurrent burnout signals across health and financial systems — "
                "broad capacity depletion risk."
            ),
        })

    return sensitivities


# =============================================================================
# 5. PATTERN CONVERGENCE
# =============================================================================

def compute_pattern_convergence(
    lens_profiles: dict[str, dict],
) -> dict:
    """
    Detect lenses that share the same load signature.
    Convergence = lenses whose load_balance status matches.
    """
    by_status: dict[str, list[str]] = {}
    for lens, profile in lens_profiles.items():
        st = profile.get("status", "transitional")
        by_status.setdefault(st, []).append(lens)

    convergent = {st: lenses for st, lenses in by_status.items() if len(lenses) >= 2}
    divergent = [lens for lens, p in lens_profiles.items()
                 if all(lens not in v for v in convergent.values())]
    return {
        "convergent_clusters": convergent,
        "divergent_lenses": divergent,
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def compute_cross_domain(
    construct_scores: dict,
    domains: list[dict],
    applied_domains: dict,
) -> dict[str, Any]:
    """Compute the full cross-domain analysis payload."""
    lens_profiles = estimate_lens_profiles(construct_scores, domains, applied_domains)
    flows = compute_flows(construct_scores, domains, applied_domains)
    compensations = compute_compensation_patterns(domains, applied_domains)
    sensitivities = compute_system_wide_sensitivities(domains, applied_domains)
    convergence = compute_pattern_convergence(lens_profiles)

    logger.info(
        "Cross-domain computed: %d flows, %d compensations, %d sensitivities, %d clusters",
        len(flows), len(compensations), len(sensitivities),
        len(convergence.get("convergent_clusters", {})),
    )

    return {
        "lens_profiles": lens_profiles,
        "flows": flows,
        "compensation_patterns": compensations,
        "system_wide_sensitivities": sensitivities,
        "pattern_convergence": convergence,
    }
