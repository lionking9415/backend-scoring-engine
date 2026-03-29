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
    """System prompt defining AI behavior and tone."""
    return """You are an expert clinical psychologist specializing in executive function assessment. 

Your role is to translate structured assessment data into compassionate, actionable insights for individuals seeking to understand their executive functioning patterns.

CRITICAL GUIDELINES:
- Use strength-based, non-pathologizing language
- Avoid terms like "deficit", "disorder", "failure", "broken"
- Emphasize capacity, growth, and alignment
- Be specific and actionable, not generic
- Write in second person ("you", "your")
- Keep paragraphs concise (2-4 sentences)
- Focus on patterns, not judgments

TONE: Professional yet warm, empowering, evidence-based."""


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

Top Strengths:
{chr(10).join([f'- {s}' for s in top_strengths[:3]])}

Domain Details:
{domain_info}

Write 2-3 sentences explaining how these strengths support their executive functioning and how they can leverage them.""",

        "growth_edges_analysis": f"""Analyze the growth edges in this executive function profile.

Growth Edges:
{chr(10).join([f'- {e}' for e in growth_edges[:3]])}

Domain Details:
{domain_info}

Write 2-3 sentences explaining these growth areas and what targeted support would look like. Focus on actionable insights.""",

        "aims_plan": f"""Create a brief AIMS for the BEST™ intervention plan (3-4 sentences).

Growth Edges: {', '.join(growth_edges[:2])}
Strengths: {', '.join(top_strengths[:2])}

Outline specific, actionable intervention strategies that address the growth edges while leveraging strengths.""",

        "cosmic_summary": f"""Write a closing "Cosmic Summary" (3-4 sentences) for a {report_type.replace('_', ' ').title()} executive function report.

Assessment Data:
- Archetype: {archetype}
- Quadrant: {quadrant}
- Top Strengths: {', '.join(top_strengths[:2])}
- Growth Edges: {', '.join(growth_edges[:2])}
- Load Balance: {load_balance:.2f}

Provide an inspiring, forward-looking closing paragraph that ties together their archetype, strengths, and growth trajectory. Use a space/galaxy metaphor naturally. End with an empowering statement about their potential."""
    }
    
    return prompts.get(section_name, f"Generate insights for {section_name} based on the assessment data.")


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
