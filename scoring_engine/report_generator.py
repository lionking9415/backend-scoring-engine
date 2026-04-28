"""
AI Report Generation Engine — Assembles prompts and generates structured reports.

This module handles:
- Prompt assembly from scoring outputs + demographics + lens
- AI report generation via OpenAI
- Report parsing into structured sections
- Validation and compliance checking
- Fallback to template-based generation
- Report storage and retrieval

CRITICAL SEPARATION RULE:
  Assessment responses + scoring logic = objective score outputs
  Demographics + lens type = interpretation context ONLY
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# SECTION VALUE NORMALIZATION
# =============================================================================
# The AI is asked to return each section as a flat string, but in practice
# it sometimes nests an object (e.g. {"summary": "...", "details": "..."})
# or returns a list of bullet items. Downstream consumers — the compliance
# validator, the PDF generator, and the frontend — all assume strings, so
# we flatten once here before they touch the data. This is the source of
# the historical "'dict' object has no attribute 'strip'" crash.
# =============================================================================


def _stringify_section_value(value: Any) -> str:
    """Flatten any AI-returned section value into a readable narrative string.

    Handles strings (passthrough), scalars (str()), dicts (rendered as
    labeled paragraphs preserving sub-structure), and lists (rendered as
    bullets when items are short, paragraphs otherwise). Returns "" for
    None / empty containers so the validator's empty-section check still
    triggers correctly.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        parts: list[str] = []
        for k, v in value.items():
            sub = _stringify_section_value(v)
            if not sub:
                continue
            label = str(k).replace("_", " ").strip()
            label = label[:1].upper() + label[1:] if label else ""
            parts.append(f"**{label}**: {sub}" if label else sub)
        return "\n\n".join(parts)
    if isinstance(value, list):
        items = [_stringify_section_value(v) for v in value]
        items = [i for i in items if i]
        if not items:
            return ""
        # Render as a bulleted list when each item is a short single-line
        # string (typical for "key takeaways" style sections); otherwise
        # join as paragraphs.
        if all(len(i) < 200 and "\n" not in i for i in items):
            return "\n".join(f"- {i}" for i in items)
        return "\n\n".join(items)
    return str(value)


def _normalize_sections(sections: Any) -> dict:
    """Coerce the AI's raw output into a {section_key: str} mapping.

    Non-dict top-level returns are turned into an empty dict so the
    fallback-template path can take over instead of crashing the validator.
    """
    if not isinstance(sections, dict):
        return {}
    return {str(k): _stringify_section_value(v) for k, v in sections.items()}


# =============================================================================
# PROMPT ASSEMBLY
# =============================================================================


# =============================================================================
# LENS DIFFERENTIATION WEIGHTS (Addendum Phase 3, Section 3)
# Applied AFTER base scoring, ONLY to interpretation outputs.
# These multipliers shift AI emphasis per lens — raw scores are NEVER altered.
# =============================================================================

LENS_DOMAIN_WEIGHTS = {
    "STUDENT_SUCCESS": {
        "action_follow_through": 1.3,
        "focus_drive": 1.3,
        "emotional_regulation": 1.0,
        "life_load": 1.2,
    },
    "PERSONAL_LIFESTYLE": {
        "action_follow_through": 1.1,
        "focus_drive": 1.0,
        "emotional_regulation": 1.4,
        "life_load": 1.4,
    },
    "PROFESSIONAL_LEADERSHIP": {
        "action_follow_through": 1.5,
        "focus_drive": 1.3,
        "emotional_regulation": 1.0,
        "life_load": 1.1,
    },
    "FAMILY_ECOSYSTEM": {
        "action_follow_through": 1.0,
        "focus_drive": 0.9,
        "emotional_regulation": 1.5,
        "life_load": 1.5,
    },
}


def _apply_lens_weights(
    action_ft: float,
    focus_drive: float,
    emotional_reg: float,
    life_load: float,
    report_type: str,
) -> tuple[float, float, float, float]:
    """
    Apply lens-specific multipliers to domain scores for interpretation only.

    Uses a soft saturating transform (smoothstep-style) instead of hard clamping
    so that high-capacity users retain differentiation after weighting:
        x' = 1 - (1 - x_raw) ** weight   when weight >= 1
        x' = x_raw ** (1 / weight)        when weight <  1
    Both forms preserve [0,1] range and emphasize / de-emphasize the score
    smoothly rather than collapsing all high values to 1.0.
    """
    weights = LENS_DOMAIN_WEIGHTS.get(report_type)
    if not weights:
        return action_ft, focus_drive, emotional_reg, life_load

    def _emphasis(x: float, w: float) -> float:
        x = max(0.0, min(1.0, x))
        if w >= 1.0:
            return round(1.0 - (1.0 - x) ** w, 3)
        return round(x ** (1.0 / max(w, 1e-6)), 3)

    return (
        _emphasis(action_ft, weights["action_follow_through"]),
        _emphasis(focus_drive, weights["focus_drive"]),
        _emphasis(emotional_reg, weights["emotional_regulation"]),
        _emphasis(life_load, weights["life_load"]),
    )


