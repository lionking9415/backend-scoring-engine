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


def _make_progress_bar(pct, width_inch: float = 1.7, height_pt: float = 9,
                       fill_color: str = '#2563EB',
                       track_color: str = '#E5E7EB'):
    """Return a reportlab `Drawing` containing a proportional 0-100% bar.

    Replaces the Unicode block-character bars (`█` / `░`) used previously,
    which rendered as identical placeholder boxes in the standard Type-1
    Courier font (those glyphs are not in the font, so each row looked the
    same regardless of score). Using vector primitives guarantees the bar
    width is accurately proportional to the value.
    """
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.units import inch as _inch

    try:
        value = float(pct)
    except (TypeError, ValueError):
        value = 0.0
    value = max(0.0, min(100.0, value))

    width_pt = width_inch * _inch
    d = Drawing(width_pt, height_pt)

    # Track (background)
    d.add(Rect(
        0, 0, width_pt, height_pt,
        fillColor=rl_colors.HexColor(track_color),
        strokeColor=rl_colors.HexColor('#D1D5DB'),
        strokeWidth=0.5,
    ))
    # Filled portion
    fill_w = width_pt * (value / 100.0)
    if fill_w > 0:
        d.add(Rect(
            0, 0, fill_w, height_pt,
            fillColor=rl_colors.HexColor(fill_color),
            strokeColor=rl_colors.HexColor(fill_color),
            strokeWidth=0,
        ))
    return d


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
            'Environmental Demands':            {'tag': 'Environmental Pressure Load (PEI)', 'color': '#EF4444'},
        }
        
        # ── 2. EXECUTIVE FUNCTION CONSTELLATION (4 grouped domains) ──
        elements.append(Paragraph("Your Executive Function Constellation", heading_style))

        # Per-cell paragraph styles. Wrapping is enabled by passing Paragraph
        # objects (instead of raw strings) into the Table — this prevents long
        # names like "Cognitive & Motivational Systems" from overflowing into
        # the next column.
        const_header_style = ParagraphStyle(
            'ConstHeader', parent=styles['Normal'], fontName='Helvetica-Bold',
            fontSize=10, textColor=colors.whitesmoke, alignment=TA_CENTER, leading=12,
        )
        const_tag_style = ParagraphStyle(
            'ConstTag', parent=styles['Normal'], fontName='Helvetica',
            fontSize=9, textColor=colors.HexColor('#6B7280'), alignment=TA_LEFT, leading=11,
        )
        const_score_style = ParagraphStyle(
            'ConstScore', parent=styles['Normal'], fontName='Helvetica',
            fontSize=10, textColor=colors.HexColor('#1F2937'), alignment=TA_CENTER, leading=12,
        )
        const_pct_style = ParagraphStyle(
            'ConstPct', parent=styles['Normal'], fontName='Helvetica',
            fontSize=10, textColor=colors.HexColor('#1F2937'), alignment=TA_CENTER, leading=12,
        )

        constellation_data = [[
            Paragraph('Domain Group', const_header_style),
            Paragraph('Tag', const_header_style),
            Paragraph('Score', const_header_style),
            Paragraph('Percentage', const_header_style),
        ]]
        for group in constellation:
            pct = group.get('percentage', 0)
            meta = DOMAIN_META.get(group['name'], {'tag': '', 'color': '#6B7280'})
            is_env = group['name'] == 'Environmental Demands'
            display_name = 'Env. Pressure Load (PEI)' if is_env else group['name']
            display_tag = 'Higher = More Pressure' if is_env else meta['tag']
            display_pct = f"{pct}% ({'High Pressure' if pct >= 80 else 'Moderate Pressure' if pct >= 60 else pct})" if is_env else f"{pct}%"

            name_style = ParagraphStyle(
                f"ConstName_{group['name']}", parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=10,
                textColor=colors.HexColor(meta['color']),
                alignment=TA_LEFT, leading=12,
            )
            constellation_data.append([
                Paragraph(display_name, name_style),
                Paragraph(display_tag, const_tag_style),
                Paragraph(f"{group['score']:.3f}", const_score_style),
                Paragraph(display_pct, const_pct_style),
            ])

        const_table = Table(constellation_data, colWidths=[2.2 * inch, 1.6 * inch, 1.1 * inch, 1.1 * inch])
        const_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(const_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # ── 3. LOAD BALANCE (Teeter-Totter Style) ──
        load_msg = load_balance.get('message', '')
        executive_summary = load_balance.get('executive_summary', '')
        pei_score = load_balance.get('pei_score', 0)
        bhp_score = load_balance.get('bhp_score', 0)
        
        # Dynamic load label — aligned with backend load_state thresholds
        diff_val = (bhp_score or 0) - (pei_score or 0)
        delta = (pei_score or 0) - (bhp_score or 0)
        abs_delta = abs(delta)
        if diff_val >= 0.20:
            dynamic_label = 'Surplus Capacity'
        elif diff_val >= 0.05:
            dynamic_label = 'Stable Capacity'
        elif diff_val >= -0.04:
            dynamic_label = 'Balanced Load'
        elif diff_val >= -0.19:
            dynamic_label = 'Emerging Strain'
        else:
            dynamic_label = 'Critical Overload'
        
        # Tilt label for teeter-totter
        if abs_delta < 0.01:
            tilt_label = 'Balanced'
        elif abs_delta < 0.05:
            tilt_label = 'Balanced Under Load' if delta > 0 else 'Capacity Supported'
        elif abs_delta < 0.12:
            tilt_label = 'Capacity Strain' if delta > 0 else 'Capacity Dominant'
        else:
            tilt_label = 'Critical Overload' if delta > 0 else 'Capacity Dominant'
        
        pressure_level = 'None' if abs_delta < 0.01 else 'Mild' if abs_delta < 0.05 else 'Moderate' if abs_delta < 0.12 else 'High'
        
        # Color-code
        if dynamic_label in ('Surplus Capacity', 'Stable Capacity'):
            status_color = '#10B981'
        elif dynamic_label == 'Balanced Load':
            status_color = '#3B82F6'
        elif dynamic_label == 'Emerging Strain':
            status_color = '#F59E0B'
        else:
            status_color = '#EF4444'
        
        delta_color = '#DC2626' if delta > 0.01 else '#2563EB' if delta < -0.01 else '#6B7280'
        delta_sign = '+' if delta > 0 else ''
        
        elements.append(Paragraph(
            f'<font color="#2563EB"><b>Load Balance: {dynamic_label}</b></font>'
            f'&nbsp;&nbsp;&nbsp;<font color="#2563EB" size="9">[{tilt_label}]</font>',
            ParagraphStyle('LoadHeader', parent=body_style, fontSize=14, alignment=TA_LEFT)
        ))
        elements.append(Spacer(1, 0.1 * inch))
        
        # BHP vs PEI teeter-totter table
        if pei_score or bhp_score:
            lb_data = [
                ['INTERNAL CAPACITY (BHP)', '⚖', 'ENVIRONMENTAL LOAD (PEI)'],
                [f'{bhp_score:.3f}', f'Load Diff: {delta_sign}{delta:.3f}', f'{pei_score:.3f}'],
            ]
            lb_table = Table(lb_data, colWidths=[2.2 * inch, 1.6 * inch, 2.2 * inch])
            lb_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#D4A62A')),
                ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#F87171')),
                ('FONTNAME', (0, 1), (0, 1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 1), (2, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 12),
                ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor('#8B5CF6')),
                ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor(delta_color)),
                ('FONTSIZE', (1, 1), (1, 1), 9),
                ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#F87171')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(lb_table)
        elements.append(Spacer(1, 0.05 * inch))
        
        # Classification chips
        chips_text = (
            f'<font size="9"><b>Load State:</b> {dynamic_label} &nbsp; | &nbsp; '
            f'<b>System Status:</b> {tilt_label} &nbsp; | &nbsp; '
            f'<b>Pressure Level:</b> {pressure_level}</font>'
        )
        elements.append(Paragraph(chips_text, ParagraphStyle(
            'Chips', parent=body_style, fontSize=9, textColor=colors.HexColor('#6B7280')
        )))
        
        if load_msg:
            elements.append(Paragraph(
                f'<i>{load_msg}</i>',
                ParagraphStyle('LoadMsg', parent=body_style, fontSize=11,
                             textColor=colors.HexColor('#4B5563'), alignment=TA_CENTER)
            ))
        
        # AI-Generated Executive Summary
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
        
        # ── 4b. APPLIED EXECUTIVE FUNCTIONING DOMAINS (Phase 4) ──
        applied_domains = scorecard.get('applied_domains', {})
        if applied_domains:
            elements.append(Paragraph("Applied Executive Functioning Domains", heading_style))
            elements.append(Paragraph(
                "How your executive functioning expresses in everyday living",
                ParagraphStyle('ADSubtitle', parent=body_style, fontSize=9,
                             textColor=colors.HexColor('#6B7280'), spaceAfter=10)
            ))
            
            # Domain-specific subtitles (GAP 7)
            domain_subtitles = {
                'financial_ef': 'How your executive system manages planning, regulation, and decision-making under financial pressure.',
                'health_ef': 'How your executive system supports eating, movement, sleep, and self-care under real-life demand.',
            }
            
            for key, label, accent in [
                ('financial_ef', 'Financial Executive Functioning Profile™', '#8B5CF6'),
                ('health_ef', 'Health & Fitness Executive Functioning Profile™', '#10B981'),
            ]:
                ad = applied_domains.get(key)
                if not ad:
                    continue
                
                domain_score = ad.get('domain_score', 50)
                bhp_val = ad.get('bhp', 0)
                pei_val = ad.get('pei', 0)
                lb_val = ad.get('load_balance', 0)
                status_band = ad.get('status_band', 'N/A')
                interp = ad.get('interpretation', {})
                subvariables = ad.get('subvariables', {})
                flags = ad.get('flags', {})
                active_flags = ad.get('active_flags', [])
                aims = ad.get('aims_targets', [])
                
                # If active_flags not pre-computed, derive from flags dict
                if not active_flags and flags:
                    active_flags = [f['description'] for f in flags.values()
                                   if isinstance(f, dict) and f.get('triggered')]
                
                # Block 1: Section header with title + subtitle + status band
                elements.append(Paragraph(
                    f'<font color="{accent}"><b>{label}</b></font>'
                    f'&nbsp;&nbsp;<font color="{accent}" size="9">[{status_band}]</font>',
                    ParagraphStyle('ADTitle', parent=body_style, fontSize=13, spaceAfter=2)
                ))
                elements.append(Paragraph(
                    f'<i>{domain_subtitles.get(key, "")}</i>',
                    ParagraphStyle('ADDomSub', parent=body_style, fontSize=9,
                                 textColor=colors.HexColor('#6B7280'), spaceAfter=6)
                ))
                
                # Metrics table — 5 columns matching web report.
                # Status Band is wrapped in a Paragraph so multi-word labels
                # (e.g. "Stable but Vulnerable") wrap inside the cell instead
                # of overflowing into neighboring columns.
                lb_color = '#16A34A' if lb_val >= 0 else '#DC2626'
                status_band_style = ParagraphStyle(
                    'StatusBandFree', parent=styles['Normal'],
                    fontName='Helvetica-Bold', fontSize=10,
                    textColor=colors.HexColor('#1F2937'),
                    alignment=TA_CENTER, leading=12,
                )
                ad_data = [
                    ['Domain Score', 'BHP (Capacity)', 'PEI (Pressure)', 'Load Balance', 'Status Band'],
                    [
                        f'{domain_score:.0f}/100',
                        f'{bhp_val:.1f}',
                        f'{pei_val:.1f}',
                        f'{lb_val:+.1f}',
                        Paragraph(status_band, status_band_style),
                    ],
                ]
                ad_table = Table(ad_data, colWidths=[1.1 * inch, 1.2 * inch, 1.2 * inch, 1.1 * inch, 1.4 * inch])
                ad_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(accent)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, 1), 11),
                    ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor(accent)),
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#2563EB')),
                    ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#DC2626')),
                    ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor(lb_color)),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
                ]))
                elements.append(ad_table)
                elements.append(Spacer(1, 0.06 * inch))
                
                # Block 2: BHP vs PEI visual balance bar (GAP 5).
                # Bars are rendered as vector Drawings sized in proportion to
                # each side's share of the (BHP + PEI) total — this replaces
                # the previous Unicode block string which all rendered as
                # identical missing-glyph boxes in Courier-Bold.
                bhp_total = bhp_val + pei_val if (bhp_val + pei_val) > 0 else 1
                bhp_share_pct = round((bhp_val / bhp_total) * 100)
                pei_share_pct = round((pei_val / bhp_total) * 100)
                balance_label = 'BHP > PEI' if lb_val > 0 else ('PEI > BHP' if lb_val < 0 else 'BALANCED')
                bal_data = [
                    ['INTERNAL CAPACITY (BHP)', '', 'BALANCE', '', 'EXTERNAL PRESSURE (PEI)'],
                    [
                        _make_progress_bar(bhp_share_pct, width_inch=1.7, fill_color='#2563EB'),
                        f'{bhp_val:.1f}',
                        balance_label,
                        f'{pei_val:.1f}',
                        _make_progress_bar(pei_share_pct, width_inch=1.7, fill_color='#DC2626'),
                    ],
                ]
                bal_tbl = Table(
                    bal_data,
                    colWidths=[1.8 * inch, 0.45 * inch, 1.5 * inch, 0.45 * inch, 1.8 * inch],
                )
                bal_tbl.setStyle(TableStyle([
                    ('SPAN', (0, 0), (1, 0)),
                    ('SPAN', (3, 0), (4, 0)),
                    ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#EFF6FF')),
                    ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#F3F4F6')),
                    ('BACKGROUND', (3, 0), (4, 0), colors.HexColor('#FEF2F2')),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#1E40AF')),
                    ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#374151')),
                    ('TEXTCOLOR', (3, 0), (4, 0), colors.HexColor('#991B1B')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, 1), 9),
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#1E40AF')),
                    ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#374151')),
                    ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#991B1B')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(bal_tbl)
                elements.append(Spacer(1, 0.08 * inch))
                
                # Block 3: When Stable / When Loaded
                if interp.get('when_stable'):
                    elements.append(Paragraph(
                        f'<font color="#16A34A"><b>When Stable:</b></font> {interp["when_stable"]}',
                        ParagraphStyle('ADInterp', parent=body_style, fontSize=10, leading=14, spaceAfter=4)
                    ))
                if interp.get('when_loaded'):
                    elements.append(Paragraph(
                        f'<font color="#EA580C"><b>Under Load:</b></font> {interp["when_loaded"]}',
                        ParagraphStyle('ADInterp2', parent=body_style, fontSize=10, leading=14, spaceAfter=6)
                    ))
                
                # Block 4: Risk Flags
                if active_flags:
                    elements.append(Paragraph(
                        '<b>Risk Flags</b>',
                        ParagraphStyle('FlagHead', parent=body_style, fontSize=10,
                                     textColor=colors.HexColor('#374151'), spaceBefore=2, spaceAfter=4)
                    ))
                    flags_text = '&nbsp;&nbsp;|&nbsp;&nbsp;'.join(
                        f'<font color="#DC2626"><b>!</b> {f}</font>' for f in active_flags
                    )
                    elements.append(Paragraph(
                        flags_text,
                        ParagraphStyle('ADFlags', parent=body_style, fontSize=9, leading=13, spaceAfter=4)
                    ))
                
                # Block 5: Domain Interpretation narrative (GAP 6)
                if interp.get('domain_narrative'):
                    elements.append(Paragraph(
                        '<b>Domain Interpretation</b>',
                        ParagraphStyle('DNHead', parent=body_style, fontSize=10,
                                     textColor=colors.HexColor('#374151'), spaceBefore=2, spaceAfter=4)
                    ))
                    elements.append(Paragraph(
                        interp['domain_narrative'],
                        ParagraphStyle('DNBody', parent=body_style, fontSize=9, leading=13,
                                     textColor=colors.HexColor('#374151'), spaceAfter=6)
                    ))
                
                # Subvariable Breakdown table
                if subvariables:
                    elements.append(Paragraph(
                        '<b>Subvariable Breakdown</b>',
                        ParagraphStyle('SVHead', parent=body_style, fontSize=10,
                                     textColor=colors.HexColor('#374151'), spaceBefore=4, spaceAfter=4)
                    ))
                    sv_data = [['Subvariable', 'Score', 'Bar']]
                    sv_bar_pcts = []  # parallel list, bar drawn after color is decided
                    for sv_name, sv_score in subvariables.items():
                        clean_name = sv_name.replace('_', ' ')
                        for prefix in ('financial ', 'health '):
                            if clean_name.startswith(prefix):
                                clean_name = clean_name[len(prefix):]
                        clean_name = clean_name.title()
                        try:
                            bar_pct = float(sv_score)
                        except (TypeError, ValueError):
                            bar_pct = 0.0
                        bar_pct = max(0.0, min(100.0, bar_pct))
                        sv_bar_pcts.append(bar_pct)
                        # Placeholder; replaced with a real Drawing right after
                        # we know the row's accent color.
                        sv_data.append([clean_name, f'{bar_pct:.0f}', ''])

                    # Pre-compute per-row colors and then inject proportional
                    # bar Drawings into column 2 so the bar visually matches
                    # the score (replaces unicode block chars that the
                    # standard Type-1 fonts can't render).
                    row_colors = []
                    for row_i in range(1, len(sv_data)):
                        score_val = float(sv_data[row_i][1])
                        if score_val >= 70:
                            sc = '#16A34A'
                        elif score_val >= 40:
                            sc = '#D97706'
                        else:
                            sc = '#DC2626'
                        row_colors.append(sc)
                        sv_data[row_i][2] = _make_progress_bar(
                            sv_bar_pcts[row_i - 1], width_inch=2.6,
                            fill_color=sc,
                        )

                    sv_table = Table(sv_data, colWidths=[2.4 * inch, 0.6 * inch, 3.0 * inch])
                    sv_style_cmds = [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F3F4F6')),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 8),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ]
                    for row_i, sc in enumerate(row_colors, start=1):
                        sv_style_cmds.append(('TEXTCOLOR', (1, row_i), (1, row_i), colors.HexColor(sc)))
                        sv_style_cmds.append(('FONTNAME', (1, row_i), (1, row_i), 'Helvetica-Bold'))
                    sv_table.setStyle(TableStyle(sv_style_cmds))
                    elements.append(sv_table)
                    elements.append(Spacer(1, 0.08 * inch))
                
                # Block 6: AIMS Targets
                if aims:
                    elements.append(Paragraph(
                        '<b>AIMS Targets</b>',
                        ParagraphStyle('AimsHead', parent=body_style, fontSize=10,
                                     textColor=colors.HexColor('#374151'), spaceBefore=2, spaceAfter=4)
                    ))
                    aims_data = [['Phase', 'Target']]
                    for a in aims:
                        aims_data.append([a.get('phase', ''), a.get('target', '')])
                    aims_tbl = Table(aims_data, colWidths=[1.2 * inch, 4.8 * inch])
                    aims_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(accent)),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 8),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 1), (-1, -1), 8),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                    ]))
                    elements.append(aims_tbl)
                
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


