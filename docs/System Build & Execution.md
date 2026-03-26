


## Phase 2
## System Build & Execution

##  THE BEST GALAXY – PHASE 2 SOW
## (SYSTEM BUILD & EXPERIENCE
## EXECUTION)
Prepared for: Backend Engineer (Gregory)
Prepared by: Dr. Sharlyn Crump
Phase Objective: Build the Live BEST Galaxy System

##  PHASE 2 PURPOSE
Phase 2 translates the Phase 1 architecture into a fully operational, user-facing system that
includes:
- Assessment Experience (Front-End)
- Scoring Engine Activation (Backend)
- Dashboard (Free ScoreCard)
## • Feature Gating + Payment Integration
- AI Report Generation System

## ⚙️ PHASE 2 CORE SYSTEMS

##  SYSTEM 1: ASSESSMENT EXPERIENCE ENGINE
##  Objective:
Deliver a low cognitive load, high engagement, gamified assessment experience


## Phase 2
## System Build & Execution


##  Requirements:
## 1. Assessment Flow
- 52-question sequence
- One question per screen (preferred)
- Progress indicator (visual, not text-heavy)

## 2. Response Input Design
- Slider or scaled selection (teeter-totter style preferred)
- Minimal text
- Clear anchors (left vs right meaning)

- UX Principles (NON-NEGOTIABLE)
## • SHOW > TELL
- Mobile-first design
- Fast response time
- No clutter or dense text

## 4. Data Capture
- All responses stored per user
- Linked to demographic intake
## • Timestamped


##  SYSTEM 2: SCORING + COMPUTATION ENGINE


## Phase 2
## System Build & Execution

##  Objective:
Convert raw responses → structured, scalable outputs

##  Requirements:
## 1. Scoring Logic Execution
- Apply Phase 1 scoring rules:
o Item coding
o Domain scoring
o PEI calculations
o BHP calculations
o Load Balance determination

- Output Structure (Required JSON)
## {
## "user_id": "",
## "archetype": "",
## "pei_score": {},
## "bhp_score": {},
## "load_balance": "",
## "domain_scores": {},
## "strengths": [],
## "growth_edges": [],
## "lens_previews": {
## "personal": "",
## "student": "",
## "professional": "",
## "family": ""
## }
## }

## 3. System Design Constraints
- Config-driven (no hardcoding)
- Version-controlled logic
- Fully auditable scoring pipeline


## Phase 2
## System Build & Execution



##  SYSTEM 3: FREE SCORECARD DASHBOARD
##  Objective:
Deliver high-value insight with intentional incompleteness

##  Required Components:

## 1. Galaxy Snapshot Header
- Archetype NAME only
- Short tagline

- EF Score Visualization
- 4-domain visual (graph, constellation, or bar)
- No deep explanation

## 3. Load Balance Indicator
## • Status:
o Balanced
o Slightly Imbalanced
o High Strain

## 4. Strengths + Growth Edges


## Phase 2
## System Build & Execution

- Top 2 strengths
- Top 2 growth edges
- Short labels only

- Four Lens Teasers (CRITICAL)
## • Personal / Lifestyle
## • Student Success
## • Professional / Leadership
## • Family Ecosystem
Each includes:
- 2–3 sentence AI-generated preview


##  SYSTEM 4: FEATURE GATING (CONVERSION
## ENGINE)
##  Objective:
Create visible but locked insight layers

##  Locked Sections:
## • Full Archetype Profile
- Domain-by-Domain Breakdown
- PEI vs BHP Deep Analysis
- AIMS for the BEST™ Intervention Plan
- Full AI Narrative Report

##  Behavior:


## Phase 2
## System Build & Execution

- Locked sections visible but blurred or disabled
- Click triggers upgrade prompt


##  SYSTEM 5: PAYMENT + ACCESS CONTROL
##  Objective:
Unlock full system after purchase

##  Requirements:
## 1. Stripe Integration
- Payment triggers:
o Individual report unlock
o Bundle unlock

## 2. Access Logic
- Free user:
o Dashboard only
o Locked sections visible
- Paid user:
o Full report access
o All sections unlocked


## 烙 SYSTEM 6: AI REPORT ENGINE
##  Objective:


## Phase 2
## System Build & Execution

Translate scores → meaningful human narrative

##  Requirements:
- AI Input
- Structured scoring JSON
- Demographic variables (tone shaping ONLY)

- AI Output Sections:
## • Galaxy Snapshot Summary
## • Archetype Profile
- Load Balance Narrative (PEI × BHP)
## • Strength Analysis
## • Growth Analysis
- AIMS for the BEST™ Plan
## • Cosmic Summary

## 3. Constraints:
- AI does NOT calculate scores
- AI only interprets


##  SYSTEM FLOW (END-TO-END)
- User completes 52-question assessment (FREE)
- Responses stored in database
- Scoring engine processes inputs
- Dashboard (ScoreCard) generated instantly
- User views:


## Phase 2
## System Build & Execution

o Archetype
o Scores
o Teasers
- User clicks locked content
- Stripe payment triggered
- Full report unlocked
- AI report generated + displayed/downloaded


##  PHASE 2 SUCCESS METRICS
## User Experience:
- Assessment completion rate
- Time to completion
- Drop-off points

## Conversion:
- Free → Paid conversion rate
- Report purchases
- Bundle uptake

## Data:
- Archetype distribution
- PEI/BHP imbalance patterns
- Demographic correlations


##  CRITICAL ARCHITECTURE RULES


## Phase 2
## System Build & Execution

- Separation of Systems
o Scoring ≠ AI ≠ UX
## 2. Demographics Handling
o Stored for research + AI tone only
o NOT used in scoring logic
## 3. Scalability
o Must support high-volume free users


##  FINAL STATEMENT
The BEST Galaxy system:
- Provides free access to self-awareness
- Captures high-value behavioral data
- Converts insight into transformation

## PHASE 2 = SYSTEM ACTIVATION
