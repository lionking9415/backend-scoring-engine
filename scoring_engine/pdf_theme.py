"""
PDF Theme Module — Reusable branded components for all BEST Galaxy PDFs.

Provides:
  - BESTPageTemplate:  running header stripe + page numbers + footer
  - build_cover_page:  branded cover page with colored blocks
  - make_donut_chart:  ring/donut score visualization
  - make_rounded_bar:  rounded-corner progress bar
  - make_callout_box:  colored left-border insight card
  - make_section_card: section header with accent stripe + number badge
  - THEME:             color palette and font constants
"""

import math
from datetime import datetime
from typing import Optional

from reportlab.graphics.shapes import Drawing, Rect, Circle, Wedge, String, Group, Line
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors as rl_colors
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, HRFlowable, Flowable,
)


# ═══════════════════════════════════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════════════════════════════════

THEME = {
    # Primary brand
    'primary':       '#4F46E5',
    'primary_dark':  '#3730A3',
    'primary_light': '#EEF2FF',
    # Accents
    'purple':        '#7C3AED',
    'purple_light':  '#F5F3FF',
    'indigo':        '#6366F1',
    'blue':          '#2563EB',
    'blue_light':    '#EFF6FF',
    'green':         '#059669',
    'green_light':   '#ECFDF5',
    'amber':         '#D97706',
    'amber_light':   '#FFFBEB',
    'red':           '#DC2626',
    'red_light':     '#FEF2F2',
    'pink':          '#EC4899',
    'pink_light':    '#FDF2F8',
    # Neutral
    'gray_900':      '#111827',
    'gray_800':      '#1F2937',
    'gray_700':      '#374151',
    'gray_600':      '#4B5563',
    'gray_500':      '#6B7280',
    'gray_400':      '#9CA3AF',
    'gray_300':      '#D1D5DB',
    'gray_200':      '#E5E7EB',
    'gray_100':      '#F3F4F6',
    'gray_50':       '#F9FAFB',
    'white':         '#FFFFFF',
}

# Lens-specific palettes
LENS_PALETTE = {
    'STUDENT_SUCCESS':          {'accent': '#6366F1', 'bg': '#EEF2FF', 'label': 'Student Success'},
    'PERSONAL_LIFESTYLE':       {'accent': '#8B5CF6', 'bg': '#F5F3FF', 'label': 'Personal / Lifestyle'},
    'PROFESSIONAL_LEADERSHIP':  {'accent': '#2563EB', 'bg': '#EFF6FF', 'label': 'Professional / Leadership'},
    'FAMILY_ECOSYSTEM':         {'accent': '#059669', 'bg': '#ECFDF5', 'label': 'Family EF Ecosystem'},
    'FULL_GALAXY':              {'accent': '#7C3AED', 'bg': '#F5F3FF', 'label': 'Cosmic Integration'},
}


# ═══════════════════════════════════════════════════════════════════════
# STYLES FACTORY
# ═══════════════════════════════════════════════════════════════════════

def get_theme_styles(accent_color: str = None):
    """Return a dict of ParagraphStyles used across all themed PDFs."""
    accent = accent_color or THEME['primary']
    base = getSampleStyleSheet()

    return {
        'title': ParagraphStyle(
            'ThemeTitle', parent=base['Heading1'],
            fontSize=26, textColor=HexColor(accent),
            spaceAfter=6, alignment=TA_CENTER, fontName='Helvetica-Bold',
            leading=32,
        ),
        'subtitle': ParagraphStyle(
            'ThemeSub', parent=base['Normal'],
            fontSize=12, textColor=HexColor(THEME['gray_500']),
            spaceAfter=18, alignment=TA_CENTER, fontName='Helvetica-Oblique',
            leading=16,
        ),
        'heading': ParagraphStyle(
            'ThemeH2', parent=base['Heading2'],
            fontSize=16, textColor=HexColor(THEME['gray_900']),
            spaceAfter=10, spaceBefore=16, fontName='Helvetica-Bold',
            leading=20,
        ),
        'subheading': ParagraphStyle(
            'ThemeH3', parent=base['Heading3'],
            fontSize=13, textColor=HexColor(THEME['gray_700']),
            spaceAfter=8, spaceBefore=12, fontName='Helvetica-Bold',
            leading=16,
        ),
        'body': ParagraphStyle(
            'ThemeBody', parent=base['BodyText'],
            fontSize=10.5, alignment=TA_JUSTIFY,
            spaceAfter=10, leading=15.5, textColor=HexColor(THEME['gray_700']),
        ),
        'body_small': ParagraphStyle(
            'ThemeBodySm', parent=base['BodyText'],
            fontSize=9, alignment=TA_JUSTIFY,
            spaceAfter=8, leading=13, textColor=HexColor(THEME['gray_600']),
        ),
        'caption': ParagraphStyle(
            'ThemeCaption', parent=base['Normal'],
            fontSize=8, textColor=HexColor(THEME['gray_400']),
            alignment=TA_CENTER, spaceAfter=4,
        ),
        'badge': ParagraphStyle(
            'ThemeBadge', parent=base['Normal'],
            fontSize=8, textColor=HexColor(accent),
            spaceAfter=2, fontName='Helvetica-Bold',
        ),
        'footer': ParagraphStyle(
            'ThemeFooter', parent=base['Normal'],
            fontSize=7.5, textColor=HexColor(THEME['gray_400']),
            alignment=TA_CENTER,
        ),
    }


