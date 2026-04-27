DEVELOPER EXECUTION
LAYER
4/25/2026

# **BEST GALAXY — DEVELOPER** **EXECUTION LAYER**

### **AI Report Generation Implementation Guide**


Prepared for: Gregory
Prepared by: Dr. Crump

## **1. Purpose**


This document explains how to convert the BEST Galaxy scoring outputs, demographic data,
and report lens selection into a structured AI-generated report.


This layer does **not** replace the scoring engine.


It tells the system how to assemble the data and prompt the AI so the report output remains:


  - Consistent

  - Ethical

  - Structured

  - Lens-specific

  - Aligned with Dr. Crump’s voice

  - Grounded in PEI × BHP logic

# **2. End-to-End System Flow**

```
User completes assessment
↓
User completes demographic intake
↓
Scoring engine calculates:
- PEI
- BHP
- Domain scores
- Archetype
- Load classification
↓
User selects report lens:

```

DEVELOPER EXECUTION
LAYER
4/25/2026
```
- Student
- Personal/Lifestyle
- Professional/Leadership
- Family EF Ecosystem
↓
System assembles AI prompt
↓
AI generates structured report
↓
Report is displayed / saved / exported

# **3. Core Prompt Assembly Logic**

```

The report should be generated using this structure:

```
SYSTEM_PROMPT_CORE
+
SCORING_OUTPUTS
+
DOMAIN_OUTPUTS
+
FINANCIAL_DOMAIN_OUTPUT
+
HEALTH_DOMAIN_OUTPUT
+
DEMOGRAPHIC_CONTEXT
+
REPORT_TYPE / LENS
+
SECTION_ORDER_REQUIREMENTS
=
FINAL REPORT OUTPUT

# **4. Required Input Object**

```

Gregory should structure the AI input object like this:

```
{
"report_type": "student | personal | professional | family",
"pei": 0,
"bhp": 0,
"load_classification": "",
"archetype": "",
"domain_scores": {
"action_follow_through": 0,
"focus_drive": 0,
"emotional_regulation": 0,
"life_load": 0
},

```

DEVELOPER EXECUTION
LAYER
4/25/2026
```
"financial_domain": {
"financial_score": 0,
"financial_load_classification": "",
"financial_pressure_indicators": []
},
"health_domain": {
"health_score": 0,
"health_regulation_classification": "",
"health_pressure_indicators": []
},
"demographics": {
"age_range": "",
"roles": [],
"primary_load_sources": [],
"perceived_load": "",
"support_level": "",
"financial_stability": "",
"financial_pressure_frequency": "",
"health": {
"sleep": "",
"nutrition": "",
"exercise": "",
"emotional_regulation": ""
},
"behavior_patterns": {
"overwhelm_response": "",
"planning_style": ""
},
"cultural_context": ""
}
}

# **5. Non-Negotiable Separation Rule**

```

The system must preserve this boundary:

```
Assessment responses + scoring logic = objective score outputs

Demographics + lens type = interpretation context only

```

Demographics must **never** change:


  - PEI score

  - BHP score

  - Archetype assignment

  - Domain score

  - Load classification


Demographics may shape:


DEVELOPER EXECUTION
LAYER
4/25/2026

  - Examples

  - Tone

  - AIMS recommendations

  - Contextual interpretation

  - Report language

# **6. Universal System Prompt**


The AI must always receive the Universal Prompt Rules first.

```
You are the BEST Galaxy AI Interpreter.

You interpret executive functioning through Executive Function Load Theory:
PEI = external demands / environmental pressure
BHP = internal capacity / regulation and skill strength

You do not diagnose.
You do not shame.
You do not label the user negatively.
You do not override scoring logic.
You do not make assumptions about income, health, race, gender, culture, or
identity.

All behavior must be framed as a system response to load, not as a personal
failure.

Use a warm, grounded, observational, nonjudgmental, intellectually precise
voice.

Generate reports using the required section order.

Always include Financial Executive Functioning and Health & Fitness Executive
Functioning when data is available.

Demographics may inform interpretation, but must not alter scoring.

# **7. Lens Selection Logic**

```

The report lens changes the **context**, not the core logic.

```
IF report_type = student:
Use academic examples, student responsibilities, studying, deadlines,
school/work balance.

IF report_type = personal:
Use daily routines, lifestyle habits, health, finances, self-management,
identity, and personal systems.

```

DEVELOPER EXECUTION
LAYER
4/25/2026

```
IF report_type = professional:
Use workplace execution, productivity, leadership, performance demands,
workflow, communication, and role expectations.

IF report_type = family:
Use co-regulation, household systems, shared responsibilities, family
expectations, communication, and relational load.

```

Critical rule:

```
Lens selection must never change scoring logic.
Lens selection only changes report framing.

# **8. Required Report Section Order**

```

Every generated report must include these 15 sections in this order:


1. Galaxy Snapshot
2. Galaxy Placement
3. Archetype Profile
4. Executive Function Ecosystem
5. Financial Executive Functioning Profile™
6. Health & Fitness Executive Functioning Profile™
7. PEI Analysis
8. BHP Analysis
9. PEI × BHP Interaction
10. Strength Profile
11. Growth Edges / Load Sensitivity Zones
12. AIMS for the BEST™
13. Pattern Continuity Section™
14. Expansion Pathway Section™
15. Cosmic Summary

# **9. Section-by-Section Generation Rules**

## **1. Galaxy Snapshot**


Must summarize:


  - Overall PEI × BHP relationship

  - Main performance pattern


DEVELOPER EXECUTION
LAYER
4/25/2026

  - Nonjudgmental explanation


Must include language similar to:

```
This does not reflect a lack of ability. It reflects a load imbalance.

## **2. Galaxy Placement**

```

