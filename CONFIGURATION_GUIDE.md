# Configuration Guide

## Overview

The BEST Executive Function Galaxy Assessment™ backend is **config-driven**. All behavioral parameters, thresholds, weights, and domain mappings are defined in `scoring_engine/config.py`. You can adjust system behavior by editing this single file — **no changes to scoring logic required**.

---

## Table of Contents

1. [Response Scale Configuration](#1-response-scale-configuration)
2. [Domain-to-Index Weight Matrix](#2-domain-to-index-weight-matrix)
3. [Quadrant Threshold](#3-quadrant-threshold)
4. [Load State Ranges](#4-load-state-ranges)
5. [Domain Classification Thresholds](#5-domain-classification-thresholds)
6. [Archetype Definitions](#6-archetype-definitions)
7. [Missing Data Handling](#7-missing-data-handling)
8. [Precision Settings](#8-precision-settings)
9. [Database Configuration](#9-database-configuration)
10. [Report Lenses](#10-report-lenses)

---

## 1. Response Scale Configuration

**Location**: `config.py` lines 65-70

### Current Setting
```python
RESPONSE_SCALES = {
    "ABCD_4": {"min_score": 1, "max_score": 4},
    "Likert_5": {"min_score": 1, "max_score": 5},
    "Likert_7": {"min_score": 1, "max_score": 7},
    "TeeterTotter_7": {"min_score": 1, "max_score": 7},
}
```

### What It Does
Defines valid response scales for assessment items. The current assessment uses `ABCD_4` (A=4, B=3, C=2, D=1).

### How to Modify
**Add a new scale** (e.g., 1-10 scale):
```python
RESPONSE_SCALES = {
    "ABCD_4": {"min_score": 1, "max_score": 4},
    "Likert_10": {"min_score": 1, "max_score": 10},  # NEW
}
```

Then update items in `item_dictionary.py`:
```python
{
    "item_id": "Q01",
    "response_scale": "Likert_10",  # Changed from ABCD_4
    "min_score": 1,
    "max_score": 10,
}
```

**Impact**: Normalization formulas automatically adjust. A response of 5 on a 1-10 scale normalizes to `(5-1)/(10-1) = 0.444`.

---

## 2. Domain-to-Index Weight Matrix

**Location**: `config.py` lines 169-177

### Current Setting
```python
DOMAIN_INDEX_WEIGHTS = {
    "EXECUTIVE_FUNCTION_SKILLS": {"PEI": 0.0, "BHP": 1.0},
    "ENVIRONMENTAL_DEMANDS":     {"PEI": 1.0, "BHP": 0.0},
    "EMOTIONAL_REGULATION":      {"PEI": 0.3, "BHP": 1.0},  # Overlapping
    "BEHAVIORAL_PATTERNS":       {"PEI": 0.0, "BHP": 1.0},
    "COGNITIVE_CONTROL":         {"PEI": 0.0, "BHP": 1.0},
    "MOTIVATIONAL_SYSTEMS":      {"PEI": 0.4, "BHP": 0.8},  # Overlapping
    "INTERNAL_STATE_FACTORS":    {"PEI": 0.6, "BHP": 0.7},  # Overlapping
}
```

### What It Does
Controls how each domain contributes to the **PEI** (external demand) and **BHP** (internal capacity) indices. This is the **key architectural feature** — domains can contribute to BOTH indices with different weights.

### How to Modify

**Example 1**: Make Emotional Regulation contribute MORE to PEI
```python
"EMOTIONAL_REGULATION": {"PEI": 0.5, "BHP": 1.0},  # Was 0.3
```

**Example 2**: Make a domain exclusive to one index
```python
"COGNITIVE_CONTROL": {"PEI": 0.0, "BHP": 1.0},  # BHP only
```

**Example 3**: Create balanced overlap
```python
"MOTIVATIONAL_SYSTEMS": {"PEI": 0.5, "BHP": 0.5},  # Equal contribution
```

### Calculation Formula
```
PEI_score = Σ(domain_score × PEI_weight) / Σ(PEI_weight)
BHP_score = Σ(domain_score × BHP_weight) / Σ(BHP_weight)
```

**Impact**: Changes the PEI and BHP scores, which shifts quadrant placement and load balance.

### Best Practices
- Weights between `0.0` and `1.0`
- At least one domain must have non-zero weight for each index
- Use overlapping weights (both PEI and BHP > 0) for domains that reflect both internal and external factors

---

## 3. Quadrant Threshold

**Location**: `config.py` line 110

### Current Setting
```python
QUADRANT_THRESHOLD = 0.50
```

### What It Does
Defines the cutoff between "High" and "Low" for both PEI and BHP, creating the 2×2 quadrant system:

```
        High BHP (≥0.50)
             │
    Q1       │       Q2
  Aligned    │    Capacity
   Flow      │     Strain
─────────────┼─────────────  PEI = 0.50
    Q4       │       Q3
Underutilized│   Overload
             │
        Low BHP (<0.50)
```

### How to Modify

**Raise threshold** (stricter definition of "high"):
```python
QUADRANT_THRESHOLD = 0.60  # Now need 60% to be "high"
```

**Lower threshold** (more lenient):
```python
QUADRANT_THRESHOLD = 0.40  # Only need 40% to be "high"
```

**Impact**: 
- Higher threshold → More users in Q3 (Overload) and Q4 (Underutilized)
- Lower threshold → More users in Q1 (Aligned Flow) and Q2 (Capacity Strain)

### Recommendation
`0.50` is the standard midpoint. Adjust only if clinical data suggests a different cutoff is more meaningful.

---

## 4. Load State Ranges

**Location**: `config.py` lines 105-111

### Current Setting
```python
LOAD_STATES = [
    {"label": "Surplus_Capacity", "min": 0.20, "max": float("inf")},
    {"label": "Stable_Capacity", "min": 0.05, "max": 0.19},
    {"label": "Balanced_Load", "min": -0.04, "max": 0.04},
    {"label": "Emerging_Strain", "min": -0.19, "max": -0.05},
    {"label": "Critical_Overload", "min": float("-inf"), "max": -0.20},
]
```

### What It Does
Classifies the **load balance** (BHP - PEI) into 5 states:

| Load Balance | State | Interpretation |
|--------------|-------|----------------|
| ≥ 0.20 | Surplus Capacity | Capacity far exceeds demand |
| 0.05 to 0.19 | Stable Capacity | Capacity exceeds demand |
| -0.04 to 0.04 | Balanced Load | Demand and capacity matched |
| -0.19 to -0.05 | Emerging Strain | Demand exceeds capacity |
| ≤ -0.20 | Critical Overload | Demand far exceeds capacity |

### How to Modify

**Widen the "Balanced" zone**:
```python
{"label": "Balanced_Load", "min": -0.10, "max": 0.10},  # Was -0.04 to 0.04
```

**Create more granular states**:
```python
LOAD_STATES = [
    {"label": "Extreme_Surplus", "min": 0.30, "max": float("inf")},
    {"label": "Surplus_Capacity", "min": 0.15, "max": 0.29},
    {"label": "Stable_Capacity", "min": 0.05, "max": 0.14},
    {"label": "Balanced_Load", "min": -0.04, "max": 0.04},
    {"label": "Emerging_Strain", "min": -0.14, "max": -0.05},
    {"label": "Moderate_Overload", "min": -0.29, "max": -0.15},
    {"label": "Critical_Overload", "min": float("-inf"), "max": -0.30},
]
```

**Impact**: Changes archetype assignment (archetypes map to quadrant + load state).

---

## 5. Domain Classification Thresholds

**Location**: `config.py` lines 117-122

### Current Setting
```python
DOMAIN_CLASSIFICATIONS = [
    {"label": "Strength", "min": 0.80, "max": 1.00},
    {"label": "Developed", "min": 0.60, "max": 0.79},
    {"label": "Emerging", "min": 0.40, "max": 0.59},
    {"label": "Growth_Edge", "min": 0.00, "max": 0.39},
]
```

### What It Does
Labels each domain based on its normalized score (0.0 to 1.0).

### How to Modify

**More granular classifications**:
```python
DOMAIN_CLASSIFICATIONS = [
    {"label": "Mastery", "min": 0.90, "max": 1.00},
    {"label": "Strength", "min": 0.75, "max": 0.89},
    {"label": "Developed", "min": 0.60, "max": 0.74},
    {"label": "Emerging", "min": 0.40, "max": 0.59},
    {"label": "Developing", "min": 0.25, "max": 0.39},
    {"label": "Growth_Edge", "min": 0.00, "max": 0.24},
]
```

**Stricter "Strength" threshold**:
```python
{"label": "Strength", "min": 0.85, "max": 1.00},  # Was 0.80
```

**Impact**: Changes which domains appear in "Top Strengths" vs "Growth Edges" lists.

---

## 6. Archetype Definitions

**Location**: `config.py` lines 187-268

### Current Setting
```python
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
    # ... 14 more archetypes
}
```

### What It Does
Maps each **quadrant + load state** combination to a named archetype with a description.

### How to Modify

**Change archetype name**:
```python
"THE_STRATEGIST": {  # Was "THE_NAVIGATOR"
    "quadrant": "Q1_Aligned_Flow",
    "load_state": "Surplus_Capacity",
    "description": "High capacity, low demand — strategically positioned and self-directed.",
}
```

**Update description**:
```python
"THE_OPTIMIZER": {
    "quadrant": "Q1_Aligned_Flow",
    "load_state": "Stable_Capacity",
    "description": "Operating at peak efficiency with capacity to spare for growth.",  # NEW
}
```

**Add a new archetype** (if you added a new load state):
```python
"THE_EXPLORER": {
    "quadrant": "Q1_Aligned_Flow",
    "load_state": "Extreme_Surplus",  # New load state from section 4
    "description": "Vast untapped potential seeking meaningful challenges.",
}
```

**Impact**: Changes the archetype label and description in the output JSON and AI narratives.

---

## 7. Missing Data Handling

**Location**: `config.py` lines 139-140

### Current Setting
```python
MISSING_DATA_RULE = "compute_available"
LOW_CONFIDENCE_THRESHOLD = 0.70
```

### What It Does
- `MISSING_DATA_RULE`: How to handle incomplete assessments
  - `"compute_available"`: Score using answered items only (current)
  - `"require_complete"`: Reject if any items missing (not implemented)
- `LOW_CONFIDENCE_THRESHOLD`: Flag results if completion rate < 70%

### How to Modify

**Stricter confidence threshold**:
```python
LOW_CONFIDENCE_THRESHOLD = 0.85  # Flag if <85% complete
```

**More lenient**:
```python
LOW_CONFIDENCE_THRESHOLD = 0.50  # Only flag if <50% complete
```

**Impact**: Changes when the `low_confidence` flag appears in output metadata.

---

## 8. Precision Settings

**Location**: `config.py` lines 153-154

### Current Setting
```python
INTERNAL_PRECISION = 4  # Decimal places for internal calculations
OUTPUT_PRECISION = 3    # Decimal places for final output
```

### What It Does
- `INTERNAL_PRECISION`: Rounding during scoring pipeline (prevents cumulative error)
- `OUTPUT_PRECISION`: Rounding in final JSON output (user-facing)

### How to Modify

**More precise output**:
```python
OUTPUT_PRECISION = 4  # Show 0.6667 instead of 0.667
```

**Less precise** (cleaner for UI):
```python
OUTPUT_PRECISION = 2  # Show 0.67 instead of 0.667
```

**Impact**: Changes decimal places in all score fields in the output JSON.

---

## 9. Database Configuration

**Location**: `config.py` lines 273-275

### Current Setting
```python
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/best_galaxy"
DATABASE_URL_SYNC = "postgresql://postgres:postgres@localhost:5432/best_galaxy"
```

### What It Does
Connection strings for PostgreSQL storage (async and sync versions).

### How to Modify

**Production database**:
```python
DATABASE_URL = "postgresql+asyncpg://user:password@prod-db.example.com:5432/best_galaxy"
DATABASE_URL_SYNC = "postgresql://user:password@prod-db.example.com:5432/best_galaxy"
```

**Environment variables** (recommended):
```python
import os
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost/best_galaxy")
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC", "postgresql://localhost/best_galaxy")
```

**Impact**: Changes where assessment results are stored.

---

## 10. Report Lenses

**Location**: `config.py` lines 19-31

### Current Setting
```python
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
```

### What It Does
Defines available report types. Same assessment data, different AI narrative interpretations.

### How to Modify

**Add a new lens**:
```python
REPORT_LENSES = [
    "PERSONAL_LIFESTYLE",
    "STUDENT_SUCCESS",
    "PROFESSIONAL_LEADERSHIP",
    "FAMILY_ECOSYSTEM",
    "CLINICAL_DIAGNOSTIC",  # NEW
]

REPORT_DISPLAY_NAMES = {
    # ... existing entries
    "CLINICAL_DIAGNOSTIC": "Clinical Diagnostic Executive Function Report",
}
```

Then add lens-specific templates in `interpretation.py`:
```python
LENS_TEMPLATES = {
    # ... existing templates
    "CLINICAL_DIAGNOSTIC": {
        "executive_summary": "Clinical assessment indicates {quadrant_interpretation}...",
        # ... more templates
    }
}
```

**Impact**: New report type available via API and multi-lens processing.

---

## Quick Reference: Common Adjustments

### Make the system more sensitive to environmental demands
```python
# Increase PEI weights for overlapping domains
DOMAIN_INDEX_WEIGHTS = {
    "EMOTIONAL_REGULATION": {"PEI": 0.5, "BHP": 1.0},  # Was 0.3
    "MOTIVATIONAL_SYSTEMS": {"PEI": 0.6, "BHP": 0.8},  # Was 0.4
    "INTERNAL_STATE_FACTORS": {"PEI": 0.8, "BHP": 0.7},  # Was 0.6
}
```

### Make "Strength" classification harder to achieve
```python
DOMAIN_CLASSIFICATIONS = [
    {"label": "Strength", "min": 0.85, "max": 1.00},  # Was 0.80
    {"label": "Developed", "min": 0.65, "max": 0.84},  # Was 0.60
    # ... rest unchanged
]
```

### Widen the "balanced" zone
```python
LOAD_STATES = [
    {"label": "Surplus_Capacity", "min": 0.15, "max": float("inf")},  # Was 0.20
    {"label": "Stable_Capacity", "min": 0.05, "max": 0.14},  # Was 0.19
    {"label": "Balanced_Load", "min": -0.10, "max": 0.04},  # Was -0.04
    {"label": "Emerging_Strain", "min": -0.19, "max": -0.11},  # Was -0.05
    {"label": "Critical_Overload", "min": float("-inf"), "max": -0.20},
]
```

---

## Testing Your Changes

After modifying `config.py`, run the test suite:

```bash
python3 -m pytest tests/ -v
```

**All 135 tests should pass.** If tests fail, check:
1. Weight matrices have at least one non-zero weight per index
2. Threshold ranges don't overlap or have gaps
3. All domains in `DOMAIN_INDEX_WEIGHTS` match `APPROVED_DOMAINS`

Generate a sample output to verify:
```bash
python3 sample_run.py
```

Check `sample_output.json` to see the impact of your changes.

---

## Advanced: Adding a New Domain

If you add a new domain to the assessment:

1. **Update `config.py`**:
```python
APPROVED_DOMAINS = [
    "EXECUTIVE_FUNCTION_SKILLS",
    "ENVIRONMENTAL_DEMANDS",
    # ... existing domains
    "SOCIAL_COGNITION",  # NEW
]

DOMAIN_INDEX_WEIGHTS = {
    # ... existing weights
    "SOCIAL_COGNITION": {"PEI": 0.5, "BHP": 0.5},  # NEW
}
```

2. **Add items to `item_dictionary.py`**:
```python
{
    "item_id": "Q53",
    "item_text": "...",
    "domain": "SOCIAL_COGNITION",  # NEW
    "subdomain": "PERSPECTIVE_TAKING",
    # ... rest of item definition
}
```

3. **Run tests** to ensure validation passes.

---

## Support

For questions about configuration:
- Review the inline comments in `config.py`
- Check `Phase 1- Section X.md` documentation files
- Run `python3 sample_run.py` to see current behavior
- Contact Dr. Sherilyn Crump for clinical interpretation guidance

**Remember**: All changes to `config.py` take effect immediately — no code recompilation needed.
