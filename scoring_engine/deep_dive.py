"""
Deep-Dive Report Generation — Phase 4.5

Two single-domain deep-dive reports the system can produce on top of any
completed assessment:

  1. Financial Deep-Dive — focused on Financial Executive Functioning
  2. Health Deep-Dive    — focused on Health & Fitness Executive Functioning

Each report is structured around 7 sections that mirror the master template
but narrow scope to a single applied domain:

   1. snapshot              — high-level archetype + status band
   2. bhp_breakdown         — internal capacity drivers
   3. pei_breakdown         — environmental pressures
   4. subvariable_detail    — domain-specific subvariable scores
   5. active_flags          — triggered behavioral flags + reframes
   6. aims_pathway          — domain-tailored AIMS targets
   7. summary               — closing synthesis with strengths + edges

Like the lens reports, deep-dives use the AI service when available and
fall back to a deterministic template otherwise.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from scoring_engine.prompts.system_prompt import SYSTEM_PROMPT_CORE
from scoring_engine.prompts.compliance import check_banned_language

logger = logging.getLogger(__name__)


DEEP_DIVE_SECTIONS = [
    {
        "key": "snapshot",
        "title": "Domain Snapshot",
        "instructions": (
            "2-3 sentences summarizing the overall load balance and status "
            "band for this single domain. Use load × capacity language."
        ),
    },
    {
        "key": "bhp_breakdown",
        "title": "Internal Capacity (BHP) Breakdown",
        "instructions": (
            "Walk through the BHP drivers visible in the subvariable scores. "
            "Identify which capacity systems are reinforcing the user and "
            "which are taxed."
        ),
    },
    {
        "key": "pei_breakdown",
        "title": "Environmental Pressure (PEI) Breakdown",
        "instructions": (
            "Describe the load this domain is currently exerting and where "
            "it concentrates. Use observable language only — never blame."
        ),
    },
    {
        "key": "subvariable_detail",
        "title": "Subvariable Detail",
        "instructions": (
            "Cover EACH subvariable that has a score. State the score range "
            "(low / moderate / high) and what it means functionally. Avoid "
            "diagnostic framing."
        ),
    },
    {
        "key": "active_flags",
        "title": "Active Behavioral Flags",
        "instructions": (
            "For each TRIGGERED flag, give a 2-sentence reframe: what the "
            "behavioral pattern looks like, and what underlying load × "
            "capacity dynamic produces it."
        ),
    },
    {
        "key": "aims_pathway",
        "title": "AIMS Pathway for This Domain",
        "instructions": (
            "Provide concrete AIMS-aligned actions for this domain only. "
            "Order them strictly Awareness → Intervention → Mastery → Sustain. "
            "Use the personalized aims_targets list as the seed."
        ),
    },
    {
        "key": "summary",
        "title": "Closing Synthesis",
        "instructions": (
            "Two short paragraphs. (1) The 1-2 strengths to anchor on, "
            "(2) the 1-2 growth edges and the next observable step."
        ),
    },
]


# =============================================================================
# CONTEXT BUILDERS
# =============================================================================

def _format_subvariables(subvariables: dict) -> str:
    if not subvariables:
        return "(none reported)"
    lines = []
    for key, info in subvariables.items():
        if isinstance(info, dict):
            score = info.get("score", info.get("value", "?"))
            band = info.get("band") or info.get("level") or ""
            lines.append(f"  - {key}: {score} {('(' + band + ')') if band else ''}")
        else:
            lines.append(f"  - {key}: {info}")
    return "\n".join(lines)


def _format_flags(flags: dict) -> str:
    if not flags:
        return "(no flags configured)"
    out = []
    for name, info in flags.items():
        if not isinstance(info, dict):
            continue
        triggered = info.get("triggered")
        desc = info.get("description", "")
        out.append(f"  - {name} [{'TRIGGERED' if triggered else 'inactive'}]: {desc}")
    return "\n".join(out) or "(none)"


def _format_aims_targets(targets: list[dict]) -> str:
    if not targets:
        return "(no AIMS targets generated)"
    lines = []
    for t in targets:
        phase = t.get("phase", "?")
        focus = t.get("focus") or t.get("target") or ""
        action = t.get("action", "")
        lines.append(f"  - [{phase}] {focus}: {action}")
    return "\n".join(lines)


def _build_context(
    domain_label: str,
    applied_domain: dict,
    construct_scores: dict,
) -> str:
    return (
        f"## DEEP-DIVE TARGET: {domain_label}\n\n"
        f"Domain Score: {applied_domain.get('domain_score', 'N/A')}/100\n"
        f"BHP (capacity): {applied_domain.get('bhp', 'N/A')}\n"
        f"PEI (load): {applied_domain.get('pei', 'N/A')}\n"
        f"Load Balance: {applied_domain.get('load_balance', 'N/A')}\n"
        f"Status Band: {applied_domain.get('status_band', 'N/A')}\n\n"
        f"Overall Assessment Context:\n"
        f"  Overall PEI: {construct_scores.get('PEI_score', 'N/A')}\n"
        f"  Overall BHP: {construct_scores.get('BHP_score', 'N/A')}\n\n"
        f"## SUBVARIABLES\n{_format_subvariables(applied_domain.get('subvariables', {}))}\n\n"
        f"## FLAGS\n{_format_flags(applied_domain.get('flags', {}))}\n\n"
        f"## AIMS TARGETS\n{_format_aims_targets(applied_domain.get('aims_targets', []))}\n"
    )


def _build_section_block() -> str:
    parts = ["## REQUIRED SECTIONS (output as JSON keys)\n"]
    for s in DEEP_DIVE_SECTIONS:
        parts.append(f"### {s['title']} (key: {s['key']})\n{s['instructions']}\n")
    return "\n".join(parts)


def _assemble_prompt(
    domain_label: str,
    applied_domain: dict,
    construct_scores: dict,
    demographics: Optional[dict],
) -> tuple[str, str]:
    from scoring_engine.report_generator import _build_demographic_context

    user_prompt = (
        _build_context(domain_label, applied_domain, construct_scores)
        + "\n"
        + _build_demographic_context(demographics)
        + "\n"
        + _build_section_block()
        + "\nReturn JSON with exactly these keys: "
        + ", ".join(s["key"] for s in DEEP_DIVE_SECTIONS)
    )
    return SYSTEM_PROMPT_CORE, user_prompt


# =============================================================================
# TEMPLATE FALLBACK (used if AI unavailable)
# =============================================================================

def _template_sections(domain_label: str, applied_domain: dict) -> dict:
    score = applied_domain.get("domain_score", 50)
    band = applied_domain.get("status_band", "Fragile Balance")
    triggered = [
        info.get("description", name)
        for name, info in (applied_domain.get("flags") or {}).items()
        if isinstance(info, dict) and info.get("triggered")
    ]
    aims = applied_domain.get("aims_targets", [])

    sub_lines = []
    for key, info in (applied_domain.get("subvariables") or {}).items():
        if isinstance(info, dict):
            sub_lines.append(f"{key}: {info.get('score', '—')}")
        else:
            sub_lines.append(f"{key}: {info}")

    aims_lines = []
    for phase in ["Awareness", "Intervention", "Mastery", "Sustain"]:
        for t in aims:
            if str(t.get("phase", "")).lower().startswith(phase.lower()[:5]):
                aims_lines.append(f"{phase} — {t.get('focus', '')}: {t.get('action', '')}")

    return {
        "snapshot": (
            f"Your {domain_label} domain currently sits at {score}/100, in the "
            f"'{band}' band. This reflects the interaction between the load this "
            f"domain is placing on you and your current capacity to meet it."
        ),
        "bhp_breakdown": (
            "Your internal capacity in this domain shows the following pattern: "
            + "; ".join(sub_lines[: max(3, len(sub_lines) // 2)] or ["—"])
        ),
        "pei_breakdown": (
            "Environmental pressure in this domain reflects the demands you are "
            "currently navigating. This is observable, not a verdict."
        ),
        "subvariable_detail": "\n".join(sub_lines) or "—",
        "active_flags": (
            "\n".join(f"- {t}" for t in triggered)
            if triggered
            else "No active flags — current patterns are within typical range."
        ),
        "aims_pathway": "\n".join(aims_lines) or (
            "Awareness — Notice early signals.\n"
            "Intervention — Pick one observable next step.\n"
            "Mastery — Practice during low-load conditions first.\n"
            "Sustain — Build a repeatable system, not isolated effort."
        ),
        "summary": (
            f"Your {domain_label} profile reveals where capacity is currently "
            f"holding ({band}). The next observable step is to anchor one "
            f"AIMS action above and track it for two weeks."
        ),
    }


# =============================================================================
# PUBLIC API
# =============================================================================

def _generate_dive(
    assessment_data: dict,
    domain_key: str,
    domain_label: str,
    demographics: Optional[dict] = None,
    user_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
) -> dict:
    from scoring_engine.report_generator import _call_ai

    applied = (assessment_data.get("applied_domains") or {}).get(domain_key)
    if not applied:
        raise ValueError(
            f"applied_domains.{domain_key} is missing — cannot run a deep-dive."
        )

    construct_scores = assessment_data.get("construct_scores", {})
    system_prompt, user_prompt = _assemble_prompt(
        domain_label, applied, construct_scores, demographics
    )

    audit_ctx = {
        "user_id": user_id,
        "assessment_id": assessment_id,
        "report_type": f"DEEP_DIVE_{domain_key.upper()}",
        "kind": "deep_dive",
    }

    sections = _call_ai(system_prompt, user_prompt, audit_context=audit_ctx)
    if not sections:
        logger.warning(
            "Deep-dive AI generation failed for %s, using template", domain_key
        )
        sections = _template_sections(domain_label, applied)

    # Compliance check — non-blocking
    all_text = " ".join(str(v) for v in sections.values() if v)
    violations = check_banned_language(all_text)
    if violations:
        logger.warning("Deep-dive language violations: %s", violations)

    return {
        "report_id": str(uuid.uuid4()),
        "report_type": f"DEEP_DIVE_{domain_key.upper()}",
        "domain_key": domain_key,
        "domain_label": domain_label,
        "sections": sections,
        "language_violations": violations,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_financial_deep_dive(
    assessment_data: dict,
    demographics: Optional[dict] = None,
    user_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
) -> dict:
    """Deep-dive into Financial Executive Functioning."""
    return _generate_dive(
        assessment_data,
        "financial_ef",
        "Financial Executive Functioning",
        demographics,
        user_id,
        assessment_id,
    )


def generate_health_deep_dive(
    assessment_data: dict,
    demographics: Optional[dict] = None,
    user_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
) -> dict:
    """Deep-dive into Health & Fitness Executive Functioning."""
    return _generate_dive(
        assessment_data,
        "health_ef",
        "Health & Fitness Executive Functioning",
        demographics,
        user_id,
        assessment_id,
    )