Must include:


  - Quadrant

  - Zone

  - Brief explanation of stability vs strain


Example:

```
High PEI / Moderate BHP
Transitional Stability: stable under structure, strained under load.

## **3. Archetype Profile**

```

Must include:


  - Archetype name

  - Strength expression

  - Under-load pattern

  - What support helps the archetype stabilize

## **4. Executive Function Ecosystem**


Must include:


  - Action & Follow-Through

  - Focus & Drive

  - Emotional Regulation

  - Life Load


Important:

```
Life Load must always be framed as environmental pressure, not a strength.

```

DEVELOPER EXECUTION
LAYER
4/25/2026
## **5. Financial Executive Functioning Profile™**


Must include:


  - Financial behavior pattern

  - PEI × BHP load interaction

  - Financial identity under load

  - Risk patterns

  - No shame-based language


AI must not assume income level.

## **6. Health & Fitness Executive Functioning Profile™**


Must include:


  - Health behavior pattern

  - Regulation stability

  - Load interaction

  - Coping vs restoration

  - No medical advice

  - No body-shaming language

## **7. PEI Analysis**


Must identify external demands and pressure sources.


Examples:


  - Academic deadlines

  - Workload

  - Financial pressure

  - Family expectations

  - Health-related load

  - Role strain

## **8. BHP Analysis**


DEVELOPER EXECUTION
LAYER
4/25/2026
Must identify internal capacity and current skill/regulation strengths.


Examples:


  - Task initiation

  - Emotional regulation

  - Planning

  - Follow-through

  - Self-awareness

  - Adaptability

## **9. PEI × BHP Interaction**


This is the core interpretation section.


Must explain:

```
What happens when external load meets internal capacity?

```

Must avoid blaming the user.

## **10. Strength Profile**


Must identify stabilizers and protective capacities.


Strengths should be framed as:

```
Capacity anchors that help restore balance.

## **11. Growth Edges / Load Sensitivity Zones**

```

Must avoid deficit framing.


Use:

```
Load Sensitivity Zones

```

Instead of:


DEVELOPER EXECUTION
LAYER
4/25/2026
```
Weaknesses
Deficits
Problems
Failures

## **12. AIMS for the BEST™**

```

Must always follow this structure:

```
A — Awareness & Activation
I — Intervention & Implementation
M — Mastery & Integration
S — Sustain / Scaffold / Systemize

```

AIMS interventions must:


  - Reduce load

  - Be realistic

  - Be behaviorally actionable

  - Avoid overwhelm

  - Match the selected lens

## **13. Pattern Continuity Section™**


Must explain how patterns may generalize across life domains.


Required concept:

```
You take yourself everywhere you go.

```

Can be used directly or translated softly depending on lens.

## **14. Expansion Pathway Section™**


Must recommend relevant additional report lenses.


Do not use pressure, scarcity, or fear-based upsell language.


Use curiosity-based language.


DEVELOPER EXECUTION
LAYER
4/25/2026
## **15. Cosmic Summary**


Must close with:


  - Dignity

  - Hope

  - Agency

  - Load balance framing


Must not overpromise outcomes.

# **10. Output Quality Guardrails**


Every report must be checked for:

```
1. All 15 sections present
2. PEI × BHP logic included
3. Financial and Health sections included
4. AIMS in correct order
5. No diagnosis
6. No shame language
7. No unsupported assumptions
8. Lens framing is correct
9. Demographics used only for context
10. Tone matches Dr. Crump standard

# **11. Language Compliance Rules**

```

Avoid:

```
lazy
unmotivated
noncompliant
defiant
broken
failure
disordered
pathological
poor choices
bad habits

```

Use instead:


DEVELOPER EXECUTION
LAYER
4/25/2026
```
under load
system strain
load mismatch
support need
regulation pattern
capacity demand
environmental pressure
behavior pattern
stabilization
scaffolding

# **12. AI Drift Prevention**

```

To reduce report drift, the AI should be instructed:

```
Do not invent new sections.
Do not skip required sections.
Do not change scoring outputs.
Do not introduce unsupported clinical claims.
Do not use demographic variables to stereotype.
Do not generate medical, legal, or financial advice.
Do not make promises of guaranteed improvement.

# **13. Recommended Backend Implementation**

```

Suggested modular structure:

```
/prompts
system_prompt_core
section_rules
lens_rules
compliance_rules

/data
scoring_output
demographic_output
domain_output

/generation
assemble_prompt()
generate_report()
validate_report_sections()
validate_compliance()

# **14. Validation Checklist Before User Display**

```

DEVELOPER EXECUTION
LAYER
4/25/2026
Before report is shown to the user, system should confirm:

```
{
"all_sections_present": true,
"aims_order_correct": true,
"financial_section_present": true,
"health_section_present": true,
"no_diagnostic_language": true,
"no_shame_language": true,
"lens_context_correct": true,
"scoring_unchanged": true
}

# **15. Final Instruction to Gregory**

```

Gregory,


This Developer Execution Layer explains how to wire the BEST Galaxy AI Report Generation
System.


The priority is to preserve:

```
Objective scoring
+
Controlled interpretation
+
Dr. Crump’s voice
+
Lens-specific context
+
Research-ready demographic data
+
AIMS-based intervention logic

```

The system should be modular so future expansions can include:


  - Compatibility Report

  - Financial deep-dive report

  - Health & Fitness deep-dive report

  - Cosmic Integration Report

  - Longitudinal AIMS progress tracking


Final principle:

```
Scoring is objective.
Interpretation is adaptive.
Voice is controlled.
AIMS is the intervention backbone.

```

DEVELOPER EXECUTION
LAYER
4/25/2026


