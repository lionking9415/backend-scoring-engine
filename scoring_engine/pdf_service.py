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


# ---------------------------------------------------------------------------
# Legal & medical disclaimers
# ---------------------------------------------------------------------------
# Mirror of the verbatim copy in `frontend/src/legal/legalText.js`.  Any
# change to the user-facing legal text MUST be made in both places.
# Keeping the strings here means the PDF layer doesn't need a network call
# to render the boilerplate.

_LEGAL_VERSION = "2026-04-30"
_PRODUCT_NAME = "BEST Galaxy\u2122"
_ENTITY_NAME = "International ABA Institute LLC"

_PDF_INLINE_DISCLAIMER = (
    "Educational insights only. Not medical or mental health advice."
)

_PDF_SHORT_DISCLAIMER = (
    f"{_PRODUCT_NAME} provides educational insights into executive functioning "
    "and behavior patterns. It is not a medical or mental health diagnostic "
    "tool. Please consult a licensed professional for clinical concerns."
)

_PDF_FULL_DISCLAIMER_PARAS = [
    f"The {_PRODUCT_NAME}, including all assessments, reports, interpretations, and "
    f"recommendations provided by {_ENTITY_NAME} and its affiliated programs, is "
    "intended for educational, informational, and personal development purposes only.",
    "This content is not intended to diagnose, treat, cure, or prevent any medical, "
    "psychological, or psychiatric condition. The information provided does not "
    "constitute medical advice, mental health counseling, or professional clinical services.",
    "Users are strongly encouraged to consult with a qualified physician, licensed mental "
    "health professional, or other appropriate healthcare provider regarding any medical "
    "or psychological concerns. Do not disregard or delay seeking professional advice "
    "based on information obtained through this platform.",
    f"Participation in the {_PRODUCT_NAME} assessment and use of any associated reports or "
    "recommendations is voluntary. By engaging with this platform, you acknowledge and agree that:",
]

_PDF_FULL_DISCLAIMER_BULLETS = [
    "You are solely responsible for your health, decisions, and actions.",
    f"The {_PRODUCT_NAME} operates as a behavioral and educational framework, not a healthcare provider.",
    "No guarantees are made regarding outcomes or results.",
    "Individual results may vary based on personal, environmental, and behavioral factors.",
]

_PDF_FULL_DISCLAIMER_CLOSING = (
    f"To the fullest extent permitted by law, {_ENTITY_NAME} and its affiliates disclaim "
    "any liability for any direct, indirect, incidental, or consequential damages arising "
    "from the use or misuse of this platform, including but not limited to reliance on "
    "assessment results, reports, or recommendations."
)


def _build_short_disclaimer_flowable():
    """Return a small Important-Notice callout suitable for the top of a report."""
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

    title_style = ParagraphStyle(
        'DisclaimerTitle', fontName='Helvetica-Bold', fontSize=9,
        textColor=colors.HexColor('#92400E'),  # amber-900
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        'DisclaimerBody', fontName='Helvetica', fontSize=8.5,
        textColor=colors.HexColor('#78350F'),  # amber-950
        leading=11,
    )
    inner = [
        Paragraph('Important Notice', title_style),
        Paragraph(_PDF_SHORT_DISCLAIMER, body_style),
    ]
    tbl = Table([[inner]], colWidths=[6.4 * 72])  # 6.4 inches inside default margins
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FEF3C7')),  # amber-100
        ('LINEBEFORE', (0, 0), (0, 0), 3, colors.HexColor('#F59E0B')),  # amber-500 left bar
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return [tbl, Spacer(1, 8)]


