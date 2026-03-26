Backend
Phase 1- Section 5
5.0 Domain Aggregation Rules
5.1 Purpose
This section defines how item-level scores are aggregated into:
• Domain scores
• Subdomain insights
• Strength profiles
• Growth edge identification
• Inputs for report narratives and AIMS interventions
This layer transforms normalized scores into interpretable behavioral patterns.
```
5.2 Domain Score Calculation (Formal Definition)
```
From Section 3:
```
domain_score = average(normalized_scores of all items within domain)
```
```
Output:
```
• Range: 0.0 → 1.0
• Each domain produces a continuous score
```
5.3 Subdomain Aggregation (If Applicable)
```
If subdomains are used:
```
subdomain_score = average(normalized_scores within subdomain)
```
```
Rule:
```
• Subdomains roll up INTO domains
• Domains DO NOT override subdomain structure
Backend
Phase 1- Section 5
5.4 Domain Classification Thresholds
Each domain score is categorized into performance bands:
Score Range Classification
```
0.80 – 1.00 Strength (High Functioning)
```
```
0.60 – 0.79 Developed (Stable but Variable)
```
```
0.40 – 0.59 Emerging (Inconsistent)
```
```
0.00 – 0.39 Growth Edge (Needs Support)
```
5.5 Strength Identification Logic
IF domain_score ≥ 0.80 → classify as Strength
These domains:
• Represent capacity anchors
• Are used to:
o Support weaker domains
o Inform AIMS intervention strategies
o Build confidence-based narratives
5.6 Growth Edge Identification Logic
IF domain_score < 0.40 → classify as Growth Edge
These domains:
• Represent load vulnerability zones
• Are prioritized for:
o Intervention planning
o Skill development
o Environmental adjustments
Backend
Phase 1- Section 5
```
5.7 Domain Ranking (Relative Strength Profile)
```
All domains must be ranked:
Sort domains from highest → lowest score
```
Output:
```
[
```
{"domain": "Emotional Regulation", "score": 0.82},
```
```
{"domain": "Task Initiation", "score": 0.74},
```
```
{"domain": "Environmental Load", "score": 0.41},
```
```
{"domain": "Behavioral Responsiveness", "score": 0.33}
```
]
5.8 Top/Bottom Domain Extraction
System must identify:
• Top 2–3 Domains → Strength anchors
• Bottom 2–3 Domains → Growth edges
5.9 Domain–Construct Interaction Mapping
Each domain must also be evaluated by construct:
```
Example:
```
```
{
```
"domain": "Task Initiation",
"BHP_component": 0.52,
"PEI_component": 0.68
```
}
```
```
Purpose:
```
• Determines if domain difficulty is:
Backend
Phase 1- Section 5
```
o Internal (capacity issue)
```
```
o External (environmental pressure)
```
```
o Interaction-based (mismatch)
```
5.10 Domain Load Interpretation Rule
IF PEI_component > BHP_component → Environment-driven strain
IF BHP_component > PEI_component → Capacity-driven pattern
IF equal → Balanced domain
5.11 Domain Contribution to Quadrant
Domains influence quadrant placement indirectly:
```
• High PEI domains → push right (higher load)
```
```
• Low BHP domains → push downward (lower capacity)
```
This supports:
• Future trajectory modeling
• AI-driven explanations
5.12 Composite Domain Profiles
Each domain must output:
```
{
```
"domain_name": "Task Initiation",
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
Backend
Phase 1- Section 5
```
5.13 Domain-to-AIMS Mapping (Intervention Bridge)
```
Each classification maps to intervention priority:
Classification AIMS Priority
Strength Sustain & Generalize
Developed Optimize
Emerging Targeted Intervention
Growth Edge Immediate Priority
5.14 Engineering Rules
• All domains must produce:
o Score
o Classification
o Rank
• System must dynamically handle:
o Any number of domains
o Any number of items per domain
• Domain calculations must be independent of:
o Report type
o User lens selection
5.15 Engineering Output
At completion of this section, Gregory should be able to:
✅ Aggregate item scores into domains
✅ Classify domain performance levels
✅ Rank domains dynamically
✅ Identify strengths and growth edges
✅ Map domains to PEI/BHP interaction
✅ Prepare structured domain profiles for reports
Backend
Phase 1- Section 5
```
5.16 Example Output (Domain Layer)
```
```
{
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
]
```
}
```