def _build_scoring_context(assessment_data: dict, report_type: str = None) -> str:
    """Build the scoring data section of the prompt from assessment output."""
    construct_scores = assessment_data.get("construct_scores", {})
    load_framework = assessment_data.get("load_framework", {})
    archetype = assessment_data.get("archetype", {})
    # Support both canonical ("domains", "summary") and legacy
    # ("domain_profiles", "summary_indicators") output shapes.
    domain_profiles = (
        assessment_data.get("domain_profiles")
        or assessment_data.get("domains")
        or []
    )
    applied = assessment_data.get("applied_domains", {})
    summary = (
        assessment_data.get("summary_indicators")
        or assessment_data.get("summary")
        or {}
    )
    cross_domain = assessment_data.get("cross_domain", {})

    # Map domain profiles to the 4 ecosystem domains
    domain_map = {}
    for dp in domain_profiles:
        domain_map[dp["name"]] = dp["score"]

    action_ft = round(
        (domain_map.get("EXECUTIVE_FUNCTION_SKILLS", 0.5) +
         domain_map.get("BEHAVIORAL_PATTERNS", 0.5)) / 2, 3
    )
    focus_drive = round(
        (domain_map.get("COGNITIVE_CONTROL", 0.5) +
         domain_map.get("MOTIVATIONAL_SYSTEMS", 0.5)) / 2, 3
    )
    emotional_reg = round(
        (domain_map.get("EMOTIONAL_REGULATION", 0.5) +
         domain_map.get("INTERNAL_STATE_FACTORS", 0.5)) / 2, 3
    )
    life_load = round(domain_map.get("ENVIRONMENTAL_DEMANDS", 0.5), 3)

    # Apply lens-specific weighting for AI interpretation (Addendum Phase 3)
    if report_type and report_type in LENS_DOMAIN_WEIGHTS:
        action_ft, focus_drive, emotional_reg, life_load = _apply_lens_weights(
            action_ft, focus_drive, emotional_reg, life_load, report_type,
        )

    fin = applied.get("financial_ef", {})
    health = applied.get("health_ef", {})

    # Cross-domain pattern context (computed in engine.cross_domain)
    flows = cross_domain.get("flows", []) or []
    flow_summary = "\n".join(
        f"- {f['from']} → {f['to']}: strength {f['strength']:.2f} ({f.get('rationale', '')})"
        for f in flows[:8]
    ) or "No significant cross-domain pressure transfers detected."

    compensation = cross_domain.get("compensation_patterns", []) or []
    comp_summary = "\n".join(
        f"- {c['stabilizer']} compensates for {c['vulnerability']} (capacity gap: {c.get('gap', 0):.2f})"
        for c in compensation[:5]
    ) or "No notable compensation patterns detected."

    sensitivities = cross_domain.get("system_wide_sensitivities", []) or []
    sens_summary = "\n".join(
        f"- {s['domain']}: {s['pattern']}"
        for s in sensitivities[:6]
    ) or "No system-wide sensitivities flagged."

    context = f"""## SCORING OUTPUTS (Objective — DO NOT modify)

PEI (External Load): {construct_scores.get('PEI_score', 0):.3f}
BHP (Internal Capacity): {construct_scores.get('BHP_score', 0):.3f}
Load Balance: {load_framework.get('load_balance', 0):.3f}
Load Classification: {load_framework.get('load_state', 'unknown')}
Quadrant: {load_framework.get('quadrant', 'unknown')}

Archetype: {archetype.get('archetype_id', 'unknown')}
Archetype Description: {archetype.get('description', '')}

## DOMAIN SCORES (0-1 scale, lens-weighted for interpretation)
Action & Follow-Through: {action_ft}
Focus & Drive: {focus_drive}
Emotional Regulation: {emotional_reg}
Life Load (Environmental Demands — inverse/pressure): {life_load}

## TOP STRENGTHS
{', '.join(summary.get('top_strengths', []))}

## GROWTH EDGES
{', '.join(summary.get('growth_edges', []))}

## FINANCIAL EXECUTIVE FUNCTIONING
Financial Score: {fin.get('domain_score', 50)}/100
Financial BHP: {fin.get('bhp', 0):.1f}
Financial PEI: {fin.get('pei', 0):.1f}
Financial Load Balance: {fin.get('load_balance', 0):.1f}
Financial Status Band: {fin.get('status_band', 'N/A')}
Financial Flags: {', '.join(f.get('description', '') for f in (fin.get('flags', {}) or {}).values() if isinstance(f, dict) and f.get('triggered'))}

## HEALTH & FITNESS EXECUTIVE FUNCTIONING
Health Score: {health.get('domain_score', 50)}/100
Health BHP: {health.get('bhp', 0):.1f}
Health PEI: {health.get('pei', 0):.1f}
Health Load Balance: {health.get('load_balance', 0):.1f}
Health Status Band: {health.get('status_band', 'N/A')}
Health Flags: {', '.join(f.get('description', '') for f in (health.get('flags', {}) or {}).values() if isinstance(f, dict) and f.get('triggered'))}

## CROSS-DOMAIN PATTERN ANALYSIS

### Load Transfer Flows (which domain pressure spreads to which)
{flow_summary}

### Compensation Patterns (where strengths offset vulnerabilities)
{comp_summary}

### System-Wide Sensitivities
{sens_summary}
"""
    return context