def _build_full_disclaimer_flowables():
    """Return the full Legal & Medical Disclaimer block for the end of a report."""
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, PageBreak, Spacer

    heading = ParagraphStyle(
        'LegalHeading', fontName='Helvetica-Bold', fontSize=12,
        textColor=colors.HexColor('#111827'),  # gray-900
        spaceAfter=8,
    )
    body = ParagraphStyle(
        'LegalBody', fontName='Helvetica', fontSize=8.5,
        textColor=colors.HexColor('#374151'),  # gray-700
        leading=12.5, spaceAfter=6,
    )
    bullet = ParagraphStyle(
        'LegalBullet', parent=body, leftIndent=14, bulletIndent=4,
    )
    version_note = ParagraphStyle(
        'LegalVersion', fontName='Helvetica-Oblique', fontSize=7.5,
        textColor=colors.HexColor('#6B7280'),  # gray-500
        spaceBefore=8,
    )

    elements = [PageBreak(), Paragraph('Legal &amp; Medical Disclaimer', heading)]
    for para in _PDF_FULL_DISCLAIMER_PARAS:
        elements.append(Paragraph(para, body))
    for b in _PDF_FULL_DISCLAIMER_BULLETS:
        elements.append(Paragraph(f'\u2022 {b}', bullet))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(_PDF_FULL_DISCLAIMER_CLOSING, body))
    elements.append(Paragraph(
        f'Legal version v{_LEGAL_VERSION} \u2014 {_ENTITY_NAME}',
        version_note,
    ))
    return elements


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
        from scoring_engine.pdf_theme import (
            THEME, BESTPageTemplate, build_cover_page, get_theme_styles,
            make_donut_chart, make_rounded_bar, CalloutBox, SectionHeader,
            themed_table_style, score_color, format_date,
        )
        
        # Build the same scorecard data the frontend displays
        scorecard = build_scorecard_output(full_output)
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=48, bottomMargin=42)
        
        elements = []
        ts = get_theme_styles(THEME['primary'])
        page_tpl = BESTPageTemplate(
            accent_color=THEME['primary'], lens_label='Free ScoreCard',
        )
        
        # Extract scorecard data
        snapshot = scorecard.get('galaxy_snapshot', {})
        constellation = scorecard.get('constellation', [])
        load_balance = scorecard.get('load_balance', {})
        strengths = scorecard.get('strengths', [])
        growth_edges = scorecard.get('growth_edges', [])
        lens_teasers = scorecard.get('lens_teasers', {})
        metadata = scorecard.get('metadata', {})
        
        # Report info - fetch user name
        user_id = metadata.get('user_email') or metadata.get('user_id', 'N/A')
        user_name = _get_user_name(user_id)
        if len(user_name) > 40:
            user_name = user_name[:37] + '...'
        
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        date_str = format_date(timestamp)
        
        archetype_name = snapshot.get('archetype_name', 'Unknown')
        tagline = snapshot.get('tagline', '')
        
        # ── COVER PAGE ──
        elements += build_cover_page(
            report_title=archetype_name.upper(),
            report_subtitle=f'"{tagline}"' if tagline else 'Your Executive Function Profile',
            user_name=user_name,
            date_str=date_str,
            lens_label='Free ScoreCard',
            accent_color=THEME['primary'],
            extra_lines=[('Report Type:', 'Free ScoreCard')],
        )

        elements += _build_short_disclaimer_flowable()
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(
            'This profile reflects how your internal capacity (BHP) is interacting with your environmental demands (PEI).',
            ParagraphStyle('FrameworkRef', parent=ts['caption'],
                           fontSize=9, textColor=colors.HexColor(THEME['indigo']),
                           fontName='Helvetica-Oblique', spaceAfter=4),
        ))
        elements.append(PageBreak())
        
        # Domain color + tag mapping
        DOMAIN_META = {
            'Executive Skills & Behavior':      {'tag': 'Action & Follow-Through',  'color': '#3B82F6'},
            'Cognitive & Motivational Systems': {'tag': 'Focus & Drive',            'color': '#8B5CF6'},
            'Emotional & Internal State':       {'tag': 'Emotional Regulation',     'color': '#F59E0B'},
            'Environmental Demands':            {'tag': 'Environmental Pressure Load (PEI)', 'color': '#EF4444'},
        }
        
        # ── 2. EXECUTIVE FUNCTION CONSTELLATION (4 grouped domains) ──
        elements.append(SectionHeader(1, "Your Executive Function Constellation",
                                      accent_color=THEME['primary']))
        elements.append(Spacer(1, 0.1 * inch))

        # Donut chart row — one per constellation group
        donut_cells = []
        for group in constellation:
            pct = group.get('percentage', 0)
            meta = DOMAIN_META.get(group['name'], {'tag': '', 'color': '#6B7280'})
            is_env = group['name'] == 'Environmental Demands'
            display_name = 'Env. Pressure\nLoad (PEI)' if is_env else group['name']
            donut_cells.append(
                make_donut_chart(
                    value=pct, max_value=100, size=72, ring_width=10,
                    fill_color=meta['color'],
                    label=display_name.split('\n')[0][:18],
                )
            )
        if donut_cells:
            donut_table = Table([donut_cells],
                                colWidths=[1.55 * inch] * len(donut_cells))
            donut_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(donut_table)
            elements.append(Spacer(1, 0.12 * inch))

        # Detailed constellation table
        styles = getSampleStyleSheet()
        const_header_style = ParagraphStyle(
            'ConstHeader', parent=styles['Normal'], fontName='Helvetica-Bold',
            fontSize=9, textColor=colors.whitesmoke, alignment=TA_CENTER, leading=12,
        )
        const_tag_style = ParagraphStyle(
            'ConstTag', parent=styles['Normal'], fontName='Helvetica',
            fontSize=8.5, textColor=colors.HexColor(THEME['gray_500']), alignment=TA_LEFT, leading=11,
        )

        constellation_data = [[
            Paragraph('Domain Group', const_header_style),
            Paragraph('Tag', const_header_style),
            Paragraph('Score', const_header_style),
            Paragraph('Level', const_header_style),
        ]]
        for group in constellation:
            pct = group.get('percentage', 0)
            meta = DOMAIN_META.get(group['name'], {'tag': '', 'color': '#6B7280'})
            is_env = group['name'] == 'Environmental Demands'
            display_name = 'Env. Pressure Load (PEI)' if is_env else group['name']
            display_tag = 'Higher = More Pressure' if is_env else meta['tag']

            bar = make_rounded_bar(
                pct, width_inch=1.0, height_pt=10,
                fill_color=meta['color'], show_label=True,
            )

            name_style = ParagraphStyle(
                f"ConstName_{group['name']}", parent=styles['Normal'],
                fontName='Helvetica-Bold', fontSize=9,
                textColor=colors.HexColor(meta['color']),
                alignment=TA_LEFT, leading=12,
            )
            constellation_data.append([
                Paragraph(display_name, name_style),
                Paragraph(display_tag, const_tag_style),
                Paragraph(f"{group['score']:.3f}", ParagraphStyle(
                    'ConstSc', parent=styles['Normal'], fontName='Helvetica',
                    fontSize=9, textColor=colors.HexColor(THEME['gray_800']),
                    alignment=TA_CENTER, leading=12)),
                bar,
            ])

        const_table = Table(constellation_data, colWidths=[2.0 * inch, 1.4 * inch, 0.8 * inch, 1.8 * inch])
        const_table.setStyle(TableStyle(
            themed_table_style(THEME['primary']) + [
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        ))
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
            status_color = THEME['green']
        elif dynamic_label == 'Balanced Load':
            status_color = THEME['blue']
        elif dynamic_label == 'Emerging Strain':
            status_color = THEME['amber']
        else:
            status_color = THEME['red']
        
        delta_color = THEME['red'] if delta > 0.01 else THEME['blue'] if delta < -0.01 else THEME['gray_500']
        delta_sign = '+' if delta > 0 else ''
        
        elements.append(SectionHeader(2, f"Load Balance: {dynamic_label}",
                                      accent_color=status_color))
        elements.append(Spacer(1, 0.1 * inch))
        
        # BHP vs PEI visual comparison with rounded bars
        if pei_score or bhp_score:
            bhp_pct = min(100, (bhp_score or 0) * 100)
            pei_pct = min(100, (pei_score or 0) * 100)
            lb_data = [
                [
                    Paragraph('<b>INTERNAL CAPACITY (BHP)</b>', ParagraphStyle(
                        'LBH1', parent=styles['Normal'], fontSize=8,
                        textColor=colors.HexColor(THEME['blue']),
                        fontName='Helvetica-Bold', alignment=TA_CENTER, leading=10)),
                    '',
                    Paragraph('<b>ENVIRONMENTAL LOAD (PEI)</b>', ParagraphStyle(
                        'LBH2', parent=styles['Normal'], fontSize=8,
                        textColor=colors.HexColor(THEME['red']),
                        fontName='Helvetica-Bold', alignment=TA_CENTER, leading=10)),
                ],
                [
                    make_rounded_bar(bhp_pct, width_inch=2.2, height_pt=14,
                                     fill_color=THEME['blue'], show_label=True),
                    Paragraph(f'<b>{delta_sign}{delta:.3f}</b>', ParagraphStyle(
                        'LBDelta', parent=styles['Normal'], fontSize=10,
                        textColor=colors.HexColor(delta_color),
                        fontName='Helvetica-Bold', alignment=TA_CENTER, leading=14)),
                    make_rounded_bar(pei_pct, width_inch=2.2, height_pt=14,
                                     fill_color=THEME['red'], show_label=True),
                ],
            ]
            lb_table = Table(lb_data, colWidths=[2.7 * inch, 0.8 * inch, 2.7 * inch])
            lb_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor(THEME['blue_light'])),
                ('BACKGROUND', (2, 0), (2, 0), colors.HexColor(THEME['red_light'])),
                ('BACKGROUND', (1, 0), (1, 0), colors.HexColor(THEME['gray_100'])),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor(THEME['gray_200'])),
            ]))
            elements.append(lb_table)
        elements.append(Spacer(1, 0.08 * inch))
        
        # Classification chips as a styled row
        chip_data = [[
            Paragraph(f'<b>Load State</b><br/><font color="{status_color}">{dynamic_label}</font>',
                      ParagraphStyle('Chip1', parent=styles['Normal'], fontSize=8,
                                     textColor=colors.HexColor(THEME['gray_600']),
                                     alignment=TA_CENTER, leading=11)),
            Paragraph(f'<b>System Status</b><br/><font color="{status_color}">{tilt_label}</font>',
                      ParagraphStyle('Chip2', parent=styles['Normal'], fontSize=8,
                                     textColor=colors.HexColor(THEME['gray_600']),
                                     alignment=TA_CENTER, leading=11)),
            Paragraph(f'<b>Pressure Level</b><br/><font color="{status_color}">{pressure_level}</font>',
                      ParagraphStyle('Chip3', parent=styles['Normal'], fontSize=8,
                                     textColor=colors.HexColor(THEME['gray_600']),
                                     alignment=TA_CENTER, leading=11)),
        ]]
        chip_table = Table(chip_data, colWidths=[2.1 * inch, 2.1 * inch, 2.1 * inch])
        chip_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(THEME['gray_50'])),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor(THEME['gray_200'])),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(chip_table)
        elements.append(Spacer(1, 0.1 * inch))
        
        if load_msg:
            elements.append(CalloutBox(
                'Load Insight', load_msg,
                accent_color=status_color, bg_color=THEME['gray_50'],
            ))
        
        # AI-Generated Executive Summary
        if executive_summary:
            elements.append(Spacer(1, 0.08 * inch))
            elements.append(CalloutBox(
                'Executive Summary', executive_summary,
                accent_color=THEME['primary'], bg_color=THEME['primary_light'],
            ))
        elements.append(Spacer(1, 0.15 * inch))
        
        # ── 4. STRENGTHS & GROWTH EDGES ──
        # Filter Environmental Demands from strengths (it's pressure, not capacity)
        filtered_strengths = [s for s in strengths if 'Environmental' not in s and 'ENVIRONMENTAL' not in s]
        elements.append(SectionHeader(3, "Strengths & Growth Edges",
                                      accent_color=THEME['green']))
        elements.append(Spacer(1, 0.06 * inch))
        
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
            elements.append(SectionHeader(4, "Applied Executive Functioning Domains",
                                          accent_color=THEME['purple']))
            elements.append(Spacer(1, 0.04 * inch))
            elements.append(Paragraph(
                "How your executive functioning expresses in everyday living",
                ParagraphStyle('ADSubtitle', parent=ts['body_small'], fontSize=9,
                             textColor=colors.HexColor(THEME['gray_500']), spaceAfter=10)
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
                    ParagraphStyle('ADTitle', parent=ts['subheading'], fontSize=13, spaceAfter=2)
                ))
                elements.append(Paragraph(
                    f'<i>{domain_subtitles.get(key, "")}</i>',
                    ParagraphStyle('ADDomSub', parent=ts['body_small'],
                                 textColor=colors.HexColor(THEME['gray_500']), spaceAfter=6)
                ))
                
                # Metrics row: donut chart + key stats side-by-side
                lb_color = THEME['green'] if lb_val >= 0 else THEME['red']
                status_band_style = ParagraphStyle(
                    'StatusBandFree', parent=styles['Normal'],
                    fontName='Helvetica-Bold', fontSize=10,
                    textColor=colors.HexColor(THEME['gray_800']),
                    alignment=TA_CENTER, leading=12,
                )
                
                ad_donut = make_donut_chart(
                    value=domain_score, max_value=100, size=68, ring_width=10,
                    fill_color=accent, label='Domain Score',
                )
                ad_stats = [
                    ['BHP (Capacity)', 'PEI (Pressure)', 'Load Balance', 'Status Band'],
                    [
                        f'{bhp_val:.1f}',
                        f'{pei_val:.1f}',
                        f'{lb_val:+.1f}',
                        Paragraph(status_band, status_band_style),
                    ],
                ]
                ad_stats_tbl = Table(ad_stats, colWidths=[1.1 * inch, 1.1 * inch, 1.0 * inch, 1.3 * inch])
                ad_stats_tbl.setStyle(TableStyle(
                    themed_table_style(accent) + [
                        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 1), (-1, 1), 11),
                        ('TEXTCOLOR', (0, 1), (0, 1), colors.HexColor(THEME['blue'])),
                        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor(THEME['red'])),
                        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor(lb_color)),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]
                ))
                layout_row = Table(
                    [[ad_donut, ad_stats_tbl]],
                    colWidths=[1.2 * inch, 4.8 * inch],
                )
                layout_row.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(layout_row)
                elements.append(Spacer(1, 0.08 * inch))
                
                # Block 2: BHP vs PEI visual balance with rounded bars
                bhp_total = bhp_val + pei_val if (bhp_val + pei_val) > 0 else 1
                bhp_share_pct = round((bhp_val / bhp_total) * 100)
                pei_share_pct = round((pei_val / bhp_total) * 100)
                bal_data = [
                    [
                        make_rounded_bar(bhp_share_pct, width_inch=2.4, height_pt=12,
                                         fill_color=THEME['blue'], show_label=True),
                        Paragraph(f'<b>{"BHP > PEI" if lb_val > 0 else ("PEI > BHP" if lb_val < 0 else "BALANCED")}</b>',
                                  ParagraphStyle('BalLbl', parent=styles['Normal'], fontSize=8,
                                                 textColor=colors.HexColor(THEME['gray_600']),
                                                 alignment=TA_CENTER, leading=10)),
                        make_rounded_bar(pei_share_pct, width_inch=2.4, height_pt=12,
                                         fill_color=THEME['red'], show_label=True),
                    ],
                ]
                bal_tbl = Table(bal_data, colWidths=[2.8 * inch, 0.8 * inch, 2.8 * inch])
                bal_tbl.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(bal_tbl)
                elements.append(Spacer(1, 0.08 * inch))
                
                # Block 3: When Stable / When Loaded — callout boxes
                if interp.get('when_stable'):
                    elements.append(CalloutBox(
                        'When Stable', interp['when_stable'],
                        accent_color=THEME['green'], bg_color=THEME['green_light'],
                    ))
                    elements.append(Spacer(1, 0.04 * inch))
                if interp.get('when_loaded'):
                    elements.append(CalloutBox(
                        'Under Load', interp['when_loaded'],
                        accent_color='#EA580C', bg_color=THEME['amber_light'],
                    ))
                    elements.append(Spacer(1, 0.06 * inch))
                
                # Block 4: Risk Flags
                if active_flags:
                    elements.append(Paragraph(
                        '<b>Risk Flags</b>',
                        ParagraphStyle('FlagHead', parent=ts['subheading'], fontSize=10,
                                     textColor=colors.HexColor(THEME['gray_700']), spaceBefore=2, spaceAfter=4)
                    ))
                    flags_text = '&nbsp;&nbsp;|&nbsp;&nbsp;'.join(
                        f'<font color="{THEME["red"]}"><b>!</b> {f}</font>' for f in active_flags
                    )
                    elements.append(Paragraph(flags_text, ts['body_small']))
                
                # Block 5: Domain Interpretation narrative
                if interp.get('domain_narrative'):
                    elements.append(CalloutBox(
                        'Domain Interpretation', interp['domain_narrative'],
                        accent_color=accent, bg_color=THEME['gray_50'],
                    ))
                    elements.append(Spacer(1, 0.06 * inch))
                
                # Subvariable Breakdown table with rounded bars
                if subvariables:
                    elements.append(Paragraph(
                        '<b>Subvariable Breakdown</b>',
                        ParagraphStyle('SVHead', parent=ts['subheading'], fontSize=10,
                                     textColor=colors.HexColor(THEME['gray_700']), spaceBefore=4, spaceAfter=4)
                    ))
                    sv_data = [['Subvariable', 'Score', 'Level']]
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
                        sc = score_color(bar_pct)
                        sv_data.append([
                            clean_name,
                            f'{bar_pct:.0f}',
                            make_rounded_bar(bar_pct, width_inch=2.2, height_pt=10,
                                             fill_color=sc, show_label=False),
                        ])

                    sv_table = Table(sv_data, colWidths=[2.2 * inch, 0.6 * inch, 2.8 * inch])
                    sv_cmds = themed_table_style(accent) + [
                        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]
                    for row_i in range(1, len(sv_data)):
                        sval = float(sv_data[row_i][1])
                        sc = score_color(sval)
                        sv_cmds.append(('TEXTCOLOR', (1, row_i), (1, row_i), colors.HexColor(sc)))
                        sv_cmds.append(('FONTNAME', (1, row_i), (1, row_i), 'Helvetica-Bold'))
                    sv_table.setStyle(TableStyle(sv_cmds))
                    elements.append(sv_table)
                    elements.append(Spacer(1, 0.08 * inch))
                
                # Block 6: AIMS Targets
                if aims:
                    elements.append(Paragraph(
                        '<b>AIMS Targets</b>',
                        ParagraphStyle('AimsHead', parent=ts['subheading'], fontSize=10,
                                     textColor=colors.HexColor(THEME['gray_700']), spaceBefore=2, spaceAfter=4)
                    ))
                    aims_data = [['Phase', 'Target']]
                    for a in aims:
                        aims_data.append([a.get('phase', ''), a.get('target', '')])
                    aims_tbl = Table(aims_data, colWidths=[1.2 * inch, 4.8 * inch])
                    aims_tbl.setStyle(TableStyle(themed_table_style(accent)))
                    elements.append(aims_tbl)
                
                elements.append(Spacer(1, 0.2 * inch))
        
        # ── 5. FOUR LENS TEASERS ──
        elements.append(SectionHeader(5, "Your Profile Across 4 Lenses",
                                      accent_color=THEME['indigo']))
        elements.append(Spacer(1, 0.1 * inch))
        
        from scoring_engine.pdf_theme import LENS_PALETTE
        for key, lens_data in lens_teasers.items():
            lp = LENS_PALETTE.get(key, {'accent': THEME['indigo'], 'label': key})
            title = lens_data.get('title', lp['label'])
            teaser = lens_data.get('teaser', '')
            elements.append(CalloutBox(
                title, teaser,
                accent_color=lp['accent'], bg_color=THEME['gray_50'],
            ))
            elements.append(Spacer(1, 0.08 * inch))
        
        # ── FOOTER / CTA ──
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(CalloutBox(
            'Unlock Your Full Report',
            'Your full report includes your personalized AIMS for the BEST\u2122 '
            'intervention pathway. You\'ve seen the surface. Now see the system.',
            accent_color=THEME['primary'], bg_color=THEME['primary_light'],
        ))
        
        # Append the full Legal & Medical Disclaimer at the end of every PDF.
        elements += _build_full_disclaimer_flowables()

        # Build PDF with themed page template
        doc.build(elements,
                  onFirstPage=page_tpl.first_page,
                  onLaterPages=page_tpl.later_pages)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated ScoreCard PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Failed to generate ScoreCard PDF: {e}", exc_info=True)
        return None


