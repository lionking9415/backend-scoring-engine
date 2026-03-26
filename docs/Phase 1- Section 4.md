##### Backend Score
Phase 1 -Section 4
```
4.0 PEI × BHP Framework (Load Interaction
```
```
Model)
```
4.1 Purpose
```
This section defines how aggregated construct scores (PEI and BHP) are translated into:
```
• User placement states
• Quadrant classification
• Load interpretation
• Inputs for report generation and AI interpretation
This framework operationalizes the core model:
```
Executive Function = Interaction between External Load (PEI) and Internal Capacity (BHP)
```
4.2 Core Inputs
From Section 3:
```
{
```
"PEI_score": 0.62,
"BHP_score": 0.48
```
}
```
These two values are the ONLY inputs required for:
• Quadrant placement
• Load balance
• State classification
4.3 Axis Definitions
Axis Variable Meaning
X-Axis PEI External demands / environmental load
Backend Score
Phase 1 -Section 4
Axis Variable Meaning
Y-Axis BHP Internal capacity / regulation ability
```
Scale:
```
• Range: 0.0 → 1.0
• Higher value = greater intensity
```
4.4 Quadrant System (Primary Classification)
```
The system is divided into four quadrants:
Quadrant Condition Interpretation
```
Q1: Aligned Flow High BHP, Low PEI Strong capacity, manageable demand
```
```
Q2: Capacity Strain High BHP, High PEI Strong capacity under heavy demand
```
```
Q3: Overload Low BHP, High PEI Demand exceeds capacity
```
```
Q4: Underutilized / Suppressed Low BHP, Low PEI Low demand, low activation
```
```
4.5 Threshold Definitions (Initial Logic)
```
To classify “high” vs “low”:
```
{
```
"threshold": 0.50
```
}
```
```
Rule:
```
• ≥ 0.50 → High
• < 0.50 → Low
4.6 Quadrant Assignment Logic
```
{
```
"if": "BHP >= 0.50 AND PEI < 0.50",
Backend Score
Phase 1 -Section 4
"quadrant": "Q1_Aligned_Flow"
```
}
```
```
{
```
"if": "BHP >= 0.50 AND PEI >= 0.50",
"quadrant": "Q2_Capacity_Strain"
```
}
```
```
{
```
"if": "BHP < 0.50 AND PEI >= 0.50",
"quadrant": "Q3_Overload"
```
}
```
```
{
```
"if": "BHP < 0.50 AND PEI < 0.50",
"quadrant": "Q4_Underutilized"
```
}
```
4.7 Load Balance Interpretation
From Section 3:
```
{
```
"load_balance": "BHP_score - PEI_score"
```
}
```
```
Meaning:
```
Value Interpretation
Positive Capacity exceeds demand
Negative Demand exceeds capacity
Near Zero Balanced system
```
4.8 Load State Classification (Secondary Layer)
```
Adds nuance beyond quadrants:
Load Range State Label
+0.20 or higher Surplus Capacity
+0.05 to +0.19 Stable Capacity
-0.04 to +0.04 Balanced Load
-0.05 to -0.19 Emerging Strain
-0.20 or lower Critical Overload
Backend Score
Phase 1 -Section 4
```
4.9 Combined Output (Quadrant + Load State)
```
```
Example:
```
```
{
```
"quadrant": "Q3_Overload",
"load_balance": -0.14,
"load_state": "Emerging_Strain"
```
}
```
```
4.10 Visualization Mapping (Frontend Support)
```
Coordinates for plotting:
```
{
```
"x": "PEI_score",
"y": "BHP_score"
```
}
```
Used for:
• Galaxy map placement
• Quadrant visualization
```
• Trajectory tracking (future feature)
```
```
4.11 Interpretation Rules (System-Level)
```
• Quadrant determines primary identity state
• Load balance determines pressure direction
• Load state determines severity/intensity
```
Hierarchy:
```
Quadrant → Load State → Domain Insights → AIMS Intervention
4.12 Engineering Rules
Backend Score
Phase 1 -Section 4
• Quadrant must ALWAYS be assigned
• Load state must ALWAYS be assigned
```
• Threshold must be configurable (future-proofing)
```
• System must support recalculation if thresholds change
4.13 Engineering Output
At completion of this section, Gregory should be able to:
✅ Compute quadrant placement
✅ Compute load balance
✅ Assign load state
✅ Generate coordinates for visualization
✅ Pass structured data into report engine
```
4.14 Example Final Output (Framework Layer)
```
```
{
```
"PEI_score": 0.62,
"BHP_score": 0.48,
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
}
```