def _build_demographic_context(demographics: dict) -> str:
    """Build demographic context section, using only AI-safe fields."""
    if not demographics:
        return "## DEMOGRAPHIC CONTEXT\nNo demographic data provided.\n"

    from scoring_engine.demographics import filter_ai_safe_demographics
    safe = filter_ai_safe_demographics(demographics)

    health = safe.get("health", {})
    behavior = safe.get("behavior_patterns", {})

    lines = ["## DEMOGRAPHIC CONTEXT (for interpretation tone only — DO NOT alter scores)"]
    if safe.get("age_range"):
        lines.append(f"Age Range: {safe['age_range']}")
    if safe.get("roles"):
        roles = safe["roles"] if isinstance(safe["roles"], list) else [safe["roles"]]
        lines.append(f"Roles: {', '.join(roles)}")
    if safe.get("primary_load_sources"):
        sources = safe["primary_load_sources"] if isinstance(safe["primary_load_sources"], list) else [safe["primary_load_sources"]]
        lines.append(f"Primary Load Sources: {', '.join(sources)}")
    if safe.get("perceived_load"):
        lines.append(f"Perceived Life Load: {safe['perceived_load']}")
    if safe.get("support_level"):
        lines.append(f"Support System: {safe['support_level']}")
    if safe.get("financial_stability"):
        lines.append(f"Financial Stability: {safe['financial_stability']}")
    if safe.get("financial_pressure_frequency"):
        lines.append(f"Financial Pressure Frequency: {safe['financial_pressure_frequency']}")
    if health:
        lines.append(f"Sleep: {health.get('sleep', 'N/A')}")
        lines.append(f"Nutrition: {health.get('nutrition', 'N/A')}")
        lines.append(f"Exercise: {health.get('exercise', 'N/A')}")
        lines.append(f"Emotional Regulation: {health.get('emotional_regulation', 'N/A')}")
    if behavior:
        lines.append(f"Overwhelm Response: {behavior.get('overwhelm_response', 'N/A')}")
        lines.append(f"Planning Style: {behavior.get('planning_style', 'N/A')}")
    if safe.get("cultural_context"):
        lines.append(f"Cultural Context: {safe['cultural_context']}")

    return "\n".join(lines) + "\n"


def _build_section_instructions(sections: list[dict], report_type: str) -> str:
    """Build section-by-section instructions for the AI."""
    from scoring_engine.prompts.lens_rules import get_lens_context

    lens = get_lens_context(report_type)
    primary_goal = lens.get('primary_goal', '')
    # Verbatim per Addendum-Phase 3 Agreement §3.7. Every report must
    # meaningfully answer this exact question; the literal text is
    # injected so the AI cannot drift from the spec wording.
    guiding_question = lens.get('guiding_question', '')

    lines = [
        f"## REPORT TYPE: {lens['label']} ({lens['icon']})",
        f"## PRIMARY LENS GOAL: {primary_goal.upper()}",
        f"Interpret ALL results through the primary lens goal: {primary_goal}.",
    ]

    if guiding_question:
        lines.extend([
            "\n## GUIDING QUESTION (Addendum Phase 3, §3.7)",
            f'"{guiding_question}"',
            (
                "Every section in this report MUST contribute to answering this "
                "exact question. Treat it as the report's foundational interpretation "
                "frame: outputs that don't connect back to it are off-lens and "
                "violate the lens differentiation contract."
            ),
        ])

    lines.extend([
        f"\n## LENS CONTEXT RULES\n{lens['context_instruction']}",
        "\n## REQUIRED SECTIONS (generate in this exact order)\n",
        "Output each section as a JSON object with keys matching the section key.",
        "Each value should be the full narrative text for that section.",
        "Do NOT include markdown headers in the text — just the narrative content.\n",
    ])

    for s in sections:
        lines.append(f"### Section {s['number']}: {s['title']} (key: \"{s['key']}\")")
        lines.append(s["instructions"])
        lines.append("")

    return "\n".join(lines)


def assemble_prompt(
    assessment_data: dict,
    report_type: str,
    demographics: Optional[dict] = None,
) -> tuple[str, str]:
    """
    Assemble the full AI prompt from all layers.
    Returns (system_prompt, user_prompt) tuple.
    """
    from scoring_engine.prompts.system_prompt import SYSTEM_PROMPT_CORE
    from scoring_engine.prompts.section_rules import get_lens_sections

    scoring_context = _build_scoring_context(assessment_data, report_type)
    demographic_context = _build_demographic_context(demographics)
    lens_sections = get_lens_sections(report_type)
    section_instructions = _build_section_instructions(lens_sections, report_type)

    user_prompt = f"""{scoring_context}

{demographic_context}

{section_instructions}

## OUTPUT FORMAT

Return a single JSON object where each key is the section key and each value is
the full narrative text for that section. Example:
{{
  "galaxy_snapshot": "Your profile reflects...",
  "galaxy_placement": "Quadrant: ...",
  ...
}}

Generate all {len(lens_sections)} sections now. Be thorough — each section should be 2-4 paragraphs.
"""

    return SYSTEM_PROMPT_CORE, user_prompt