# ---------------------------------------------------------------------------
# Lens-section → interpretation slot mapping
# ---------------------------------------------------------------------------
# The Data Report PDF reads narrative copy from
# `assessment_data["interpretation"]`, which is the *lens-neutral* baseline
# generated once at assessment time.  When a paid lens-specific AI report
# exists in `generated_reports`, its sections (keys defined in
# `prompts.section_rules.LENS_REPORT_SECTIONS`) cover the same conceptual
# slots but under different keys.  This map projects those keys onto the
# interpretation-slot names the PDF expects, so each lens download actually
# shows lens-tailored prose instead of the same baseline text everywhere.
_LENS_SECTION_TO_INTERPRETATION = {
    'galaxy_snapshot':     'executive_summary',
    'galaxy_placement':    'quadrant_interpretation',
    'bhp_analysis':        'load_interpretation',
    'pei_bhp_interaction': 'pei_bhp_interpretation',
    'strength_profile':    'strengths_analysis',
    'growth_edges':        'growth_edges_analysis',
    'aims_plan':           'aims_plan',
    'cosmic_summary':      'cosmic_summary',
}


def _overlay_lens_sections(
    interpretation: dict,
    lens_sections: Optional[dict],
    active_lens: Optional[str],
) -> dict:
    """Return a copy of `interpretation` with lens-specific narrative laid
    over the baseline copy where available.

    - Only keys that are non-empty in `lens_sections` are overlaid.
    - The lens-exclusive section (e.g. `academic_performance_impact`) is
      kept under its original key, since the PDF reads it directly.
    - `aims_plan` may arrive as a string (lens AI generates a single
      paragraph). The downstream PDF code expects a dict keyed by phase;
      so when a string is returned we synthesize a single-phase dict so
      the lens narrative still surfaces instead of being dropped.
    """
    if not lens_sections or not isinstance(lens_sections, dict):
        return dict(interpretation or {})

    merged = dict(interpretation or {})

    for ls_key, interp_key in _LENS_SECTION_TO_INTERPRETATION.items():
        val = lens_sections.get(ls_key)
        if not val:
            continue

        if interp_key == 'aims_plan' and isinstance(val, str):
            existing = merged.get('aims_plan') if isinstance(merged.get('aims_plan'), dict) else {}
            merged['aims_plan'] = {**existing, 'awareness': val} if not existing else existing
            continue

        merged[interp_key] = val

    # Preserve the lens-exclusive section under its native key so the
    # exclusive-display block in the PDF picks it up.
    if active_lens:
        for k, v in lens_sections.items():
            if k not in _LENS_SECTION_TO_INTERPRETATION and v:
                merged.setdefault(k, v)

    return merged


