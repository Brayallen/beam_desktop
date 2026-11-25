from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from beam_designer import BeamLoads, LumberSection, SECTION_SOURCES
from design_io import SavedDesign


NAVY = colors.HexColor("#1F2F47")
BLUE = colors.HexColor("#2563EB")
GREEN = colors.HexColor("#18864B")
RED = colors.HexColor("#BD2C2C")
MUTED = colors.HexColor("#667085")
GRID = colors.HexColor("#D9E1EA")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
LIGHT_GREEN = colors.HexColor("#EAF7EF")
LIGHT_RED = colors.HexColor("#FCECEC")


class BeamDiagram(Flowable):
    def __init__(self, result: dict, width: float, height: float = 162):
        super().__init__()
        self.result = result
        self.width = width
        self.height = height

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return self.width, self.height

    @staticmethod
    def _arrow(canvas, x, y_start, y_end, color, width=1.2):
        canvas.setStrokeColor(color)
        canvas.setLineWidth(width)
        canvas.line(x, y_start, x, y_end)
        direction = 1 if y_end > y_start else -1
        canvas.line(x, y_end, x - 3.2, y_end - direction * 5)
        canvas.line(x, y_end, x + 3.2, y_end - direction * 5)

    def draw(self):
        canvas = self.canv
        result = self.result
        left, right = 54, self.width - 30
        beam_y = 91
        beam_width = right - left
        canvas.saveState()
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(5)
        canvas.line(left, beam_y, right, beam_y)

        if result["support"] == "simple":
            canvas.setFillColor(colors.HexColor("#AAB5C2"))
            canvas.setStrokeColor(NAVY)
            canvas.setLineWidth(0.8)
            canvas.line(left, beam_y - 3, left - 12, beam_y - 22)
            canvas.line(left, beam_y - 3, left + 12, beam_y - 22)
            canvas.line(left - 12, beam_y - 22, left + 12, beam_y - 22)
            canvas.line(right, beam_y - 3, right - 12, beam_y - 22)
            canvas.line(right, beam_y - 3, right + 12, beam_y - 22)
            canvas.line(right - 12, beam_y - 22, right + 12, beam_y - 22)
            for dx in (-7, 0, 7):
                canvas.circle(right + dx, beam_y - 26, 1.8, stroke=1, fill=0)
        else:
            wall_x = left - 13
            canvas.setFillColor(colors.HexColor("#AAB5C2"))
            canvas.rect(wall_x, beam_y - 22, 13, 44, stroke=0, fill=1)
            canvas.setStrokeColor(NAVY)
            canvas.setLineWidth(0.8)
            for offset in range(-19, 20, 7):
                canvas.line(wall_x, beam_y + offset, wall_x - 8, beam_y + offset - 7)

        span = result["span"]

        def x_at(position):
            return left + position / span * beam_width

        for index, load in enumerate(result["loads"].uniform, start=1):
            x1, x2 = x_at(load.start), x_at(load.end)
            line_y = beam_y + 34
            canvas.setStrokeColor(BLUE)
            canvas.setLineWidth(1)
            canvas.line(x1, line_y, x2, line_y)
            arrow_count = max(3, min(11, int((x2 - x1) / 30) + 1))
            for arrow_index in range(arrow_count):
                fraction = arrow_index / max(1, arrow_count - 1)
                self._arrow(canvas, x1 + fraction * (x2 - x1), line_y - 2, beam_y + 4, BLUE)
            canvas.setFillColor(NAVY)
            canvas.setFont("Helvetica", 7.5)
            canvas.drawCentredString(
                (x1 + x2) / 2,
                line_y + 5,
                f"w{index} = {load.value:.3f} kip/ft",
            )

        for index, load in enumerate(result["loads"].point, start=1):
            x = x_at(load.position)
            self._arrow(canvas, x, beam_y + 58, beam_y + 4, RED, 1.4)
            canvas.setFillColor(RED)
            canvas.setFont("Helvetica-Bold", 7.5)
            canvas.drawCentredString(x, beam_y + 61, f"P{index} = {load.value:.3f} kip")

        reaction = result["reaction"]
        self._arrow(canvas, left, beam_y - 48, beam_y - 5, GREEN, 1.4)
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(left + 8, beam_y - 47, f"R_A = {reaction['RA']:.3f} kip")
        if result["support"] == "simple":
            self._arrow(canvas, right, beam_y - 48, beam_y - 5, GREEN, 1.4)
            canvas.drawRightString(right - 8, beam_y - 47, f"R_B = {reaction['RB']:.3f} kip")
        else:
            canvas.drawString(
                left + 40,
                beam_y - 47,
                f"M_A = {reaction['MA']:.3f} kip-ft",
            )

        dimension_y = 13
        canvas.setStrokeColor(MUTED)
        canvas.setLineWidth(0.8)
        canvas.line(left, dimension_y, right, dimension_y)
        canvas.line(left, dimension_y - 4, left, dimension_y + 4)
        canvas.line(right, dimension_y - 4, right, dimension_y + 4)
        canvas.line(left, dimension_y, left + 5, dimension_y + 2)
        canvas.line(left, dimension_y, left + 5, dimension_y - 2)
        canvas.line(right, dimension_y, right - 5, dimension_y + 2)
        canvas.line(right, dimension_y, right - 5, dimension_y - 2)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString((left + right) / 2, dimension_y - 11, f"L = {span:.3f} ft")
        canvas.restoreState()


