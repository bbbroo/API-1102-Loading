from __future__ import annotations

from io import BytesIO
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.backend.reporting.models import DetailedReportData, EquationTrace, PlotArtifact
from app.backend.reporting.service import first_intermediate
from app.standards.metadata import APP_VERSION, ENGINE_VERSION, SOURCE_WORKBOOKS, STANDARDS_VERSION

NAVY = colors.HexColor("#263746")
NAVY_DARK = colors.HexColor("#15293c")
LINE = colors.HexColor("#ccd6e0")
GRID = colors.HexColor("#d7dee6")
SOFT = colors.HexColor("#f8fafc")
TEXT = colors.HexColor("#111827")
MUTED = colors.HexColor("#53687f")
GREEN = colors.HexColor("#027a48")
GREEN_BG = colors.HexColor("#ecfdf3")
RED = colors.HexColor("#b42318")
RED_BG = colors.HexColor("#fee4e2")
AMBER = colors.HexColor("#b54708")
AMBER_BG = colors.HexColor("#fffaeb")
GRAY_BG = colors.HexColor("#f2f4f7")

PAGE_WIDTH, PAGE_HEIGHT = letter
LEFT_MARGIN = 36
RIGHT_MARGIN = 36
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
CARD_CELL = ParagraphStyle("CardCell", fontName="Helvetica", fontSize=8, leading=10, textColor=TEXT)
CARD_LABEL = ParagraphStyle("CardCellLabel", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=TEXT)
CARD_HEADER = ParagraphStyle("CardCellHeader", fontName="Helvetica-Bold", fontSize=8, leading=10, textColor=NAVY)


class PageSectionBar(Flowable):
    def __init__(self, title: str):
        super().__init__()
        self.title = title.upper()
        self.width = CONTENT_WIDTH
        self.height = 32

    def wrap(self, availWidth, availHeight):
        return availWidth, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(NAVY_DARK)
        canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(10, 10, f"PAGE {canvas.getPageNumber()} - {self.title}")
        canvas.restoreState()


class StatusBadge(Flowable):
    def __init__(self, status: str):
        super().__init__()
        self.status = status or "Not Calculated"
        self.label = self.status if self.status in {"Pass", "Fail", "Needs Review", "Not Calculated"} else self.status
        self.width = max(0.7 * inch, min(1.2 * inch, 0.24 * inch + len(self.label) * 4.6))
        self.height = 20

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        color, background = status_colors(self.status)
        solid = self.status in {"Pass", "Fail", "Needs Review"}
        fill = color if solid else background
        text_color = colors.white if solid else color
        canvas.setFillColor(fill)
        canvas.setStrokeColor(color)
        canvas.roundRect(0, 1, self.width, self.height - 2, 3, fill=1, stroke=1)
        canvas.setStrokeColor(text_color)
        canvas.setFillColor(text_color)
        icon_x = 12
        icon_y = self.height / 2
        if self.status == "Pass":
            canvas.circle(icon_x, icon_y, 5, fill=0, stroke=1)
            canvas.setLineWidth(1.2)
            canvas.line(icon_x - 3, icon_y, icon_x - 1, icon_y - 2.5)
            canvas.line(icon_x - 1, icon_y - 2.5, icon_x + 4, icon_y + 3)
        elif self.status == "Fail":
            canvas.circle(icon_x, icon_y, 5, fill=0, stroke=1)
            canvas.setLineWidth(1.2)
            canvas.line(icon_x - 3, icon_y - 3, icon_x + 3, icon_y + 3)
            canvas.line(icon_x - 3, icon_y + 3, icon_x + 3, icon_y - 3)
        elif self.status == "Needs Review":
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawCentredString(icon_x, icon_y - 4, "!")
        else:
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawCentredString(icon_x, icon_y - 3, "-")
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawString(23, 6, self.label)
        canvas.restoreState()