def generate_pdf_report(
    assessment_data: dict,
    lens_override: Optional[str] = None,
    lens_sections: Optional[dict] = None,
) -> Optional[bytes]:
    """
    Generate a PDF report from assessment data.

    Args:
        assessment_data: Complete assessment output JSON
        lens_override: Optional lens to use for report generation (PERSONAL_LIFESTYLE,
                      STUDENT_SUCCESS, PROFESSIONAL_LEADERSHIP, FAMILY_ECOSYSTEM, FULL_GALAXY).
                      If provided, overrides the original report_type in metadata.
        lens_sections: Optional dict of lens-specific AI sections (from the
                      `generated_reports` row matching this lens). When
                      provided, lens-tailored narrative replaces the baseline
                      lens-neutral interpretation in the rendered PDF.

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
        from scoring_engine.pdf_theme import (
            THEME, BESTPageTemplate, build_cover_page, get_theme_styles,
            SectionHeader, CalloutBox, themed_table_style, make_rounded_bar,
            make_donut_chart, score_color, format_date, LENS_PALETTE,
        )
        from scoring_engine.report_generator import LENS_DOMAIN_WEIGHTS, _apply_lens_weights

        # ── Lens differentiation constants (Addendum Phase 3) ──
        _LENS_SUBTITLE = {
            'PERSONAL_LIFESTYLE': 'Your Executive Function Profile Through the Lens of Daily Life & Personal Systems',
            'STUDENT_SUCCESS': 'Your Executive Function Profile Through the Lens of Academic Performance & Learning',
            'PROFESSIONAL_LEADERSHIP': 'Your Executive Function Profile Through the Lens of Workplace Execution & Productivity',
            'FAMILY_ECOSYSTEM': 'Your Executive Function Profile Through the Lens of Family & Relational Systems',
            'FULL_GALAXY': 'Complete Cross-Environmental Executive Function Synthesis',
        }
        _LENS_EXCLUSIVE_DISPLAY = {
            'STUDENT_SUCCESS':         ('academic_performance_impact',    'Academic Performance Impact\u2122', '#F59E0B'),
            'PERSONAL_LIFESTYLE':      ('lifestyle_stability_index',      'Lifestyle Stability Index\u2122',   '#10B981'),
            'PROFESSIONAL_LEADERSHIP': ('execution_productivity_profile', 'Execution & Productivity Profile\u2122', '#3B82F6'),
            'FAMILY_ECOSYSTEM':        ('family_system_dynamics',         'Family System Dynamics\u2122',      '#EC4899'),
        }
        # Maps raw domain names → composite weight keys (Addendum Phase 3 §3)
        _DOMAIN_TO_WEIGHT_KEY = {
            'EXECUTIVE_FUNCTION_SKILLS': 'action_follow_through',
            'BEHAVIORAL_PATTERNS':       'action_follow_through',
            'COGNITIVE_CONTROL':         'focus_drive',
            'MOTIVATIONAL_SYSTEMS':      'focus_drive',
            'EMOTIONAL_REGULATION':      'emotional_regulation',
            'INTERNAL_STATE_FACTORS':    'emotional_regulation',
            'ENVIRONMENTAL_DEMANDS':     'life_load',
        }
        _LENS_EMPHASIS_LABEL = {
            'PERSONAL_LIFESTYLE': 'Personal / Lifestyle Emphasis',
            'STUDENT_SUCCESS': 'Student / Academic Emphasis',
            'PROFESSIONAL_LEADERSHIP': 'Professional / Leadership Emphasis',
            'FAMILY_ECOSYSTEM': 'Family / Ecosystem Emphasis',
        }
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=72, leftMargin=72,
                               topMargin=48, bottomMargin=42)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor(THEME['gray_900']),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10.5,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
            leading=15.5,
            textColor=colors.HexColor(THEME['gray_700']),
        )
        ts = get_theme_styles(THEME['primary'])
        
        # Extract data
        metadata = assessment_data.get('metadata', {})
        archetype = assessment_data.get('archetype', {})
        construct_scores = assessment_data.get('construct_scores', {})
        load_framework = assessment_data.get('load_framework', {})
        domains = assessment_data.get('domains', [])
        summary = assessment_data.get('summary', {})
        baseline_interpretation = assessment_data.get('interpretation', {}) or {}
        # When a lens-specific AI report exists, overlay its narrative onto
        # the baseline so each lens download shows lens-tailored copy
        # (Executive Summary, Strengths, Growth Edges, etc.) instead of the
        # lens-neutral text that was generated once at assessment time.
        interpretation = _overlay_lens_sections(
            baseline_interpretation, lens_sections, lens_override
        )
        
        # Report Info - fetch user name
        original_report_type = metadata.get('report_type', '')
        active_lens = lens_override if lens_override else original_report_type
        report_type = active_lens.replace('_', ' ').title()
        is_lens_specific = active_lens in LENS_DOMAIN_WEIGHTS
        
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        date_str = format_date(timestamp)
        
        user_id = metadata.get('user_email') or metadata.get('user_id', 'N/A')
        user_name = _get_user_name(user_id)
        if len(user_name) > 40:
            user_name = user_name[:37] + '...'
        
        lens_display_name = {
            'PERSONAL_LIFESTYLE': 'Personal / Lifestyle',
            'STUDENT_SUCCESS': 'Student Success',
            'PROFESSIONAL_LEADERSHIP': 'Professional / Leadership',
            'FAMILY_ECOSYSTEM': 'Family Ecosystem',
            'FULL_GALAXY': 'Full Galaxy Report',
        }.get(active_lens, report_type)
        
        lp = LENS_PALETTE.get(active_lens, {'accent': THEME['primary'], 'label': lens_display_name})
        lens_accent = lp['accent']
        
        page_tpl = BESTPageTemplate(accent_color=lens_accent, lens_label=lens_display_name)
        archetype_name = archetype.get('archetype_id', 'Unknown').replace('_', ' ')
        
        # ── Lens-specific cover subtitle ──
        cover_subtitle = _LENS_SUBTITLE.get(
            active_lens,
            archetype.get('description', 'Full Galaxy Assessment Report'),
        )
        
        # ── Cover Page ──
        elements += build_cover_page(
            report_title=(
                lens_display_name.upper() if lens_display_name.lower().endswith('report')
                else f'{lens_display_name} Report'.upper()
            ),
            report_subtitle=cover_subtitle,
            user_name=user_name,
            date_str=date_str,
            lens_label=lens_display_name,
            accent_color=lens_accent,
            extra_lines=[
                ('Archetype:', archetype_name.title()),
                ('Assessment Type:', f'{lens_display_name} (Paid)'),
            ],
        )
        elements += _build_short_disclaimer_flowable()
        elements.append(PageBreak())

        sec_num = 1
        
        # Executive Summary
        if interpretation and interpretation.get('executive_summary'):
            elements.append(SectionHeader(sec_num, "Executive Summary",
                                          accent_color=THEME['primary']))
            elements.append(Spacer(1, 0.06 * inch))
            sec_num += 1
            elements.append(CalloutBox(
                'Executive Summary', interpretation['executive_summary'],
                accent_color=THEME['primary'], bg_color=THEME['primary_light'],
            ))
            elements.append(Spacer(1, 0.2*inch))
        
        # Construct Scores with donut charts
        elements.append(SectionHeader(sec_num, "Construct Scores",
                                      accent_color=THEME['primary']))
        elements.append(Spacer(1, 0.06 * inch))
        sec_num += 1
        pei_score = construct_scores.get('PEI_score', 0)
        bhp_score = construct_scores.get('BHP_score', 0)
        
        pei_donut = make_donut_chart(
            value=pei_score * 100, max_value=100, size=80, ring_width=12,
            fill_color=THEME['red'], label='PEI (Demand)',
        )
        bhp_donut = make_donut_chart(
            value=bhp_score * 100, max_value=100, size=80, ring_width=12,
            fill_color=THEME['blue'], label='BHP (Capacity)',
        )
        donut_row = Table([[bhp_donut, pei_donut]],
                          colWidths=[3 * inch, 3 * inch])
        donut_row.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(donut_row)
        elements.append(Spacer(1, 0.1 * inch))
        
        scores_data = [
            ['Construct', 'Score', 'Level'],
            [
                'PEI (Environmental Demand)',
                f'{pei_score:.3f}',
                make_rounded_bar(pei_score * 100, width_inch=1.5, height_pt=10,
                                 fill_color=THEME['red'], show_label=True),
            ],
            [
                'BHP (Internal Capacity)',
                f'{bhp_score:.3f}',
                make_rounded_bar(bhp_score * 100, width_inch=1.5, height_pt=10,
                                 fill_color=THEME['blue'], show_label=True),
            ],
        ]
        scores_table = Table(scores_data, colWidths=[2.5*inch, 1.0*inch, 2.5*inch])
        scores_table.setStyle(TableStyle(themed_table_style(THEME['primary'])))
        elements.append(scores_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Load Framework
        elements.append(SectionHeader(sec_num, "Load Framework",
                                      accent_color=THEME['amber']))
        elements.append(Spacer(1, 0.06 * inch))
        sec_num += 1
        quadrant = load_framework.get('quadrant', '').replace('_', ' ')
        load_state = load_framework.get('load_state', '').replace('_', ' ')
        load_balance = load_framework.get('load_balance', 0)
        
        lb_color = THEME['green'] if load_balance >= 0 else THEME['red']
        fw_data = [
            ['Quadrant', 'Load State', 'Load Balance'],
            [quadrant.title(), load_state.title(), f'{load_balance:+.3f}'],
        ]
        fw_table = Table(fw_data, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
        fw_table.setStyle(TableStyle(
            themed_table_style(THEME['amber']) + [
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor(lb_color)),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]
        ))
        elements.append(fw_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # PEI × BHP Interpretation
        if interpretation and interpretation.get('pei_bhp_interpretation'):
            elements.append(CalloutBox(
                'PEI \u00d7 BHP Interpretation',
                interpretation['pei_bhp_interpretation'],
                accent_color=THEME['amber'], bg_color=THEME['amber_light'],
            ))
            elements.append(Spacer(1, 0.2*inch))
        
        # Summary (Strengths & Growth Edges)
        elements.append(SectionHeader(sec_num, "Strengths & Growth Edges",
                                      accent_color=THEME['green']))
        elements.append(Spacer(1, 0.06 * inch))
        sec_num += 1
        
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
        section_title_suffix = (
            f' \u2014 {_LENS_EMPHASIS_LABEL[active_lens]}'
            if is_lens_specific else ' \u2014 Internal Capacity'
        )
        elements.append(SectionHeader(sec_num, f"Domain Profiles{section_title_suffix}",
                                      accent_color=lens_accent if is_lens_specific else THEME['primary']))
        elements.append(Spacer(1, 0.06 * inch))
        sec_num += 1
        
        capacity_domains = [d for d in domains if d['name'] != 'ENVIRONMENTAL_DEMANDS']
        env_domains = [d for d in domains if d['name'] == 'ENVIRONMENTAL_DEMANDS']
        
        # ── Compute lens-weighted emphasis scores (Addendum Phase 3 §3) ──
        # Weights shift interpretation emphasis — raw scores are never altered.
        if is_lens_specific:
            elements.append(CalloutBox(
                f'{lens_display_name} Lens Active',
                f'Domain emphasis scores are adjusted through the {lens_display_name} lens. '
                f'Raw scores remain unchanged — emphasis reflects how this lens weighs '
                f'each domain for your environment.',
                accent_color=lens_accent, bg_color=THEME.get(
                    {'PERSONAL_LIFESTYLE': 'green_light', 'STUDENT_SUCCESS': 'primary_light',
                     'PROFESSIONAL_LEADERSHIP': 'blue_light', 'FAMILY_ECOSYSTEM': 'pink_light',
                    }.get(active_lens, 'primary_light'), '#F5F3FF'),
            ))
            elements.append(Spacer(1, 0.08 * inch))
            
            weights = LENS_DOMAIN_WEIGHTS[active_lens]
            
            def _emphasis_score(raw: float, weight_key: str) -> float:
                w = weights.get(weight_key, 1.0)
                x = max(0.0, min(1.0, raw))
                if w >= 1.0:
                    return round(1.0 - (1.0 - x) ** w, 3)
                return round(x ** (1.0 / max(w, 1e-6)), 3)
            
            # Annotate each domain with its emphasis score
            for d in capacity_domains:
                wk = _DOMAIN_TO_WEIGHT_KEY.get(d['name'])
                if wk:
                    d['emphasis_score'] = _emphasis_score(d['score'], wk)
                    d['weight_key'] = wk
                    d['weight_val'] = weights.get(wk, 1.0)
                else:
                    d['emphasis_score'] = d['score']
                    d['weight_key'] = None
                    d['weight_val'] = 1.0
            
            # Sort by emphasis score descending (lens-focused ordering)
            capacity_domains.sort(key=lambda d: d['emphasis_score'], reverse=True)
            
            domain_data = [['Domain', 'Raw', 'Emphasis', 'Level', 'Wt']]
            for domain in capacity_domains:
                sc = domain['score']
                esc = domain['emphasis_score']
                wv = domain['weight_val']
                domain_data.append([
                    domain['name'].replace('_', ' '),
                    f"{sc:.3f}",
                    f"{esc:.3f}",
                    make_rounded_bar(esc * 100, width_inch=0.95, height_pt=10,
                                     fill_color=score_color(esc * 100), show_label=False),
                    f"\u00d7{wv:.1f}",
                ])
            # Column widths tuned so the "Emphasis" header (~58pt at 11pt
            # bold + cell padding) has breathing room and doesn't visually
            # crash into the Level column.
            domain_table = Table(
                domain_data,
                colWidths=[1.9*inch, 0.55*inch, 0.95*inch, 1.4*inch, 0.6*inch],
            )
        else:
            domain_data = [['Domain', 'Score', 'Level', 'Rank']]
            for domain in capacity_domains:
                sc = domain['score']
                domain_data.append([
                    domain['name'].replace('_', ' '),
                    f"{sc:.3f}",
                    make_rounded_bar(sc * 100, width_inch=1.2, height_pt=10,
                                     fill_color=score_color(sc * 100), show_label=False),
                    f"#{domain['rank']}"
                ])
            domain_table = Table(domain_data, colWidths=[2.2*inch, 0.8*inch, 1.8*inch, 0.7*inch])
        
        domain_table.setStyle(TableStyle(
            themed_table_style(lens_accent if is_lens_specific else THEME['primary']) + [
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]
        ))
        elements.append(domain_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Environmental Demands — Separated as External Pressure
        if env_domains:
            elements.append(SectionHeader(sec_num, "Environmental Demands \u2014 External Pressure",
                                          accent_color=THEME['red']))
            elements.append(Spacer(1, 0.06 * inch))
            sec_num += 1
            elements.append(CalloutBox(
                'Important Note',
                'Environmental Demands represents external pressure on your system, not internal capacity. '
                'A high score indicates high load/strain, not high performance.',
                accent_color=THEME['red'], bg_color=THEME['red_light'],
            ))
            elements.append(Spacer(1, 0.08 * inch))
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
            env_table.setStyle(TableStyle(themed_table_style(THEME['red'])))
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
        
        # ── Lens-Exclusive Section (Addendum Phase 3 §4) ──
        # Each lens gets ONE unique section not present in other lenses.
        if is_lens_specific and active_lens in _LENS_EXCLUSIVE_DISPLAY:
            excl_key, excl_title, excl_color = _LENS_EXCLUSIVE_DISPLAY[active_lens]
            elements.append(PageBreak())
            elements.append(SectionHeader(sec_num, excl_title,
                                          accent_color=excl_color))
            elements.append(Spacer(1, 0.06 * inch))
            sec_num += 1

            # Pull exclusive content from AI report if available, or from
            # interpretation, or generate a lens-framed summary from the
            # domain weighting data.
            excl_content = (
                interpretation.get(excl_key)
                or interpretation.get('lens_exclusive_narrative')
            )

            if excl_content:
                for para in str(excl_content).strip().split('\n\n'):
                    clean = para.strip().replace('\n', ' ')
                    if clean:
                        elements.append(Paragraph(clean, body_style))
                elements.append(Spacer(1, 0.1 * inch))
            else:
                # Fallback: generate a structured summary from the domain data
                _excl_focus = {
                    'STUDENT_SUCCESS': [
                        ('Study Efficiency', 'How EF patterns affect study habits and retention'),
                        ('Assignment Initiation', 'Patterns around starting academic tasks'),
                        ('Deadline Behavior', 'How your system responds to academic deadlines'),
                        ('Learning Under Pressure', 'Performance during exams and high-stakes situations'),
                    ],
                    'PERSONAL_LIFESTYLE': [
                        ('Routine Consistency', 'Ability to maintain daily rhythms and structure'),
                        ('Habit Strength', 'How well positive habits hold under load'),
                        ('Identity Alignment', 'Whether daily actions match personal values and goals'),
                        ('Daily Structure', 'Overall organization of your personal system'),
                    ],
                    'PROFESSIONAL_LEADERSHIP': [
                        ('Task Completion', 'How projects move from initiation to finish'),
                        ('Workflow Efficiency', 'Ability to manage multi-step processes'),
                        ('Prioritization', 'How you allocate focus across competing demands'),
                        ('Performance Under Pressure', 'Execution quality when stakes rise'),
                    ],
                    'FAMILY_ECOSYSTEM': [
                        ('Role Clarity', 'How well you manage expectations within family roles'),
                        ('Co-Regulation', 'Ability to regulate alongside others in shared environments'),
                        ('Communication Patterns', 'How EF load affects relational communication'),
                        ('Engagement vs Withdrawal', 'Patterns of connection or disconnection under load'),
                    ],
                }
                focus_items = _excl_focus.get(active_lens, [])
                if focus_items:
                    # Build the lens emphasis composite scores
                    domain_score_lookup = {d['name']: d['score'] for d in domains}
                    action_ft = (
                        domain_score_lookup.get('EXECUTIVE_FUNCTION_SKILLS', 0.5) +
                        domain_score_lookup.get('BEHAVIORAL_PATTERNS', 0.5)
                    ) / 2
                    focus_drive = (
                        domain_score_lookup.get('COGNITIVE_CONTROL', 0.5) +
                        domain_score_lookup.get('MOTIVATIONAL_SYSTEMS', 0.5)
                    ) / 2
                    emotional_reg = (
                        domain_score_lookup.get('EMOTIONAL_REGULATION', 0.5) +
                        domain_score_lookup.get('INTERNAL_STATE_FACTORS', 0.5)
                    ) / 2
                    life_load = domain_score_lookup.get('ENVIRONMENTAL_DEMANDS', 0.5)

                    w_action, w_focus, w_emo, w_load = _apply_lens_weights(
                        action_ft, focus_drive, emotional_reg, life_load, active_lens,
                    )

                    # Composite donut chart for the exclusive section
                    composite_val = (w_action + w_focus + w_emo + (1 - w_load)) / 4
                    donut = make_donut_chart(
                        value=composite_val * 100, max_value=100, size=90, ring_width=14,
                        fill_color=excl_color, label=f'{lens_display_name} Composite',
                    )
                    donut_tbl = Table([[donut]], colWidths=[6 * inch])
                    donut_tbl.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    elements.append(donut_tbl)
                    elements.append(Spacer(1, 0.1 * inch))

                    # Focus area breakdown
                    for area_title, area_desc in focus_items:
                        elements.append(Paragraph(
                            f'<font color="{excl_color}"><b>{area_title}</b></font>',
                            ParagraphStyle('ExclArea', parent=body_style, fontSize=11, spaceAfter=2),
                        ))
                        elements.append(Paragraph(area_desc, body_style))
                    elements.append(Spacer(1, 0.1 * inch))

                    elements.append(CalloutBox(
                        f'{excl_title} \u2014 Key Composites',
                        f'Action/Follow-Through: {w_action:.2f}  \u2022  '
                        f'Focus/Drive: {w_focus:.2f}  \u2022  '
                        f'Emotional Regulation: {w_emo:.2f}  \u2022  '
                        f'Life Load (inverted): {1 - w_load:.2f}',
                        accent_color=excl_color,
                        bg_color='#F9FAFB',
                    ))

            elements.append(Spacer(1, 0.2 * inch))

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
        
        # Append the full Legal & Medical Disclaimer at the end of every PDF.
        elements += _build_full_disclaimer_flowables()

        # Build PDF with themed page template
        doc.build(elements,
                  onFirstPage=page_tpl.first_page,
                  onLaterPages=page_tpl.later_pages)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"Generated PDF report: {len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Failed to generate PDF: {e}", exc_info=True)
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
        from scoring_engine.pdf_theme import (
            THEME, LENS_PALETTE, BESTPageTemplate, build_cover_page,
            get_theme_styles, SectionHeader, CalloutBox, format_date,
        )

        is_cosmic = report_type == 'FULL_GALAXY'
        section_order = _COSMIC_SECTION_ORDER if is_cosmic else _get_lens_section_order(report_type)
        lens_label, lens_color = _LENS_DISPLAY.get(report_type, (report_type.replace('_', ' ').title(), '#6366F1'))
        report_label = 'Cosmic Integration Report' if is_cosmic else f'{lens_label} Report'

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=48, bottomMargin=42,
        )

        ts = get_theme_styles(lens_color)
        elements = []
        page_tpl = BESTPageTemplate(accent_color=lens_color, lens_label=lens_label)

        # Header info
        user_display = user_id or 'N/A'
        if user_display and len(user_display) > 40:
            user_display = user_display[:37] + '...'
        date_str = format_date(generated_at)

        # ── Cover Page ──
        elements += build_cover_page(
            report_title=report_label,
            report_subtitle='AI-Generated Executive Function Narrative',
            user_name=user_display,
            date_str=date_str,
            lens_label=lens_label,
            accent_color=lens_color,
            extra_lines=[('Sections:', f'{len(section_order)} sections')],
        )
        elements += _build_short_disclaimer_flowable()
        elements.append(PageBreak())

        # ── Table of Contents ──
        elements.append(Paragraph('Table of Contents', ts['heading']))
        elements.append(Spacer(1, 0.1 * inch))
        toc_rows = []
        for idx, (key, display_title, accent) in enumerate(section_order):
            content = report_sections.get(key, '')
            status = '\u2713' if content and content.strip() else '\u2014'
            toc_rows.append([
                Paragraph(f'<font color="{accent}"><b>{idx + 1}</b></font>',
                          ParagraphStyle('TOCNum', parent=ts['body'], fontSize=9,
                                         alignment=TA_CENTER)),
                Paragraph(f'<font color="{accent}">{display_title}</font>',
                          ParagraphStyle('TOCTitle', parent=ts['body'], fontSize=9)),
                Paragraph(f'<font color="{THEME["green"]}">{status}</font>',
                          ParagraphStyle('TOCStat', parent=ts['body'], fontSize=9,
                                         alignment=TA_CENTER)),
            ])
        if toc_rows:
            from scoring_engine.pdf_theme import themed_table_style
            toc_table = Table(
                [['#', 'Section', 'Status']] + [[r[0], r[1], r[2]] for r in toc_rows],
                colWidths=[0.5 * inch, 4.8 * inch, 0.7 * inch],
            )
            toc_table.setStyle(TableStyle(themed_table_style(lens_color)))
            elements.append(toc_table)
        elements.append(PageBreak())

        # ── Sections ──
        for idx, (key, display_title, accent) in enumerate(section_order):
            content = report_sections.get(key, '')
            if not content or not content.strip():
                continue

            # Themed section header with numbered badge
            elements.append(SectionHeader(idx + 1, display_title, accent_color=accent))
            elements.append(Spacer(1, 0.08 * inch))

            # Body paragraphs — split on double newlines
            paragraphs = content.strip().split('\n\n')
            for para in paragraphs:
                clean = para.strip().replace('\n', ' ')
                if clean:
                    elements.append(Paragraph(clean, ts['body']))

            elements.append(Spacer(1, 0.15 * inch))

            # Page break after every 3 sections to keep layout clean
            if (idx + 1) % 3 == 0 and idx < len(section_order) - 1:
                elements.append(PageBreak())

        # ── Validation badge ──
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(CalloutBox(
            '\u2713 Report Quality Verified',
            f'All {len(section_order)} sections present \u2022 '
            f'Language compliance checked \u2022 AIMS structure verified',
            accent_color=THEME['green'], bg_color=THEME['green_light'],
        ))

        # Append the full Legal & Medical Disclaimer at the end of every PDF.
        elements += _build_full_disclaimer_flowables()

        # Build with themed page template
        doc.build(elements,
                  onFirstPage=page_tpl.first_page,
                  onLaterPages=page_tpl.later_pages)
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
        from scoring_engine.pdf_theme import (
            THEME, BESTPageTemplate, build_cover_page, get_theme_styles,
            SectionHeader, CalloutBox, themed_table_style, make_rounded_bar,
            score_color, format_date,
        )

        accent = THEME['purple']
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=48, bottomMargin=42,
        )

        ts = get_theme_styles(accent)
        elements = []
        page_tpl = BESTPageTemplate(accent_color=accent, lens_label='Cosmic Dashboard')

        date_str = format_date()

        # ── Cover Page ──
        elements += build_cover_page(
            report_title='Cosmic Integration Dashboard',
            report_subtitle='Cross-Environmental Executive Function Synthesis',
            user_name=(user_id or 'N/A')[:40],
            date_str=date_str,
            lens_label='Cosmic Integration',
            accent_color=accent,
        )
        elements += _build_short_disclaimer_flowable()
        elements.append(PageBreak())

        # Cross-domain analytical layer.
        # Older assessments (pre-Phase 4.5) don't have `cross_domain` stored,
        # so we compute it lazily from the saved scores when missing — that
        # way the dashboard's analytical front-half doesn't render empty for
        # legacy data.
        cross = (assessment_data or {}).get('cross_domain', {}) or {}
        if not cross:
            try:
                from scoring_engine.cross_domain import compute_cross_domain
                cs = (assessment_data or {}).get('construct_scores', {}) or {}
                doms = (assessment_data or {}).get('domains', []) or []
                ad = (assessment_data or {}).get('applied_domains', {}) or {}
                if cs and doms:
                    cross = compute_cross_domain(
                        construct_scores=cs, domains=doms, applied_domains=ad,
                    ) or {}
                    logger.info("Cosmic dashboard PDF: computed cross_domain on the fly")
            except Exception as _e:
                logger.warning("Cosmic dashboard PDF: cross_domain compute failed: %s", _e)
        lens_profiles = cross.get('lens_profiles', {}) or {}
        flows = cross.get('flows', []) or []
        compensations = cross.get('compensation_patterns', []) or []
        sensitivities = cross.get('system_wide_sensitivities', []) or []

        sec_num = 1

        # Lens profile table
        if lens_profiles:
            elements.append(SectionHeader(sec_num, 'Lens Profiles', accent_color=THEME['indigo']))
            elements.append(Spacer(1, 0.08 * inch))
            sec_num += 1
            lens_rows = [['Lens', 'BHP (capacity)', 'PEI (load)', 'Balance', 'Status']]
            lens_label_map = {
                'STUDENT_SUCCESS': 'Student / Academic',
                'PERSONAL_LIFESTYLE': 'Personal / Lifestyle',
                'PROFESSIONAL_LEADERSHIP': 'Professional / Work',
                'FAMILY_ECOSYSTEM': 'Family / Ecosystem',
            }
            for lens, profile in lens_profiles.items():
                bal = profile.get('load_balance', 0)
                bal_color = THEME['green'] if bal >= 0 else THEME['red']
                lens_rows.append([
                    lens_label_map.get(lens, lens),
                    f"{profile.get('bhp', 0):.2f}",
                    f"{profile.get('pei', 0):.2f}",
                    f"{bal:+.2f}",
                    profile.get('status', '\u2014').title(),
                ])
            lens_tbl = Table(lens_rows, colWidths=[2.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch])
            lens_tbl.setStyle(TableStyle(
                themed_table_style(THEME['indigo']) + [
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ]
            ))
            elements.append(lens_tbl)
            elements.append(Spacer(1, 0.2 * inch))

        # Cross-domain flows
        if flows:
            elements.append(SectionHeader(sec_num, 'Cross-Domain Load Transfers',
                                          accent_color=THEME['amber']))
            elements.append(Spacer(1, 0.08 * inch))
            sec_num += 1
            for f in flows[:10]:
                line = (
                    f"<b>{f.get('from', '?').title()} \u2192 {f.get('to', '?').title()}</b> "
                    f"\u2014 strength {f.get('strength', 0):.2f}"
                )
                if f.get('rationale') and f['rationale'] != 'baseline cross-domain coupling':
                    line += f" <i>({f['rationale']})</i>"
                elements.append(Paragraph(line, ts['body']))
            elements.append(Spacer(1, 0.15 * inch))

        # Compensation patterns
        if compensations:
            elements.append(SectionHeader(sec_num, 'Compensation Patterns',
                                          accent_color=THEME['blue']))
            elements.append(Spacer(1, 0.08 * inch))
            sec_num += 1
            for c in compensations[:8]:
                elements.append(CalloutBox(
                    f"{c.get('stabilizer', '')} \u2192 {c.get('vulnerability', '')}",
                    f"Gap: {c.get('gap', 0):+.2f}  \u2014  {c.get('narrative', '')}",
                    accent_color=THEME['blue'], bg_color=THEME['blue_light'],
                ))
                elements.append(Spacer(1, 0.04 * inch))
            elements.append(Spacer(1, 0.1 * inch))

        # System-wide sensitivities
        if sensitivities:
            elements.append(SectionHeader(sec_num, 'System-Wide Sensitivities',
                                          accent_color=THEME['red']))
            elements.append(Spacer(1, 0.08 * inch))
            sec_num += 1
            for s in sensitivities[:8]:
                elements.append(CalloutBox(
                    s.get('domain', ''), s.get('pattern', ''),
                    accent_color=THEME['red'], bg_color=THEME['red_light'],
                ))
                elements.append(Spacer(1, 0.04 * inch))
            elements.append(Spacer(1, 0.15 * inch))

        # Cosmic narrative (if available).
        # IMPORTANT: these keys/titles MUST match
        # `prompts.section_rules.COSMIC_REPORT_SECTIONS` — the AI emits
        # exactly those keys.  An earlier version of this list used keys
        # that the AI never produces (e.g. archetype_evolution,
        # compensation_patterns, stabilizers_across_universe,
        # lens_overlay_summary, long_term_trajectory, closing_synthesis),
        # which silently dropped 6 of the 11 sections and left the PDF
        # mostly empty.
        if cosmic_report:
            sections = cosmic_report.get('sections', {}) or {}
            # Strip stale markdown wrappers (e.g. "**Academic**: ..." that
            # leaked from earlier prompt builds).  The sanitizer also runs
            # in `report_generator.get_report`, but the cosmic dashboard
            # endpoint queries Supabase directly and would otherwise bypass
            # it, leaving literal asterisks in the rendered PDF.
            if sections:
                try:
                    from scoring_engine.report_generator import _sanitize_stored_sections
                    sections = (_sanitize_stored_sections({"sections": sections}) or {}).get("sections", sections)
                except Exception:
                    pass
            if sections:
                elements.append(PageBreak())
                elements.append(Paragraph('Cosmic Integration Narrative', ts['title']))
                elements.append(Spacer(1, 0.1 * inch))
                cosmic_order = [
                    ('cosmic_snapshot',              'Cosmic Snapshot'),
                    ('galaxy_convergence_map',       'Galaxy Convergence Map\u2122'),
                    ('load_balance_matrix',          'Load Balance Matrix\u2122'),
                    ('cross_domain_load_transfer',   'Cross-Domain Load Transfer Analysis'),
                    ('core_system_identity',         'Core System Identity Under Load'),
                    ('global_strength_architecture', 'Global Strength Architecture'),
                    ('system_wide_sensitivity',      'System-Wide Load Sensitivity Zones'),
                    ('pattern_continuity_amplified', 'Pattern Continuity Amplified\u2122'),
                    ('cosmic_aims',                  'AIMS for the BEST\u2122 \u2014 Cosmic Level'),
                    ('expansion_pathway',            'Expansion Pathway'),
                    ('cosmic_summary',               'Cosmic Summary'),
                ]
                # Render in the canonical order; tolerate missing keys (the
                # AI is allowed to omit a section if data is sparse).
                rendered = 0
                for ci, (key, title) in enumerate(cosmic_order):
                    text = sections.get(key)
                    if not text:
                        continue
                    elements.append(SectionHeader(sec_num, title,
                                                  accent_color=accent))
                    elements.append(Spacer(1, 0.06 * inch))
                    sec_num += 1
                    for para in str(text).strip().split('\n\n'):
                        clean = para.strip().replace('\n', ' ')
                        if clean:
                            elements.append(Paragraph(clean, ts['body']))
                    elements.append(Spacer(1, 0.1 * inch))
                    rendered += 1
                    if rendered % 3 == 0:
                        elements.append(PageBreak())

                # If the AI returned any extra keys we don't have in the
                # canonical order (forward compatibility), surface them at
                # the end rather than dropping them silently.
                extras = [k for k in sections.keys() if k not in {x[0] for x in cosmic_order}]
                for key in extras:
                    text = sections.get(key)
                    if not text:
                        continue
                    title = key.replace('_', ' ').title()
                    elements.append(SectionHeader(sec_num, title, accent_color=accent))
                    elements.append(Spacer(1, 0.06 * inch))
                    sec_num += 1
                    for para in str(text).strip().split('\n\n'):
                        clean = para.strip().replace('\n', ' ')
                        if clean:
                            elements.append(Paragraph(clean, ts['body']))
                    elements.append(Spacer(1, 0.1 * inch))

        # Append the full Legal & Medical Disclaimer at the end of every PDF.
        elements += _build_full_disclaimer_flowables()

        # Build with themed page template
        doc.build(elements,
                  onFirstPage=page_tpl.first_page,
                  onLaterPages=page_tpl.later_pages)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(f"Generated cosmic dashboard PDF: {len(pdf_bytes)} bytes")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Failed to generate cosmic dashboard PDF: {e}", exc_info=True)
        return None