class ResultChart(Flowable):
    def __init__(self, title: str, values: list[float], unit: str, color, height: float = 138):
        super().__init__()
        self.title = title
        self.values = values
        self.unit = unit
        self.color = color
        self.height = height

    def wrap(self, avail_width, avail_height):
        self.width = avail_width
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        width, height = self.width, self.height
        left, right, bottom, top = 48, width - 12, 27, height - 23
        y_values = self.values
        y_min, y_max = min(0.0, min(y_values)), max(0.0, max(y_values))
        if y_max == y_min:
            y_max, y_min = y_max + 1.0, y_min - 1.0
        padding = (y_max - y_min) * 0.06
        y_min -= padding
        y_max += padding

        def sy(value):
            return bottom + (value - y_min) / (y_max - y_min) * (top - bottom)

        x_values = self.x_values
        x_min, x_max = x_values[0], x_values[-1]
        x_range = x_max - x_min or 1.0

        def sx(value):
            return left + (value - x_min) / x_range * (right - left)

        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(2, height - 11, self.title)
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.45)
        for fraction in (0, 0.5, 1):
            y = bottom + fraction * (top - bottom)
            canvas.line(left, y, right, y)
        zero_y = sy(0.0)
        canvas.setStrokeColor(MUTED)
        canvas.setLineWidth(0.7)
        canvas.line(left, zero_y, right, zero_y)
        canvas.line(left, bottom, left, top)
        canvas.line(left, bottom, right, bottom)

        canvas.setFillColor(MUTED)
        canvas.setFont("Helvetica", 6.8)
        for fraction, label in ((0, f"{y_min:.3f}"), (1, f"{y_max:.3f}")):
            y = bottom + fraction * (top - bottom)
            canvas.drawRightString(left - 4, y - 2, label)
        for fraction in (0, 0.5, 1):
            x = left + fraction * (right - left)
            value = x_min + fraction * (x_max - x_min)
            canvas.line(x, bottom, x, bottom - 3)
            canvas.drawCentredString(x, bottom - 11, f"{value:.2f}")

        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString((left + right) / 2, 3, "Position, x (ft)")
        canvas.saveState()
        canvas.translate(8, (bottom + top) / 2)
        canvas.rotate(90)
        canvas.drawCentredString(0, 0, self.unit)
        canvas.restoreState()

        canvas.setStrokeColor(self.color)
        canvas.setLineWidth(1.45)
        path = canvas.beginPath()
        path.moveTo(sx(x_values[0]), sy(y_values[0]))
        for x_value, y_value in zip(x_values[1:], y_values[1:]):
            path.lineTo(sx(x_value), sy(y_value))
        canvas.drawPath(path, stroke=1, fill=0)
        canvas.restoreState()

def _styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            leading=25,
            textColor=NAVY,
            alignment=0,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=NAVY,
            spaceBefore=7,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10.4,
            textColor=NAVY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallMuted",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=MUTED,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.7,
            leading=9.5,
            textColor=NAVY,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.7,
            leading=9,
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="DateRight",
            parent=styles["SmallMuted"],
            alignment=TA_RIGHT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Status",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
        )
    )
    return styles