def _build_cosmic_lens_emphasis(report_type_to_weights: dict) -> str:
    """Build a textual summary of how each lens emphasizes core domains."""
    from scoring_engine.prompts.lens_rules import LENS_RULES

    lines = ["## LENS EMPHASIS PROFILE (interpretation weights per lens)"]
    for lens, weights in report_type_to_weights.items():
        emphasis = ", ".join(f"{k}={v:.2f}" for k, v in weights.items())
        lines.append(f"- {lens}: {emphasis}")

    # Surface each lens's verbatim §3.7 guiding question so the cosmic
    # synthesis stays anchored to the four real-world frames it must
    # weave together (Addendum Phase 3 §3.7 + §7).
    questions = [
        (lens, LENS_RULES.get(lens, {}).get("guiding_question"))
        for lens in report_type_to_weights
    ]
    if any(q for _, q in questions):
        lines.append("")
        lines.append("## LENS GUIDING QUESTIONS (each must remain answerable in the synthesis)")
        for lens, q in questions:
            if q:
                lines.append(f'- {lens}: "{q}"')
    return "\n".join(lines)


def assemble_cosmic_prompt(
    lens_reports: dict[str, dict],
    assessment_data: dict,
    demographics: Optional[dict] = None,
) -> tuple[str, str]:
    """
    Assemble the Cosmic Integration report prompt.
    Requires all 4 lens reports as input.

    Includes the FULL content of every required section per lens (no
    truncation) so the AI has full visibility for cross-lens synthesis.
    """
    from scoring_engine.prompts.system_prompt import SYSTEM_PROMPT_CORE
    from scoring_engine.prompts.section_rules import (
        COSMIC_REPORT_SECTIONS,
        LENS_REPORT_SECTIONS,
        LENS_EXCLUSIVE_SECTIONS,
    )

    scoring_context = _build_scoring_context(assessment_data)
    demographic_context = _build_demographic_context(demographics)
    lens_emphasis = _build_cosmic_lens_emphasis(LENS_DOMAIN_WEIGHTS)

    # Sections we want the AI to see from each lens. The full master template
    # plus the lens-exclusive section so cross-lens synthesis is complete.
    base_keys = [s["key"] for s in LENS_REPORT_SECTIONS]

    lens_summaries = []
    for lens_name, report in lens_reports.items():
        exclusive_key = LENS_EXCLUSIVE_SECTIONS.get(lens_name, {}).get("key")
        section_keys = list(base_keys) + ([exclusive_key] if exclusive_key else [])
        parts = [f"### {lens_name} Report"]
        for key in section_keys:
            text = report.get(key)
            if text:
                parts.append(f"\n[{key}]\n{text}")
        lens_summaries.append("\n".join(parts))

    lens_text = "\n\n---\n\n".join(lens_summaries)

    section_lines = [
        "## COSMIC INTEGRATION REPORT",
        "\nYou have access to all 4 full lens reports below.",
        "You must SYNTHESIZE patterns across all lenses — do NOT repeat or summarize individually.",
        "AVOID: 'Here's your student result... here's your personal...'",
        "INSTEAD: 'Across your academic, personal, professional, and family environments, a consistent pattern emerges...'",
        "\n" + lens_emphasis,
        "\nApply this emphasis when synthesizing: a domain that scores moderately but is heavily",
        "weighted in two or more lenses indicates a high-leverage cross-environmental pattern.",
        "\n## ALL 4 LENS REPORTS (FULL CONTENT)\n",
        lens_text,
        "\n## REQUIRED SECTIONS (generate in this exact order)\n",
        "Output as JSON with section keys.\n",
    ]

    for s in COSMIC_REPORT_SECTIONS:
        section_lines.append(f"### Section {s['number']}: {s['title']} (key: \"{s['key']}\")")
        section_lines.append(s["instructions"])
        section_lines.append("")

    user_prompt = f"""{scoring_context}

{demographic_context}

{chr(10).join(section_lines)}

## OUTPUT FORMAT

Return a single JSON object where each key is the section key and each value is
the full narrative text. Generate all 11 sections.
"""

    return SYSTEM_PROMPT_CORE, user_prompt


# =============================================================================
# REPORT GENERATION
# =============================================================================