def render_detailed_pdf(data: DetailedReportData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=96,
        bottomMargin=54,
        pageCompression=0,
    )
    styles = get_styles()
    values = first_intermediate(data.intermediate_values)
    calc = data.calculation
    project = data.project
    scenario = data.scenario
    results = data.results
    story: list[Any] = []

    story += [
        PageSectionBar("Report Summary"),
        Spacer(1, 14),
        two_column(
            card("Project & Calculation", metadata_rows(project, calc, scenario), col_widths=[1.25 * inch, 2.12 * inch]),
            card("Purpose & References", purpose_rows(calc), col_widths=[1.0 * inch, 2.37 * inch]),
        ),
        Spacer(1, 12),
        two_column(
            card("Key Inputs", input_rows(values, calc.calculation_type), col_widths=[1.25 * inch, 2.12 * inch]),
            card("Controlling Check", [["Overall Result", status_badge(results.get("overall_result", "Not Calculated"))], ["Controlling Check", results.get("controlling_check") or "-"], ["Scenario Calculated", results.get("calculated_at", "-")]], col_widths=[1.25 * inch, 2.12 * inch]),
        ),
        Spacer(1, 12),
        card("Results Summary", result_rows(results), header_rows=1, col_widths=[1.9 * inch, 1.25 * inch, 1.25 * inch, 1.1 * inch, 1.0 * inch], style_rows=result_status_styles(results)),
        Spacer(1, 12),
        Paragraph("This report supports engineering documentation and review. It does not replace engineering judgment, applicable codes, standards, client requirements, or independent checking.", styles["Note"]),
        PageBreak(),
        PageSectionBar("Table of Contents"),
        Spacer(1, 14),
        card("Report Sections", [["1", "Report summary"], ["2", "Input summary and warnings"], ["3", "Symbol legend"], ["4", "Detailed formula trace"], ["5", "Intermediate values"], ["6", "Generated coefficient plots"], ["Appendix", "Full-size plots and lookup fallbacks"]], col_widths=[1.0 * inch, 5.78 * inch]),
        PageBreak(),
        PageSectionBar("Input Summary"),
        Spacer(1, 14),
        two_column(
            card("Project & Calculation", metadata_rows(project, calc, scenario), col_widths=[1.25 * inch, 2.12 * inch]),
            card("Key Inputs", input_rows(values, calc.calculation_type), col_widths=[1.25 * inch, 2.12 * inch]),
        ),
    ]

    if data.options.include_warnings:
        story += [
            Spacer(1, 12),
            card("Critical Warnings", warning_rows(data.critical_warnings), col_widths=[1.0 * inch, 1.1 * inch, 4.68 * inch]),
            Spacer(1, 10),
            card("Informational Warnings", warning_rows(data.informational_warnings), col_widths=[1.0 * inch, 1.1 * inch, 4.68 * inch]),
        ]

    story += [
        PageBreak(),
        PageSectionBar("Symbol Legend"),
        Spacer(1, 14),
        card("Symbols", symbol_rows(calc.calculation_type), header_rows=1, col_widths=[1.0 * inch, 5.78 * inch]),
    ]

    if data.options.include_formula_trace:
        story.extend(formula_trace_pages(data.equations, data.plots, styles))

    if data.options.include_intermediates:
        story += [PageBreak(), PageSectionBar("Intermediate Values"), Spacer(1, 14)]
        for title, rows in intermediate_sections(values, calc.calculation_type):
            story.append(card(title, rows, col_widths=[1.5 * inch, 5.28 * inch]))
            story.append(Spacer(1, 10))

    if data.options.include_plots:
        story += [PageBreak(), PageSectionBar("Generated Coefficient Plots"), Spacer(1, 14)]
        if data.plots:
            for plot in data.plots[:8]:
                story.extend(plot_block(plot, styles, full_size=False))
        else:
            story.append(Paragraph("No interpolation traces were available for generated plots.", styles["Normal"]))

    if data.options.include_appendix_plots:
        story += [PageBreak(), PageSectionBar("Appendix: Full-Size Plots"), Spacer(1, 14)]
        for plot in data.plots:
            story.extend(plot_block(plot, styles, full_size=True))

    story += [
        PageBreak(),
        PageSectionBar("References"),
        Spacer(1, 14),
        card("References", [["Source Workbooks", ", ".join(SOURCE_WORKBOOKS.values())], ["Application", f"App {APP_VERSION} | Engine {ENGINE_VERSION} | Standards {STANDARDS_VERSION}"], ["Plot Notice", "Generated coefficient plots use the app's implemented lookup data and digitized graph underlays for visual traceability. Verify against the governing standard."]], col_widths=[1.4 * inch, 5.38 * inch]),
    ]

    doc.build(
        story,
        onFirstPage=lambda canvas, built_doc: page_frame(canvas, built_doc, data),
        onLaterPages=lambda canvas, built_doc: page_frame(canvas, built_doc, data),
    )
    return buffer.getvalue()


