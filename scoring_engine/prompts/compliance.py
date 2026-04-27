"""
Compliance rules — Language validation and quality guardrails for AI reports.
"""

import re
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# BANNED LANGUAGE
# =============================================================================

BANNED_WORDS = [
    "lazy", "unmotivated", "noncompliant", "defiant", "broken",
    "failure", "disordered", "pathological", "poor choices", "bad habits",
    "weakness", "deficit", "disorder", "dysfunctional", "incompetent",
    "incapable", "hopeless", "worthless",
]

BANNED_PHRASES = [
    "you always", "you never", "you lack", "you fail",
    "you struggle with", "your problem is", "you can't",
    "you should be ashamed", "what's wrong with you",
]

# =============================================================================
# REQUIRED LANGUAGE PATTERNS
# =============================================================================

REQUIRED_CONCEPTS = {
    "galaxy_snapshot": ["load", "capacity"],
    "aims_plan": ["awareness", "intervention", "mastery", "sustain"],
    "cosmic_aims": ["awareness", "intervention", "mastery", "sustain"],
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Banned-word regex contexts where the word is being NEGATED or used in a
# meta/compliance-aware way (e.g. "this is not a weakness"). Patterns are
# matched against a small lookback window before the violation.
SAFE_CONTEXTS = [
    # "not a failure" / "not reflect a failure"
    r"not\s+(?:a\s+)?(?:personal\s+)?failure",
    r"not\s+(?:a\s+)?failure",
    r"not\s+reflect\s+(?:a\s+)?(?:personal\s+)?failure",
    r"not\s+as\s+(?:a\s+)?(?:personal\s+)?failure",
    # Negated forms of weakness / deficit / disorder etc.
    r"not\s+(?:a\s+)?weakness(?:es)?",
    r"are\s+not\s+weakness(?:es)?",
    r"not\s+(?:a\s+)?deficit(?:s)?",
    r"not\s+(?:a\s+)?disorder(?:ed|s)?",
    r"not\s+dysfunctional",
    r"not\s+pathological",
    r"not\s+broken",
    r"not\s+lazy",
    r"not\s+unmotivated",
    r"not\s+a\s+sign\s+of\s+failure",
    r"not\s+about\s+(?:weakness|deficit|disorder|failure)",
    # Reframing language
    r"instead\s+of\s+(?:weakness|deficit|disorder|failure|problem)",
    r"rather\s+than\s+(?:weakness|deficit|disorder|failure|problem)",
    # Compliance disclaimers about banned framing
    r"avoid\s+(?:framing|labeling)\s+as\s+",
]


def check_banned_language(text: str) -> list[str]:
    """Check text for banned words and phrases. Returns list of violations."""
    violations = []
    text_lower = text.lower()

    for word in BANNED_WORDS:
        matches = list(re.finditer(r'\b' + re.escape(word) + r'\b', text_lower))
        for m in matches:
            # Check if this match is within a safe negation context
            start = max(0, m.start() - 40)
            context = text_lower[start:m.end() + 5]
            safe = any(re.search(pat, context) for pat in SAFE_CONTEXTS)
            if not safe:
                violations.append(f"Banned word found: '{word}'")
                break  # one violation per word is enough

    for phrase in BANNED_PHRASES:
        if phrase in text_lower:
            violations.append(f"Banned phrase found: '{phrase}'")

    return violations


def validate_section_presence(report_sections: dict, required_keys: list[str]) -> dict:
    """
    Validate that all required sections are present and non-empty.
    Returns validation result dict.
    """
    missing = []
    empty = []

    for key in required_keys:
        if key not in report_sections:
            missing.append(key)
        elif not report_sections[key] or not report_sections[key].strip():
            empty.append(key)

    return {
        "all_sections_present": len(missing) == 0,
        "missing_sections": missing,
        "empty_sections": empty,
        "valid": len(missing) == 0 and len(empty) == 0,
    }


def validate_aims_order(aims_text: str) -> bool:
    """Check that AIMS sections appear in correct A-I-M-S order."""
    if not aims_text:
        return False

    text_lower = aims_text.lower()
    positions = {}
    for label, keywords in [
        ("A", ["awareness", "activation"]),
        ("I", ["intervention", "implementation"]),
        ("M", ["mastery", "integration"]),
        ("S", ["sustain", "scaffold", "systemize"]),
    ]:
        for kw in keywords:
            pos = text_lower.find(kw)
            if pos >= 0:
                positions[label] = min(positions.get(label, 999999), pos)
                break

    if len(positions) < 4:
        return False

    order = sorted(positions.keys(), key=lambda k: positions[k])
    return order == ["A", "I", "M", "S"]


def validate_required_concepts(report_sections: dict) -> dict:
    """
    Verify that sections in REQUIRED_CONCEPTS contain all the keywords
    they must include (e.g. galaxy_snapshot must mention load AND capacity).
    """
    missing_concepts: dict[str, list[str]] = {}
    for section_key, required in REQUIRED_CONCEPTS.items():
        text = report_sections.get(section_key)
        if not text:
            continue
        text_lower = text.lower()
        absent = [kw for kw in required if kw.lower() not in text_lower]
        if absent:
            missing_concepts[section_key] = absent
    return {
        "concepts_present": len(missing_concepts) == 0,
        "missing_concepts": missing_concepts,
    }


def validate_lens_exclusive(
    report_sections: dict,
    report_type: str,
) -> dict:
    """
    Verify the lens-exclusive section is present for single-lens reports.
    For FULL_GALAXY (cosmic) reports there is no lens-exclusive section.
    """
    from scoring_engine.prompts.section_rules import LENS_EXCLUSIVE_SECTIONS

    if report_type == "FULL_GALAXY":
        return {"lens_exclusive_present": True, "expected_key": None}

    spec = LENS_EXCLUSIVE_SECTIONS.get(report_type)
    if not spec:
        return {"lens_exclusive_present": True, "expected_key": None}

    key = spec["key"]
    text = report_sections.get(key, "") or ""
    return {
        "lens_exclusive_present": bool(text.strip()),
        "expected_key": key,
    }


def validate_report(report_sections: dict, required_keys: list[str], report_type: str) -> dict:
    """
    Full validation of a generated report.
    Returns the validation checklist as specified in the client docs.
    """
    # Section presence
    section_check = validate_section_presence(report_sections, required_keys)

    # Language compliance
    all_text = " ".join(str(v) for v in report_sections.values() if v)
    language_violations = check_banned_language(all_text)

    # AIMS order
    aims_text = report_sections.get("aims_plan", "") or report_sections.get("cosmic_aims", "")
    aims_correct = validate_aims_order(aims_text)

    # Financial and health presence (single-lens only)
    fin_present = bool(report_sections.get("financial_ef_profile", "").strip()) if "financial_ef_profile" in required_keys else True
    health_present = bool(report_sections.get("health_ef_profile", "").strip()) if "health_ef_profile" in required_keys else True

    # Required concepts (galaxy_snapshot mentions load+capacity, etc.)
    concept_check = validate_required_concepts(report_sections)

    # Lens-exclusive section present for non-cosmic reports
    lens_excl_check = validate_lens_exclusive(report_sections, report_type)

    result = {
        "all_sections_present": section_check["all_sections_present"],
        "missing_sections": section_check["missing_sections"],
        "empty_sections": section_check["empty_sections"],
        "aims_order_correct": aims_correct,
        "financial_section_present": fin_present,
        "health_section_present": health_present,
        "no_diagnostic_language": len(language_violations) == 0,
        "no_shame_language": len(language_violations) == 0,
        "language_violations": language_violations,
        "concepts_present": concept_check["concepts_present"],
        "missing_concepts": concept_check["missing_concepts"],
        "lens_exclusive_present": lens_excl_check["lens_exclusive_present"],
        "lens_exclusive_expected": lens_excl_check["expected_key"],
        "lens_context_correct": report_type in [
            "STUDENT_SUCCESS", "PERSONAL_LIFESTYLE",
            "PROFESSIONAL_LEADERSHIP", "FAMILY_ECOSYSTEM", "FULL_GALAXY",
        ],
        "scoring_unchanged": True,  # Always true — AI cannot change scores
        "valid": (
            section_check["valid"]
            and len(language_violations) == 0
            and aims_correct
            and fin_present
            and health_present
            and concept_check["concepts_present"]
            and lens_excl_check["lens_exclusive_present"]
        ),
    }

    if not result["valid"]:
        logger.warning(f"Report validation failed: {result}")

    return result
