Backend
Phase 1- Section 6
```
6.0 Output Structure (JSON Schema for
```
```
Scoring & Reporting)
```
6.1 Purpose
This section defines the standardized output schema that the backend system must produce
after scoring is complete.
This JSON structure serves as the single source of truth for:
```
• Report generation (PDF, dashboard, UI)
```
```
• Visualization layers (Galaxy map, quadrants)
```
```
• AI interpretation layer (future-ready)
```
• Data storage and analytics
All system outputs must conform exactly to this structure to ensure consistency across all
applications.
6.2 Output Architecture Overview
The output is organized into six core layers:
1. Metadata
2. Item-Level Data (optional but recommended)
3. Domain Profiles
4. Construct Scores (PEI & BHP)
5. Load Framework (Quadrant + State)
6. Summary Indicators (Strengths, Growth Edges)
```
6.3 Full JSON Schema (Master Output)
```
```
{
```
```
"metadata": {
```
"assessment_id": "BEST_EF_GALAXY_V1",
"user_id": "UUID_OR_HASH",
"timestamp": "ISO_8601",
"report_type": "student | personal | professional | family"
```
},
```
Backend
Phase 1- Section 6
```
"construct_scores": {
```
"PEI_score": 0.62,
"BHP_score": 0.48
```
},
```
```
"load_framework": {
```
"quadrant": "Q3_Overload",
"load_balance": -0.14,
"load_state": "Emerging_Strain",
```
"coordinates": {
```
"x": 0.62,
"y": 0.48
```
}
```
```
},
```
"domains": [
```
{
```
"name": "Emotional Regulation",
"score": 0.82,
"classification": "Strength",
"rank": 1
```
},
```
```
{
```
"name": "Task Initiation",
"score": 0.52,
"classification": "Emerging",
"rank": 4,
```
"construct_balance": {
```
"PEI": 0.68,
"BHP": 0.52,
"interpretation": "Environment-driven strain"
```
}
```
```
}
```
],
```
"summary": {
```
"top_strengths": [
"Emotional Regulation",
"Cognitive Flexibility"
],
"growth_edges": [
"Task Initiation",
"Behavioral Responsiveness"
]
```
},
```
"items": [
```
{
```
"item_id": "Q01",
"domain": "Task Initiation",
"construct": "BHP",
Backend
Phase 1- Section 6
"raw_response": 4,
"adjusted_score": 4,
"normalized_score": 0.75
```
}
```
]
```
}
```
6.4 Metadata Requirements
Field Description
assessment_id Version control for system
```
user_id Unique identifier (must be anonymizable)
```
```
timestamp ISO format (UTC recommended)
```
report_type Determines interpretation lens
6.5 Construct Score Object
Must always include:
```
{
```
```
"PEI_score": "float (0.0–1.0)",
```
```
"BHP_score": "float (0.0–1.0)"
```
```
}
```
6.6 Load Framework Object
Must always include:
• Quadrant
• Load balance
• Load state
• Coordinates
This object feeds:
• Visualizations
• Narrative generation
• AI interpretation
Backend
Phase 1- Section 6
6.7 Domain Object Structure
Each domain must include:
Field Required
name
score
classification
rank
construct_balance Optional but recommended
6.8 Summary Object Rules
System must extract:
• Top 2–3 highest domains → top_strengths
• Bottom 2–3 lowest domains → growth_edges
```
6.9 Item-Level Data (Optional but HIGHLY Recommended)
```
```
Purpose:
```
• Debugging
• Transparency
• Future analytics
• AI explainability
```
6.10 Engineering Rules (Critical)
```
• JSON must be strictly structured and valid
• No missing required fields
• All numeric values must be:
Backend
Phase 1- Section 6
o Float type
```
o Rounded ONLY at final output stage (2–3 decimals)
```
• Field names must remain consistent across system
```
6.11 Extensibility (Future-Proofing)
```
Schema must allow for:
• Archetype assignment
• Trajectory tracking
• AI-generated narratives
• Multi-report bundling
```
• Demographic overlays (already planned ✅)
```
```
6.12 System Flow (End-to-End)
```
Assessment Input
↓
```
Item Coding Dictionary (Section 2)
```
↓
```
Scoring Engine (Section 3)
```
↓
```
PEI × BHP Framework (Section 4)
```
↓
```
Domain Aggregation (Section 5)
```
↓
```
JSON Output (Section 6)
```
↓
Report Generator / UI / AI Layer
6.13 Engineering Outcome
At completion of this section, Gregory should be able to:
✅ Generate a complete output object
✅ Feed output into report templates
✅ Build visualization layers
Backend
Phase 1- Section 6
✅ Store results in database
✅ Prepare system for AI interpretation
```
6.14 FINAL NOTE (FOR GREGORY)
```
This JSON output is the contract layer of the system.
• All upstream logic must resolve INTO this structure
• All downstream systems must READ from this structure
No component should bypass or modify this schema outside of defined transformations.