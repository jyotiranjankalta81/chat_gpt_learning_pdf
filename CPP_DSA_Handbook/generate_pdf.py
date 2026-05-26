#!/usr/bin/env python3
"""
Generate a comprehensive PDF from all Markdown sections of the C++ DSA Handbook.
Uses ReportLab for PDF generation with proper formatting.
"""

import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ─── Page Setup ───────────────────────────────────────────────────────────────
OUTPUT_FILE = "CPP_DSA_Interview_Handbook.pdf"

SECTIONS = [
    "README.md",
    "Section1_CPP_Fundamentals.md",
    "Section2_STL_Deep_Dive.md",
    "Section3_DSA_Foundations.md",
    "Section4_DSA_Patterns.md",
    "Section5_Competitive_Programming.md",
    "Section6_Interview_Preparation.md",
    "Section7_Monthly_Roadmap.md",
]

# ─── Color Palette ────────────────────────────────────────────────────────────
C_DARK_BG    = colors.HexColor("#1e1e2e")
C_HEADER_BG  = colors.HexColor("#313244")
C_CODE_BG    = colors.HexColor("#2a2a3e")
C_ACCENT     = colors.HexColor("#cba6f7")   # Purple
C_ACCENT2    = colors.HexColor("#89dceb")   # Cyan
C_H1         = colors.HexColor("#cba6f7")
C_H2         = colors.HexColor("#89b4fa")   # Blue
C_H3         = colors.HexColor("#a6e3a1")   # Green
C_H4         = colors.HexColor("#f9e2af")   # Yellow
C_TEXT       = colors.HexColor("#cdd6f4")
C_CODE_TEXT  = colors.HexColor("#a6e3a1")   # Green for code
C_CODE_COMM  = colors.HexColor("#6c7086")   # Comments
C_TABLE_HDR  = colors.HexColor("#45475a")
C_TABLE_ALT  = colors.HexColor("#313244")
C_HR         = colors.HexColor("#585b70")
C_WHITE      = colors.white

# ─── Styles ───────────────────────────────────────────────────────────────────
def make_styles():
    styles = {}

    styles['h1'] = ParagraphStyle(
        'H1', fontName='Helvetica-Bold', fontSize=22,
        textColor=C_H1, spaceAfter=10, spaceBefore=20,
        leading=28, backColor=C_HEADER_BG,
        borderPad=8, leftIndent=-8
    )
    styles['h2'] = ParagraphStyle(
        'H2', fontName='Helvetica-Bold', fontSize=17,
        textColor=C_H2, spaceAfter=8, spaceBefore=16,
        leading=22
    )
    styles['h3'] = ParagraphStyle(
        'H3', fontName='Helvetica-Bold', fontSize=14,
        textColor=C_H3, spaceAfter=6, spaceBefore=12,
        leading=18
    )
    styles['h4'] = ParagraphStyle(
        'H4', fontName='Helvetica-Bold', fontSize=12,
        textColor=C_H4, spaceAfter=4, spaceBefore=8,
        leading=16
    )
    styles['body'] = ParagraphStyle(
        'Body', fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, spaceAfter=6, spaceBefore=2,
        leading=14
    )
    styles['bullet'] = ParagraphStyle(
        'Bullet', fontName='Helvetica', fontSize=10,
        textColor=C_TEXT, spaceAfter=3, spaceBefore=1,
        leading=13, leftIndent=16, bulletIndent=4
    )
    styles['code'] = ParagraphStyle(
        'Code', fontName='Courier', fontSize=8.5,
        textColor=C_CODE_TEXT, spaceAfter=2, spaceBefore=2,
        leading=11, backColor=C_CODE_BG,
        borderPad=6, leftIndent=0
    )
    styles['blockquote'] = ParagraphStyle(
        'Blockquote', fontName='Helvetica-Oblique', fontSize=10,
        textColor=C_ACCENT2, spaceAfter=6, spaceBefore=4,
        leading=14, leftIndent=20,
        borderLeftColor=C_ACCENT, borderLeftWidth=3, borderLeftPadding=8
    )
    styles['toc_title'] = ParagraphStyle(
        'TOCTitle', fontName='Helvetica-Bold', fontSize=26,
        textColor=C_H1, spaceAfter=16, alignment=TA_CENTER
    )
    styles['toc_sub'] = ParagraphStyle(
        'TOCSub', fontName='Helvetica', fontSize=13,
        textColor=C_TEXT, spaceAfter=6, alignment=TA_CENTER
    )
    styles['toc_entry'] = ParagraphStyle(
        'TOCEntry', fontName='Helvetica', fontSize=11,
        textColor=C_H2, spaceAfter=5, leading=16
    )
    return styles