def generate_report(
    assessment_data: dict,
    report_type: str,
    demographics: Optional[dict] = None,
    max_retries: int = 2,
    user_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
) -> dict:
    """
    Generate a full AI report for a given lens.

    Returns dict with:
      - report_id: unique identifier
      - report_type: lens used
      - sections: dict of section_key -> narrative text
      - validation: validation results
      - generated_at: timestamp
    """
    from scoring_engine.prompts.section_rules import get_lens_sections
    from scoring_engine.prompts.compliance import validate_report

    lens_sections = get_lens_sections(report_type)
    expected_keys = [s["key"] for s in lens_sections]

    system_prompt, user_prompt = assemble_prompt(assessment_data, report_type, demographics)

    audit_ctx = {
        "user_id": user_id or assessment_data.get("metadata", {}).get("user_id"),
        "assessment_id": assessment_id or assessment_data.get("metadata", {}).get("assessment_id"),
        "report_type": report_type,
        "kind": "lens_report",
    }

    # Try AI generation
    sections = _call_ai(
        system_prompt, user_prompt,
        max_retries=max_retries, audit_context=audit_ctx,
    )

    # If AI fails, use template fallback
    if not sections:
        logger.warning(f"AI generation failed for {report_type}, using template fallback")
        sections = _generate_template_report(assessment_data, report_type, demographics)

    # Coerce any nested-object / list section values into flat strings.
    # The AI sometimes returns {"key": {"summary": ..., "details": ...}}
    # which the downstream validator + PDF code can't handle.
    sections = _normalize_sections(sections)

    # Validate
    validation = validate_report(sections, expected_keys, report_type)

    # If validation fails due to missing sections, fill stubs
    if not validation["all_sections_present"]:
        for key in validation["missing_sections"]:
            sections[key] = "[Section pending — AI generation incomplete]"
        validation = validate_report(sections, expected_keys, report_type)

    report_id = str(uuid.uuid4())

    return {
        "report_id": report_id,
        "report_type": report_type,
        "sections": sections,
        "validation": validation,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def generate_cosmic_report(
    lens_reports: dict[str, dict],
    assessment_data: dict,
    demographics: Optional[dict] = None,
    user_id: Optional[str] = None,
    assessment_id: Optional[str] = None,
) -> dict:
    """
    Generate the Cosmic Integration Report from all 4 lens reports.
    """
    from scoring_engine.prompts.section_rules import COSMIC_SECTION_KEYS
    from scoring_engine.prompts.compliance import validate_report

    system_prompt, user_prompt = assemble_cosmic_prompt(
        lens_reports, assessment_data, demographics
    )

    audit_ctx = {
        "user_id": user_id or assessment_data.get("metadata", {}).get("user_id"),
        "assessment_id": assessment_id or assessment_data.get("metadata", {}).get("assessment_id"),
        "report_type": "FULL_GALAXY",
        "kind": "cosmic_report",
    }

    sections = _call_ai(system_prompt, user_prompt, max_retries=2, audit_context=audit_ctx)

    if not sections:
        logger.warning("AI generation failed for Cosmic report, using template fallback")
        sections = _generate_cosmic_template(assessment_data, lens_reports, demographics)

    # Coerce any nested-object / list section values into flat strings before
    # validation. (Cosmic prompts are the largest and most likely to elicit a
    # non-flat shape from gpt-4o, which previously crashed the validator.)
    sections = _normalize_sections(sections)

    validation = validate_report(sections, COSMIC_SECTION_KEYS, "FULL_GALAXY")

    if not validation["all_sections_present"]:
        for key in validation["missing_sections"]:
            sections[key] = "[Section pending — AI generation incomplete]"

    return {
        "report_id": str(uuid.uuid4()),
        "report_type": "FULL_GALAXY",
        "sections": sections,
        "validation": validation,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# AI CALL
# =============================================================================

def _call_ai(
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 2,
    audit_context: Optional[dict] = None,
) -> Optional[dict]:
    """Call OpenAI API and parse structured JSON response.

    audit_context: optional dict ({user_id, assessment_id, report_type}) used
    to write a prompt/response audit record via scoring_engine.audit.
    """
    from scoring_engine import audit
    try:
        from scoring_engine.ai_service import get_openai_client
        client = get_openai_client()
        if not client:
            logger.warning("OpenAI client not available")
            audit.log_ai_call(
                audit_context, system_prompt, user_prompt,
                response_text=None, error="openai_client_unavailable",
            )
            return None

        last_error = None
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=12000,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                sections = json.loads(content)

                if isinstance(sections, dict) and len(sections) > 0:
                    logger.info(f"AI generated {len(sections)} sections (attempt {attempt + 1})")
                    audit.log_ai_call(
                        audit_context, system_prompt, user_prompt,
                        response_text=content, error=None, attempt=attempt + 1,
                    )
                    return sections
                else:
                    last_error = "empty_or_invalid_response"
                    logger.warning(f"AI returned empty/invalid response (attempt {attempt + 1})")

            except json.JSONDecodeError as e:
                last_error = f"json_decode_error: {e}"
                logger.warning(f"AI response JSON parse error (attempt {attempt + 1}): {e}")
            except Exception as e:
                last_error = f"api_error: {e}"
                logger.error(f"AI call failed (attempt {attempt + 1}): {e}")

        audit.log_ai_call(
            audit_context, system_prompt, user_prompt,
            response_text=None, error=last_error,
        )
        return None

    except Exception as e:
        logger.error(f"AI service error: {e}")
        audit.log_ai_call(
            audit_context, system_prompt, user_prompt,
            response_text=None, error=f"service_error: {e}",
        )
        return None


# =============================================================================
# TEMPLATE FALLBACK (when AI is unavailable)
# =============================================================================

def _generate_template_report(
    assessment_data: dict,
    report_type: str,
    demographics: Optional[dict] = None,
) -> dict:
    """Generate a template-based report as fallback when AI is unavailable."""
    construct = assessment_data.get("construct_scores", {})
    load = assessment_data.get("load_framework", {})
    archetype = assessment_data.get("archetype", {})
    summary = assessment_data.get("summary_indicators", {})
    applied = assessment_data.get("applied_domains", {})
    fin = applied.get("financial_ef", {})
    health = applied.get("health_ef", {})

    pei = construct.get("PEI_score", 0)
    bhp = construct.get("BHP_score", 0)
    quadrant = load.get("quadrant", "Unknown")
    load_state = load.get("load_state", "Unknown")
    arch_name = archetype.get("archetype_id", "Unknown").replace("_", " ")
    arch_desc = archetype.get("description", "")
    strengths = summary.get("top_strengths", [])
    growth = summary.get("growth_edges", [])

    balance_str = "strain" if pei > bhp else "stabilization"
    interp = fin.get("interpretation", {})

    sections = {
        "galaxy_snapshot": (
            f"Your profile reflects a system with {'developing' if bhp < 0.5 else 'established'} "
            f"internal capacity (BHP: {bhp:.2f}) navigating "
            f"{'elevated' if pei > 0.5 else 'moderate'} external demands (PEI: {pei:.2f}). "
            f"Your system is currently in a state of {balance_str}. "
            f"This does not reflect a lack of ability. It reflects a load "
            f"{'imbalance' if pei > bhp else 'balance'}, where "
            f"{'external demands temporarily exceed' if pei > bhp else 'internal capacity meets'} "
            f"available regulatory support."
        ),
        "galaxy_placement": (
            f"Quadrant: {quadrant.replace('_', ' ')}\n"
            f"Zone: {load_state.replace('_', ' ')}\n"
            f"Your system demonstrates capability under structured conditions. "
            f"Performance may become less predictable when demands stack."
        ),
        "archetype_profile": (
            f"Archetype: {arch_name}\n\n{arch_desc}\n\n"
            f"Under increased load, your natural strengths may shift into patterns of "
            f"delayed initiation or scattered focus. Your system benefits from clarity, "
            f"structure, and reduced cognitive load at the point of action."
        ),
        "ef_ecosystem": (
            f"Action & Follow-Through: "
            f"{'Strong' if bhp > 0.5 else 'Developing'} when expectations are clear. "
            f"May reduce when multiple tasks compete.\n\n"
            f"Focus & Drive: Naturally engaged when work is meaningful. "
            f"Can become fragmented under competing demands.\n\n"
            f"Emotional Regulation: Generally {'stable' if bhp > 0.45 else 'variable'}. "
            f"Sensitive to cumulative stress.\n\n"
            f"Life Load (Environmental Demands): "
            f"Current load is {'elevated' if pei > 0.5 else 'moderate'}. "
            f"This domain is acting as a "
            f"{'primary pressure source' if pei > 0.6 else 'moderate influence'} within your system."
        ),
        "financial_ef_profile": (
            f"Financial Executive Functioning Profile™\n\n"
            f"Score: {fin.get('domain_score', 50)}/100 | Status: {fin.get('status_band', 'N/A')}\n\n"
            f"Your financial executive functioning reflects your system's ability to manage "
            f"planning, regulation, and decision-making under financial pressure. "
            f"{interp.get('domain_narrative', interp.get('when_stable', ''))}"
        ),
        "health_ef_profile": (
            f"Health & Fitness Executive Functioning Profile™\n\n"
            f"Score: {health.get('domain_score', 50)}/100 | Status: {health.get('status_band', 'N/A')}\n\n"
            f"Your health executive functioning reflects how your system supports eating, "
            f"movement, sleep, and self-care under real-life demand. "
            f"{health.get('interpretation', {}).get('domain_narrative', health.get('interpretation', {}).get('when_stable', ''))}"
        ),
        "pei_analysis": (
            f"Your current PEI (external load) is {pei:.2f}. "
            f"Primary pressure sources in your environment may include competing responsibilities, "
            f"financial considerations, and daily demands that draw from the same executive "
            f"functioning resources simultaneously."
        ),
        "bhp_analysis": (
            f"Your current BHP (internal capacity) is {bhp:.2f}. "
            f"Your system demonstrates capacity in areas such as: "
            f"{', '.join(strengths[:3]) if strengths else 'adaptive thinking, awareness'}. "
            f"Strain may occur when tasks require sustained organization or when demands "
            f"overlap without clear sequencing."
        ),
        "pei_bhp_interaction": (
            f"Your profile reflects a system where "
            f"{'external demands currently exceed internal capacity' if pei > bhp else 'internal capacity is meeting external demands'}. "
            f"When demands increase, understanding may remain intact while execution consistency "
            f"becomes variable. This creates a pattern where capability exists but consistent "
            f"performance depends on load conditions."
        ),
        "strength_profile": (
            f"Your consistent strengths include: "
            f"{', '.join(s.replace('_', ' ').title() for s in strengths) if strengths else 'adaptive thinking, awareness, capacity for growth'}. "
            f"These act as capacity anchors that help restore balance and support "
            f"long-term development when paired with structure."
        ),
        "growth_edges": (
            f"Your load sensitivity zones include: "
            f"{', '.join(g.replace('_', ' ').title() for g in growth) if growth else 'task initiation under pressure, sustained follow-through'}. "
            f"These are not weaknesses — they are points where total system load exceeds "
            f"available support structures."
        ),
        "aims_plan": (
            f"A — Awareness & Activation: Recognize when demands begin to overlap. "
            f"Identify early signals such as delay, fatigue, or reduced follow-through.\n\n"
            f"I — Intervention & Implementation: Break tasks into single-step actions. "
            f"Use external structure tools. Introduce one simple financial awareness habit. "
            f"Stabilize one health anchor.\n\n"
            f"M — Mastery & Integration: Practice consistency under low-pressure conditions. "
            f"Gradually apply strategies during higher-demand periods. Track patterns, not perfection.\n\n"
            f"S — Sustain / Scaffold / Systemize: Build repeatable routines. "
            f"Create weekly planning resets. Reduce decision fatigue through pre-structured systems."
        ),
    }

    # Add lens-exclusive section (Addendum Phase 3)
    from scoring_engine.prompts.section_rules import LENS_EXCLUSIVE_SECTIONS
    exclusive = LENS_EXCLUSIVE_SECTIONS.get(report_type)
    if exclusive:
        sections[exclusive["key"]] = (
            f"{exclusive['title']}\n\n"
            f"Your executive functioning profile in this domain reflects "
            f"{'strong capacity' if bhp > 0.5 else 'developing capacity'} "
            f"under {'elevated' if pei > 0.5 else 'moderate'} load conditions. "
            f"Patterns observed here connect directly to your PEI × BHP interaction, "
            f"showing how your system responds when demands in this specific area increase."
        )

    sections["pattern_continuity"] = (
        f"This pattern may appear across multiple areas of your life. "
        f"The core pattern is: stability when demands are contained, variability when "
        f"demands overlap. This reflects a system responding to pressure — not a lack "
        f"of ability. You take yourself everywhere you go — but the environment determines "
        f"how your system expresses itself."
    )
    sections["expansion_pathway"] = (
        f"To expand your insight and see how this pattern adapts across different "
        f"areas of your life, you might explore additional report lenses. "
        f"Each lens reveals how the same core executive functioning system operates "
        f"within different environmental contexts."
    )
    sections["cosmic_summary"] = (
        f"Your system is capable, adaptive, and responsive. "
        f"When demands are balanced, you demonstrate focus, engagement, and follow-through. "
        f"The goal is not to push harder. It is to align your environment and support "
        f"your system so your performance becomes consistent — not conditional."
    )

    return sections


def _generate_cosmic_template(
    assessment_data: dict,
    lens_reports: dict[str, dict],
    demographics: Optional[dict] = None,
) -> dict:
    """Generate a template-based Cosmic Integration report as fallback."""
    construct = assessment_data.get("construct_scores", {})
    pei = construct.get("PEI_score", 0)
    bhp = construct.get("BHP_score", 0)
    summary = assessment_data.get("summary_indicators", {})
    strengths = summary.get("top_strengths", [])
    growth = summary.get("growth_edges", [])

    sections = {
        "cosmic_snapshot": (
            f"Across your academic, personal, professional, and family environments, "
            f"a consistent pattern emerges: you are a capable system operating under "
            f"{'sustained and overlapping' if pei > 0.5 else 'moderate'} external demands. "
            f"When expectations are structured and manageable, you demonstrate focus, "
            f"engagement, and follow-through. As demands increase and overlap, your system "
            f"may shift into delayed initiation and reduced consistency."
        ),
        "galaxy_convergence_map": (
            f"Across all four environments, your patterns show strong alignment. "
            f"Converging pattern: stability when expectations are clear and load is contained, "
            f"variability when multiple demands compete simultaneously. "
            f"Task initiation becomes more effortful under pressure across all domains."
        ),
        "load_balance_matrix": (
            f"High Stability Zones: Structured tasks with clear expectations.\n"
            f"Transitional Zones: Daily routines, personal organization, financial planning.\n"
            f"High Strain Zones: Overlapping responsibilities, unstructured environments, "
            f"periods of fatigue or reduced regulation."
        ),
        "cross_domain_load_transfer": (
            f"Your system demonstrates clear load transfer patterns. "
            f"Financial pressure increases mental load and decision fatigue, reducing focus "
            f"in other areas. Health inconsistency reduces energy and task initiation capacity. "
            f"When multiple domains increase pressure simultaneously, your system may reach "
            f"capacity faster, leading to avoidance or delay."
        ),
        "core_system_identity": (
            f"Across environments, when pressure increases, your system tends to shift into "
            f"a reflective state where internal awareness remains strong but external execution "
            f"becomes more effortful. This may look like: thinking clearly but acting less "
            f"consistently, wanting to engage but lacking bandwidth."
        ),
        "global_strength_architecture": (
            f"Across all domains, your consistent strengths include: "
            f"{', '.join(s.replace('_', ' ').title() for s in strengths[:4]) if strengths else 'adaptive thinking, awareness, capacity for growth'}. "
            f"These act as System Stabilizers that support recovery and long-term growth."
        ),
        "system_wide_sensitivity": (
            f"Across all environments, the same sensitivity points appear: "
            f"{', '.join(g.replace('_', ' ').title() for g in growth[:4]) if growth else 'task initiation under pressure, sustained follow-through'}. "
            f"These are not weaknesses — they are points where total system load exceeds "
            f"available support structures."
        ),
        "pattern_continuity_amplified": (
            f"Across your life, one pattern consistently emerges: you operate effectively "
            f"when load is contained, and your performance becomes variable when demands "
            f"overlap. This pattern is present in school, work, personal routines, and "
            f"family interactions. You take yourself everywhere you go — but the environment "
            f"determines how your system expresses itself."
        ),
        "cosmic_aims": (
            f"A — Awareness: Recognize when multiple domains begin to overlap. "
            f"Identify early signals: delay, fatigue, reduced follow-through.\n\n"
            f"I — Intervention: Prioritize one primary domain at a time during high load. "
            f"Reduce overlap where possible.\n\n"
            f"M — Mastery: Stabilize consistency in one domain. "
            f"Gradually extend stability into others.\n\n"
            f"S — Systemize: Build life-wide systems, not isolated habits. "
            f"Create weekly planning resets and predictable routines."
        ),
        "expansion_pathway": (
            f"To deepen your system understanding, consider: Financial Deep-Dive Report, "
            f"Health & Fitness Deep-Dive Report, or Compatibility Report. "
            f"These provide targeted insight into specific domains driving your overall load system."
        ),
        "cosmic_summary": (
            f"You are not inconsistent across your life. You are a consistent system "
            f"responding to different levels of pressure. Across all environments, your "
            f"ability remains intact. What changes is: load, structure, and support. "
            f"The goal is not to become someone different in each area. It is to "
            f"understand your system once — and support it everywhere."
        ),
    }

    return sections


# =============================================================================
# REPORT STORAGE
# =============================================================================

# In-memory store for reports (used when database unavailable)
_report_store: dict[str, dict] = {}


def store_report(
    user_id: str,
    assessment_id: str,
    report: dict,
) -> str:
    """Store a generated report. Returns report_id."""
    report_id = report.get("report_id", str(uuid.uuid4()))

    # Try database first
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()

        record = {
            "id": report_id,
            "user_id": user_id,
            "assessment_id": assessment_id,
            "report_type": report["report_type"],
            "sections": report["sections"],
            "validation": report.get("validation"),
            "generated_at": report.get("generated_at", datetime.now(timezone.utc).isoformat()),
        }

        client.table("generated_reports").insert(record).execute()
        logger.info(f"Report stored in DB: id={report_id}, user={user_id}, type={report['report_type']}")
        return report_id

    except Exception as e:
        logger.warning(f"DB storage failed, using memory: {e}")
        _report_store[report_id] = {
            "user_id": user_id,
            "assessment_id": assessment_id,
            **report,
        }
        return report_id


def get_report(report_id: str) -> Optional[dict]:
    """Retrieve a generated report by ID."""
    # Try database
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()
        response = (
            client.table("generated_reports")
            .select("*")
            .eq("id", report_id)
            .maybe_single()
            .execute()
        )
        if response.data:
            return response.data
    except Exception as e:
        logger.warning(f"DB lookup failed: {e}")

    # Fallback to memory
    return _report_store.get(report_id)


def get_user_lens_reports(user_id: str, assessment_id: str) -> dict[str, dict]:
    """Get all lens reports for a user's assessment. Returns {lens_type: sections}."""
    reports = {}

    # Try database
    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()
        response = (
            client.table("generated_reports")
            .select("id, report_type, sections")
            .eq("user_id", user_id)
            .eq("assessment_id", assessment_id)
            .neq("report_type", "FULL_GALAXY")
            .execute()
        )
        if response.data:
            for r in response.data:
                reports[r["report_type"]] = r["sections"]
            return reports
    except Exception as e:
        logger.warning(f"DB lookup failed: {e}")

    # Fallback to memory
    for rid, rdata in _report_store.items():
        if (rdata.get("user_id") == user_id and
            rdata.get("assessment_id") == assessment_id and
            rdata.get("report_type") != "FULL_GALAXY"):
            reports[rdata["report_type"]] = rdata["sections"]

    return reports


def get_user_lens_report_ids(user_id: str, assessment_id: str) -> dict[str, str]:
    """Get report IDs for a user's lens reports. Returns {lens_type: report_id}."""
    ids = {}

    try:
        from scoring_engine.supabase_client import get_supabase_client
        client = get_supabase_client()
        response = (
            client.table("generated_reports")
            .select("id, report_type")
            .eq("user_id", user_id)
            .eq("assessment_id", assessment_id)
            .execute()
        )
        if response.data:
            for r in response.data:
                ids[r["report_type"]] = r["id"]
            return ids
    except Exception as e:
        logger.warning(f"DB report ID lookup failed: {e}")

    # Fallback to memory
    for rid, rdata in _report_store.items():
        if (rdata.get("user_id") == user_id and
            rdata.get("assessment_id") == assessment_id):
            ids[rdata["report_type"]] = rdata.get("report_id", rid)

    return ids


def check_cosmic_eligibility(user_id: str, assessment_id: str) -> dict:
    """Check if a user has all 4 lenses to unlock the Cosmic Integration Report."""
    reports = get_user_lens_reports(user_id, assessment_id)
    required = {"STUDENT_SUCCESS", "PERSONAL_LIFESTYLE", "PROFESSIONAL_LEADERSHIP", "FAMILY_ECOSYSTEM"}
    completed = set(reports.keys()) & required
    missing = required - completed

    return {
        "eligible": len(missing) == 0,
        "completed_lenses": list(completed),
        "missing_lenses": list(missing),
        "total_completed": len(completed),
        "total_required": len(required),
    }
