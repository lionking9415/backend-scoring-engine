"""
AI Service Module — OpenAI Integration for Report Generation (Phase 2)
Translates structured scoring output into AI-generated narratives.

This module handles:
- OpenAI API client initialization
- Prompt engineering for each report section
- AI-powered narrative generation
- Fallback to template-based generation if API unavailable
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OpenAI client (lazy initialization)
_openai_client = None


def get_openai_client():
    """Get or initialize OpenAI client."""
    global _openai_client
    
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set - AI generation will use templates")
            return None
        
        try:
            from openai import OpenAI
            _openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None
    
    return _openai_client


def generate_ai_narrative(
    section_name: str,
    scoring_data: dict,
    report_type: str,
    max_tokens: int = 300,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Generate AI narrative for a specific report section.
    
    Args:
        section_name: Name of the section (e.g., "executive_summary", "archetype_profile")
        scoring_data: Structured scoring output from the engine
        report_type: Report lens (PERSONAL_LIFESTYLE, STUDENT_SUCCESS, etc.)
        max_tokens: Maximum tokens for AI response
        temperature: AI creativity (0.0-1.0)
    
    Returns:
        AI-generated narrative string, or None if generation fails
    """
    client = get_openai_client()
    if not client:
        return None
    
    try:
        prompt = _build_prompt(section_name, scoring_data, report_type)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective model
            messages=[
                {
                    "role": "system",
                    "content": _get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        narrative = response.choices[0].message.content.strip()
        logger.info(f"Generated AI narrative for {section_name}: {len(narrative)} chars")
        return narrative
        
    except Exception as e:
        logger.error(f"AI generation failed for {section_name}: {e}")
        return None


def _get_system_prompt() -> str:
    """System prompt defining AI behavior and tone.

    Uses the canonical SYSTEM_PROMPT_CORE from `scoring_engine.prompts.system_prompt`
    so this per-section / load-summary path enforces the SAME non-negotiable
    rules as the master-template lens reports (Universal Prompt Rules §2).
    A short addendum is appended that is specific to the short-form summaries
    this module produces (length / second-person / Environmental Demands framing).
    """
    from scoring_engine.prompts.system_prompt import SYSTEM_PROMPT_CORE

    short_form_addendum = """

## SHORT-FORM OUTPUT RULES (specific to ScoreCard / per-section summaries)

- Write in the second person ("you", "your").
- Keep paragraphs concise (2-4 sentences) unless a section explicitly asks for more.
- Be specific and actionable; avoid generic filler.
- Environmental Demands represents EXTERNAL PRESSURE on the system, not internal
  capacity or strength. A high Environmental Demands score means high load/strain,
  not high performance. Never describe Environmental Demands as a strength or
  positive anchor. Frame it as demand, pressure, or load that the system must
  manage."""

    return SYSTEM_PROMPT_CORE + short_form_addendum


def _build_prompt(section_name: str, scoring_data: dict, report_type: str) -> str:
    """Build section-specific prompt from scoring data."""
    
    # Extract key data points
    archetype = scoring_data.get("archetype", {}).get("archetype_id", "Unknown")
    quadrant = scoring_data.get("load_framework", {}).get("quadrant", "")
    load_state = scoring_data.get("load_framework", {}).get("load_state", "")
    pei_score = scoring_data.get("construct_scores", {}).get("PEI_score", 0)
    bhp_score = scoring_data.get("construct_scores", {}).get("BHP_score", 0)
    load_balance = scoring_data.get("load_framework", {}).get("load_balance", 0)
    
    domains = scoring_data.get("domains", [])
    top_strengths = scoring_data.get("summary", {}).get("top_strengths", [])
    growth_edges = scoring_data.get("summary", {}).get("growth_edges", [])
    
    # Format domain info
    domain_info = "\n".join([
        f"- {d['name']}: {d['score']:.2f} ({d['classification']})"
        for d in domains[:5]  # Top 5 domains
    ])
    
    # Section-specific prompts
    prompts = {
        "executive_summary": f"""Write a 3-4 sentence executive summary for a {report_type.replace('_', ' ').title()} executive function report.

Assessment Data:
- Archetype: {archetype}
- Quadrant: {quadrant}
- Load State: {load_state}
- PEI Score: {pei_score:.2f} (environmental demand)
- BHP Score: {bhp_score:.2f} (internal capacity)
- Load Balance: {load_balance:.2f}
- Top Strengths: {', '.join(top_strengths[:2])}
- Growth Edges: {', '.join(growth_edges[:2])}

Provide a concise overview that captures the individual's current executive functioning state and primary patterns.""",

        "archetype_profile": f"""Write a detailed archetype profile (2-3 paragraphs) for someone identified as "{archetype}".

Context:
- Quadrant: {quadrant}
- Load State: {load_state}
- Report Type: {report_type.replace('_', ' ').title()}

Explain what this archetype means, how it manifests in their daily life, and what it reveals about their executive functioning patterns. Be specific and actionable.""",

        "pei_bhp_interpretation": f"""Explain the interaction between PEI (environmental demand) and BHP (internal capacity) for this individual.

Scores:
- PEI: {pei_score:.2f}
- BHP: {bhp_score:.2f}
- Difference: {load_balance:.2f}
- Quadrant: {quadrant}

Write 2-3 sentences explaining whether their challenges are driven by external demands, internal capacity, or a mismatch between the two. Be specific about what this means for them.""",

        "strengths_analysis": f"""Analyze the top strengths in this executive function profile.
IMPORTANT: Environmental Demands is NOT a strength — it represents external pressure. Only discuss internal capacity domains as strengths.

Top Strengths (capacity domains only):
{chr(10).join([f'- {s}' for s in top_strengths[:3] if s != 'ENVIRONMENTAL_DEMANDS'])}

Domain Details:
{domain_info}

Write 2-3 sentences explaining how these internal capacity strengths support their executive functioning and how they can leverage them. Do NOT include Environmental Demands as a strength.""",

        "growth_edges_analysis": f"""Analyze the growth edges in this executive function profile.

Growth Edges:
{chr(10).join([f'- {e}' for e in growth_edges[:3]])}

Domain Details:
{domain_info}

Write 2-3 sentences explaining these growth areas and what targeted support would look like. Focus on actionable insights.""",

        "aims_plan": f"""Create a brief AIMS for the BEST™ intervention plan following the A→I→M→S order (Awareness, Intervention, Mastery, Sustain).

Growth Edges: {', '.join(growth_edges[:2])}
Strengths (internal capacity only): {', '.join([s for s in top_strengths[:3] if s != 'ENVIRONMENTAL_DEMANDS'])}
Environmental Load: {'High' if pei_score > 0.7 else 'Moderate' if pei_score > 0.4 else 'Low'}

IMPORTANT: Environmental Demands should NOT appear in Sustain. Sustain is only for internal capacity strengths.
If environmental load is high, address it in Awareness (recognizing pressure) and Intervention (environmental adjustments).
Outline specific, actionable strategies that address growth edges while leveraging internal capacity strengths.

Include these closing sentences in each phase:
- Awareness: "This phase helps you identify where environmental load (PEI) may be exceeding your current internal capacity (BHP)."
- Intervention: "Intervention focuses on both strengthening internal capacity (BHP) and reducing excessive environmental load (PEI)."
- Mastery: "Mastery increases your system's ability to function effectively under varying levels of environmental load."
- Sustain: "Sustain stabilizes your system so it can maintain balance even as environmental demands fluctuate." """,

        "cosmic_summary": f"""Write a closing "Cosmic Summary" (3-4 sentences) for a {report_type.replace('_', ' ').title()} executive function report.

Assessment Data:
- Archetype: {archetype}
- Quadrant: {quadrant}
- Top Strengths (internal capacity): {', '.join([s for s in top_strengths[:2] if s != 'ENVIRONMENTAL_DEMANDS'])}
- Growth Edges: {', '.join(growth_edges[:2])}
- Load Balance: {load_balance:.2f}
- Environmental Load: {'High - significant external pressure' if pei_score > 0.7 else 'Moderate' if pei_score > 0.4 else 'Low'}

IMPORTANT: Frame Environmental Demands as external pressure/challenge on the system, NOT as a strength or guiding force.
Provide an inspiring, forward-looking closing paragraph that ties together their archetype, internal capacity strengths, and growth trajectory while acknowledging the environmental demands they face. Use a space/galaxy metaphor naturally. End with an empowering statement."""
    }
    
    return prompts.get(section_name, f"Generate insights for {section_name} based on the assessment data.")


def generate_load_balance_summary(scoring_output: dict) -> str:
    """
    Generate AI-powered 2-3 sentence executive summary for load balance section.
    This is used in the free ScoreCard to provide dynamic, personalized insights.
    
    Args:
        scoring_output: Complete scoring output from the engine
    
    Returns:
        AI-generated summary string, or fallback template if AI unavailable
    """
    client = get_openai_client()
    
    # Extract load balance data
    load_framework = scoring_output.get("load_framework", {})
    coords = load_framework.get("coordinates", {})
    pei_score = load_framework.get("PEI_score") or load_framework.get("pei_score") or coords.get("x", 0)
    bhp_score = load_framework.get("BHP_score") or load_framework.get("bhp_score") or coords.get("y", 0)
    load_balance = load_framework.get("load_balance", 0)
    quadrant = load_framework.get("quadrant", "")
    load_state = load_framework.get("load_state", "")
    
    # Determine load label
    diff = pei_score - bhp_score
    if abs(diff) <= 0.5:
        load_label = "Balanced Under Load"
    elif diff > 0.5:
        load_label = "Load Dominant (External)"
    else:
        load_label = "Capacity Dominant (Internal)"
    
    # Fallback summaries if AI unavailable
    fallback_summaries = {
        "Balanced Under Load": "You are operating with strong internal capacity, while your environment is placing sustained demands on your system. You are maintaining performance, but this pattern may require adjustment to remain sustainable over time.",
        "Load Dominant (External)": "Your environmental demands are currently exceeding your internal capacity. This mismatch may be driving challenges in executive functioning. Targeted strategies can help restore balance.",
        "Capacity Dominant (Internal)": "Your internal capacity is currently exceeding the demands placed on you by your environment. This surplus creates room for growth and proactive development of executive functioning skills."
    }
    
    if not client:
        return fallback_summaries.get(load_label, fallback_summaries["Balanced Under Load"])
    
    try:
        prompt = f"""Write a 2-3 sentence executive summary explaining this individual's load balance state.

Load Balance Data:
- PEI Score (Environmental Demand): {pei_score:.2f}
- BHP Score (Internal Capacity): {bhp_score:.2f}
- Load Balance: {load_balance:.2f}
- Load State: {load_state}
- Quadrant: {quadrant}
- Load Label: {load_label}

IMPORTANT: Environmental Load represents external PRESSURE, not strength. High PEI means high strain on the system.
If PEI is very high (>0.8) and exceeds BHP, this is a Critical Overload state — frame accordingly.
Do NOT use report-type-specific language like 'Student Success'. Use 'assessment results' for broader applicability.

Provide a clear, actionable summary that:
1. Explains the relationship between their environmental demands and internal capacity
2. Describes what this means for their executive functioning
3. Notes that high environmental load represents pressure, not performance
4. Hints at sustainability or next steps

Use second person ("you", "your"). Be compassionate and strength-based. Keep it concise (2-3 sentences max)."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": _get_system_prompt()
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info(f"Generated AI load balance summary: {len(summary)} chars")
        return summary
        
    except Exception as e:
        logger.error(f"AI load balance summary generation failed: {e}")
        return fallback_summaries.get(load_label, fallback_summaries["Balanced Under Load"])


def generate_full_ai_interpretation(scoring_output: dict) -> dict:
    """
    Generate complete AI interpretation for all report sections.
    Falls back to template-based generation if AI unavailable.
    
    Args:
        scoring_output: Complete scoring output from the engine
    
    Returns:
        Dictionary with AI-generated narratives for each section
    """
    report_type = scoring_output.get("metadata", {}).get("report_type", "PERSONAL_LIFESTYLE")
    
    sections = [
        "executive_summary",
        "archetype_profile",
        "pei_bhp_interpretation",
        "strengths_analysis",
        "growth_edges_analysis",
        "aims_plan",
        "cosmic_summary"
    ]
    
    interpretation = {}
    
    for section in sections:
        ai_narrative = generate_ai_narrative(section, scoring_output, report_type)
        
        if ai_narrative:
            interpretation[section] = ai_narrative
        else:
            # Fallback to template-based generation
            from scoring_engine.interpretation import generate_full_interpretation
            template_interp = generate_full_interpretation(scoring_output)
            
            # Map section names
            section_map = {
                "executive_summary": "executive_summary",
                "archetype_profile": "quadrant_interpretation",
                "pei_bhp_interpretation": "pei_bhp_interpretation",
                "strengths_analysis": "strengths_analysis",
                "growth_edges_analysis": "growth_edges_analysis",
                "aims_plan": "aims_plan",
                "cosmic_summary": "cosmic_summary"
            }
            
            template_key = section_map.get(section, section)
            interpretation[section] = template_interp.get(template_key, "")
    
    # Add load interpretation
    ai_load = generate_ai_narrative("load_interpretation", scoring_output, report_type, max_tokens=200)
    if ai_load:
        interpretation["load_interpretation"] = ai_load
    else:
        from scoring_engine.interpretation import generate_load_narrative
        load_state = scoring_output.get("load_framework", {}).get("load_state", "")
        interpretation["load_interpretation"] = generate_load_narrative(load_state)
    
    return interpretation