# ═══════════════════════════════════════════════════════════════════════
# PAGE TEMPLATE — Header stripe + footer with page numbers
# ═══════════════════════════════════════════════════════════════════════

class BESTPageTemplate:
    """Canvas callbacks for running header/footer on every page.

    Usage:
        tpl = BESTPageTemplate(accent_color='#4F46E5', lens_label='Student Success')
        doc.build(elements, onFirstPage=tpl.first_page, onLaterPages=tpl.later_pages)
    """

    def __init__(self, accent_color: str = None, lens_label: str = '',
                 confidential: bool = True):
        self.accent = accent_color or THEME['primary']
        self.lens_label = lens_label
        self.confidential = confidential

    def _draw_header(self, canvas, doc):
        """Thin accent stripe at the top of every page."""
        canvas.saveState()
        page_w, page_h = letter
        # Accent stripe (full width, 4pt high)
        canvas.setFillColor(HexColor(self.accent))
        canvas.rect(0, page_h - 4, page_w, 4, fill=1, stroke=0)
        # Secondary thin line
        canvas.setFillColor(HexColor(THEME['gray_200']))
        canvas.rect(0, page_h - 5.5, page_w, 1, fill=1, stroke=0)
        canvas.restoreState()

    def _draw_footer(self, canvas, doc):
        """Page number + brand footer."""
        canvas.saveState()
        page_w, _ = letter
        y = 24
        # Left: brand
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(HexColor(THEME['gray_400']))
        canvas.drawString(doc.leftMargin, y,
                          "BEST Executive Function Galaxy Assessment\u2122")
        # Center: confidential
        if self.confidential:
            canvas.drawCentredString(page_w / 2, y, "CONFIDENTIAL")
        # Right: page number
        canvas.drawRightString(page_w - doc.rightMargin, y,
                               f"Page {doc.page}")
        # Thin line above footer
        canvas.setStrokeColor(HexColor(THEME['gray_200']))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, y + 10, page_w - doc.rightMargin, y + 10)
        canvas.restoreState()

    def first_page(self, canvas, doc):
        """Cover page — no header, just footer."""
        self._draw_footer(canvas, doc)

    def later_pages(self, canvas, doc):
        """Subsequent pages — header + footer."""
        self._draw_header(canvas, doc)
        self._draw_footer(canvas, doc)


# ═══════════════════════════════════════════════════════════════════════
# COVER PAGE BUILDER
# ═══════════════════════════════════════════════════════════════════════