# ─── Markdown Parser ──────────────────────────────────────────────────────────
def parse_markdown(text, styles):
    """Convert markdown text to a list of ReportLab flowables."""
    elements = []
    lines = text.split('\n')
    i = 0
    in_code_block = False
    code_lines = []
    code_lang = ''

    while i < len(lines):
        line = lines[i]

        # Code block start/end
        if line.strip().startswith('```'):
            if in_code_block:
                # End of code block — render it
                code_text = '\n'.join(code_lines)
                if code_text.strip():
                    # Wrap long lines
                    wrapped = []
                    for cl in code_lines:
                        if len(cl) > 90:
                            # Soft wrap at 90 chars
                            while len(cl) > 90:
                                wrapped.append(cl[:90])
                                cl = '  ' + cl[90:]
                            wrapped.append(cl)
                        else:
                            wrapped.append(cl)
                    code_text = '\n'.join(wrapped)
                    # Escape XML special chars
                    code_text = code_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    pre = Preformatted(code_text, styles['code'])
                    elements.append(pre)
                    elements.append(Spacer(1, 4))
                in_code_block = False
                code_lines = []
                code_lang = ''
            else:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Horizontal rule
        if stripped in ('---', '===', '***') or re.match(r'^-{3,}$', stripped):
            elements.append(HRFlowable(width="100%", thickness=0.5,
                                        color=C_HR, spaceAfter=8, spaceBefore=8))
            i += 1
            continue

        # Headings
        if stripped.startswith('#### '):
            text_content = stripped[5:].strip()
            elements.append(Paragraph(escape_xml(text_content), styles['h4']))
            i += 1
            continue
        if stripped.startswith('### '):
            text_content = stripped[4:].strip()
            elements.append(Paragraph(escape_xml(text_content), styles['h3']))
            i += 1
            continue
        if stripped.startswith('## '):
            text_content = stripped[3:].strip()
            elements.append(Paragraph(escape_xml(text_content), styles['h2']))
            i += 1
            continue
        if stripped.startswith('# '):
            text_content = stripped[2:].strip()
            elements.append(Paragraph(escape_xml(text_content), styles['h1']))
            elements.append(HRFlowable(width="100%", thickness=1,
                                        color=C_ACCENT, spaceAfter=6, spaceBefore=2))
            i += 1
            continue

        # Blockquote
        if stripped.startswith('> '):
            quote_text = stripped[2:]
            elements.append(Paragraph(escape_xml(quote_text), styles['blockquote']))
            i += 1
            continue

        # Table rows
        if stripped.startswith('|') and stripped.endswith('|'):
            table_rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                row_line = lines[i].strip()
                # Skip separator rows
                if re.match(r'^\|[-:| ]+\|$', row_line):
                    i += 1
                    continue
                cells = [c.strip() for c in row_line.strip('|').split('|')]
                table_rows.append(cells)
                i += 1
            if table_rows:
                elements.extend(build_table(table_rows))
            continue

        # Bullet points
        if stripped.startswith('- ') or stripped.startswith('* '):
            bullet_text = stripped[2:]
            elements.append(Paragraph(
                f'• {escape_xml(inline_format(bullet_text))}',
                styles['bullet']
            ))
            i += 1
            continue

        # Numbered list
        if re.match(r'^\d+\. ', stripped):
            num_text = re.sub(r'^\d+\. ', '', stripped)
            num = re.match(r'^(\d+)\.', stripped).group(1)
            elements.append(Paragraph(
                f'{num}. {escape_xml(inline_format(num_text))}',
                styles['bullet']
            ))
            i += 1
            continue

        # Normal paragraph
        if stripped:
            elements.append(Paragraph(
                escape_xml(inline_format(stripped)),
                styles['body']
            ))
            elements.append(Spacer(1, 2))

        i += 1

    return elements


