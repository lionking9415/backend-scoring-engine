Backend
Phase 1- Section 7
```
7.0 AI Interpretation Layer (Narrative &
```
```
Personalization Engine)
```
7.1 Purpose
```
This section defines how structured output data (Section 6) is translated into:
```
• Personalized narrative reports
• Insight generation
```
• Intervention recommendations (AIMS)
```
```
• Multi-lens interpretation (Personal, Student, Professional, Family)
```
This layer does NOT change scores.
It interprets them.
7.2 System Role
Scoring Engine → produces DATA
AI Layer → produces MEANING
The AI layer functions as a translation system that converts:
• Numerical outputs
→ into
• Human-readable, emotionally intelligent, and actionable insights
```
7.3 Core Input (From Section 6 JSON)
```
The AI layer receives:
```
• construct_scores (PEI, BHP)
```
```
• load_framework (quadrant, load state)
```
```
• domains (scores, classification, rank)
```
```
• summary (strengths, growth edges)
```
```
• metadata (report_type, demographics later)
```
Backend
Phase 1- Section 7
7.4 AI Interpretation Hierarchy
All narratives must follow this order:
1. Quadrant (identity state)
2. Load State (pressure level)
3. Domain Patterns (strengths + growth edges)
4. Construct Interaction (PEI vs BHP meaning)
5. AIMS Intervention Pathway
⚠️This order is non-negotiable
It ensures consistency across all reports
7.5 Quadrant Narrative Rules
Each quadrant maps to a core identity tone
Quadrant Narrative Frame
Q1 Aligned Flow Empowered, stable, optimized
Q2 Capacity Strain Capable but stretched
Q3 Overload Under pressure, support needed
Q4 Underutilized Untapped potential
Example Output:
“You are currently operating in a state where environmental demands are exceeding your
available capacity…”
7.6 Load State Narrative Rules
Load state defines intensity and urgency
Load State Tone
Surplus Capacity Expansion, growth
Backend
Phase 1- Section 7
Load State Tone
Stable Capacity Maintenance
Balanced Load Stability
Emerging Strain Caution
Critical Overload Immediate support
7.7 Domain Narrative Generation
AI must:
1. Highlight Top Strengths
2. Explain How they support EF
3. Identify Growth Edges
4. Explain why breakdown occurs
```
Example:
```
“Your strength in Emotional Regulation provides a stabilizing anchor, allowing you to remain
composed under pressure…”
```
7.8 Construct Interpretation (KEY DIFFERENTIATOR)
```
AI must explicitly interpret:
```
Is the issue INTERNAL (BHP)?
```
```
Is the issue EXTERNAL (PEI)?
```
Or is it a MISMATCH?
```
Example:
```
“Your challenges with task initiation are not due to lack of ability, but rather the level of
environmental demand exceeding your current capacity…”
🔥 THIS is your market differentiator
Backend
Phase 1- Section 7
7.9 Multi-Lens Report Adaptation
Same data → different interpretation tone
Report Type Perspective
Personal Lifestyle, self-regulation
Student Academic performance
Professional Workplace execution
Family System dynamics
```
Rule:
```
• Scoring NEVER changes
• Only interpretation context changes
```
7.10 AIMS Integration (Intervention Engine)
```
AI must map results into:
AIMS for the BEST™
Phase Purpose
Awareness & Activation Insight + recognition
Intervention & Implementation Skill building
Mastery & Integration Habit formation
Sustain / Systemize Long-term stability
7.11 AIMS Mapping Logic
Strength → Sustain & Generalize
Developed → Optimize
Emerging → Targeted Intervention
Growth Edge → Immediate Action
Backend
Phase 1- Section 7
```
7.12 Tone & Ethical Rules (CRITICAL)
```
All AI output MUST:
• Be non-pathologizing
• Be strength-based
• Avoid labels like:
o “deficit”
o “disorder”
o “failure”
• Emphasize:
o capacity
o growth
o alignment
Example Rule:
❌ “You struggle with…”
✅ “Your system is currently experiencing…”
```
7.13 Personalization Inputs (Future-Ready)
```
AI layer will incorporate:
```
• Demographics (age, role, environment)
```
• User-selected report lens
```
• Historical data (future feature)
```
⚠️These inputs:
• Modify interpretation
• DO NOT change scores
```
7.14 Output Structure (AI Layer)
```
AI produces structured narrative blocks:
Backend
Phase 1- Section 7
```
{
```
"executive_summary": "string",
"quadrant_interpretation": "string",
"load_interpretation": "string",
"strengths_analysis": "string",
"growth_edges_analysis": "string",
"pei_bhp_interpretation": "string",
```
"aims_plan": {
```
"awareness": "string",
"intervention": "string",
"mastery": "string",
"sustain": "string"
```
}
```
```
}
```
7.15 Engineering Rules
• AI must ONLY use provided JSON input
• No hallucinated data
• No score modification
```
• Output must be modular (section-based)
```
```
• Must support regeneration (same input → same structure)
```
7.16 Engineering Outcome
At completion of this section, Gregory should be able to:
✅ Pass JSON into AI prompt layer
✅ Generate structured narrative outputs
✅ Adapt narrative by report type
✅ Maintain consistency across users
```
7.17 System Flow (Final Layer)
```
```
JSON Output (Section 6)
```
↓
AI Prompt Layer
↓
```
Narrative Blocks (Section 7)
```
Backend
Phase 1- Section 7
↓
##### Report Generator (PDF/UI)