def build_cover_page(
    report_title: str,
    report_subtitle: str,
    user_name: str,
    date_str: str,
    lens_label: str = '',
    accent_color: str = None,
    extra_lines: list = None,
) -> list:
    """Return a list of Flowables that compose a branded cover page.

    The cover uses colored blocks, a large title, metadata table,
    and a divider — all within the normal platypus flow so they
    respect margins automatically.
    """
    accent = accent_color or THEME['primary']
    styles = get_theme_styles(accent)
    elements = []

    # Top spacer
    elements.append(Spacer(1, 0.8 * inch))

    # Decorative top block
    elements.append(_ColorBlock(
        width=6.5 * inch, height=6, color=accent, radius=3,
    ))
    elements.append(Spacer(1, 0.35 * inch))

    # Brand line
    elements.append(Paragraph(
        "BEST Executive Function Galaxy Assessment\u2122",
        ParagraphStyle('CoverBrand', parent=styles['caption'],
                       fontSize=10, textColor=HexColor(THEME['gray_500']),
                       spaceAfter=12, alignment=TA_CENTER),
    ))

    # Main title
    elements.append(Paragraph(report_title, ParagraphStyle(
        'CoverTitle', parent=styles['title'],
        fontSize=28, spaceAfter=8, leading=34,
    )))

    # Subtitle
    if report_subtitle:
        elements.append(Paragraph(report_subtitle, ParagraphStyle(
            'CoverSubtitle', parent=styles['subtitle'],
            fontSize=13, spaceAfter=20,
        )))

    # Secondary decorative line
    elements.append(_ColorBlock(
        width=2 * inch, height=3, color=accent, radius=1.5,
    ))
    elements.append(Spacer(1, 0.4 * inch))

    # Info box
    info_rows = [
        ['Prepared for:', user_name[:45] if user_name else 'N/A'],
        ['Report Date:', date_str],
    ]
    if lens_label:
        info_rows.append(['Report Lens:', lens_label])
    if extra_lines:
        for lbl, val in extra_lines:
            info_rows.append([lbl, val])

    info_table = Table(info_rows, colWidths=[1.6 * inch, 4.4 * inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), HexColor(THEME['primary_dark'])),
        ('TEXTCOLOR', (1, 0), (1, -1), HexColor(THEME['gray_800'])),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor(THEME['gray_50'])),
        ('ROUNDEDCORNERS', [6, 6, 6, 6]),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor(THEME['gray_200'])),
    ]))
    elements.append(info_table)

    elements.append(Spacer(1, 0.5 * inch))

    # Bottom decorative block
    elements.append(_ColorBlock(
        width=6.5 * inch, height=3, color=THEME['gray_200'], radius=1.5,
    ))

    return elements


# ═══════════════════════════════════════════════════════════════════════
# DONUT / RING CHART
# ═══════════════════════════════════════════════════════════════════════

def make_donut_chart(
    value: float,
    max_value: float = 100,
    size: float = 80,
    ring_width: float = 12,
    fill_color: str = '#4F46E5',
    track_color: str = '#E5E7EB',
    label: str = '',
    show_pct: bool = True,
) -> Drawing:
    """Return a Drawing of a donut/ring chart with optional center label.

    Args:
        value:       current value (e.g. 72)
        max_value:   scale maximum (default 100)
        size:        overall drawing size in points
        ring_width:  thickness of the ring
        fill_color:  active arc color
        track_color: background arc color
        label:       text below center value
        show_pct:    show percentage in center
    """
    d = Drawing(size, size + (16 if label else 0))
    cx, cy = size / 2, size / 2 + (16 if label else 0)
    radius = (size - ring_width) / 2

    pct = max(0.0, min(1.0, value / max_value)) if max_value else 0
    sweep_angle = pct * 360

    # Track (full ring)
    d.add(_arc_wedge(cx, cy, radius, ring_width, 0, 360,
                     HexColor(track_color)))

    # Filled arc
    if sweep_angle > 0.5:
        d.add(_arc_wedge(cx, cy, radius, ring_width, 90, sweep_angle,
                         HexColor(fill_color)))

    # Center text
    if show_pct:
        center_text = f"{int(pct * 100)}%"
        d.add(String(cx, cy - 5, center_text,
                     fontSize=14, fontName='Helvetica-Bold',
                     fillColor=HexColor(fill_color),
                     textAnchor='middle'))

    # Label below
    if label:
        d.add(String(cx, 4, label,
                     fontSize=7, fontName='Helvetica',
                     fillColor=HexColor(THEME['gray_600']),
                     textAnchor='middle'))

    return d


def _arc_wedge(cx, cy, radius, width, start_angle, sweep, color):
    """Create a thick arc using a Wedge with inner radius cutout.

    ReportLab doesn't have a native ring shape, so we approximate
    with an outer wedge minus an inner filled circle.  For simplicity
    we use the Wedge shape which draws a pie-slice, then overlay a
    white circle in the center.
    """
    g = Group()
    outer_r = radius + width / 2
    inner_r = radius - width / 2

    # Full circle case — Wedge with sweep=360 triggers bezierArc
    # division by zero in ReportLab, so we use a Circle instead.
    if sweep >= 359.9:
        g.add(Circle(cx, cy, outer_r, fillColor=color,
                     strokeColor=None, strokeWidth=0))
    elif sweep > 0.5:
        w = Wedge(cx, cy, outer_r,
                  startangledegrees=start_angle,
                  endangledegrees=start_angle - sweep,
                  fillColor=color, strokeColor=None, strokeWidth=0)
        g.add(w)
    else:
        # Near-zero sweep — nothing to draw
        pass

    # Inner circle (mask) — always draw to cut out the ring center
    g.add(Circle(cx, cy, inner_r,
                 fillColor=HexColor('#FFFFFF'),
                 strokeColor=None, strokeWidth=0))
    return g


