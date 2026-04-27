


## Compatibility Lens: Score Logic
## 4/18/2026


 DOCUMENT 1: Compatibility Scoring
## Logic Specification
## 1. Purpose
This document defines the mathematical and computational logic used to calculate
compatibility between two users within the BEST Galaxy system.
This layer must remain:
- deterministic
- modular
- independent of narrative generation

## 2. Inputs
## Person Object Structure
Each user is represented as:
## Person {
BHP_total: number (0–100),
PEI_total: number (0–100),

domains: {
action_follow_through: number,
focus_drive: number,
emotional_regulation: number,
environmental_load: number,
financial_ef: number,
health_ef: number
## },

triggers: [array of flags],
stabilizers: [array of flags],

archetype: string,
stage: string,
aims_phase: string
## }


## Compatibility Lens: Score Logic
## 4/18/2026



## 3. Core Compatibility Scores
## 3.1 Load Balance Compatibility
## Directional Calculations
A_to_B = 100 - abs(A.BHP_total - B.PEI_total)
B_to_A = 100 - abs(B.BHP_total - A.PEI_total)
## Combined Score
Load_Balance = (A_to_B + B_to_A) / 2
## Adjustments
- If both PEI > 75 → subtract 10–15 penalty
- If both BHP < 40 → subtract 10–15 penalty
- If one BHP > 70 and other PEI < 50 → add 5–10 stabilization bonus

## 3.2 Regulation Compatibility
Regulation = weighted(
alignment,
recovery_fit,
co_regulation,
repair_capacity
## )
Suggested weights:
- alignment: 30%
- recovery fit: 25%
- co-regulation: 25%
- repair capacity: 20%

## 3.3 Executive Function Partnership Score


## Compatibility Lens: Score Logic
## 4/18/2026


EF_Partnership = weighted(
action_follow_through_match,
focus_drive_match,
consistency,
complementarity
## )
## Weights:
- action/follow-through: 35%
- focus/drive: 25%
- consistency: 20%
- complementarity bonus: 20%

## 3.4 Conflict Risk Score
Conflict_Risk =
sum(trigger_overlap + domain_conflicts + instability_patterns)
Normalize to 0–100.

## 3.5 Recovery & Repair Score
Repair = weighted(
recovery_speed,
accountability,
willingness,
problem_solving,
reconnection_probability
## )
## Weights:
- recovery speed: 20%
- accountability: 25%
- willingness: 20%
- problem-solving: 20%
- reconnection: 15%



## Compatibility Lens: Score Logic
## 4/18/2026


3.6 Real-Life Systems Score
Real_Life = weighted(
communication,
home_routines,
financial_ef,
health_ef,
decision_making,
stress_adaptation
## )
## Weights:
- communication: 20%
- home/routines: 15%
- financial EF: 20%
- health EF: 15%
- decision-making: 15%
- stress adaptation: 15%

## 4. Overall Compatibility Score
## Overall =
(0.25 * Load_Balance) +
## (0.20 * Regulation) +
(0.15 * EF_Partnership) +
## (0.15 * Repair) +
(0.15 * Real_Life) +
(0.10 * (100 - Conflict_Risk))

## 5. Asymmetry Calculation
Asymmetry = abs(A_to_B - B_to_A)

## 6. Band Classification
## Overall Compatibility


## Compatibility Lens: Score Logic
## 4/18/2026


## • 85–100 → Highly Stabilizing
## • 70–84 → Strong Match
## • 55–69 → Moderate
## • 40–54 → Strained
## • 0–39 → High Turbulence
## Asymmetry
## • 0–7 → Balanced
- 8–15 → Moderate asymmetry
- 16+ → High asymmetry

## 7. Pair Type Assignment Logic
Based on:
- Overall score
## • Asymmetry
## • Conflict Risk
- Repair score
## Example:
IF Overall > 80 AND Conflict < 30 → Balanced Stabilizers
IF Overall 65–80 AND Repair high → Growth-Oriented Match
IF Asymmetry > 15 → Intense but Uneven
IF Conflict > 70 → High-Trigger Pair