def escape_xml(text):
    """Escape XML special characters."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def inline_format(text):
    """Convert inline markdown formatting to ReportLab XML."""
    # Bold + italic: ***text***
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    # Italic: *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    # Inline code: `code`
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" color="#a6e3a1">\1</font>', text)
    # Links: [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'<i><u>\1</u></i>', text)
    return text


def build_table(rows):
    """Build a styled table from rows."""
    if not rows:
        return []

    # Determine column count from first row
    ncols = max(len(r) for r in rows)
    # Pad rows to uniform column count
    padded = [r + [''] * (ncols - len(r)) for r in rows]

    col_width = (A4[0] - 2.4 * inch) / ncols

    # Style cells
    styled_rows = []
    for ri, row in enumerate(padded):
        styled_row = []
        for ci, cell in enumerate(row):
            style = ParagraphStyle(
                f'tc_{ri}_{ci}',
                fontName='Helvetica-Bold' if ri == 0 else 'Helvetica',
                fontSize=8.5,
                textColor=C_WHITE if ri == 0 else C_TEXT,
                leading=11
            )
            styled_row.append(Paragraph(escape_xml(inline_format(cell)), style))
        styled_rows.append(styled_row)

    col_widths = [col_width] * ncols
    t = Table(styled_rows, colWidths=col_widths, repeatRows=1)

    table_style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HDR),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
        # Alternating rows
        *[('BACKGROUND', (0, ri), (-1, ri), C_TABLE_ALT)
          for ri in range(1, len(padded), 2)],
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.25, C_HR),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, C_HR),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        # Align
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    t.setStyle(table_style)
    return [t, Spacer(1, 8)]


# ─── Cover Page ───────────────────────────────────────────────────────────────
def make_cover_page(styles):
    elements = []
    elements.append(Spacer(1, 1.5 * inch))

    elements.append(Paragraph(
        "C++ DSA<br/>Interview Handbook",
        ParagraphStyle('Cover', fontName='Helvetica-Bold', fontSize=38,
                       textColor=C_H1, alignment=TA_CENTER, leading=46,
                       spaceAfter=20)
    ))

    elements.append(HRFlowable(width="80%", thickness=2,
                                color=C_ACCENT, spaceAfter=20, spaceBefore=5))

    elements.append(Paragraph(
        "Complete FAANG / MAANG Preparation Guide",
        ParagraphStyle('Sub', fontName='Helvetica', fontSize=16,
                       textColor=C_H2, alignment=TA_CENTER, spaceAfter=10)
    ))

    elements.append(Paragraph(
        "From Beginner Syntax to Advanced DSA Mastery",
        ParagraphStyle('Sub2', fontName='Helvetica-Oblique', fontSize=13,
                       textColor=C_TEXT, alignment=TA_CENTER, spaceAfter=30)
    ))

    elements.append(Spacer(1, 0.5 * inch))

    targets = [
        "FAANG / MAANG (Google · Meta · Amazon · Apple · Netflix · Microsoft)",
        "Big Tech (Uber · Airbnb · Atlassian · Siemens)",
        "Global Banks (Morgan Stanley · Wells Fargo · Citi · HSBC)",
    ]
    for t in targets:
        elements.append(Paragraph(
            f"▸  {t}",
            ParagraphStyle('Target', fontName='Helvetica', fontSize=11,
                           textColor=C_ACCENT2, alignment=TA_CENTER, spaceAfter=6)
        ))

    elements.append(Spacer(1, 0.8 * inch))

    info_data = [
        ["Language", "Timeline", "Level"],
        ["C++17", "1 Month", "Beginner → Advanced"],
    ]
    info_col_width = (A4[0] - 3 * inch) / 3
    info_table = Table(
        [[Paragraph(escape_xml(c), ParagraphStyle(
            f'it_{ri}_{ci}',
            fontName='Helvetica-Bold' if ri == 0 else 'Helvetica',
            fontSize=11,
            textColor=C_WHITE if ri == 0 else C_ACCENT,
            alignment=TA_CENTER, leading=14
        )) for ci, c in enumerate(row)] for ri, row in enumerate(info_data)],
        colWidths=[info_col_width] * 3
    )
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_TABLE_HDR),
        ('BACKGROUND', (0, 1), (-1, 1), C_CODE_BG),
        ('GRID', (0, 0), (-1, -1), 0.5, C_HR),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(info_table)

    elements.append(Spacer(1, 0.8 * inch))
    elements.append(Paragraph(
        "Generated May 2026 · For 5+ Year Backend Engineers Targeting Top-Tier Tech",
        ParagraphStyle('Footer', fontName='Helvetica', fontSize=9,
                       textColor=C_CODE_COMM, alignment=TA_CENTER)
    ))

    elements.append(PageBreak())
    return elements


# ─── Table of Contents ────────────────────────────────────────────────────────
def make_toc(styles):
    elements = []
    elements.append(Paragraph("Table of Contents", styles['toc_title']))
    elements.append(HRFlowable(width="100%", thickness=1.5,
                                color=C_ACCENT, spaceAfter=16))

    toc_entries = [
        ("Section 1", "C++ Fundamentals",
         "Syntax · Types · OOP · Templates · Lambdas"),
        ("Section 2", "STL Deep Dive",
         "vector · map · unordered_map · set · priority_queue · algorithms"),
        ("Section 3", "DSA Foundations",
         "Complexity · Recursion · Sorting · Searching · Divide & Conquer"),
        ("Section 4", "Complete DSA Pattern System",
         "15 patterns: Sliding Window · Two Pointers · DP · Backtracking · Graphs + more"),
        ("Section 5", "Competitive Programming Optimization",
         "Fast I/O · Memory · STL tricks · Bitset · Mathematical optimizations"),
        ("Section 6", "Interview Preparation",
         "FAANG mindset · 7-step framework · Communication · Company insights"),
        ("Section 7", "1-Month Roadmap",
         "Daily plan · LeetCode Top 75 · Mock schedule · Progress tracker"),
    ]

    for num, title, desc in toc_entries:
        elements.append(Paragraph(
            f'<b><font color="#89b4fa">{num}</font></b>  '
            f'<b><font color="#cdd6f4">{title}</font></b>',
            styles['toc_entry']
        ))
        elements.append(Paragraph(
            f'    {desc}',
            ParagraphStyle('TOCDesc', fontName='Helvetica-Oblique',
                           fontSize=9.5, textColor=C_CODE_COMM,
                           spaceAfter=10, leftIndent=20)
        ))

    elements.append(PageBreak())
    return elements


# ─── Page Template Callbacks ──────────────────────────────────────────────────
def on_first_page(canvas, doc):
    canvas.setFillColor(C_DARK_BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)


def on_later_pages(canvas, doc):
    canvas.setFillColor(C_DARK_BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    # Header bar
    canvas.setFillColor(C_HEADER_BG)
    canvas.rect(0, A4[1] - 0.45 * inch, A4[0], 0.45 * inch, fill=1, stroke=0)
    canvas.setFillColor(C_ACCENT)
    canvas.setFont('Helvetica-Bold', 9)
    canvas.drawString(0.5 * inch, A4[1] - 0.3 * inch, "C++ DSA Interview Handbook")
    canvas.setFillColor(C_TEXT)
    canvas.setFont('Helvetica', 9)
    canvas.drawRightString(A4[0] - 0.5 * inch, A4[1] - 0.3 * inch,
                           f"Page {doc.page}")
    # Footer bar
    canvas.setFillColor(C_HEADER_BG)
    canvas.rect(0, 0, A4[0], 0.35 * inch, fill=1, stroke=0)
    canvas.setFillColor(C_CODE_COMM)
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(A4[0] / 2, 0.12 * inch,
                             "FAANG · MAANG · Big Tech · Global Banks — C++ | May 2026")


# ─── Main Builder ─────────────────────────────────────────────────────────────
def build_pdf():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, OUTPUT_FILE)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.55 * inch,
        title="C++ DSA Interview Handbook",
        author="FAANG Preparation Guide",
        subject="Complete C++ DSA for Technical Interviews",
    )

    styles = make_styles()
    all_elements = []

    # Cover
    all_elements.extend(make_cover_page(styles))
    # Table of Contents
    all_elements.extend(make_toc(styles))

    # Each section
    for filename in SECTIONS:
        filepath = os.path.join(script_dir, filename)
        if not os.path.exists(filepath):
            print(f"  Warning: {filename} not found, skipping.")
            continue

        print(f"  Processing {filename}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        section_elements = parse_markdown(content, styles)
        all_elements.extend(section_elements)
        all_elements.append(PageBreak())

    print(f"\nBuilding PDF...")
    doc.build(all_elements,
              onFirstPage=on_first_page,
              onLaterPages=on_later_pages)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    print("=" * 60)
    print("  C++ DSA Interview Handbook — PDF Generator")
    print("=" * 60)
    path = build_pdf()
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"\nSuccess! File: {path}")
    print(f"Size: {size_mb:.2f} MB")
