"""
PDF Service Module — Report PDF Generation (Phase 2)
Generates professional PDF reports from assessment results.

This module handles:
- PDF layout and styling
- Report content formatting
- Chart/graph generation
- PDF file creation and streaming
"""

import io
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


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
            PageBreak, Image
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
        
        # Report Info
        report_type = metadata.get('report_type', '').replace('_', ' ').title()
        timestamp = metadata.get('timestamp', datetime.now().isoformat())
        date_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%B %d, %Y')
        
        # Use user_email if available, otherwise fall back to user_id
        user_display = metadata.get('user_email') or metadata.get('user_id', 'N/A')
        if len(user_display) > 40:
            user_display = user_display[:37] + '...'
        
        info_data = [
            ['Report Type:', report_type],
            ['Generated:', date_str],
            ['User:', user_display]
        ]
        info_table = Table(info_data, colWidths=[2*inch, 4*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6B7280')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
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
        elements.append(Paragraph("Summary", heading_style))
        
        strengths = summary.get('top_strengths', [])
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
        
        # Domain Profiles
        elements.append(Paragraph("Domain Profiles", heading_style))
        
        domain_data = [['Domain', 'Score', 'Classification', 'Rank']]
        for domain in domains:
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
        elements.append(PageBreak())
        
        # Interpretation Sections
        if interpretation:
            elements.append(Paragraph("Detailed Interpretation", heading_style))
            
            sections = [
                ('Quadrant Analysis', 'quadrant_interpretation'),
                ('Load State Analysis', 'load_interpretation'),
                ('Strengths Analysis', 'strengths_analysis'),
                ('Growth Edges Analysis', 'growth_edges_analysis'),
            ]
            
            for section_title, section_key in sections:
                if interpretation.get(section_key):
                    elements.append(Paragraph(section_title, 
                                            ParagraphStyle('SubHeading',
                                                         parent=styles['Heading3'],
                                                         fontSize=13,
                                                         textColor=colors.HexColor('#4B5563'),
                                                         spaceAfter=8,
                                                         spaceBefore=12,
                                                         fontName='Helvetica-Bold')))
                    elements.append(Paragraph(interpretation[section_key], body_style))
                    elements.append(Spacer(1, 0.15*inch))
        
        # AIMS Plan
        if interpretation and interpretation.get('aims_plan'):
            elements.append(PageBreak())
            elements.append(Paragraph("AIMS for the BEST™ Plan", heading_style))
            
            aims_plan = interpretation['aims_plan']
            for phase, content in aims_plan.items():
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
