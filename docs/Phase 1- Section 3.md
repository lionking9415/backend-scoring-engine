##### Backend Score
Phase 1-Section 3
3.0 Scoring Logic
3.1 Purpose
This section defines the full transformation pipeline for converting raw user responses into:
• Standardized item scores
• Domain-level scores
```
• Construct-level scores (PEI & BHP)
```
• Aggregated outputs for interpretation and reporting
All scoring must follow a deterministic, step-by-step process to ensure consistency across all
users and report types.
3.2 Scoring Pipeline Overview
Each response passes through the following sequence:
Raw Response → Direction Adjustment → Weighted Score → Domain Aggregation →
Construct Aggregation → Final Output
3.3 Step 1: Raw Response Capture
User responses are captured exactly as selected:
```
Example:
```
```
{
```
"item_id": "Q01",
"response": 4
```
}
```
No transformation occurs at this stage.
```
3.4 Step 2: Direction Adjustment (Reverse Scoring)
```
Backend Score
Phase 1-Section 3
If direction = reverse, the score must be inverted.
```
Formula:
```
```
adjusted_score = (max_score + min_score) - raw_response
```
```
Example (Likert 1–5):
```
```
adjusted_score = (5 + 1) - 4 = 2
```
```
Rule:
```
• If forward → adjusted_score = raw_response
• If reverse → apply formula above
3.5 Step 3: Weight Application
Each adjusted score is multiplied by its assigned weight.
```
Formula:
```
```
weighted_score = adjusted_score × weight
```
```
Default:
```
```
weight = 1.0
```
```
3.6 Step 4: Normalization (Recommended for Cross-Scale
```
```
Consistency)
```
To ensure comparability across different scale types:
```
Formula:
```
```
normalized_score = (weighted_score - min_score) / (max_score - min_score)
```
Output Range:
Backend Score
Phase 1-Section 3
0.0 → 1.0
This allows:
• Likert_5 and Likert_7 to coexist
• TeeterTotter scales to align with standard scoring
3.7 Step 5: Domain Aggregation
Scores are grouped by domain.
```
Formula:
```
```
domain_score = sum(normalized_scores for all items in domain) /
```
number_of_items
```
Output:
```
• Each domain produces a value between 0.0 – 1.0
```
3.8 Step 6: Construct Aggregation (PEI vs BHP)
```
Scores are grouped by construct.
```
Formulas:
```
```
PEI_score = average(normalized_scores of all PEI items)
```
```
BHP_score = average(normalized_scores of all BHP items)
```
```
3.9 Step 7: Load Interaction Calculation (CORE MODEL)
```
This is the heart of your system.
Load Difference:
```
load_balance = BHP_score - PEI_score
```
Backend Score
Phase 1-Section 3
```
Interpretation:
```
Condition Meaning
```
BHP > PEI Capacity exceeds demand (regulated state)
```
```
PEI > BHP Demand exceeds capacity (overload state)
```
BHP ≈ PEI Balanced load
```
3.10 Optional: Load Ratio (Advanced Insight)
```
```
load_ratio = BHP_score / PEI_score
```
Used for:
• Sensitivity analysis
• AI interpretation layer
• Future predictive modeling
3.11 Missing Data Handling Rules
If a user skips items:
```
Rule Options (Choose One – MUST BE LOCKED):
```
```
Option A (Recommended):
```
• Compute using available items only
Option B:
• Require all responses before scoring
Option C:
```
• Impute missing values (not recommended for Phase 1)
```
Backend Score
Phase 1-Section 3
```
3.12 Scoring Example (End-to-End)
```
```
{
```
"item_id": "Q01",
"raw_response": 4,
"direction": "reverse",
"adjusted_score": 2,
"weight": 1.0,
"normalized_score": 0.25
```
}
```
```
3.13 Output Structure (Pre-Aggregation)
```
After item-level scoring:
```
{
```
"item_id": "Q01",
"domain": "Executive Functioning Core Skills",
"construct": "BHP",
"normalized_score": 0.75
```
}
```
```
3.14 Engineering Rules (Non-Negotiable)
```
• All calculations must be deterministic
• No rounding until final output stage
```
• Use floating-point precision (recommended: 4 decimal places internal)
```
• Maintain traceability:
o raw → adjusted → weighted → normalized
3.15 Engineering Outcome
At completion of this section, Gregory should be able to:
✅ Build scoring functions
✅ Process any number of items dynamically
✅ Generate domain scores
✅ Generate PEI & BHP scores
Backend Score
Phase 1-Section 3
✅ Compute load balance
✅ Output structured data for reporting