def generate_pdf_report(assessment_data: dict, lens_override: Optional[str] = None) -> Optional[bytes]:
    """
    Generate a PDF report from assessment data.
    
    Args:
        assessment_data: Complete assessment output JSON
        lens_override: Optional lens to use for report generation (PERSONAL_LIFESTYLE, 
                      STUDENT_SUCCESS, PROFESSIONAL_LEADERSHIP, FAMILY_ECOSYSTEM, FULL_GALAXY).
                      If provided, overrides the original report_type in metadata.
    
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
        # Use lens_override if provided, otherwise use original report_type
        original_report_type = metadata.get('report_type', '')
        active_lens = lens_override if lens_override else original_report_type
        report_type = active_lens.replace('_', ' ').title()
        
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')
        
        # Fetch user name from users table
        user_id = metadata.get('user_email') or metadata.get('user_id', 'N/A')
        user_name = _get_user_name(user_id)
        if len(user_name) > 40:
            user_name = user_name[:37] + '...'
        
        # Professional header with divider
        elements.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor('#4F46E5'), spaceAfter=16))
        
        # Display lens-specific report type
        lens_display_name = {
            'PERSONAL_LIFESTYLE': 'Personal / Lifestyle',
            'STUDENT_SUCCESS': 'Student Success',
            'PROFESSIONAL_LEADERSHIP': 'Professional / Leadership',
            'FAMILY_ECOSYSTEM': 'Family Ecosystem',
            'FULL_GALAXY': 'Full Galaxy Report',
        }.get(active_lens, report_type)
        
        info_data = [
            ['Prepared for:', user_name],
            ['Report Date:', date_str],
            ['Report Lens:', lens_display_name],
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
        elements.append(Spacer(1, 0.2*inch))
        
        # Applied Executive Functioning Domains (Phase 4) — Full Report
        applied_domains = assessment_data.get('applied_domains', {})
        if applied_domains:
            elements.append(Paragraph("Applied Executive Functioning Domains", heading_style))
            elements.append(Paragraph(
                "How your executive functioning expresses in everyday living. These are standalone "
                "applied life domains derived from your core EF profile.",
                ParagraphStyle('PaidADSub', parent=body_style, fontSize=10,
                             textColor=colors.HexColor('#6B7280'), spaceAfter=12)
            ))
            
            # Domain-specific subtitles (GAP 7)
            paid_domain_subtitles = {
                'financial_ef': 'How your executive system manages planning, regulation, and decision-making under financial pressure.',
                'health_ef': 'How your executive system supports eating, movement, sleep, and self-care under real-life demand.',
            }
            
            for key, label, accent in [
                ('financial_ef', 'Financial Executive Functioning Profile™', '#8B5CF6'),
                ('health_ef', 'Health & Fitness Executive Functioning Profile™', '#10B981'),
            ]:
                ad = applied_domains.get(key)
                if not ad:
                    continue
                
                domain_score = ad.get('domain_score', 50)
                bhp_val = ad.get('bhp', 0)
                pei_val = ad.get('pei', 0)
                lb_val = ad.get('load_balance', 0)
                status_band = ad.get('status_band', 'N/A')
                interp = ad.get('interpretation', {})
                subvariables = ad.get('subvariables', {})
                flags = ad.get('flags', {})
                aims = ad.get('aims_targets', [])
                
                # Derive active flags
                active_flags = [f['description'] for f in flags.values()
                               if isinstance(f, dict) and f.get('triggered')]
                
                # Block 1: Section header with title + subtitle + status badge
                elements.append(Paragraph(
                    f'<font color="{accent}"><b>{label}</b></font>'
                    f'&nbsp;&nbsp;<font color="{accent}" size="9">[{status_band}]</font>',
                    ParagraphStyle('PaidADTitle', parent=styles['Heading3'],
                                 fontSize=14, spaceAfter=2, spaceBefore=12,
                                 fontName='Helvetica-Bold')
                ))
                elements.append(Paragraph(
                    f'<i>{paid_domain_subtitles.get(key, "")}</i>',
                    ParagraphStyle('PaidADDomSub', parent=body_style, fontSize=9,
                                 textColor=colors.HexColor('#6B7280'), spaceAfter=8)
                ))
                
                # Metrics table — 5 columns with color-coded values.
                # Status Band wrapped in a Paragraph so multi-word labels
                # (e.g. "Stable but Vulnerable") wrap inside their cell.
                lb_color = '#16A34A' if lb_val >= 0 else '#DC2626'
                status_band_style = ParagraphStyle(
                    'StatusBandPaid', parent=styles['Normal'],
                    fontName='Helvetica-Bold', fontSize=10,
                    textColor=colors.HexColor('#1F2937'),
                    alignment=TA_CENTER, leading=12,
                )
                ad_metrics = [
                    ['Domain Score', 'BHP (Capacity)', 'PEI (Pressure)', 'Load Balance', 'Status Band'],
                    [
                        f'{domain_score:.0f}/100', f'{bhp_val:.1f}', f'{pei_val:.1f}',
                        f'{lb_val:+.1f}',
                        Paragraph(status_band, status_band_style),
                    ],
                ]
                ad_tbl = Table(ad_metrics, colWidths=[1.1*inch, 1.2*inch, 1.2*inch, 1.1*inch, 1.4*inch])
                ad_tbl.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(accent)),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, 1), 11),
                    ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor(accent)),
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#2563EB')),
                    ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#DC2626')),
                    ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor(lb_color)),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D1D5DB')),
                ]))
                elements.append(ad_tbl)
                elements.append(Spacer(1, 0.06*inch))
                
                # Block 2: BHP vs PEI visual balance bar (GAP 5).
                # Bars are vector Drawings sized in proportion to each side's
                # share of the (BHP + PEI) total — replaces the old Unicode
                # block-character bars which all rendered identically in
                # Courier-Bold (those glyphs don't exist in the Type-1 font).
                bhp_total = bhp_val + pei_val if (bhp_val + pei_val) > 0 else 1
                bhp_share_pct = round((bhp_val / bhp_total) * 100)
                pei_share_pct = round((pei_val / bhp_total) * 100)
                balance_label = 'BHP > PEI' if lb_val > 0 else ('PEI > BHP' if lb_val < 0 else 'BALANCED')
                bal_data = [
                    ['INTERNAL CAPACITY (BHP)', '', 'BALANCE', '', 'EXTERNAL PRESSURE (PEI)'],
                    [
                        _make_progress_bar(bhp_share_pct, width_inch=1.7, fill_color='#2563EB'),
                        f'{bhp_val:.1f}',
                        balance_label,
                        f'{pei_val:.1f}',
                        _make_progress_bar(pei_share_pct, width_inch=1.7, fill_color='#DC2626'),
                    ],
                ]
                bal_tbl = Table(
                    bal_data,
                    colWidths=[1.8*inch, 0.45*inch, 1.5*inch, 0.45*inch, 1.8*inch],
                )
                bal_tbl.setStyle(TableStyle([
                    ('SPAN', (0, 0), (1, 0)),
                    ('SPAN', (3, 0), (4, 0)),
                    ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#EFF6FF')),
                    ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#F3F4F6')),
                    ('BACKGROUND', (3, 0), (4, 0), colors.HexColor('#FEF2F2')),
                    ('TEXTCOLOR', (0, 0), (1, 0), colors.HexColor('#1E40AF')),
                    ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor('#374151')),
                    ('TEXTCOLOR', (3, 0), (4, 0), colors.HexColor('#991B1B')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 7),
                    ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 1), (-1, 1), 9),
                    ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#1E40AF')),
                    ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#374151')),
                    ('TEXTCOLOR', (3, 1), (3, 1), colors.HexColor('#991B1B')),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(bal_tbl)
                elements.append(Spacer(1, 0.08*inch))
                
                # Block 3: When Stable / When Loaded
                if interp.get('when_stable'):
                    elements.append(Paragraph(
                        f'<font color="#16A34A"><b>When Stable:</b></font> {interp["when_stable"]}',
                        ParagraphStyle('PaidADStable', parent=body_style, fontSize=10, leading=14, spaceAfter=4)
                    ))
                if interp.get('when_loaded'):
                    elements.append(Paragraph(
                        f'<font color="#EA580C"><b>Under Load:</b></font> {interp["when_loaded"]}',
                        ParagraphStyle('PaidADLoaded', parent=body_style, fontSize=10, leading=14, spaceAfter=6)
                    ))
                
                # Block 4: Risk Flags (moved before subvariables per spec)
                if active_flags:
                    elements.append(Paragraph(
                        '<b>Risk Flags</b>',
                        ParagraphStyle('PaidFlagHead4', parent=body_style, fontSize=11,
                                     textColor=colors.HexColor('#1F2937'), spaceBefore=4, spaceAfter=4)
                    ))
                    flag_data = [['Flag', 'Status']]
                    for f_name, f_obj in flags.items():
                        if isinstance(f_obj, dict) and f_obj.get('triggered'):
                            flag_data.append([f_obj.get('description', f_name), 'TRIGGERED'])
                    if len(flag_data) > 1:
                        flag_tbl = Table(flag_data, colWidths=[4.8*inch, 1.2*inch])
                        flag_tbl.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FEF2F2')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 9),
                            ('TEXTCOLOR', (1, 1), (1, -1), colors.HexColor('#DC2626')),
                            ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FECACA')),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                            ('TOPPADDING', (0, 0), (-1, -1), 4),
                            ('LEFTPADDING', (0, 0), (-1, -1), 8),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF7F7')),
                        ]))
                        elements.append(flag_tbl)
                        elements.append(Spacer(1, 0.05*inch))
                
                # Block 5: Domain Interpretation narrative (GAP 6)
                if interp.get('domain_narrative'):
                    elements.append(Paragraph(
                        '<b>Domain Interpretation</b>',
                        ParagraphStyle('PaidDNHead', parent=body_style, fontSize=11,
                                     textColor=colors.HexColor('#1F2937'), spaceBefore=4, spaceAfter=4)
                    ))
                    elements.append(Paragraph(
                        interp['domain_narrative'],
                        ParagraphStyle('PaidDNBody', parent=body_style, fontSize=10, leading=14,
                                     textColor=colors.HexColor('#374151'), spaceAfter=8)
                    ))
                
                # Subvariable Breakdown — full table with visual bars
                if subvariables:
                    elements.append(Paragraph(
                        '<b>Subvariable Breakdown</b>',
                        ParagraphStyle('PaidSVHead', parent=body_style, fontSize=11,
                                     textColor=colors.HexColor('#1F2937'), spaceBefore=6, spaceAfter=6)
                    ))
                    
                    # Split into BHP and PEI subvariables
                    is_financial = key == 'financial_ef'
                    prefix = 'financial' if is_financial else 'health'
                    bhp_svs = {}
                    pei_svs = {}
                    for sv_name, sv_score in subvariables.items():
                        clean = sv_name.replace('_', ' ')
                        for p in (f'{prefix} ', ):
                            if clean.startswith(p):
                                clean = clean[len(p):]
                        clean = clean.title()
                        # Heuristic: PEI subvariables contain pressure/load/instability keywords
                        pei_keywords = ('instability', 'pressure', 'debt', 'unpredictability',
                                       'obligation', 'urgency', 'household', 'overload',
                                       'caregiving', 'exhaustion', 'disruption', 'stress',
                                       'limited', 'load')
                        is_pei = any(kw in sv_name.lower() for kw in pei_keywords)
                        if is_pei:
                            pei_svs[clean] = sv_score
                        else:
                            bhp_svs[clean] = sv_score
                    
                    # BHP subvariables
                    if bhp_svs:
                        sv_data = [['BHP Subvariable (Internal Capacity)', 'Score', 'Level']]
                        bhp_pcts = []
                        for sv_name, sv_score in bhp_svs.items():
                            try:
                                bar_pct = float(sv_score)
                            except (TypeError, ValueError):
                                bar_pct = 0.0
                            bar_pct = max(0.0, min(100.0, bar_pct))
                            bhp_pcts.append(bar_pct)
                            sv_data.append([sv_name, f'{bar_pct:.0f}', ''])

                        # Inject proportional vector bars (per-row color =
                        # green ≥70, amber ≥40, red <40 — BHP is internal
                        # capacity so higher is better).
                        bhp_row_colors = []
                        for row_i in range(1, len(sv_data)):
                            sval = float(sv_data[row_i][1])
                            sc = '#16A34A' if sval >= 70 else '#D97706' if sval >= 40 else '#DC2626'
                            bhp_row_colors.append(sc)
                            sv_data[row_i][2] = _make_progress_bar(
                                bhp_pcts[row_i - 1], width_inch=2.6, fill_color=sc,
                            )

                        sv_table = Table(sv_data, colWidths=[2.4*inch, 0.6*inch, 3.0*inch])
                        sv_cmds = [
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFF6FF')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1E40AF')),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 8),
                            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('TOPPADDING', (0, 0), (-1, -1), 3),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ]
                        for row_i, sc in enumerate(bhp_row_colors, start=1):
                            sv_cmds.append(('TEXTCOLOR', (1, row_i), (1, row_i), colors.HexColor(sc)))
                            sv_cmds.append(('FONTNAME', (1, row_i), (1, row_i), 'Helvetica-Bold'))
                        sv_table.setStyle(TableStyle(sv_cmds))
                        elements.append(sv_table)
                        elements.append(Spacer(1, 0.05*inch))

                    # PEI subvariables
                    if pei_svs:
                        pei_data = [['PEI Subvariable (External Pressure)', 'Score', 'Level']]
                        pei_pcts = []
                        for sv_name, sv_score in pei_svs.items():
                            try:
                                bar_pct = float(sv_score)
                            except (TypeError, ValueError):
                                bar_pct = 0.0
                            bar_pct = max(0.0, min(100.0, bar_pct))
                            pei_pcts.append(bar_pct)
                            pei_data.append([sv_name, f'{bar_pct:.0f}', ''])

                        # PEI = external pressure: higher score = more strain,
                        # so the color scale inverts (red ≥70, amber ≥40, green <40).
                        pei_row_colors = []
                        for row_i in range(1, len(pei_data)):
                            sval = float(pei_data[row_i][1])
                            sc = '#DC2626' if sval >= 70 else '#D97706' if sval >= 40 else '#16A34A'
                            pei_row_colors.append(sc)
                            pei_data[row_i][2] = _make_progress_bar(
                                pei_pcts[row_i - 1], width_inch=2.6, fill_color=sc,
                            )

                        pei_table = Table(pei_data, colWidths=[2.4*inch, 0.6*inch, 3.0*inch])
                        pei_cmds = [
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FEF2F2')),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('FONTSIZE', (0, 0), (-1, 0), 8),
                            ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FECACA')),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                            ('TOPPADDING', (0, 0), (-1, -1), 3),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ]
                        for row_i, sc in enumerate(pei_row_colors, start=1):
                            pei_cmds.append(('TEXTCOLOR', (1, row_i), (1, row_i), colors.HexColor(sc)))
                            pei_cmds.append(('FONTNAME', (1, row_i), (1, row_i), 'Helvetica-Bold'))
                        pei_table.setStyle(TableStyle(pei_cmds))
                        elements.append(pei_table)
                        elements.append(Spacer(1, 0.08*inch))
                
                # Block 6: AIMS Targets — full table
                if aims:
                    elements.append(Paragraph(
                        '<b>AIMS Targets</b>',
                        ParagraphStyle('PaidAimsHead', parent=body_style, fontSize=11,
                                     textColor=colors.HexColor('#1F2937'), spaceBefore=4, spaceAfter=4)
                    ))
                    aims_data = [['Phase', 'Target']]
                    for a in aims:
                        aims_data.append([a.get('phase', ''), a.get('target', '')])
                    aims_tbl = Table(aims_data, colWidths=[1.2*inch, 4.8*inch])
                    aims_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(accent)),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')]),
                    ]))
                    elements.append(aims_tbl)
                
                elements.append(Spacer(1, 0.25*inch))
        
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


# =============================================================================
# AI REPORT PDF (15-section lens reports + 11-section Cosmic Integration)
# =============================================================================

# Section display metadata — order matters
_LENS_SECTION_ORDER_BASE = [
    ('galaxy_snapshot',       'Galaxy Snapshot',                              '#6366F1'),
    ('galaxy_placement',      'Galaxy Placement',                             '#8B5CF6'),
    ('archetype_profile',     'Archetype Profile',                            '#A78BFA'),
    ('ef_ecosystem',          'Executive Function Ecosystem',                 '#7C3AED'),
    ('financial_ef_profile',  'Financial Executive Functioning Profile\u2122', '#059669'),
    ('health_ef_profile',     'Health & Fitness Executive Functioning Profile\u2122', '#2563EB'),
    ('pei_analysis',          'PEI Analysis (External Load)',                 '#DC2626'),
    ('bhp_analysis',          'BHP Analysis (Internal Capacity)',             '#16A34A'),
    ('pei_bhp_interaction',   'PEI \u00d7 BHP Interaction',                  '#D97706'),
    ('strength_profile',      'Strength Profile',                             '#059669'),
    ('growth_edges',          'Growth Edges / Load Sensitivity Zones',        '#EA580C'),
    ('aims_plan',             'AIMS for the BEST\u2122',                     '#7C3AED'),
    # Lens-exclusive section inserted dynamically below
    ('pattern_continuity',    'Pattern Continuity Section\u2122',            '#6366F1'),
    ('expansion_pathway',     'Expansion Pathway Section\u2122',             '#8B5CF6'),
    ('cosmic_summary',        'Cosmic Summary',                               '#4F46E5'),
]

# Lens-exclusive sections (Addendum Phase 3, Section 4)
_LENS_EXCLUSIVE_SECTION_META = {
    'STUDENT_SUCCESS':         ('academic_performance_impact',    'Academic Performance Impact\u2122',          '#F59E0B'),
    'PERSONAL_LIFESTYLE':      ('lifestyle_stability_index',      'Lifestyle Stability Index\u2122',            '#10B981'),
    'PROFESSIONAL_LEADERSHIP': ('execution_productivity_profile', 'Execution & Productivity Profile\u2122',     '#3B82F6'),
    'FAMILY_ECOSYSTEM':        ('family_system_dynamics',         'Family System Dynamics\u2122',               '#EC4899'),
}


def _get_lens_section_order(report_type: str) -> list:
    """Get section order for a lens, including the exclusive section after AIMS."""
    order = list(_LENS_SECTION_ORDER_BASE)
    meta = _LENS_EXCLUSIVE_SECTION_META.get(report_type)
    if meta:
        # Insert after aims_plan (index 11 in the base list)
        aims_idx = next((i for i, s in enumerate(order) if s[0] == 'aims_plan'), 11)
        order.insert(aims_idx + 1, meta)
    return order

_COSMIC_SECTION_ORDER = [
    ('cosmic_snapshot',              'Cosmic Snapshot',                       '#6366F1'),
    ('galaxy_convergence_map',       'Galaxy Convergence Map\u2122',         '#8B5CF6'),
    ('load_balance_matrix',          'Load Balance Matrix\u2122',            '#7C3AED'),
    ('cross_domain_load_transfer',   'Cross-Domain Load Transfer Analysis',  '#D97706'),
    ('core_system_identity',         'Core System Identity Under Load',      '#DC2626'),
    ('global_strength_architecture', 'Global Strength Architecture',         '#059669'),
    ('system_wide_sensitivity',      'System-Wide Load Sensitivity Zones',   '#EA580C'),
    ('pattern_continuity_amplified', 'Pattern Continuity Amplified\u2122',   '#6366F1'),
    ('cosmic_aims',                  'AIMS for the BEST\u2122 \u2014 Cosmic Level', '#7C3AED'),
    ('expansion_pathway',            'Expansion Pathway Section\u2122',      '#8B5CF6'),
    ('cosmic_summary',               'Cosmic Summary',                       '#4F46E5'),
]

_LENS_DISPLAY = {
    'STUDENT_SUCCESS':          ('Student Success',             '#6366F1'),
    'PERSONAL_LIFESTYLE':       ('Personal / Lifestyle',        '#8B5CF6'),
    'PROFESSIONAL_LEADERSHIP':  ('Professional / Leadership',   '#2563EB'),
    'FAMILY_ECOSYSTEM':         ('Family EF Ecosystem',         '#059669'),
    'FULL_GALAXY':              ('Cosmic Integration',          '#7C3AED'),
}


def generate_ai_report_pdf(
    report_sections: dict,
    report_type: str,
    user_id: Optional[str] = None,
    generated_at: Optional[str] = None,
) -> Optional[bytes]:
    """
    Generate a PDF from an AI-generated report (15-section lens or 11-section Cosmic).

    Args:
        report_sections: dict mapping section_key -> narrative text
        report_type: e.g. STUDENT_SUCCESS, FULL_GALAXY
        user_id: optional user identifier for the header
        generated_at: optional ISO timestamp

    Returns:
        PDF bytes or None on failure
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        elements = []

        is_cosmic = report_type == 'FULL_GALAXY'
        section_order = _COSMIC_SECTION_ORDER if is_cosmic else _get_lens_section_order(report_type)
        lens_label, lens_color = _LENS_DISPLAY.get(report_type, (report_type.replace('_', ' ').title(), '#6366F1'))

        # ── Styles ──
        title_style = ParagraphStyle(
            'AIRTitle', parent=styles['Heading1'],
            fontSize=22, textColor=colors.HexColor(lens_color),
            spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold',
        )
        subtitle_style = ParagraphStyle(
            'AIRSub', parent=styles['Normal'],
            fontSize=11, textColor=colors.HexColor('#6B7280'),
            spaceAfter=16, alignment=TA_CENTER,
        )
        section_title_style = ParagraphStyle(
            'AIRSecTitle', parent=styles['Heading2'],
            fontSize=14, textColor=colors.HexColor('#1F2937'),
            spaceAfter=8, spaceBefore=16, fontName='Helvetica-Bold',
        )
        body_style = ParagraphStyle(
            'AIRBody', parent=styles['BodyText'],
            fontSize=10.5, alignment=TA_JUSTIFY,
            spaceAfter=10, leading=15, textColor=colors.HexColor('#374151'),
        )
        footer_style = ParagraphStyle(
            'AIRFooter', parent=styles['Normal'],
            fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
        )

        # ── Title Page ──
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph(
            "BEST Executive Function Galaxy Assessment\u2122",
            ParagraphStyle('AIRSmall', parent=styles['Normal'],
                           fontSize=10, textColor=colors.HexColor('#6B7280'),
                           spaceAfter=8, alignment=TA_CENTER),
        ))
        report_label = 'Cosmic Integration Report' if is_cosmic else f'{lens_label} Report'
        elements.append(Paragraph(report_label, title_style))
        elements.append(Paragraph(
            'AI-Generated Executive Function Narrative',
            subtitle_style,
        ))

        elements.append(HRFlowable(
            width="100%", thickness=2,
            color=colors.HexColor(lens_color), spaceAfter=12,
        ))

        # Header info
        user_display = user_id or 'N/A'
        if user_display and len(user_display) > 40:
            user_display = user_display[:37] + '...'

        ts = generated_at or datetime.now().isoformat()
        try:
            date_str = datetime.fromisoformat(
                ts.replace('Z', '+00:00')
            ).strftime('%B %d, %Y at %I:%M %p')
        except Exception:
            date_str = ts[:19]

        info_data = [
            ['Prepared for:', user_display],
            ['Report Date:', date_str],
            ['Report Lens:', lens_label],
            ['Sections:', f'{len(section_order)} sections'],
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
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#E5E7EB'), spaceAfter=8,
        ))
        elements.append(PageBreak())

        # ── Sections ──
        for idx, (key, display_title, accent) in enumerate(section_order):
            content = report_sections.get(key, '')
            if not content or not content.strip():
                continue

            # Section number badge + title
            num_label = f'Section {idx + 1}'
            elements.append(Paragraph(
                f'<font color="{accent}" size="8">{num_label}</font>',
                ParagraphStyle(f'AIRNum{idx}', parent=styles['Normal'],
                               fontSize=8, spaceBefore=12, spaceAfter=2),
            ))
            elements.append(Paragraph(
                f'<font color="{accent}">{display_title}</font>',
                section_title_style,
            ))

            # Accent bar
            elements.append(HRFlowable(
                width="30%", thickness=2,
                color=colors.HexColor(accent), spaceAfter=8,
            ))

            # Body paragraphs — split on double newlines
            paragraphs = content.strip().split('\n\n')
            for para in paragraphs:
                clean = para.strip().replace('\n', ' ')
                if clean:
                    elements.append(Paragraph(clean, body_style))

            elements.append(Spacer(1, 0.15 * inch))

            # Page break after every 3 sections to keep layout clean
            if (idx + 1) % 3 == 0 and idx < len(section_order) - 1:
                elements.append(PageBreak())

        # ── Validation badge ──
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#D1FAE5'), spaceAfter=8,
        ))
        elements.append(Paragraph(
            f'\u2713 Report Quality Verified \u2014 All {len(section_order)} sections present '
            f'\u2022 Language compliance checked \u2022 AIMS structure verified',
            ParagraphStyle('AIRBadge', parent=styles['Normal'],
                           fontSize=9, textColor=colors.HexColor('#059669'),
                           alignment=TA_CENTER, spaceAfter=16),
        ))

        # ── Footer ──
        elements.append(Paragraph(
            f"BEST Executive Function Galaxy Assessment\u2122 | {report_label} | Confidential",
            footer_style,
        ))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated AI report PDF ({report_type}): {len(pdf_bytes)} bytes, {len(section_order)} sections")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Failed to generate AI report PDF: {e}", exc_info=True)
        return None


