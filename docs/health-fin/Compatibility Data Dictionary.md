


## Compatibility Data Dictionary
## 4/18/2026


 DOCUMENT 2: Compatibility Data
## Dictionary
## 1. Purpose
Defines all variables, ranges, and meanings used in the compatibility system.

## 2. Core Variables
BHP_total
- Type: float (0–100)
- Meaning: Internal executive functioning capacity
- Higher = stronger regulation, stability, resilience

PEI_total
- Type: float (0–100)
- Meaning: External load / environmental pressure
- Higher = more demand, stress, complexity

## 3. Domain Variables
action_follow_through
- Initiation, task completion, consistency
focus_drive
- Attention, persistence, motivation


## Compatibility Data Dictionary
## 4/18/2026


emotional_regulation
- Stress response, emotional control, recovery
environmental_load
- External strain (inverse domain)
financial_ef
- Budgeting, planning, financial decision-making
health_ef
- Health habits, routine consistency, coping

## 4. Derived Variables
A_to_B
- A’s ability to tolerate B’s load
B_to_A
- B’s ability to tolerate A’s load

Load_Balance
- Combined directional compatibility

Conflict_Risk
- Probability of triggering instability


## Compatibility Data Dictionary
## 4/18/2026



## Repair
- Ability to recover after rupture

Real_Life
- Functional compatibility in daily systems

## Asymmetry
- Difference in relational experience between partners

- Trigger Flags (Examples)
- avoidance_under_stress
- impulsive_decision_making
- shutdown_response
- overcontrol_response
- emotional reactivity
- inconsistency patterns

- Stabilizer Flags (Examples)
- structured routine builder
- emotional regulator
- planner/organizer
- repair initiator
- consistency anchor



## Compatibility Data Dictionary
## 4/18/2026


- Match Types (Output Variable)
pair_type: enum {
balanced_stabilizers,
growth_oriented,
intense_uneven,
high_trigger,
supportive_strained,
complementary_builders,
parallel_disconnected,
turbulent_under_load
## }


