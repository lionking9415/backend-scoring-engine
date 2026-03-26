##### Backend Score
Phase 1-Section 2
2.0 Item Coding Dictionary
2.1 Purpose
The Item Coding Dictionary defines how each assessment question is translated into a structured,
machine-readable format for scoring, aggregation, and interpretation.
This dictionary serves as the single source of truth for:
• How each item is categorized
• How each response is scored
• How items contribute to domain, construct, and total scores
• How data is passed into the scoring engine and output schema
All assessment items must be fully defined within this structure to ensure consistency,
scalability, and zero ambiguity during implementation.
```
2.2 Required Fields (Per Item)
```
Each question in the assessment must be coded using the following fields:
Field Name Description
```
item_id Unique identifier for each question (e.g., Q01, Q02…)
```
item_text Full question text presented to user
domain Primary domain classification
subdomain Secondary classification within domain
```
construct PEI (external) or BHP (internal)
```
direction forward or reverse scoring
```
weight Numerical weight (default = 1.0 unless specified)
```
```
response_scale Type of scale (e.g., Likert_5, TeeterTotter_7)
```
min_score Minimum possible value
max_score Maximum possible value
```
2.3 Domain Structure (Locked Categories)
```
Backend Score
Phase 1-Section 2
All items must map into one of the predefined domains:
1. Executive Functioning Core Skills
2. Environmental Load / External Demands (PEI)
3. Internal Regulation / Behavioral Health (BHP)
4. Emotional & Cognitive Patterns
5. Behavioral Responsiveness & Habits
6. Function of Behavior
7. Behaviorally-Mediated Internal Factors
⚠️Note: Final domain labels must match exactly across:
• Assessment
• Scoring engine
• Report outputs
```
(No variations allowed once locked)
```
2.4 Construct Mapping Rules
Each item must be explicitly classified into one construct:
• PEI → External demand, environmental pressure, contextual load
• BHP → Internal capacity, regulation ability, behavioral readiness
```
Rule:
```
• No item can belong to both constructs
• Construct assignment determines how the item contributes to:
o Load calculations
o Quadrant placement
o PEI × BHP interaction logic
2.5 Directionality Rules
Each item must define scoring direction:
Backend Score
Phase 1-Section 2
• forward → Higher response = higher EF strength
• reverse → Higher response = lower EF strength
```
Example:
```
• “I stay organized with my tasks” → forward
• “I feel overwhelmed by simple tasks” → reverse
2.6 Response Scale Types
Supported response scales:
Scale Type Description
Likert_5 1–5 agreement scale
Likert_7 1–7 agreement scale
```
TeeterTotter_7 Bidirectional scale (maladaptive ↔ adaptive)
```
Teeter-Totter Rule:
• Center point = neutral
• Left side = maladaptive behavior
• Right side = adaptive replacement behavior
```
2.7 Example Item (Fully Coded)
```
```
{
```
"item_id": "Q01",
"item_text": "I am able to start tasks without procrastinating",
"domain": "Executive Functioning Core Skills",
"subdomain": "Task Initiation",
"construct": "BHP",
"direction": "forward",
"weight": 1.0,
"response_scale": "Likert_5",
"min_score": 1,
"max_score": 5
```
}
```
Backend Score
Phase 1-Section 2
2.8 Reverse-Scored Example
```
{
```
"item_id": "Q02",
"item_text": "I often feel overwhelmed before starting tasks",
"domain": "Emotional & Cognitive Patterns",
"subdomain": "Task Avoidance",
"construct": "BHP",
"direction": "reverse",
"weight": 1.0,
"response_scale": "Likert_5",
"min_score": 1,
"max_score": 5
```
}
```
```
2.9 Validation Rules (Critical for Engineering)
```
Before scoring begins, the system must validate:
• All items have required fields populated
• No duplicate item_id values
• All domains match approved domain list
• Construct values are ONLY PEI or BHP
• Direction values are ONLY forward or reverse
• Response scale aligns with min/max values
If validation fails → system should throw error and stop processing
2.10 Engineering Outcome
At completion of this section:
Gregory should be able to:
```
✅ Load all items into a structured dataset (array of objects)
```
✅ Programmatically loop through items
✅ Apply scoring rules consistently
✅ Route items into domains and constructs
```
✅ Prepare data for scoring engine (Section 3)
```
Backend Score
Phase 1-Section 2