def get_styles():
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "Helvetica"
    styles["Normal"].fontSize = 9
    styles["Normal"].leading = 11
    styles.add(ParagraphStyle("HeaderLeft", parent=styles["Normal"], fontSize=9, leading=11, textColor=NAVY))
    styles.add(ParagraphStyle("HeaderRight", parent=styles["Normal"], fontSize=10, leading=12, textColor=TEXT, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("HeaderKicker", parent=styles["Normal"], fontSize=7.5, leading=9, textColor=TEXT, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("CardText", parent=styles["Normal"], fontSize=8, leading=10, textColor=TEXT))
    styles.add(ParagraphStyle("CardLabel", parent=styles["Normal"], fontSize=8, leading=10, textColor=TEXT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("Note", parent=styles["Italic"], fontSize=8, leading=10, textColor=MUTED))
    styles.add(ParagraphStyle("PlotNote", parent=styles["Italic"], fontSize=7.8, leading=9, textColor=MUTED))
    return styles


def page_frame(canvas, doc, data: DetailedReportData) -> None:
    canvas.saveState()
    calc = data.calculation
    calc_date = calc.date.isoformat() if hasattr(calc.date, "isoformat") else (calc.date or "2026-05-24")
    y = PAGE_HEIGHT - 52
    canvas.setFillColor(NAVY)
    canvas.setFont("Helvetica-Bold", 28)
    canvas.drawString(LEFT_MARGIN, y - 8, "HDR")
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(LEFT_MARGIN + 70, y + 4, f"API RP 1102 {calc.calculation_type.upper()} LOADING CALCULATOR")
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(MUTED)
    canvas.drawString(LEFT_MARGIN + 70, y - 12, "GAS PIPELINE - TECHNICAL TOOL")
    canvas.setFillColor(TEXT)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y + 20, "ENGINEERING CALCULATION PACKAGE")
    canvas.setFont("Helvetica", 12)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y + 1, f"API RP 1102 {calc.calculation_type} Loading Analysis")
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y - 14, f"Calc {calc.calc_number or '-'} - Rev {calc.revision or '0'} - {calc_date} - {calc.status or '-'}")
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(1)
    canvas.line(LEFT_MARGIN, PAGE_HEIGHT - 80, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 80)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(LEFT_MARGIN + 2, 32, "API RP 1102 Loading Calculator - Detailed Scenario Report")
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN - 2, 32, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def two_column(left: Table, right: Table) -> Table:
    table = Table([[left, right]], colWidths=[3.4 * inch, 3.4 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def card(title: str, rows: list[list[Any]], header_rows: int = 0, col_widths: list[float] | None = None, style_rows: list[tuple] | None = None) -> Table:
    body = [[title] + [""] * (max((len(row) for row in rows), default=1) - 1)]
    body.extend(normalize_rows(rows, header_rows=header_rows))
    table = Table(body, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    row_background_start = 1 + header_rows
    commands = [
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("BOX", (0, 0), (-1, -1), 0.7, LINE),
        ("INNERGRID", (0, 1), (-1, -1), 0.45, GRID),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 1), (-1, -1), TEXT),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ]
    if row_background_start <= len(body) - 1:
        commands.append(("ROWBACKGROUNDS", (0, row_background_start), (-1, -1), [colors.white, SOFT]))
    if header_rows:
        commands.extend(
            [
                ("BACKGROUND", (0, 1), (-1, header_rows), SOFT),
                ("FONTNAME", (0, 1), (-1, header_rows), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (-1, header_rows), NAVY),
            ]
        )
    if style_rows:
        commands.extend(style_rows)
    table.setStyle(TableStyle(commands))
    return table


def normalize_rows(rows: list[list[Any]], header_rows: int = 0) -> list[list[Any]]:
    width = max((len(row) for row in rows), default=1)
    normalized: list[list[Any]] = []
    for row_index, row in enumerate(rows):
        padded = row + [""] * (width - len(row))
        normalized.append(
            [
                cell_value(value, header=row_index < header_rows, label_cell=column_index == 0)
                for column_index, value in enumerate(padded)
            ]
        )
    return normalized


def cell_value(value: Any, *, header: bool = False, label_cell: bool = False) -> Any:
    if isinstance(value, Flowable):
        return value
    if value is None:
        text = "-"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value)
    else:
        text = str(value)
    style = CARD_HEADER if header else CARD_LABEL if label_cell else CARD_CELL
    return Paragraph(escape(text), style)


def status_badge(status: str) -> StatusBadge:
    return StatusBadge(status or "Not Calculated")


def status_colors(status: str):
    if status == "Pass":
        return GREEN, GREEN_BG
    if status == "Fail":
        return RED, RED_BG
    if status == "Needs Review":
        return AMBER, AMBER_BG
    return MUTED, GRAY_BG


