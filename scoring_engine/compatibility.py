"""
Compatibility Report — Phase 4.5

Compares two completed BEST Galaxy assessments and produces a synthesis
report describing how the two systems interact: where they reinforce, where
they may compound strain, and where co-regulation potential is highest.

This module is intentionally pair-aware (not n-ary). It assumes both inputs
have already been processed through the scoring engine and contain the
canonical output structure (construct_scores, domains, applied_domains,
cross_domain).

NOTE: This is a structural / load-pattern compatibility report — NOT a
romantic-fit report. It is consumable by any pair (couple, parent/child,
co-founders, teammates).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


COMPATIBILITY_SECTIONS = [
    {
        "key": "overview",
        "title": "System Compatibility Overview",
        "instructions": (
            "Two-paragraph framing: name both systems by their archetype, "
            "describe the shared operating climate (combined PEI/BHP), and "
            "preview the structural compatibility theme."
        ),
    },
    {
        "key": "load_compatibility",
        "title": "Load Pattern Compatibility",
        "instructions": (
            "Compare PEI load profiles. Where are demands aligned? Where do "
            "they offset? Where do they amplify each other? Use observable "
            "language."
        ),
    },
    {
        "key": "capacity_compatibility",
        "title": "Capacity Pattern Compatibility",
        "instructions": (
            "Compare BHP capacity profiles. Highlight where one partner's "
            "strength meets the other's edge, and where shared edges may "
            "compound."
        ),
    },
    {
        "key": "complementary_stabilizers",
        "title": "Complementary Stabilizers",
        "instructions": (
            "Identify strengths in System A that scaffold weaknesses in "
            "System B, and vice versa. Use AIMS framing."
        ),
    },
    {
        "key": "shared_sensitivities",
        "title": "Shared Sensitivities",
        "instructions": (
            "Identify domains where BOTH systems show strain. These are "
            "the areas where the pair must collaboratively scaffold."
        ),
    },
    {
        "key": "co_regulation_aims",
        "title": "Co-Regulation AIMS Pathway",
        "instructions": (
            "Generate a joint AIMS pathway: Awareness → Intervention → "
            "Mastery → Sustain. Each step must be a JOINT action both "
            "systems can take together."
        ),
    },
    {
        "key": "compatibility_summary",
        "title": "Closing Synthesis",
        "instructions": (
            "Single paragraph: name the dominant compatibility theme, the "
            "single highest-leverage co-regulation move, and one shared "
            "edge to watch."
        ),
    },
]


# =============================================================================
# DETERMINISTIC ANALYSIS (drives the AI prompt + the template fallback)
# =============================================================================

def _compute_compatibility_metrics(a: dict, b: dict) -> dict:
    """Compute the deterministic compatibility signal pair."""
    a_cs = a.get("construct_scores", {})
    b_cs = b.get("construct_scores", {})

    a_pei = a_cs.get("PEI_score", 0.5)
    a_bhp = a_cs.get("BHP_score", 0.5)
    b_pei = b_cs.get("PEI_score", 0.5)
    b_bhp = b_cs.get("BHP_score", 0.5)

    combined_pei = (a_pei + b_pei) / 2
    combined_bhp = (a_bhp + b_bhp) / 2

    # Domain alignment — for each shared domain, measure absolute distance
    a_domains = {d["name"]: d.get("score", 0.5) for d in a.get("domains", [])}
    b_domains = {d["name"]: d.get("score", 0.5) for d in b.get("domains", [])}
    shared = set(a_domains) & set(b_domains)
    domain_alignment = []
    for name in shared:
        delta = a_domains[name] - b_domains[name]
        domain_alignment.append({
            "domain": name,
            "a_score": round(a_domains[name], 3),
            "b_score": round(b_domains[name], 3),
            "delta": round(delta, 3),
            "alignment": (
                "aligned" if abs(delta) < 0.10
                else ("complementary" if abs(delta) >= 0.20 else "asymmetric")
            ),
        })
    domain_alignment.sort(key=lambda x: abs(x["delta"]), reverse=True)

    # Shared sensitivities — domains where BOTH are < 0.45
    shared_strain = [
        x for x in domain_alignment
        if x["a_score"] <= 0.45 and x["b_score"] <= 0.45
    ]

    # Complementary pairs — A high, B low (or vice versa) by >= 0.20
    complementary = [x for x in domain_alignment if abs(x["delta"]) >= 0.20]

    return {
        "a_archetype": (a.get("archetype") or {}).get("archetype_id"),
        "b_archetype": (b.get("archetype") or {}).get("archetype_id"),
        "a_pei": round(a_pei, 3),
        "a_bhp": round(a_bhp, 3),
        "b_pei": round(b_pei, 3),
        "b_bhp": round(b_bhp, 3),
        "combined_pei": round(combined_pei, 3),
        "combined_bhp": round(combined_bhp, 3),
        "combined_balance": round(combined_bhp - combined_pei, 3),
        "domain_alignment": domain_alignment,
        "complementary_pairs": complementary,
        "shared_sensitivities": shared_strain,
    }


def _build_metrics_block(metrics: dict) -> str:
    align = "\n".join(
        f"  - {x['domain']}: A={x['a_score']}, B={x['b_score']}, "
        f"delta={x['delta']:+}, {x['alignment']}"
        for x in metrics["domain_alignment"][:10]
    ) or "  (no shared domains)"

    comp = "\n".join(
        f"  - {x['domain']}: gap {x['delta']:+}"
        for x in metrics["complementary_pairs"][:6]
    ) or "  (none)"

    strain = "\n".join(
        f"  - {x['domain']}: A={x['a_score']}, B={x['b_score']}"
        for x in metrics["shared_sensitivities"][:6]
    ) or "  (none)"

    return (
        "## COMPATIBILITY METRICS (objective — do not modify)\n"
        f"System A archetype: {metrics['a_archetype']}\n"
        f"System B archetype: {metrics['b_archetype']}\n\n"
        f"System A: PEI={metrics['a_pei']}, BHP={metrics['a_bhp']}\n"
        f"System B: PEI={metrics['b_pei']}, BHP={metrics['b_bhp']}\n"
        f"Combined: PEI={metrics['combined_pei']}, BHP={metrics['combined_bhp']}, "
        f"balance={metrics['combined_balance']}\n\n"
        f"### Domain alignment (sorted by largest gap)\n{align}\n\n"
        f"### Complementary pairs (gaps >= 0.20)\n{comp}\n\n"
        f"### Shared sensitivities (both <= 0.45)\n{strain}\n"
    )


def _build_section_block() -> str:
    parts = ["## REQUIRED SECTIONS (output as JSON keys)\n"]
    for s in COMPATIBILITY_SECTIONS:
        parts.append(f"### {s['title']} (key: {s['key']})\n{s['instructions']}\n")
    return "\n".join(parts)


def _assemble_prompt(metrics: dict) -> tuple[str, str]:
    from scoring_engine.prompts.system_prompt import SYSTEM_PROMPT_CORE

    user_prompt = (
        "## COMPATIBILITY REPORT\n\n"
        "You are synthesizing TWO completed BEST Galaxy assessments into a "
        "single compatibility narrative. Use load × capacity language only. "
        "Never characterize either system as deficient or pathological.\n\n"
        + _build_metrics_block(metrics)
        + "\n"
        + _build_section_block()
        + "\nReturn JSON with exactly these keys: "
        + ", ".join(s["key"] for s in COMPATIBILITY_SECTIONS)
    )
    return SYSTEM_PROMPT_CORE, user_prompt


# =============================================================================
# TEMPLATE FALLBACK
# =============================================================================

def _template_sections(metrics: dict) -> dict:
    a_arch = metrics.get("a_archetype") or "System A"
    b_arch = metrics.get("b_archetype") or "System B"
    comp = metrics["complementary_pairs"][:3]
    strain = metrics["shared_sensitivities"][:3]

    return {
        "overview": (
            f"This pair combines {a_arch} and {b_arch}. "
            f"Combined load × capacity reads as PEI={metrics['combined_pei']}, "
            f"BHP={metrics['combined_bhp']} (balance {metrics['combined_balance']:+.2f}). "
            "The two systems together shape a shared operating climate that "
            "is more than the sum of their parts."
        ),
        "load_compatibility": (
            f"System A operates with a PEI of {metrics['a_pei']:.2f}; "
            f"System B with {metrics['b_pei']:.2f}. Where these are close, "
            "demands are felt similarly. Where they diverge, one partner is "
            "carrying a heavier share of environmental load."
        ),
        "capacity_compatibility": (
            f"System A capacity (BHP) sits at {metrics['a_bhp']:.2f}; "
            f"System B at {metrics['b_bhp']:.2f}. Differences create natural "
            "scaffolding opportunities; similarity creates a shared baseline."
        ),
        "complementary_stabilizers": (
            "Complementary domains:\n"
            + "\n".join(
                f"- {x['domain']}: A={x['a_score']}, B={x['b_score']}"
                for x in comp
            )
            if comp else
            "No high-gap complementary domains detected — both systems track "
            "closely on most dimensions."
        ),
        "shared_sensitivities": (
            "Shared strain:\n"
            + "\n".join(
                f"- {x['domain']}: A={x['a_score']}, B={x['b_score']}"
                for x in strain
            )
            if strain else
            "No shared low-capacity domains identified."
        ),
        "co_regulation_aims": (
            "Awareness — Name shared early-warning signals you both notice.\n"
            "Intervention — Pick ONE shared anchor (sleep, pre-conflict pause, "
            "weekly money check-in) and run it for two weeks.\n"
            "Mastery — Practice during low-pressure windows; reinforce what "
            "works for both systems before scaling.\n"
            "Sustain — Build a repeatable shared system; review monthly."
        ),
        "compatibility_summary": (
            "The dominant theme is interactive load × capacity: the pair's "
            "next observable move is to align on one shared scaffold and "
            "watch the highest-shared-strain domain together."
        ),
    }


# =============================================================================
# PUBLIC API
# =============================================================================

def generate_compatibility_report(
    assessment_a: dict,
    assessment_b: dict,
    user_a_id: Optional[str] = None,
    user_b_id: Optional[str] = None,
) -> dict:
    """
    Generate a compatibility report between two completed assessments.
    """
    from scoring_engine.report_generator import _call_ai

    metrics = _compute_compatibility_metrics(assessment_a, assessment_b)
    system_prompt, user_prompt = _assemble_prompt(metrics)

    audit_ctx = {
        "user_id": user_a_id,
        "assessment_id": (assessment_a.get("metadata") or {}).get("assessment_id"),
        "report_type": "COMPATIBILITY",
        "kind": "compatibility_report",
    }

    sections = _call_ai(system_prompt, user_prompt, audit_context=audit_ctx)
    if not sections:
        logger.warning("Compatibility AI generation failed, using template")
        sections = _template_sections(metrics)

    return {
        "report_id": str(uuid.uuid4()),
        "report_type": "COMPATIBILITY",
        "user_a_id": user_a_id,
        "user_b_id": user_b_id,
        "metrics": metrics,
        "sections": sections,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
