Demographic Intake
4/25/2026

# 📄 BEST GALAXY — DEMOGRAPHIC **INTAKE (FINAL)**

### **_Mapped for Research + AI Interpretation Layer_**


Prepared for: Gregory

# 🧠 1. CORE DESIGN PRINCIPLE


Each item is tagged for:


  - **[R] Research Use**

  - **[AI] Interpretation Use**

  - **[R+AI] Both**

# 🔒 CRITICAL RULE (SYSTEM-WIDE)


Demographic data MUST NOT alter scoring outputs
Demographic data MAY influence AI interpretation, tone, and AIMS recommendations

# 📊 2. DEMOGRAPHIC INTAKE **STRUCTURE**

## 🔹 SECTION 1: AGE & DEVELOPMENTAL STAGE


**Q1. What is your age range?**


  - 13–17

  - 18–24


Demographic Intake
4/25/2026


  - 25–34

  - 35–44

  - 45–54

  - 55+


**Tag:** [R+AI]
**AI Use:** Life-stage framing (student vs adult vs midlife load)

## 🔹 SECTION 2: GENDER IDENTITY (OPTIONAL)


**Q2. How do you identify?**


  - Female

  - Male

  - Non-binary

  - Prefer to self-describe: ______

  - Prefer not to say


**Tag:** [R]
**AI Use:** ❌ (Do NOT use in interpretation to avoid bias)

## 🔹 SECTION 3: RACE / ETHNICITY (OPTIONAL — **MULTI-SELECT)**


**Q3. Please select all that apply:**


  - Black / African American

  - Hispanic / Latino

  - White

  - Asian

  - Native American / Indigenous

  - Middle Eastern / North African

  - Pacific Islander

  - Other: ______

  - Prefer not to say


**Tag:** [R]
**AI Use:** ⚠️ Only for **cultural humility tone shaping if explicitly enabled later**


Demographic Intake
4/25/2026
## 🔹 SECTION 4: PRIMARY ROLE IDENTITY


**Q4. Which roles currently describe you? (Select all that apply)**


  - Student

  - Full-time employee

  - Part-time employee

  - Entrepreneur / Business owner

  - Parent / Caregiver

  - Unemployed / Between roles

  - Other: ______


**Tag:** [R+AI]
**AI Use:** Determines lens-relevant examples + AIMS context

## 🔹 SECTION 5: PRIMARY ENVIRONMENTAL LOAD **SOURCE**


**Q5. What areas place the MOST demand on your daily life? (Select up to 3)**


  - School / Academics

  - Work / Career

  - Parenting / Caregiving

  - Finances

  - Health / Physical well-being

  - Relationships

  - Major life transition


**Tag:** [R+AI]
**AI Use:** Direct PEI context shaping

## 🔹 SECTION 6: PERCEIVED LIFE LOAD


**Q6. How would you describe your current life load?**


  - Light

  - Manageable

  - Heavy

  - Overwhelming


Demographic Intake
4/25/2026


**Tag:** [R+AI]
**AI Use:** Validates PEI perception vs score

## 🔹 SECTION 7: SUPPORT SYSTEM


**Q7. How would you describe your current support system?**


  - Strong and consistent

  - Available but inconsistent

  - Limited

  - No support


**Tag:** [R+AI]
**AI Use:** Adjusts AIMS recommendations (external scaffolding)

# 💰 SECTION 8: FINANCIAL CONTEXT


**Q8. How would you describe your current financial stability?**


  - Stable

  - Somewhat stable

  - Uncertain

  - High financial stress


**Tag:** [R+AI]
**AI Use:** Financial PEI modifier


**Q9. How often do financial concerns impact your daily decisions?**


  - Rarely

  - Sometimes

  - Often

  - Constantly


**Tag:** [R+AI]
**AI Use:** Financial load intensity


Demographic Intake
4/25/2026

# 🏃 SECTION 9: HEALTH & REGULATION **CONTEXT**


**Q10. How consistent is your sleep routine?**


  - Very consistent

  - Somewhat consistent

  - Inconsistent

  - Highly irregular


**Q11. How would you describe your nutrition habits?**


  - Consistent and balanced

  - Somewhat consistent

  - Inconsistent

  - Highly irregular


**Q12. How often do you engage in physical movement or exercise?**


  - Regularly

  - Occasionally

  - Rarely

  - Not at all


**Q13. How would you describe your ability to emotionally regulate under stress?**


  - Strong and consistent

  - Moderate

  - Inconsistent

  - Difficult


Demographic Intake
4/25/2026


**Tag:** [R+AI] (All Health Items)
**AI Use:** Health regulation layer + AIMS targeting

# 🔄 SECTION 10: EXECUTIVE FUNCTION **CONTEXT (SELF-PERCEPTION)**


**Q14. When tasks become overwhelming, what is your most common response?**


  - Break tasks into smaller steps

  - Delay or avoid

  - Jump between tasks

  - Seek help

  - Push through with stress


**Tag:** [R+AI]
**AI Use:** Behavior pattern confirmation


**Q15. How do you typically approach planning and organization?**


  - Structured and consistent

  - Somewhat structured

  - Inconsistent

  - Avoid planning


**Tag:** [R+AI]

# 🌍 SECTION 11: CULTURAL & **CONTEXTUAL LENS (OPTIONAL)**


**Q16. Are there any cultural, community, or personal values that shape how you approach**
**work, school, or daily life?**
(Open response)


Demographic Intake
4/25/2026


**Tag:** [R+AI]
**AI Use:** Tone sensitivity + contextual respect (if used)

# 🧬 3. AI VARIABLE MAPPING (FOR **GREGORY)**

## 🔧 Output Object Example

```
{
"age_range": "",
"roles": [],
"primary_load_sources": [],
"perceived_load": "",
"support_level": "",
"financial_stability": "",
"financial_pressure_frequency": "",
"health": {
"sleep": "",
"nutrition": "",
"exercise": "",
"emotional_regulation": ""
},
"behavior_patterns": {
"overwhelm_response": "",
"planning_style": ""
},
"cultural_context": ""
}

# 🔒 4. AI USAGE CONSTRAINTS

```

AI MUST:


  - ❌ NOT infer sensitive traits (race, gender, etc.)

  - ❌ NOT stereotype

  - ❌ NOT override assessment scores


AI MAY:


  - Use:

`o` Role


Demographic Intake
4/25/2026


`o` Load perception

`o` Financial + health context

`o` Behavior responses


To:


  - Personalize tone

  - Adjust AIMS

  - Provide relevant examples