def result_rows(results: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Check", "Calculated (psi)", "Allowable (psi)", "Utilization", "Status"]]
    for check in results.get("checks", []):
        rows.append([check.get("name", "-"), fmt(check.get("calculated_psi")), fmt(check.get("allowable_psi")), f"{float(check.get('utilization', 0)) * 100:.1f}%", status_badge(check.get("result", "-"))])
    return rows


def result_status_styles(results: dict[str, Any]) -> list[tuple]:
    commands: list[tuple] = []
    for row_index, check in enumerate(results.get("checks", []), start=2):
        color, background = status_colors(str(check.get("result", "")))
        commands.extend([("BACKGROUND", (4, row_index), (4, row_index), background), ("TEXTCOLOR", (4, row_index), (4, row_index), color)])
    return commands


def metadata_rows(project, calc, scenario) -> list[list[str]]:
    return [
        ["Project", project.project_name or "-"],
        ["Project No.", project.project_number or "-"],
        ["Client", project.client or "-"],
        ["Location", project.location or "-"],
        ["Crossing", calc.crossing_name or "-"],
        ["Calculation Type", calc.calculation_type],
        ["Scenario", scenario.scenario_name or "Base Case"],
        ["Prepared By", calc.prepared_by or "-"],
        ["Checked By", calc.checked_by or "-"],
        ["Status", calc.status or "-"],
    ]


def purpose_rows(calc) -> list[list[str]]:
    return [
        ["Basis", "API RP 1102, 7th Ed. (2007, R2024)"],
        ["Purpose", f"Check combined stress of buried gas pipeline crossing under internal pressure and external {calc.calculation_type.lower()} loading."],
        ["References", "49 CFR Part 192, ASME B31.8, source workbooks"],
        ["Notes", calc.notes or "Allowables per API RP 1102 tables and ASME B31.8 design factor."],
    ]


def input_rows(values: dict[str, Any], calculation_type: str) -> list[list[str]]:
    keys = ["nps", "outside_diameter", "wall_thickness", "cover_depth", "bored_diameter", "operating_pressure", "soil_type", "soil_unit_weight", "pipe_specification", "pipe_grade"]
    if calculation_type == "Railroad":
        keys += ["surface_pressure", "number_of_tracks"]
    else:
        keys += ["pavement_type", "axle_configuration", "design_wheel_load"]
    return [[label(key), fmt_input(values.get(key))] for key in keys if key in values]


def warning_rows(warnings: list[dict[str, Any]]) -> list[list[str]]:
    if not warnings:
        return [["Severity", "Message", ""], ["None", "No warnings in this category.", ""]]
    return [["Severity", "Code", "Message"]] + [[w.get("severity", ""), w.get("code", ""), w.get("message", "")] for w in warnings]


def symbol_rows(calculation_type: str) -> list[list[str]]:
    mode = [["Fi", "Impact factor"], ["KH", "Circumferential live-load stiffness coefficient"], ["GH", "Circumferential geometry factor"], ["KL", "Longitudinal live-load stiffness coefficient"], ["GL", "Longitudinal geometry factor"]]
    if calculation_type == "Railroad":
        mode = [["Nh", "Double-track circumferential factor"], ["NL", "Double-track longitudinal factor"]] + mode
    shared = [["D", "Pipe outside diameter"], ["t", "Pipe wall thickness"], ["H", "Cover depth"], ["Bd", "Bore diameter"], ["SHi", "Internal pressure hoop stress"], ["SHe", "Earth load stress"], ["Seff", "Effective stress"], ["SMYS", "Specified minimum yield strength"]]
    return [["Symbol", "Meaning"]] + mode + shared


def equation_card(equation: EquationTrace, index: int, width: float = 3.4 * inch) -> Table:
    rows = [
        ["ITEM", "DETAILS"],
        ["Equation", equation.equation],
        ["Substitution", equation.substitution],
        ["Result", equation.result],
        ["Allowable", equation.allowable],
        ["Utilization", equation.utilization],
        ["Status", status_badge(equation.status)],
    ]
    return card(f"{index}   {equation.equation_id} - {equation.title}".upper(), rows, header_rows=1, col_widths=[1.15 * inch, width - 1.15 * inch])


def plot_card(plot: PlotArtifact | None, styles, width: float = 3.4 * inch) -> Table:
    if plot and plot.image_bytes:
        image = plot_image(plot, width=width - 0.32 * inch, height=2.1 * inch)
        body = [[image]]
    else:
        body = [[Paragraph("Plot could not be generated. Lookup values are listed in the plot appendix.", styles["CardText"])]]
    return card("INTERPOLATION PLOT", body, col_widths=[width])


def formula_trace_pages(equations: list[EquationTrace], plots: list[PlotArtifact], styles) -> list[Any]:
    flowables: list[Any] = [PageBreak(), PageSectionBar("Detailed Formula Trace"), Spacer(1, 14)]
    page_slots = 0
    for index, equation in enumerate(equations, start=1):
        plot = relevant_plot_for_equation(equation, plots)
        if page_slots >= 3:
            flowables += [PageBreak(), PageSectionBar("Detailed Formula Trace"), Spacer(1, 14)]
            page_slots = 0
        if plot:
            row = paired_formula_plot(equation_card(equation, index), plot_card(plot, styles))
            flowables.append(KeepTogether([row, Spacer(1, 7), Paragraph(plot.notes, styles["PlotNote"])]))
            flowables.append(Spacer(1, 22))
            page_slots += 1
        else:
            flowables.append(KeepTogether([equation_card(equation, index, width=6.8 * inch), Spacer(1, 8)]))
            flowables.append(Spacer(1, 16))
            page_slots += 1
    return flowables


def paired_formula_plot(formula: Table, plot: Table) -> Table:
    table = Table([[formula, plot]], colWidths=[3.55 * inch, 3.15 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def relevant_plot_for_equation(equation: EquationTrace, plots: list[PlotArtifact]) -> PlotArtifact | None:
    text = f"{equation.title} {equation.substitution}".lower()
    candidate_tokens = ["khh", "ghh", "klh", "glh", "khr", "ghr", "klr", "glr", "nh", "nl", "khe", "be", "ee", "fi"]
    tokens = [token for token in candidate_tokens if coefficient_token_present(text, token)]
    if not tokens:
        return None
    for token in tokens:
        for plot in plots:
            if token in plot.table_name.lower() or token in (plot.figure_label or "").lower():
                return plot
    return None


def coefficient_token_present(text: str, token: str) -> bool:
    if len(token) <= 2:
        candidates = [
            f"{token}=",
            f"{token} =",
            f" {token} ",
            f" {token},",
            f" {token};",
            f"({token})",
        ]
        return any(candidate in text for candidate in candidates)
    return token in text


def intermediate_sections(values: dict[str, Any], calculation_type: str) -> list[tuple[str, list[list[str]]]]:
    return [
        ("Internal Pressure", rows_for(values, ["SHi", "SHi_internal", "allowable_hoop"])),
        ("Earth Load", rows_for(values, ["Khe", "Be", "Ee", "SHe"])),
        (f"{calculation_type} Loading", rows_for(values, ["Fi", "KHh", "GHh", "KLh", "GLh", "SHh", "SLh", "KHr", "GHr", "KLr", "GLr", "Nh", "NL", "SHr", "SLr"])),
        ("Combined Stresses", rows_for(values, ["S1", "S2", "S3", "Seff", "allowable_effective"])),
        ("Fatigue / Welds", rows_for(values, ["SFG", "SFL", "allowable_girth", "allowable_longitudinal"])),
    ]


def rows_for(values: dict[str, Any], keys: list[str]) -> list[list[str]]:
    rows = [[key, fmt_input(values.get(key))] for key in keys if key in values]
    return rows or [["Value", "No stored intermediate values for this section."]]


def plot_block(plot: PlotArtifact, styles, full_size: bool = False):
    heading = plot.title if not plot.underlay_used else f"{plot.title} - API 1102 curve underlay"
    width = 6.65 * inch if full_size else 4.9 * inch
    height = 3.75 * inch if full_size else 2.75 * inch
    if plot.image_bytes:
        plot_content: list[list[Any]] = [[plot_image(plot, width=width, height=height)]]
    else:
        plot_content = [[Paragraph("Plot could not be generated. Lookup values used are listed below.", styles["CardText"])]]
    parts: list[Any] = [card(heading, plot_content, col_widths=[6.78 * inch if full_size else 5.05 * inch])]
    parts.append(Paragraph(plot.notes, styles["PlotNote"]))
    parts.append(Spacer(1, 6))
    parts.append(card("Lookup Values", plot.lookup_values, col_widths=[1.55 * inch, 5.23 * inch]))
    parts.append(Spacer(1, 14))
    return parts


def plot_image(plot: PlotArtifact, width: float, height: float) -> Image:
    return Image(BytesIO(plot.image_bytes or b""), width=width, height=height)


def fmt(value: Any) -> str:
    try:
        return f"{float(value):,.1f}"
    except (TypeError, ValueError):
        return "-"


def fmt_input(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:,.4g}"
    return str(value if value is not None else "-")


def label(key: str) -> str:
    return key.replace("_", " ").title()
