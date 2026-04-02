"""
PDF Service Module — Report PDF Generation (Phase 2)
Generates professional PDF reports from assessment results.

This module handles:
- PDF layout and styling
- Report content formatting
- Chart/graph generation
- PDF file creation and streaming
- Free ScoreCard PDF (matches web ScoreCard view)
- Full Report PDF (matches paid Full Galaxy Report view)
"""

import io
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


def _get_user_name(user_id: str) -> str:
    """Fetch user name from users table, fallback to email."""
    try:
        from scoring_engine.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        if supabase:
            result = supabase.table('users').select('name, email').eq('email', user_id).maybe_single().execute()
            if result.data:
                return result.data.get('name') or result.data.get('email', user_id)
    except Exception as e:
        logger.debug(f"Could not fetch user name: {e}")
    return user_id


def generate_scorecard_pdf(full_output: dict) -> Optional[bytes]:
    """
    Generate a FREE ScoreCard PDF that matches the web ScoreCard view exactly.
    
    Uses the same build_scorecard_output logic to ensure data consistency:
      1. Galaxy Snapshot (archetype name + tagline)
      2. EF Constellation (4 grouped domains with percentages)
      3. Load Balance status
      4. Top 2 Strengths + Top 2 Growth Edges
      5. Four Lens Teasers
    
    Args:
        full_output: The FULL assessment result (as stored in DB/memory)
    
    Returns:
        PDF file as bytes, or None if generation fails
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        from scoring_engine.output import build_scorecard_output
        
        # Build the same scorecard data the frontend displays
        scorecard = build_scorecard_output(full_output)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'SCTitle', parent=styles['Heading1'],
            fontSize=24, textColor=colors.HexColor('#4F46E5'),
            spaceAfter=10, alignment=TA_CENTER, fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'SCSubtitle', parent=styles['Normal'],
            fontSize=13, textColor=colors.HexColor('#6366F1'),
            spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Oblique'
        )
        heading_style = ParagraphStyle(
            'SCHeading', parent=styles['Heading2'],
            fontSize=16, textColor=colors.HexColor('#312E81'),
            spaceAfter=12, spaceBefore=16, fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'SCBody', parent=styles['BodyText'],
            fontSize=11, alignment=TA_JUSTIFY, spaceAfter=12, leading=16
        )
        
        # Extract scorecard data
        snapshot = scorecard.get('galaxy_snapshot', {})
        constellation = scorecard.get('constellation', [])
        load_balance = scorecard.get('load_balance', {})
        strengths = scorecard.get('strengths', [])
        growth_edges = scorecard.get('growth_edges', [])
        lens_teasers = scorecard.get('lens_teasers', {})
        metadata = scorecard.get('metadata', {})
        
        # ── 1. TITLE / ARCHETYPE ──
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("BEST Executive Function Galaxy Assessment™", ParagraphStyle(
            'SmallTitle', parent=styles['Normal'],
            fontSize=11, textColor=colors.HexColor('#6B7280'),
            spaceAfter=8, alignment=TA_CENTER, fontName='Helvetica'
        )))
        elements.append(Paragraph("FREE SCORECARD", ParagraphStyle(
            'TierBadge', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#10B981'),
            spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold'
        )))
        
        archetype_name = snapshot.get('archetype_name', 'Unknown')
        elements.append(Paragraph(archetype_name.upper(), title_style))
        tagline = snapshot.get('tagline', '')
        if tagline:
            elements.append(Paragraph(f'"{tagline}"', subtitle_style))
        
        # Framework Reference Line (Item 5)
        framework_ref_style = ParagraphStyle(
            'FrameworkRef', parent=styles['Normal'],
            fontSize=9, textColor=colors.HexColor('#6366F1'),
            spaceAfter=16, alignment=TA_CENTER, fontName='Helvetica-Oblique'
        )
        elements.append(Paragraph(
            'This profile reflects how your internal capacity (BHP) is interacting with your environmental demands (PEI).',
            framework_ref_style
        ))
        
        # Report info - fetch user name
        user_id = metadata.get('user_email') or metadata.get('user_id', 'N/A')
        user_name = _get_user_name(user_id)
        if len(user_name) > 40:
            user_name = user_name[:37] + '...'
        
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        try:
            date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')
        except Exception:
            date_str = timestamp[:10]
        
        # Professional header box
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#4F46E5'), spaceAfter=12))
        info_data = [
            ['Prepared for:', user_name],
            ['Report Date:', date_str],
            ['Report Type:', 'Free ScoreCard'],
        ]
        info_table = Table(info_data, colWidths=[1.8 * inch, 4.2 * inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#312E81')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB'), spaceAfter=16))
        
        # Domain color + tag mapping (Items 1 & 2)
        DOMAIN_META = {
            'Executive Skills & Behavior':      {'tag': 'Action & Follow-Through',  'color': '#3B82F6'},
            'Cognitive & Motivational Systems': {'tag': 'Focus & Drive',            'color': '#8B5CF6'},
            'Emotional & Internal State':       {'tag': 'Emotional Regulation',     'color': '#F59E0B'},
            'Environmental Demands':            {'tag': 'Life Load',                'color': '#EF4444'},
        }
        
        # ── 2. EXECUTIVE FUNCTION CONSTELLATION (4 grouped domains) ──
        elements.append(Paragraph("Your Executive Function Constellation", heading_style))
        
        constellation_data = [['Domain Group', 'Tag', 'Score', 'Percentage']]
        row_colors_map = []  # track domain colors per row
        for group in constellation:
            pct = group.get('percentage', 0)
            meta = DOMAIN_META.get(group['name'], {'tag': '', 'color': '#6B7280'})
            is_env = group['name'] == 'Environmental Demands'
            display_name = 'Life Load' if is_env else group['name']
            display_tag = 'Higher = More Pressure' if is_env else meta['tag']
            display_pct = f"{pct}% ({'High Pressure' if pct >= 80 else 'Moderate Pressure' if pct >= 60 else pct})" if is_env else f"{pct}%"
            constellation_data.append([
                display_name,
                display_tag,
                f"{group['score']:.3f}",
                display_pct
            ])
            row_colors_map.append(meta['color'])
        
        const_table = Table(constellation_data, colWidths=[2.2 * inch, 1.6 * inch, 1.1 * inch, 1.1 * inch])
        table_style_cmds = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('FONTSIZE', (1, 1), (1, -1), 9),
            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#6B7280')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]
        # Apply domain colors to each row
        for i, dc in enumerate(row_colors_map):
            row_idx = i + 1
            table_style_cmds.append(('TEXTCOLOR', (0, row_idx), (0, row_idx), colors.HexColor(dc)))
            table_style_cmds.append(('FONTNAME', (0, row_idx), (0, row_idx), 'Helvetica-Bold'))
        const_table.setStyle(TableStyle(table_style_cmds))
        elements.append(const_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # ── 3. LOAD BALANCE ──
        elements.append(Paragraph("Load Balance", heading_style))
        load_status = load_balance.get('status', 'Unknown')
        load_msg = load_balance.get('message', '')
        executive_summary = load_balance.get('executive_summary', '')
        pei_score = load_balance.get('pei_score', 0)
        bhp_score = load_balance.get('bhp_score', 0)
        
        # Dynamic load label — aligned with backend load_state thresholds
        if pei_score and bhp_score:
            diff = bhp_score - pei_score  # BHP - PEI (positive = capacity surplus)
            if diff >= 0.20:
                dynamic_label = 'Surplus Capacity'
            elif diff >= 0.05:
                dynamic_label = 'Stable Capacity'
            elif diff >= -0.04:
                dynamic_label = 'Balanced Load'
            elif diff >= -0.19:
                dynamic_label = 'Emerging Strain'
            else:
                dynamic_label = 'Critical Overload'
        elif 'Balanced' in load_status and 'Imbalanced' not in load_status:
            dynamic_label = 'Balanced Load'
        elif 'Slightly' in load_status:
            dynamic_label = 'Emerging Strain'
        elif 'High' in load_status:
            dynamic_label = 'Critical Overload'
        else:
            dynamic_label = 'Emerging Strain'
        
        # Color-code load status
        if dynamic_label in ('Surplus Capacity', 'Stable Capacity'):
            status_color = '#10B981'
        elif dynamic_label == 'Balanced Load':
            status_color = '#3B82F6'
        elif dynamic_label == 'Emerging Strain':
            status_color = '#F59E0B'
        else:
            status_color = '#EF4444'
        
        elements.append(Paragraph(
            f'<font color="{status_color}"><b>{dynamic_label}</b></font>',
            ParagraphStyle('LoadStatus', parent=body_style, fontSize=14, alignment=TA_LEFT)
        ))
        
        # Note: BHP/PEI numeric scores are hidden in Free ScoreCard (visual bars only)
        # Numeric values are only shown in paid Full Report PDF
        
        if load_msg:
            elements.append(Paragraph(load_msg, body_style))
        
        # AI-Generated Executive Summary (Item 4)
        if executive_summary:
            elements.append(Spacer(1, 0.1 * inch))
            summary_style = ParagraphStyle(
                'ExecSummary', parent=body_style, fontSize=10,
                textColor=colors.HexColor('#374151'), leading=15,
                borderColor=colors.HexColor('#E5E7EB'), borderWidth=1,
                borderPadding=8, backColor=colors.HexColor('#F9FAFB')
            )
            elements.append(Paragraph(executive_summary, summary_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # ── 4. STRENGTHS & GROWTH EDGES ──
        # Filter Environmental Demands from strengths (it's pressure, not capacity)
        filtered_strengths = [s for s in strengths if 'Environmental' not in s and 'ENVIRONMENTAL' not in s]
        elements.append(Paragraph("Summary", heading_style))
        
        summary_data = [['Top Strengths', 'Growth Edges']]
        max_len = max(len(filtered_strengths), len(growth_edges), 1)
        for i in range(max_len):
            s = filtered_strengths[i] if i < len(filtered_strengths) else ''
            g = growth_edges[i] if i < len(growth_edges) else ''
            summary_data.append([s, g])
        
        sum_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
        sum_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#10B981')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#F59E0B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
        ]))
        elements.append(sum_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # ── 5. FOUR LENS TEASERS ──
        elements.append(Paragraph("Your Profile Across 4 Lenses", heading_style))
        
        lens_icons = {
            'PERSONAL_LIFESTYLE': 'Personal / Lifestyle',
            'STUDENT_SUCCESS': 'Student Success',
            'PROFESSIONAL_LEADERSHIP': 'Professional / Leadership',
            'FAMILY_ECOSYSTEM': 'Family / Ecosystem',
        }
        
        for key, lens_data in lens_teasers.items():
            title = lens_data.get('title', lens_icons.get(key, key))
            teaser = lens_data.get('teaser', '')
            elements.append(Paragraph(
                f'<b>{title}</b>',
                ParagraphStyle('LensTitle', parent=body_style, fontSize=12,
                             textColor=colors.HexColor('#312E81'), spaceAfter=4)
            ))
            elements.append(Paragraph(teaser, body_style))
            elements.append(Spacer(1, 0.1 * inch))
        
        # ── FOOTER ──
        elements.append(Spacer(1, 0.4 * inch))
        footer_style = ParagraphStyle(
            'SCFooter', parent=styles['Normal'],
            fontSize=8, textColor=colors.grey, alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "BEST Executive Function Galaxy Assessment™ | Free ScoreCard | Confidential",
            footer_style
        ))
        # AIMS Teaser (Item 7)
        elements.append(Paragraph(
            "Your full report includes your personalized AIMS for the BEST\u2122 intervention pathway.",
            ParagraphStyle('AimsTeaser', parent=footer_style,
                         fontSize=9, textColor=colors.HexColor('#4F46E5'), fontName='Helvetica-Bold')
        ))
        elements.append(Spacer(1, 0.1 * inch))
        # Updated CTA (Item 6)
        elements.append(Paragraph(
            "You've seen the surface. Now see the system.",
            ParagraphStyle('CTALine', parent=footer_style,
                         fontSize=10, textColor=colors.HexColor('#6366F1'), fontName='Helvetica-Oblique')
        ))
        
        # Build PDF
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated ScoreCard PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Failed to generate ScoreCard PDF: {e}", exc_info=True)
        return None


def generate_pdf_report(assessment_data: dict) -> Optional[bytes]:
    """
    Generate a PDF report from assessment data.
    
    Args:
        assessment_data: Complete assessment output JSON
    
    Returns:
        PDF file as bytes, or None if generation fails
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, Image, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4F46E5'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#312E81'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=16
        )
        
        # Extract data
        metadata = assessment_data.get('metadata', {})
        archetype = assessment_data.get('archetype', {})
        construct_scores = assessment_data.get('construct_scores', {})
        load_framework = assessment_data.get('load_framework', {})
        domains = assessment_data.get('domains', [])
        summary = assessment_data.get('summary', {})
        interpretation = assessment_data.get('interpretation', {})
        
        # Title Page
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph("BEST Executive Function", title_style))
        elements.append(Paragraph("Galaxy Assessment™", title_style))
        elements.append(Spacer(1, 0.3*inch))
        
        # Archetype
        archetype_name = archetype.get('archetype_id', 'Unknown').replace('_', ' ')
        elements.append(Paragraph(f"<b>{archetype_name}</b>", heading_style))
        elements.append(Paragraph(archetype.get('description', ''), body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # Report Info - fetch user name
        report_type = metadata.get('report_type', '').replace('_', ' ').title()
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')
        
        # Fetch user name from users table
        user_id = metadata.get('user_email') or metadata.get('user_id', 'N/A')
        user_name = _get_user_name(user_id)
        if len(user_name) > 40:
            user_name = user_name[:37] + '...'
        
        # Professional header with divider
        elements.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#4F46E5'), spaceAfter=16))
        
        info_data = [
            ['Prepared for:', user_name],
            ['Report Date:', date_str],
            ['Report Type:', report_type],
            ['Assessment Type:', 'Full Galaxy Report (Paid)'],
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#312E81')),
            ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#1F2937')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(info_table)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E5E7EB'), spaceAfter=20))
        elements.append(PageBreak())
        
        # Executive Summary
        if interpretation and interpretation.get('executive_summary'):
            elements.append(Paragraph("Executive Summary", heading_style))
            elements.append(Paragraph(interpretation['executive_summary'], body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Construct Scores
        elements.append(Paragraph("Construct Scores", heading_style))
        pei_score = construct_scores.get('PEI_score', 0)
        bhp_score = construct_scores.get('BHP_score', 0)
        
        scores_data = [
            ['Construct', 'Score', 'Percentage'],
            ['PEI (Environmental Demand)', f'{pei_score:.3f}', f'{int(pei_score * 100)}%'],
            ['BHP (Internal Capacity)', f'{bhp_score:.3f}', f'{int(bhp_score * 100)}%'],
        ]
        scores_table = Table(scores_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        scores_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
        ]))
        elements.append(scores_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Load Framework
        elements.append(Paragraph("Load Framework", heading_style))
        quadrant = load_framework.get('quadrant', '').replace('_', ' ')
        load_state = load_framework.get('load_state', '').replace('_', ' ')
        load_balance = load_framework.get('load_balance', 0)
        
        framework_text = f"""
        <b>Quadrant:</b> {quadrant}<br/>
        <b>Load State:</b> {load_state}<br/>
        <b>Load Balance:</b> {load_balance:.3f} (BHP - PEI)
        """
        elements.append(Paragraph(framework_text, body_style))
        elements.append(Spacer(1, 0.2*inch))
        
        # PEI × BHP Interpretation
        if interpretation and interpretation.get('pei_bhp_interpretation'):
            elements.append(Paragraph(interpretation['pei_bhp_interpretation'], body_style))
            elements.append(Spacer(1, 0.2*inch))
        
        # Summary (Strengths & Growth Edges)
        # Filter Environmental Demands from strengths (it's pressure, not capacity)
        elements.append(Paragraph("Summary", heading_style))
        
        strengths = [s for s in summary.get('top_strengths', []) if s != 'ENVIRONMENTAL_DEMANDS']
        growth_edges = summary.get('growth_edges', [])
        
        summary_data = [['Top Strengths', 'Growth Edges']]
        max_len = max(len(strengths), len(growth_edges))
        for i in range(max_len):
            strength = strengths[i].replace('_', ' ') if i < len(strengths) else ''
            edge = growth_edges[i].replace('_', ' ') if i < len(growth_edges) else ''
            summary_data.append([strength, edge])
        
        summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10B981')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#F59E0B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(summary_table)
        elements.append(PageBreak())
        
        # Domain Profiles — Internal Capacity Domains
        elements.append(Paragraph("Domain Profiles — Internal Capacity", heading_style))
        
        capacity_domains = [d for d in domains if d['name'] != 'ENVIRONMENTAL_DEMANDS']
        env_domains = [d for d in domains if d['name'] == 'ENVIRONMENTAL_DEMANDS']
        
        domain_data = [['Domain', 'Score', 'Classification', 'Rank']]
        for domain in capacity_domains:
            domain_data.append([
                domain['name'].replace('_', ' '),
                f"{domain['score']:.3f}",
                domain['classification'],
                f"#{domain['rank']}"
            ])
        
        domain_table = Table(domain_data, colWidths=[2.5*inch, 1.2*inch, 1.5*inch, 0.8*inch])
        domain_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(domain_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Environmental Demands — Separated as External Pressure
        if env_domains:
            elements.append(Paragraph("Environmental Demands — External Pressure", heading_style))
            env_note_style = ParagraphStyle('EnvNote', parent=body_style, fontSize=10,
                                            textColor=colors.HexColor('#DC2626'), leading=14)
            elements.append(Paragraph(
                "Environmental Demands represents external pressure on your system, not internal capacity. "
                "A high score indicates high load/strain, not high performance.",
                env_note_style
            ))
            env_data = [['Domain', 'Score', 'Load Level', 'Rank']]
            for domain in env_domains:
                score = domain['score']
                load_level = 'High Load' if score >= 0.8 else 'Elevated Pressure' if score >= 0.6 else 'Moderate Load'
                env_data.append([
                    domain['name'].replace('_', ' '),
                    f"{score:.3f}",
                    load_level,
                    f"#{domain['rank']}"
                ])
            env_table = Table(env_data, colWidths=[2.5*inch, 1.2*inch, 1.5*inch, 0.8*inch])
            env_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FCA5A5')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEF2F2')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(env_table)
        elements.append(PageBreak())
        
        # Interpretation Sections
        if interpretation:
            elements.append(Paragraph("Detailed Interpretation", heading_style))
            
            sub_heading_style = ParagraphStyle('SubHeading',
                                             parent=styles['Heading3'],
                                             fontSize=13,
                                             textColor=colors.HexColor('#4B5563'),
                                             spaceAfter=8,
                                             spaceBefore=12,
                                             fontName='Helvetica-Bold')
            
            sections = [
                ('Quadrant Analysis', 'quadrant_interpretation'),
                ('Load State Analysis', 'load_interpretation'),
                ('Strengths Analysis', 'strengths_analysis'),
            ]
            
            for section_title, section_key in sections:
                if interpretation.get(section_key):
                    elements.append(Paragraph(section_title, sub_heading_style))
                    elements.append(Paragraph(interpretation[section_key], body_style))
                    elements.append(Spacer(1, 0.15*inch))
            
            # Load & Pressure Analysis — separated from Strengths
            if pei_score >= 0.6:
                elements.append(Paragraph('Load &amp; Pressure Analysis', sub_heading_style))
                elements.append(Paragraph(
                    'Your system is currently operating under high environmental load, meaning that '
                    'external demands are placing sustained pressure on your internal capacity. This '
                    'level of demand is not a reflection of strength, but rather the intensity of what '
                    'your system is being required to manage. When environmental load is elevated, even '
                    'strong internal skills can become strained over time. Adjusting, reducing, or '
                    'restructuring these external demands will be an important part of restoring balance '
                    'and supporting long-term performance.',
                    body_style
                ))
                elements.append(Spacer(1, 0.15*inch))
            
            # Growth Edges Analysis
            if interpretation.get('growth_edges_analysis'):
                elements.append(Paragraph('Growth Edges Analysis', sub_heading_style))
                elements.append(Paragraph(interpretation['growth_edges_analysis'], body_style))
                elements.append(Spacer(1, 0.15*inch))
        
        # AIMS Plan — enforced order: Awareness → Intervention → Mastery → Sustain
        if interpretation and interpretation.get('aims_plan'):
            elements.append(PageBreak())
            elements.append(Paragraph("AIMS for the BEST™ Plan", heading_style))
            
            aims_plan = interpretation['aims_plan']
            aims_order = ['awareness', 'intervention', 'mastery', 'sustain']
            for phase in aims_order:
                content = aims_plan.get(phase, '')
                if content:
                    phase_title = phase.replace('_', ' ').title()
                    elements.append(Paragraph(f"<b>{phase_title}</b>", body_style))
                    elements.append(Paragraph(content, body_style))
                    elements.append(Spacer(1, 0.1*inch))
        
        # Cosmic Summary
        if interpretation and interpretation.get('cosmic_summary'):
            elements.append(Spacer(1, 0.3*inch))
            cosmic_style = ParagraphStyle(
                'CosmicSummary',
                parent=styles['BodyText'],
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=12,
                leading=18,
                textColor=colors.HexColor('#4F46E5'),
                fontName='Helvetica-Oblique'
            )
            elements.append(Paragraph("Cosmic Summary", heading_style))
            elements.append(Paragraph(interpretation['cosmic_summary'], cosmic_style))
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "BEST Executive Function Galaxy Assessment™ | Confidential Report",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated PDF report: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}")
        return None