# ═══════════════════════════════════════════════════════════════════════
# ROUNDED PROGRESS BAR
# ═══════════════════════════════════════════════════════════════════════

def make_rounded_bar(
    pct: float,
    width_inch: float = 2.0,
    height_pt: float = 12,
    fill_color: str = '#4F46E5',
    track_color: str = '#E5E7EB',
    show_label: bool = False,
) -> Drawing:
    """Return a Drawing with a rounded-corner progress bar.

    Args:
        pct:         0–100 fill percentage
        width_inch:  total bar width
        height_pt:   bar height in points
        fill_color:  bar fill
        track_color: bar background
        show_label:  show percentage text to the right of the bar
    """
    value = max(0.0, min(100.0, float(pct) if pct else 0))
    w_pt = width_inch * inch
    label_w = 30 if show_label else 0
    total_w = w_pt + label_w
    d = Drawing(total_w, height_pt)
    r = height_pt / 2  # corner radius

    # Track
    d.add(Rect(0, 0, w_pt, height_pt, rx=r, ry=r,
               fillColor=HexColor(track_color),
               strokeColor=HexColor(THEME['gray_300']),
               strokeWidth=0.3))

    # Fill
    fill_w = w_pt * (value / 100.0)
    if fill_w > 0:
        # Clamp minimum fill width to avoid rendering artifacts
        fill_w = max(fill_w, height_pt)
        fill_w = min(fill_w, w_pt)
        d.add(Rect(0, 0, fill_w, height_pt, rx=r, ry=r,
                    fillColor=HexColor(fill_color),
                    strokeColor=None, strokeWidth=0))

    # Optional label
    if show_label:
        d.add(String(w_pt + 6, height_pt / 2 - 3.5, f"{value:.0f}%",
                      fontSize=8, fontName='Helvetica-Bold',
                      fillColor=HexColor(fill_color),
                      textAnchor='start'))

    return d


# ═══════════════════════════════════════════════════════════════════════
# CALLOUT BOX (insight highlight with left accent border)
# ═══════════════════════════════════════════════════════════════════════

class CalloutBox(Flowable):
    """A card-like box with a thick colored left border and light background.

    Usage:
        elements.append(CalloutBox(
            "When Stable", "Your system operates with clear ...",
            accent_color='#16A34A', bg_color='#ECFDF5',
        ))
    """

    def __init__(self, heading: str, body: str,
                 accent_color: str = '#4F46E5',
                 bg_color: str = '#F9FAFB',
                 width: float = None,
                 border_width: float = 4):
        super().__init__()
        self.heading = heading
        self.body = body
        self.accent_color = accent_color
        self.bg_color = bg_color
        self._width = width or (6.5 * inch)
        self.border_width = border_width
        self._built = None

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        inner_w = self._width - self.border_width - 24  # padding
        # Measure text height
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        styles = getSampleStyleSheet()
        h_style = ParagraphStyle('_cb_h', parent=styles['Normal'],
                                 fontSize=10, fontName='Helvetica-Bold',
                                 textColor=HexColor(self.accent_color),
                                 leading=13)
        b_style = ParagraphStyle('_cb_b', parent=styles['Normal'],
                                 fontSize=9.5, leading=13.5,
                                 textColor=HexColor(THEME['gray_700']))
        h_para = Paragraph(self.heading, h_style)
        b_para = Paragraph(self.body, b_style)
        hw, hh = h_para.wrap(inner_w, availHeight)
        bw, bh = b_para.wrap(inner_w, availHeight)
        self._built = (h_para, hh, b_para, bh)
        self.height = hh + bh + 20  # 10 top + 6 gap + 4 bottom
        return (self._width, self.height)

    def draw(self):
        canvas = self.canv
        h_para, hh, b_para, bh = self._built

        # Background
        canvas.saveState()
        canvas.setFillColor(HexColor(self.bg_color))
        canvas.roundRect(0, 0, self._width, self.height, 4, fill=1, stroke=0)
        canvas.restoreState()

        # Left accent border
        canvas.saveState()
        canvas.setFillColor(HexColor(self.accent_color))
        canvas.roundRect(0, 0, self.border_width, self.height, 2, fill=1, stroke=0)
        canvas.restoreState()

        # Outer border (very subtle)
        canvas.saveState()
        canvas.setStrokeColor(HexColor(THEME['gray_200']))
        canvas.setLineWidth(0.3)
        canvas.roundRect(0, 0, self._width, self.height, 4, fill=0, stroke=1)
        canvas.restoreState()

        # Draw text
        x_offset = self.border_width + 12
        y_cursor = self.height - 10 - hh
        h_para.drawOn(canvas, x_offset, y_cursor)
        y_cursor -= bh + 4
        b_para.drawOn(canvas, x_offset, y_cursor)