def _paragraph(value: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(value, style)


def _table(data, widths, header=True, row_heights=None):
    table = Table(data, colWidths=widths, rowHeights=row_heights, repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ]
        )
        if len(data) > 1:
            commands.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BLUE]))
    else:
        commands.append(("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_BLUE]))
    table.setStyle(TableStyle(commands))
    return table


def _on_page(canvas, document):
    canvas.saveState()
    width, height = letter
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.6)
    canvas.line(document.leftMargin, height - 34, width - document.rightMargin, height - 34)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(NAVY)
    canvas.drawString(document.leftMargin, height - 26, "BEAM DESIGNER  |  CALCULATION SHEET")
    canvas.setStrokeColor(GRID)
    canvas.line(document.leftMargin, 33, width - document.rightMargin, 33)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(document.leftMargin, 21, "Preliminary analysis — verify assumptions and project criteria.")
    canvas.drawRightString(width - document.rightMargin, 21, f"Page {document.page}")
    canvas.restoreState()


def _validate_result(design: SavedDesign, result: dict) -> None:
    if result is None:
        raise ValueError("Analyze the current beam inputs before creating a calculation sheet.")
    expected_loads = BeamLoads(design.point_loads, design.uniform_loads)
    section = result.get("section")
    matches = (
        result.get("support") == design.support
        and result.get("span") == design.span_ft
        and result.get("loads") == expected_loads
        and getattr(section, "designation", None) == design.section
        and abs(result.get("deflection_limit", 0.0) - design.deflection_limit_in) < 1e-12
    )
    if design.material == "lumber":
        matches = matches and isinstance(section, LumberSection)
        matches = matches and result.get("orientation") == design.lumber_orientation
    else:
        matches = matches and not isinstance(section, LumberSection)
    if not matches:
        raise ValueError("The calculation results do not match the current inputs. Analyze the beam again.")


def create_calculation_sheet(path: str | Path, design: SavedDesign, result: dict) -> None:
    _validate_result(design, result)

    destination = Path(path)
    document = SimpleDocTemplate(
        str(destination),
        pagesize=letter,
        rightMargin=0.58 * inch,
        leftMargin=0.58 * inch,
        topMargin=0.57 * inch,
        bottomMargin=0.52 * inch,
        title="Beam Designer Calculation Sheet",
        author="Beam Designer",
        subject="Preliminary beam analysis results",
    )
    styles = _styles()
    content_width = letter[0] - document.leftMargin - document.rightMargin
    story = []

    today = datetime.now().astimezone().strftime("%B %d, %Y")
    title_row = Table(
        [[
            Paragraph("Beam Designer Calculation Sheet", styles["ReportTitle"]),
            Paragraph(f"Report date<br/><b>{today}</b>", styles["DateRight"]),
        ]],
        colWidths=[content_width * 0.72, content_width * 0.28],
    )
    title_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.extend([Spacer(1, 3), title_row, Spacer(1, 9)])

    overall_pass = result["overall_pass"]
    status_text = "OVERALL DESIGN STATUS: PASS" if overall_pass else "OVERALL DESIGN STATUS: FAIL"
    status_table = Table([[Paragraph(status_text, styles["Status"])]], colWidths=[content_width])
    status_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN if overall_pass else LIGHT_RED),
                ("BOX", (0, 0), (-1, -1), 0.8, GREEN if overall_pass else RED),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.extend([status_table, Paragraph("Design Inputs", styles["SectionHeading"])])

    section = result["section"]
    is_lumber = isinstance(section, LumberSection)
    orientation = design.lumber_orientation if is_lumber else "Not applicable"
    material_name = "Lumber" if is_lumber else "Steel"
    section_label = (
        f"{design.section} — {section.species}, {section.grade}" if is_lumber else design.section
    )
    properties = (
        f"E = {result['E'] / 1_000_000:.3f} Mpsi; I = {result['I']:.3f} in^4; "
        f"S = {result['S']:.3f} in^3"
    )
    input_rows = [
        ["Support", "Simply supported" if design.support == "simple" else "Cantilever",
         "Span", f"{design.span_ft:.3f} ft"],
        ["Material", material_name, "Section", section_label],
        ["Orientation", orientation, "Deflection limit", f"{design.deflection_limit_in:.3f} in"],
        ["Section properties", properties, "Allowable bending", f"{result['allowable']:.3f} ksi"],
    ]
    input_table = _table(
        [[_paragraph(cell, styles["TableCell"]) for cell in row] for row in input_rows],
        [content_width * 0.17, content_width * 0.34, content_width * 0.18, content_width * 0.31],
        header=False,
    )
    story.append(input_table)
    source_key = "lumber" if is_lumber else "steel"
    story.append(
        Paragraph(
            "Section data: " + SECTION_SOURCES[source_key] + ".",
            styles["SmallMuted"],
        )
    )

    story.append(Paragraph("Applied Loads", styles["SectionHeading"]))
    load_rows = [[
        _paragraph("Load", styles["TableHeader"]),
        _paragraph("Magnitude", styles["TableHeader"]),
        _paragraph("Location / extent", styles["TableHeader"]),
    ]]
    for index, load in enumerate(design.point_loads, start=1):
        load_rows.append(
            [
                _paragraph(f"Point load P{index}", styles["TableCell"]),
                _paragraph(f"{load.value:.3f} kip", styles["TableCell"]),
                _paragraph(f"x = {load.position:.3f} ft", styles["TableCell"]),
            ]
        )
    for index, load in enumerate(design.uniform_loads, start=1):
        load_rows.append(
            [
                _paragraph(f"Uniform load w{index}", styles["TableCell"]),
                _paragraph(f"{load.value:.3f} kip/ft", styles["TableCell"]),
                _paragraph(f"{load.start:.3f}–{load.end:.3f} ft", styles["TableCell"]),
            ]
        )
    if len(load_rows) == 1:
        load_rows.append([_paragraph("No user-entered loads", styles["TableCell"]), "", ""])
    story.append(_table(load_rows, [content_width * 0.34, content_width * 0.25, content_width * 0.41]))

    story.append(Paragraph("Beam, Loads, and Reactions", styles["SectionHeading"]))
    story.append(BeamDiagram(result, content_width))
    deflection_chart = ResultChart(
        "Deflection Diagram — Deflection (in)",
        result["deflection"],
        "Deflection (in)",
        colors.HexColor("#D97706"),
        height=132,
    )
    deflection_chart.x_values = result["deflection_x"]
    story.append(deflection_chart)

    story.append(Paragraph("Engineering Assumptions and Limitations", styles["SectionHeading"]))
    assumptions = [
        "Prismatic, homogeneous, linearly elastic beam; small-deflection theory.",
        "Vertical loads only; major-axis bending; deflection includes bending only, with shear deformation ignored.",
        "Simply supported or cantilever boundary conditions only. No axial load, torsion, shear design, connection design, buckling, lateral-torsional buckling, or web yielding checks.",
        "No load combinations, safety-factor or load-duration adjustments, live-load patterns, seismic/wind analysis, or beam self-weight are included.",
        "Preliminary educational calculation only; verify design criteria, section properties, material values, and applicable codes with the responsible engineer.",
    ]
    story.append(
        _paragraph(
            "<br/>".join(f"- {item}" for item in assumptions),
            styles["SmallBody"],
        )
    )
    story.append(Spacer(1, 5))
    story.append(
        Paragraph(
            "Sign convention: downward applied loads are positive; diagram values follow the Beam Designer analysis results. "
            "Deflection and diagram signs are reported as calculated.",
            styles["SmallMuted"],
        )
    )
    story.append(PageBreak())

    story.append(Paragraph("Analysis Results", styles["SectionHeading"]))
    results_rows = [
        ["Result", "Value", "Location / criterion"],
        ["Maximum shear", f"{abs(result['max_shear']):.3f} kip",
         f"x = {result['shear_location']:.3f} ft"],
        ["Maximum bending moment", f"{abs(result['max_moment']):.3f} kip-ft",
         f"x = {result['moment_location']:.3f} ft"],
        ["Maximum deflection", f"{abs(result['max_deflection']):.4f} in",
         f"x = {result['deflection_location']:.3f} ft"],
        ["Support reaction R_A", f"{result['reaction']['RA']:.3f} kip",
         "At left support / fixed end"],
    ]
    if design.support == "simple":
        results_rows.append(["Support reaction R_B", f"{result['reaction']['RB']:.3f} kip", "At right support"])
    else:
        results_rows.append(["Fixed-end moment M_A", f"{result['reaction']['MA']:.3f} kip-ft", "At fixed support"])
    story.append(_table(results_rows, [content_width * 0.38, content_width * 0.28, content_width * 0.34]))
    story.append(Spacer(1, 7))

    bending_status = "PASS" if result["bending_pass"] else "FAIL"
    deflection_status = "PASS" if result["deflection_pass"] else "FAIL"
    check_rows = [
        ["Check", "Demand / allowable", "Utilization", "Status"],
        [
            "Bending stress",
            f"{result['bending_stress']:.3f} / {result['allowable']:.3f} ksi",
            f"{result['bending_ratio'] * 100:.1f}%",
            bending_status,
        ],
        [
            "Deflection",
            f"{abs(result['max_deflection']):.4f} / {result['deflection_limit']:.4f} in",
            f"{result['deflection_ratio'] * 100:.1f}%",
            deflection_status,
        ],
    ]
    checks_table = _table(
        check_rows,
        [content_width * 0.27, content_width * 0.38, content_width * 0.17, content_width * 0.18],
    )
    checks_table.setStyle(
        TableStyle(
            [
                ("TEXTCOLOR", (3, 1), (3, 1), GREEN if result["bending_pass"] else RED),
                ("TEXTCOLOR", (3, 2), (3, 2), GREEN if result["deflection_pass"] else RED),
                ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(checks_table)

    shear_chart = ResultChart(
        "Shear Force Diagram — V (kip)", result["shear"], "V (kip)", BLUE, height=190
    )
    shear_chart.x_values = result["x"]
    story.append(shear_chart)
    moment_chart = ResultChart(
        "Bending Moment Diagram — M (kip-ft)",
        result["moment"],
        "M (kip-ft)",
        GREEN,
        height=190,
    )
    moment_chart.x_values = result["x"]
    story.append(moment_chart)

    document.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
