**🌌 THE BEST GALAXY**

**🔧 ENGINEERING NAMING + MAPPING SPEC (FOR GREGORY)**

This document ensures that:\
👉 Frontend (user experience)\
👉 Backend (logic + scoring)\
👉 Reports (outputs)

...are ALL aligned under one unified naming system

**🔹 1. MASTER SYSTEM NAME (GLOBAL CONSTANT)**

**System Name (Canonical)**

BEST_EXECUTIVE_FUNCTION_GALAXY_ASSESSMENT

**Display Name (User-Facing)**

**The BEST Executive Function Galaxy Assessment™**

**Description**

A multi-domain executive function assessment system that evaluates
performance across four environmental lenses using PEI × BHP load
modeling.

**🔹 2. EXPERIENCE LAYER (FRONTEND ONLY)**

⚠️ NOT used in scoring or backend logic\
⚠️ Used ONLY for UI/UX and marketing

experience_name: \"BEST Galaxy Executive Function Journey\"\
experience_type: \"interactive_assessment\"

**🔹 3. REPORT LENS ARCHITECTURE (CORE SYSTEM)**

This is CRITICAL --- Gregory will use this for:

-   Routing logic

-   Report generation

-   UI display

-   Database tagging

**🎯 REPORT LENSES (ENUM)**

report_lens = \[\
\"PERSONAL_LIFESTYLE\",\
\"STUDENT_SUCCESS\",\
\"PROFESSIONAL_LEADERSHIP\",\
\"FAMILY_ECOSYSTEM\"\
\]

**🎯 REPORT DISPLAY NAMES**

PERSONAL_LIFESTYLE → \"Personal Executive Function Galaxy Report\"\
\
STUDENT_SUCCESS → \"Student Success Executive Function Galaxy Report\"\
\
PROFESSIONAL_LEADERSHIP → \"Professional Executive Function Galaxy
Report\"\
\
FAMILY_ECOSYSTEM → \"Family Executive Function Galaxy Report\"

**🔹 4. CORE CONSTRUCTS (DO NOT CHANGE)**

These are your **scientific backbone variables**

PEI = \"Probability Environment Index\" // External Load\
BHP = \"Behavioral Health Probability\" // Internal Capacity

**🎯 SYSTEM MODEL**

EXECUTIVE_FUNCTION = f(PEI × BHP)

👉 This is your **core algorithmic identity**

**🔹 5. DOMAIN ARCHITECTURE (LEVEL 1)**

These are your **scoring buckets**

⚠️ Gregory will map ALL items to these

domains = \[\
\"EXECUTIVE_FUNCTION_SKILLS\",\
\"ENVIRONMENTAL_DEMANDS\",\
\"EMOTIONAL_REGULATION\",\
\"BEHAVIORAL_PATTERNS\",\
\"COGNITIVE_CONTROL\",\
\"MOTIVATIONAL_SYSTEMS\",\
\"INTERNAL_STATE_FACTORS\"\
\]

(We can refine names later if needed --- this is structurally sound for
now)

**🔹 6. ITEM CODING STRUCTURE (PHASE 1 REQUIREMENT)**

Each question MUST follow this format:

item_id: \"Q001\"\
domain: \"EXECUTIVE_FUNCTION_SKILLS\"\
subdomain: \"TASK_INITIATION\"\
construct: \"BHP\" // or PEI\
direction: \"positive\" // or reverse\
weight: 1.0

**🎯 REQUIRED FIELDS (NO EXCEPTIONS)**

item_id\
question_text\
domain\
subdomain\
construct (PEI or BHP)\
direction (positive/reverse)\
weight\
response_scale

**🔹 7. SCORING LOGIC (SIMPLIFIED FOR BUILD)**

**Step 1: Raw Score**

User response (Likert / Teeter-Totter)

**Step 2: Reverse Score (if applicable)**

if direction == \"reverse\":\
score = max_scale - response

**Step 3: Apply Weight**

weighted_score = score \* weight

**Step 4: Aggregate**

**By Construct:**

PEI_total\
BHP_total

**By Domain:**

domain_scores\[domain\] = sum(weighted_scores)

**🔹 8. PEI × BHP LOAD MODEL (CORE FEATURE)**

This is your differentiator 🔥

load_balance = BHP_total - PEI_total

**🎯 INTERPRETATION**

if load_balance \> threshold:\
state = \"CAPACITY_DOMINANT\"\
\
elif load_balance \< -threshold:\
state = \"DEMAND_DOMINANT\"\
\
else:\
state = \"BALANCED\"

**🔹 9. REPORT GENERATION STRUCTURE**

**INPUT:**

user_id\
selected_lens\
scores (domains + PEI + BHP)

**OUTPUT:**

{\
\"galaxy_snapshot\": {},\
\"lens\": \"STUDENT_SUCCESS\",\
\"archetype\": {},\
\"pei_score\": value,\
\"bhp_score\": value,\
\"load_state\": \"BALANCED\",\
\"domain_breakdown\": {},\
\"strengths\": \[\],\
\"growth_edges\": \[\],\
\"aims_plan\": {}\
}

**🔹 10. ARCHITECTURE RULE (VERY IMPORTANT)**

👉 SAME DATA\
👉 DIFFERENT INTERPRETATION

This is KEY for Gregory:

assessment_data = ONE\
\
reports = MANY (based on lens)

⚠️ DO NOT duplicate scoring\
⚠️ ONLY change interpretation layer

**🔹 11. NAMING CONVENTION RULES**

**Backend:**

-   ALL CAPS

-   Snake case

**Frontend:**

-   Human readable

-   Branded language

**Example:**

  -----------------------------------------------------------------------
  **Layer**   **Name**
  ----------- -----------------------------------------------------------
  Backend     STUDENT_SUCCESS

  Frontend    Student Success Executive Function Galaxy Report
  -----------------------------------------------------------------------

**🔹 12. FUTURE EXPANSION**

System must support:

\- multi-report selection\
- bundle reports\
- AI interpretation layer\
- dashboard integration\
- longitudinal tracking