# ═══════════════════════════════════════════════════════════════════════
# SECTION HEADER CARD (number badge + accent stripe + title)
# ═══════════════════════════════════════════════════════════════════════

class SectionHeader(Flowable):
    """A section heading with a colored badge, accent underline, and title.

    Renders as:
        [1]  Galaxy Snapshot
        ═══════════════════  (accent colored)
    """

    def __init__(self, number: int, title: str,
                 accent_color: str = '#4F46E5',
                 width: float = None):
        super().__init__()
        self.number = number
        self.title = title
        self.accent_color = accent_color
        self._width = width or (6.5 * inch)
        self.height = 36  # fixed height

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        return (self._width, self.height)

    def draw(self):
        canvas = self.canv

        # Badge circle
        badge_r = 10
        badge_cx = badge_r + 2
        badge_cy = self.height - badge_r - 4
        canvas.saveState()
        canvas.setFillColor(HexColor(self.accent_color))
        canvas.circle(badge_cx, badge_cy, badge_r, fill=1, stroke=0)
        canvas.setFillColor(HexColor('#FFFFFF'))
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawCentredString(badge_cx, badge_cy - 3.5, str(self.number))
        canvas.restoreState()

        # Title text
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 14)
        canvas.setFillColor(HexColor(THEME['gray_900']))
        canvas.drawString(badge_cx + badge_r + 8, badge_cy - 5, self.title)
        canvas.restoreState()

        # Accent underline
        canvas.saveState()
        canvas.setStrokeColor(HexColor(self.accent_color))
        canvas.setLineWidth(2)
        line_y = 2
        canvas.line(0, line_y, self._width * 0.35, line_y)
        # Fade-out extension
        canvas.setStrokeColor(HexColor(THEME['gray_200']))
        canvas.setLineWidth(0.5)
        canvas.line(self._width * 0.35, line_y, self._width, line_y)
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════════
# COLOR BLOCK (decorative horizontal rule)
# ═══════════════════════════════════════════════════════════════════════

class _ColorBlock(Flowable):
    """A thin colored rectangle used as a decorative divider."""

    def __init__(self, width: float, height: float, color: str, radius: float = 0):
        super().__init__()
        self._width = width
        self.height = height
        self.color = color
        self.radius = radius

    def wrap(self, availWidth, availHeight):
        self._width = min(self._width, availWidth)
        return (self._width, self.height)

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(HexColor(self.color))
        if self.radius:
            canvas.roundRect(
                (self.canv._pagesize[0] - self._width) / 2 - 72,  # center
                0, self._width, self.height, self.radius, fill=1, stroke=0,
            )
        else:
            canvas.rect(0, 0, self._width, self.height, fill=1, stroke=0)
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════════
# THEMED TABLE HELPERS
# ═══════════════════════════════════════════════════════════════════════

def themed_table_style(accent: str = None, has_header: bool = True):
    """Return a base TableStyle list for consistently branded tables."""
    accent = accent or THEME['primary']
    cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor(THEME['gray_200'])),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [HexColor(THEME['white']), HexColor(THEME['gray_50'])]),
    ]
    if has_header:
        cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor(accent)),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor(THEME['white'])),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
        ]
    return cmds


def score_color(value: float, inverted: bool = False) -> str:
    """Return a hex color for a 0-100 score value.

    Normal:   >=70 green, >=40 amber, <40 red
    Inverted: >=70 red, >=40 amber, <40 green (for PEI/pressure)
    """
    if inverted:
        if value >= 70:
            return THEME['red']
        return THEME['amber'] if value >= 40 else THEME['green']
    if value >= 70:
        return THEME['green']
    return THEME['amber'] if value >= 40 else THEME['red']


# ═══════════════════════════════════════════════════════════════════════
# UTILITY: format timestamp
# ═══════════════════════════════════════════════════════════════════════

def format_date(ts: str = None) -> str:
    """Parse an ISO timestamp into a display string."""
    if not ts:
        return datetime.now().strftime('%B %d, %Y')
    try:
        return datetime.fromisoformat(
            ts.replace('Z', '+00:00')
        ).strftime('%B %d, %Y at %I:%M %p')
    except Exception:
        return ts[:19] if len(ts) >= 19 else ts
