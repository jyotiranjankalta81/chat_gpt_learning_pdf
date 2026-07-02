"""Shared PDF styles and utilities for the Interview Prep Blueprint."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, PageBreak, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas

DARK_BLUE = colors.HexColor("#0d2137")
MED_BLUE = colors.HexColor("#1a5276")
LIGHT_BLUE = colors.HexColor("#d6eaf8")
ACCENT_TEAL = colors.HexColor("#148f77")
ACCENT_GOLD = colors.HexColor("#b7950b")
LIGHT_GOLD = colors.HexColor("#fef9e7")
LIGHT_GREY = colors.HexColor("#f4f6f7")
MED_GREY = colors.HexColor("#bdc3c7")
WHITE = colors.white
BLACK = colors.black
GREEN_BG = colors.HexColor("#e8f8f5")
ORANGE_BG = colors.HexColor("#fdf2e9")
PURPLE_BG = colors.HexColor("#f4ecf7")
RED_BG = colors.HexColor("#fdedec")


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, footer_text="", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.footer_text = footer_text

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#888888"))
        self.drawCentredString(
            A4[0] / 2, 1.0 * cm,
            f"{self.footer_text}  •  Page {self._pageNumber} of {page_count}"
        )
        self.restoreState()


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "CoverTitle", fontSize=32, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=8, leading=40,
    ))
    styles.add(ParagraphStyle(
        "CoverSubtitle", fontSize=15, fontName="Helvetica",
        textColor=colors.HexColor("#a9cce3"), alignment=TA_CENTER,
        spaceAfter=6, leading=20,
    ))
    styles.add(ParagraphStyle(
        "SectionTitle", fontSize=17, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER, spaceAfter=4, leading=22,
    ))
    styles.add(ParagraphStyle(
        "SubTitle", fontSize=12, fontName="Helvetica-Bold",
        textColor=DARK_BLUE, alignment=TA_LEFT, spaceAfter=4, spaceBefore=8, leading=16,
    ))
    styles.add(ParagraphStyle(
        "SubSubTitle", fontSize=10, fontName="Helvetica-Bold",
        textColor=MED_BLUE, alignment=TA_LEFT, spaceAfter=3, spaceBefore=6, leading=14,
    ))
    styles.add(ParagraphStyle(
        "BodyText2", fontSize=9, fontName="Helvetica",
        textColor=BLACK, alignment=TA_JUSTIFY, spaceAfter=4, leading=13,
    ))
    styles.add(ParagraphStyle(
        "TableHeader", fontSize=8, fontName="Helvetica-Bold",
        textColor=WHITE, alignment=TA_CENTER, leading=11,
    ))
    styles.add(ParagraphStyle(
        "Cell", fontSize=7.5, fontName="Helvetica",
        textColor=BLACK, alignment=TA_LEFT, leading=10,
    ))
    styles.add(ParagraphStyle(
        "CellSmall", fontSize=6.5, fontName="Helvetica",
        textColor=BLACK, alignment=TA_LEFT, leading=9,
    ))
    styles.add(ParagraphStyle(
        "CellCenter", fontSize=7.5, fontName="Helvetica",
        textColor=BLACK, alignment=TA_CENTER, leading=10,
    ))
    styles.add(ParagraphStyle(
        "CellBold", fontSize=7.5, fontName="Helvetica-Bold",
        textColor=DARK_BLUE, alignment=TA_LEFT, leading=10,
    ))
    styles.add(ParagraphStyle(
        "Note", fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#555555"), alignment=TA_LEFT,
        spaceAfter=4, leading=12,
    ))
    styles.add(ParagraphStyle(
        "TOCEntry", fontSize=10, fontName="Helvetica",
        textColor=DARK_BLUE, alignment=TA_LEFT, spaceAfter=3, leading=14,
    ))
    return styles


def section_banner(title, styles, bg=DARK_BLUE):
    data = [[Paragraph(title, styles["SectionTitle"])]]
    t = Table(data, colWidths=[17.5 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return t


def std_table(header_row, data_rows, col_widths, styles, font_style="Cell", header_bg=DARK_BLUE):
    header = [Paragraph(h, styles["TableHeader"]) for h in header_row]
    body = [[Paragraph(str(c), styles[font_style]) for c in row] for row in data_rows]
    table_data = [header] + body
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("GRID", (0, 0), (-1, -1), 0.35, MED_GREY),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(len(data_rows)):
        bg = LIGHT_GREY if i % 2 == 0 else WHITE
        row_styles.append(("BACKGROUND", (0, i + 1), (-1, i + 1), bg))
    t.setStyle(TableStyle(row_styles))
    return t


def checklist_table(items, styles, col_widths=None):
    rows = [[Paragraph(f"☐  {item}", styles["Cell"])] for item in items]
    t = Table(rows, colWidths=[col_widths or 17.5 * cm])
    t.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def revision_dates(day_num, start_date_day=1):
    """Spaced repetition revision schedule from first encounter day."""
    offsets = [0, 2, 6, 13, 20, 29]
    return ", ".join(f"D{day_num + o}" for o in offsets if day_num + o <= 39)