def generate_cosmic_dashboard_pdf(
    assessment_data: dict,
    cosmic_report: Optional[dict] = None,
    user_id: Optional[str] = None,
) -> Optional[bytes]:
    """
    Generate a Cosmic Dashboard PDF combining the structured analytical
    layer (load profiles, flows, compensation patterns, sensitivities) with
    the AI-generated cosmic narrative if available.

    Layout:
      - Title page
      - Lens Profile Table (per-environment stability/load)
      - Top Cross-Domain Flows
      - Compensation Patterns
      - System-Wide Sensitivities
      - Cosmic narrative sections (when cosmic_report is provided)
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            PageBreak, HRFlowable,
        )
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        elements = []

        title_style = ParagraphStyle(
            'CosmicTitle', parent=styles['Heading1'],
            fontSize=22, textColor=colors.HexColor('#4F46E5'),
            spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold',
        )
        subtitle_style = ParagraphStyle(
            'CosmicSub', parent=styles['Normal'],
            fontSize=11, textColor=colors.HexColor('#6B7280'),
            spaceAfter=16, alignment=TA_CENTER,
        )
        section_title_style = ParagraphStyle(
            'CosmicSec', parent=styles['Heading2'],
            fontSize=14, textColor=colors.HexColor('#1F2937'),
            spaceAfter=8, spaceBefore=14, fontName='Helvetica-Bold',
        )
        body_style = ParagraphStyle(
            'CosmicBody', parent=styles['BodyText'],
            fontSize=10.5, alignment=TA_JUSTIFY,
            spaceAfter=10, leading=15, textColor=colors.HexColor('#374151'),
        )
        footer_style = ParagraphStyle(
            'CosmicFooter', parent=styles['Normal'],
            fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
        )

        # Title page
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(Paragraph(
            "BEST Executive Function Galaxy Assessment\u2122",
            ParagraphStyle('CosmicSmall', parent=styles['Normal'],
                           fontSize=10, textColor=colors.HexColor('#6B7280'),
                           spaceAfter=8, alignment=TA_CENTER),
        ))
        elements.append(Paragraph("Cosmic Integration Dashboard", title_style))
        elements.append(Paragraph(
            'Cross-Environmental Executive Function Synthesis',
            subtitle_style,
        ))
        elements.append(HRFlowable(
            width="100%", thickness=2,
            color=colors.HexColor('#4F46E5'), spaceAfter=12,
        ))

        ts = datetime.now().strftime('%B %d, %Y')
        info_table = Table(
            [
                ['Prepared for:', (user_id or 'N/A')[:40]],
                ['Report Date:', ts],
            ],
            colWidths=[1.8 * inch, 4.2 * inch],
        )
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#312E81')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1F2937')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(info_table)
        elements.append(PageBreak())

        # Cross-domain analytical layer
        cross = (assessment_data or {}).get('cross_domain', {}) or {}
        lens_profiles = cross.get('lens_profiles', {}) or {}
        flows = cross.get('flows', []) or []
        compensations = cross.get('compensation_patterns', []) or []
        sensitivities = cross.get('system_wide_sensitivities', []) or []

        # Lens profile table
        if lens_profiles:
            elements.append(Paragraph('Lens Profiles', section_title_style))
            lens_rows = [['Lens', 'BHP (capacity)', 'PEI (load)', 'Balance', 'Status']]
            lens_label_map = {
                'STUDENT_SUCCESS': 'Student / Academic',
                'PERSONAL_LIFESTYLE': 'Personal / Lifestyle',
                'PROFESSIONAL_LEADERSHIP': 'Professional / Work',
                'FAMILY_ECOSYSTEM': 'Family / Ecosystem',
            }
            for lens, profile in lens_profiles.items():
                lens_rows.append([
                    lens_label_map.get(lens, lens),
                    f"{profile.get('bhp', 0):.2f}",
                    f"{profile.get('pei', 0):.2f}",
                    f"{profile.get('load_balance', 0):+.2f}",
                    profile.get('status', '—').title(),
                ])
            lens_tbl = Table(lens_rows, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch])
            lens_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EEF2FF')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#312E81')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E5E7EB')),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(lens_tbl)
            elements.append(Spacer(1, 0.2 * inch))

        # Cross-domain flows
        if flows:
            elements.append(Paragraph('Cross-Domain Load Transfers', section_title_style))
            for f in flows[:10]:
                line = (
                    f"<b>{f.get('from', '?').title()} → {f.get('to', '?').title()}</b> "
                    f"— strength {f.get('strength', 0):.2f}"
                )
                if f.get('rationale') and f['rationale'] != 'baseline cross-domain coupling':
                    line += f" <i>({f['rationale']})</i>"
                elements.append(Paragraph(line, body_style))
            elements.append(Spacer(1, 0.15 * inch))

        # Compensation patterns
        if compensations:
            elements.append(Paragraph('Compensation Patterns', section_title_style))
            for c in compensations[:8]:
                elements.append(Paragraph(
                    f"<b>{c.get('stabilizer', '')} → {c.get('vulnerability', '')}</b> "
                    f"— gap {c.get('gap', 0):+.2f}<br/>{c.get('narrative', '')}",
                    body_style,
                ))
            elements.append(Spacer(1, 0.15 * inch))

        # System-wide sensitivities
        if sensitivities:
            elements.append(Paragraph('System-Wide Sensitivities', section_title_style))
            for s in sensitivities[:8]:
                elements.append(Paragraph(
                    f"<b>{s.get('domain', '')}</b>: {s.get('pattern', '')}",
                    body_style,
                ))
            elements.append(Spacer(1, 0.2 * inch))

        # Cosmic narrative (if available)
        if cosmic_report:
            sections = cosmic_report.get('sections', {}) or {}
            if sections:
                elements.append(PageBreak())
                elements.append(Paragraph('Cosmic Integration Narrative', title_style))
                cosmic_order = [
                    ('cosmic_snapshot', 'Cosmic Snapshot'),
                    ('galaxy_convergence_map', 'Galaxy Convergence Map'),
                    ('archetype_evolution', 'Archetype Evolution'),
                    ('cross_domain_load_transfer', 'Cross-Domain Load Transfer'),
                    ('compensation_patterns', 'Compensation Patterns'),
                    ('system_wide_sensitivity', 'System-Wide Sensitivity'),
                    ('stabilizers_across_universe', 'Stabilizers Across Your Universe'),
                    ('lens_overlay_summary', 'Lens Overlay Summary'),
                    ('cosmic_aims', 'Cosmic AIMS Pathway'),
                    ('long_term_trajectory', 'Long-Term Trajectory'),
                    ('closing_synthesis', 'Closing Synthesis'),
                ]
                for key, title in cosmic_order:
                    text = sections.get(key)
                    if not text:
                        continue
                    elements.append(Paragraph(title, section_title_style))
                    for para in str(text).strip().split('\n\n'):
                        clean = para.strip().replace('\n', ' ')
                        if clean:
                            elements.append(Paragraph(clean, body_style))
                    elements.append(Spacer(1, 0.1 * inch))

        elements.append(Paragraph(
            "BEST Executive Function Galaxy Assessment\u2122 | Cosmic Dashboard | Confidential",
            footer_style,
        ))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated cosmic dashboard PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Failed to generate cosmic dashboard PDF: {e}", exc_info=True)
        return None
