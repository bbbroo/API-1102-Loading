from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
import re
from typing import Any
from xml.sax.saxutils import escape

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
from reportlab.platypus import Flowable, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.backend.reporting.models import DetailedReportData, EquationTrace, PlotArtifact
from app.backend.reporting.service import first_intermediate
from app.standards.metadata import APP_VERSION, ENGINE_VERSION, SOURCE_WORKBOOKS, STANDARDS_VERSION

NAVY = colors.HexColor("#253646")
NAVY_DARK = colors.HexColor("#12263a")
BLUE_GRAY = colors.HexColor("#506176")
LINE = colors.HexColor("#cbd5e1")
GRID = colors.HexColor("#dce3eb")
SOFT = colors.HexColor("#f7f9fc")
SOFTER = colors.HexColor("#fbfcfe")
TEXT = colors.HexColor("#111827")
MUTED = colors.HexColor("#55677c")
GREEN = colors.HexColor("#027a48")
GREEN_BG = colors.HexColor("#ecfdf3")
RED = colors.HexColor("#b42318")
RED_BG = colors.HexColor("#fee4e2")
AMBER = colors.HexColor("#b54708")
AMBER_BG = colors.HexColor("#fffaeb")
TRACE = colors.HexColor("#475467")
TRACE_BG = colors.HexColor("#f2f4f7")
NA = colors.HexColor("#667085")
NA_BG = colors.HexColor("#f8fafc")

PAGE_WIDTH, PAGE_HEIGHT = letter
LEFT_MARGIN = 34
RIGHT_MARGIN = 34
TOP_MARGIN = 76
BOTTOM_MARGIN = 42
CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
MISSING = "\u2014"
ROOT_DIR = Path(__file__).resolve().parents[3]
HDR_LOGO_SVG = ROOT_DIR / "frontend" / "src" / "assets" / "hdr-logo.svg"
PLOT_NOTICE = (
    "Generated coefficient plots use implemented lookup data and digitized graph underlays for traceability. "
    "Verify coefficient values against the governing standard."
)

CELL = ParagraphStyle("ReportCell", fontName="Helvetica", fontSize=7.7, leading=9.3, textColor=TEXT)
CELL_SMALL = ParagraphStyle("ReportCellSmall", fontName="Helvetica", fontSize=7.0, leading=8.3, textColor=TEXT)
LABEL = ParagraphStyle("ReportLabel", parent=CELL, fontName="Helvetica-Bold")
HEADER_CELL = ParagraphStyle("ReportHeaderCell", parent=CELL, fontName="Helvetica-Bold", textColor=NAVY)
CARD_TITLE = ParagraphStyle("ReportCardTitle", fontName="Helvetica-Bold", fontSize=9.0, leading=10.5, textColor=colors.white)

_HDR_LOGO_IMAGE: ImageReader | None = None


def hdr_logo_image() -> ImageReader | None:
    global _HDR_LOGO_IMAGE
    if _HDR_LOGO_IMAGE is not None:
        return _HDR_LOGO_IMAGE
    if not HDR_LOGO_SVG.exists():
        return None
    svg = HDR_LOGO_SVG.read_text(encoding="utf-8")
    doc = fitz.open(stream=svg.encode("utf-8"), filetype="svg")
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=True)
    _HDR_LOGO_IMAGE = ImageReader(BytesIO(pix.tobytes("png")))
    return _HDR_LOGO_IMAGE


class SectionBar(Flowable):
    def __init__(self, title: str):
        super().__init__()
        self.title = title.upper()
        self.width = CONTENT_WIDTH
        self.height = 24

    def wrap(self, availWidth, availHeight):
        return availWidth, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(NAVY_DARK)
        canvas.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(10, 7, f"PAGE {canvas.getPageNumber()} - {self.title}")
        canvas.restoreState()


class StatusBadge(Flowable):
    def __init__(self, status: str):
        super().__init__()
        self.status = normalized_status(status)
        self.width = 0.76 * inch if self.status == "Trace" else max(0.76 * inch, min(1.35 * inch, 0.28 * inch + len(self.status) * 4.7))
        self.height = 19

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        canvas = self.canv
        canvas.saveState()
        fg, bg, solid = status_palette(self.status)
        canvas.setFillColor(fg if solid else bg)
        canvas.setStrokeColor(fg)
        canvas.roundRect(0, 1, self.width, self.height - 2, 3, fill=1, stroke=1)
        text_color = colors.white if solid else fg
        canvas.setStrokeColor(text_color)
        canvas.setFillColor(text_color)
        icon_x = 12
        icon_y = self.height / 2
        if self.status == "Pass":
            canvas.circle(icon_x, icon_y, 5, fill=0, stroke=1)
            canvas.setLineWidth(1.1)
            canvas.line(icon_x - 3, icon_y, icon_x - 1, icon_y - 2.5)
            canvas.line(icon_x - 1, icon_y - 2.5, icon_x + 4, icon_y + 3)
        elif self.status == "Fail":
            canvas.circle(icon_x, icon_y, 5, fill=0, stroke=1)
            canvas.setLineWidth(1.1)
            canvas.line(icon_x - 3, icon_y - 3, icon_x + 3, icon_y + 3)
            canvas.line(icon_x - 3, icon_y + 3, icon_x + 3, icon_y - 3)
        elif self.status in {"Needs Review", "Warning"}:
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawCentredString(icon_x, icon_y - 4, "!")
        elif self.status == "Trace":
            canvas.setFont("Helvetica-Bold", 7.8)
            canvas.drawCentredString(self.width / 2, 5.6, "Trace")
            canvas.restoreState()
            return
        else:
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawCentredString(icon_x, icon_y - 3, "-")
        canvas.setFont("Helvetica-Bold", 7.8)
        canvas.drawString(23, 5.6, self.status)
        canvas.restoreState()


class StatusStrip(Flowable):
    def __init__(self, data: DetailedReportData):
        super().__init__()
        self.data = data
        self.width = CONTENT_WIDTH
        self.height = 44

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        results = self.data.results
        items = [
            ("Overall Result", normalized_status(results.get("overall_result"))),
            ("Controlling Check", clean_text(results.get("controlling_check"))),
            ("Maximum Utilization", maximum_utilization(results)),
            ("Scenario", self.data.scenario.scenario_name or "Base Case"),
        ]
        canvas = self.canv
        canvas.saveState()
        canvas.setFillColor(NAVY_DARK)
        canvas.roundRect(0, 0, self.width, self.height, 4, fill=1, stroke=0)
        cell_w = self.width / len(items)
        for index, (label_text, value) in enumerate(items):
            x = index * cell_w
            if index:
                canvas.setStrokeColor(colors.HexColor("#40566b"))
                canvas.line(x, 7, x, self.height - 7)
            canvas.setFillColor(colors.HexColor("#d7e0eb"))
            canvas.setFont("Helvetica-Bold", 6.8)
            canvas.drawString(x + 9, self.height - 14, label_text.upper())
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 12 if index in {1, 2} else 10)
            canvas.drawString(x + 9, 10, str(value)[:26])
        canvas.restoreState()


class PipelineSchematic(Flowable):
    def __init__(self, values: dict[str, Any], calculation_type: str):
        super().__init__()
        self.values = values
        self.mode = "railroad" if calculation_type == "Railroad" else "highway"
        self.scale = 0.395
        self.diagram_width = 565
        self.diagram_height = 380
        self.width = self.diagram_width * self.scale
        self.height = self.diagram_height * self.scale

    def wrap(self, availWidth, availHeight):
        return min(self.width, availWidth), self.height

    def draw(self):
        canvas = self.canv
        cover = max(float_or(self.values.get("cover_depth"), 6), 0.1)
        d = max(float_or(self.values.get("outside_diameter"), 12.75), 0.1)
        bd = max(float_or(self.values.get("bored_diameter"), 14.75), d)
        tw = max(float_or(self.values.get("wall_thickness"), 0.25), 0.01)
        load = self.values.get("surface_pressure") if self.mode == "railroad" else self.values.get("design_wheel_load")
        load_label = f"w = {clean_number(load or 13.9, 1)} psi" if self.mode == "railroad" else f"W = {clean_number(load or 10000, 0)} lb"
        surface_y = 116 if self.mode == "railroad" else 108
        surface_height = 16 if self.mode == "railroad" else 24
        label_allowance = 56
        cover_in = cover * 12
        vertical_span_in = cover_in + (d + bd) / 2
        available_height = max(120, self.diagram_height - surface_y - label_allowance)
        available_width = 224
        geom_scale = min(available_height / vertical_span_in, available_width / bd)
        pipe_size = max(d * geom_scale, 6)
        bore_size = max(bd * geom_scale, pipe_size + 4)
        scaled_cover_height = cover_in * geom_scale
        pipe_top_y = surface_y + scaled_cover_height
        pipe_center_y = pipe_top_y + pipe_size / 2
        bore_top_y = pipe_center_y - bore_size / 2
        cover_start_y = surface_y
        cover_line_height = max(pipe_top_y - cover_start_y, 1)
        pipe_wall_size = max(2, min(8, tw * geom_scale))
        bore_border_size = max(2, min(7, ((bd - d) / 2) * geom_scale))

        canvas.saveState()
        canvas.scale(self.scale, self.scale)
        canvas.setStrokeColor(LINE)
        canvas.setFillColor(colors.HexColor("#f6fbfc"))
        canvas.rect(0, 0, self.diagram_width, self.diagram_height, fill=1, stroke=1)

        canvas.setFillColor(colors.HexColor("#eef7f8"))
        canvas.rect(0, self._y(0, surface_y), self.diagram_width, surface_y, fill=1, stroke=0)
        soil_top = surface_y + surface_height
        canvas.setFillColor(colors.HexColor("#e8ddc3"))
        canvas.rect(0, 0, self.diagram_width, self.diagram_height - soil_top, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#73694d"))
        canvas.setFont("Helvetica-Bold", 15)
        label_text = "Soil / backfill"
        label_w = canvas.stringWidth(label_text, "Helvetica-Bold", 15)
        label_right = self.diagram_width - 82
        label_bottom_y = self._y(soil_top + 34, 15)
        canvas.setFillColor(colors.HexColor("#f2ead7"))
        canvas.roundRect(label_right - label_w - 16, label_bottom_y - 4, label_w + 16, 23, 4, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#73694d"))
        canvas.drawRightString(label_right, label_bottom_y, label_text)

        if self.mode == "railroad":
            self._draw_train(canvas, surface_y)
            self._draw_track(canvas, surface_y)
            canvas.setFillColor(colors.HexColor("#4b5563"))
            canvas.rect(0, self._y(surface_y, surface_height), self.diagram_width, surface_height, fill=1, stroke=0)
            canvas.setFillColor(colors.HexColor("#2b3138"))
            canvas.rect(0, self._y(surface_y, 5), self.diagram_width, 5, fill=1, stroke=0)
        else:
            y0 = self._y(surface_y, surface_height)
            segment = self.diagram_width / 5
            for index in range(5):
                canvas.setFillColor(colors.HexColor("#6c737d") if index % 2 == 0 else colors.HexColor("#8a939d"))
                canvas.rect(index * segment, y0, segment, surface_height, fill=1, stroke=0)
            canvas.setStrokeColor(colors.HexColor("#5f6570"))
            canvas.setLineWidth(4)
            canvas.line(0, self._y(surface_y, 0), self.diagram_width, self._y(surface_y, 0))
            canvas.setStrokeColor(colors.HexColor("#8b7c5b"))
            canvas.setLineWidth(5)
            canvas.line(0, self._y(surface_y + surface_height, 0), self.diagram_width, self._y(surface_y + surface_height, 0))
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 11)
            canvas.drawCentredString(self.diagram_width / 2, y0 + surface_height / 2 - 4, "Road surface")
            self._draw_vehicle(canvas, surface_y)
            canvas.setStrokeColor(colors.white)
            canvas.setLineWidth(3)
            road_y = self._y(surface_y + 13, 0)
            x = self.diagram_width / 2 - 58
            while x < self.diagram_width / 2 + 58:
                canvas.line(x, road_y, min(x + 24, self.diagram_width / 2 + 58), road_y)
                x += 38

        load_x = self.diagram_width / 2
        load_y = surface_y - 74
        canvas.setFillColor(RED)
        canvas.setStrokeColor(RED)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawCentredString(load_x, self._y(load_y, 12), load_label)
        arrow_top = load_y + 16
        arrow_bottom = load_y + 47
        canvas.setLineWidth(3)
        canvas.line(load_x, self._y(arrow_top, 0), load_x, self._y(arrow_bottom, 0))
        canvas.line(load_x - 7, self._y(arrow_bottom - 7, 0), load_x, self._y(arrow_bottom, 0))
        canvas.line(load_x + 7, self._y(arrow_bottom - 7, 0), load_x, self._y(arrow_bottom, 0))

        cover_x = 58
        cover_y = self._y(cover_start_y + cover_line_height, 0)
        canvas.setStrokeColor(colors.HexColor("#7f5f35"))
        canvas.setLineWidth(3)
        # Main dimension line between the arrowhead bases
        canvas.line(cover_x, cover_y + 8, cover_x, cover_y + cover_line_height - 8)
        # Top arrowhead: tip at surface, base set inward (points outward/upward)
        canvas.line(cover_x - 8, cover_y + cover_line_height - 8, cover_x, cover_y + cover_line_height)
        canvas.line(cover_x + 8, cover_y + cover_line_height - 8, cover_x, cover_y + cover_line_height)
        # Bottom arrowhead: tip at pipe, base set inward (points outward/downward)
        canvas.line(cover_x - 8, cover_y + 8, cover_x, cover_y)
        canvas.line(cover_x + 8, cover_y + 8, cover_x, cover_y)
        canvas.setFillColor(colors.HexColor("#4b3920"))
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(cover_x + 14, cover_y + cover_line_height / 2 - 6, f"H = {clean_number(cover, 1)} ft to top of pipe")

        bore_x = self.diagram_width / 2
        bore_y = self._y(bore_top_y + bore_size, 0)
        bore_r = bore_size / 2
        pipe_r = pipe_size / 2
        canvas.setFillColor(colors.HexColor("#e7ecf1"))
        canvas.setStrokeColor(colors.HexColor("#bcae8d"))
        canvas.setLineWidth(bore_border_size)
        canvas.circle(bore_x, bore_y + bore_r, bore_r, fill=1, stroke=1)
        canvas.setFillColor(colors.HexColor("#c8d2db"))
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(pipe_wall_size)
        canvas.circle(bore_x, bore_y + bore_r, pipe_r, fill=1, stroke=1)
        canvas.setFillColor(colors.white)
        canvas.circle(bore_x, bore_y + bore_r, pipe_r * 0.62, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#17212b"))
        canvas.setFont("Helvetica-Bold", 10)
        pipe_label = f"D {clean_number(d, 3)} in"
        pipe_label_x = bore_x + bore_r + 8
        pipe_label_y = bore_y + bore_r - 3.5
        pipe_label_w = canvas.stringWidth(pipe_label, "Helvetica-Bold", 10)
        canvas.setFillColor(colors.white)
        canvas.roundRect(pipe_label_x - 2, pipe_label_y - 8, pipe_label_w + 4, 13, 3, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#17212b"))
        canvas.drawString(pipe_label_x, pipe_label_y, pipe_label)
        canvas.setFillColor(colors.HexColor("#475467"))
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawCentredString(bore_x, bore_y - 24, f"Bd {clean_number(bd, 3)} in")
        canvas.restoreState()

    def _y(self, css_y: float, height: float) -> float:
        return self.diagram_height - css_y - height

    def _draw_vehicle(self, canvas, surface_y: float) -> None:
        left = self.diagram_width / 2 - 64
        top = surface_y - 41
        bottom = self._y(top + 40, 0)
        canvas.setFillColor(colors.HexColor("#24313f"))
        canvas.roundRect(left + 8, bottom + 9, 73, 25, 4, fill=1, stroke=0)
        canvas.roundRect(left + 73, bottom + 9, 45, 34, 8, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#b9dce8"))
        canvas.roundRect(left + 88, bottom + 25, 19, 10, 2, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#f8fafc"))
        canvas.setStrokeColor(colors.HexColor("#1f2933"))
        canvas.setLineWidth(6)
        canvas.circle(left + 36, bottom + 10, 11, fill=1, stroke=1)
        canvas.circle(left + 97, bottom + 10, 11, fill=1, stroke=1)

    def _draw_track(self, canvas, surface_y: float) -> None:
        left = self.diagram_width / 2 - 85
        top = surface_y - 12
        # Draw ties: frontend uses transform:rotate(90deg) on 10×28 elements,
        # making them appear as 28×10 horizontal bars centered at (left+x+5, top+13)
        canvas.setFillColor(colors.HexColor("#7a5a3a"))
        for x in (30, 80, 130):
            canvas.roundRect(left + x - 9, self._y(top + 8, 10), 28, 10, 2, fill=1, stroke=0)
        # Draw single rail above ties, between wheels and ties
        canvas.setFillColor(colors.HexColor("#2b3138"))
        canvas.roundRect(left, self._y(top + 3, 5), 170, 5, 2, fill=1, stroke=0)

    def _draw_train(self, canvas, surface_y: float) -> None:
        cx = self.diagram_width / 2
        container_left = cx - 77
        train_top = surface_y - 47  # CSS top of train body elements (container top 64 + 5)
        engine_left = container_left + 15
        engine_right = engine_left + 56
        car_left = container_left + 154 - 14 - 68  # right edge - 14 - width
        car_right = car_left + 68
        wheel_centers_y = 100.5  # CSS center-y (wheel bottom 107 at rail top 107)

        # engine body
        canvas.setFillColor(colors.HexColor("#263746"))
        canvas.roundRect(engine_left, self._y(train_top, 28), 56, 28, 8, fill=1, stroke=0)
        # engine smokestack (::before)
        canvas.roundRect(engine_left + 8, self._y(train_top - 9, 10), 18, 10, 3, fill=1, stroke=0)
        # engine window (::after)
        canvas.setFillColor(colors.HexColor("#b9dce8"))
        canvas.roundRect(engine_right - 8 - 16, self._y(train_top + 7, 9), 16, 9, 2, fill=1, stroke=0)

        # car body
        canvas.setFillColor(colors.HexColor("#354658"))
        canvas.roundRect(car_left, self._y(train_top, 28), 68, 28, 8, fill=1, stroke=0)
        # car window (::after)
        canvas.setFillColor(colors.HexColor("#b9dce8"))
        canvas.roundRect(car_right - 12 - 30, self._y(train_top + 7, 9), 30, 9, 2, fill=1, stroke=0)

        # wheels
        wheel_y = self._y(wheel_centers_y, 0)
        canvas.setFillColor(colors.HexColor("#f8fafc"))
        canvas.setStrokeColor(colors.HexColor("#1f2933"))
        canvas.setLineWidth(4)
        wheel_radius = 4.5
        for wx in (container_left + 24 + 6.5, container_left + 53 + 6.5,
                   container_left + 154 - 54 - 6.5, container_left + 154 - 23 - 6.5):
            canvas.circle(wx, wheel_y, wheel_radius, fill=1, stroke=1)


def render_detailed_pdf(data: DetailedReportData) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        pageCompression=0,
    )
    styles = get_styles()
    story: list[Any] = []
    story.extend(executive_calculation_sheet(data, styles))
    story.extend(input_register_and_warnings(data, styles))
    story.extend(symbols_and_methodology(data, styles))
    if data.options.include_formula_trace:
        story.extend(detailed_formula_trace(data, styles))
    if data.options.include_intermediates:
        story.extend(intermediate_values_dashboard(data, styles))
    if data.options.include_plots:
        story.extend(coefficient_lookup_summary(data, styles))
    if data.options.include_appendix_plots:
        story.extend(appendix_full_size_plots(data, styles))
    story.extend(references_page(data, styles))
    doc.build(story, onFirstPage=lambda c, d: page_frame(c, d, data), onLaterPages=lambda c, d: page_frame(c, d, data))
    return buffer.getvalue()


def executive_calculation_sheet(data: DetailedReportData, styles) -> list[Any]:
    values = first_intermediate(data.intermediate_values)
    return [
        SectionBar("Executive Calculation Sheet"),
        Spacer(1, 6),
        StatusStrip(data),
        Spacer(1, 6),
        two_column(
            card("Project & Calculation", executive_metadata_rows(data), col_widths=[1.08 * inch, 2.25 * inch]),
            card("Purpose & References", executive_purpose_rows(data), col_widths=[0.92 * inch, 2.41 * inch]),
        ),
        Spacer(1, 6),
        two_column(
            card("Inputs & Assumptions", executive_input_rows(values, data.calculation.calculation_type), col_widths=[1.2 * inch, 2.13 * inch]),
            card("Pipeline Cross-Section Schematic", [[PipelineSchematic(values, data.calculation.calculation_type)]], col_widths=[3.33 * inch]),
        ),
        Spacer(1, 6),
        two_column(
            card("Intermediate Calculations", executive_intermediate_rows(values, data.calculation.calculation_type), col_widths=[1.25 * inch, 2.08 * inch]),
            card("Report Metadata", timing_rows(data), col_widths=[1.25 * inch, 2.08 * inch]),
        ),
        Spacer(1, 6),
        card("Results Summary", result_rows(data.results), header_rows=1, col_widths=[1.86 * inch, 1.14 * inch, 1.13 * inch, 0.98 * inch, 1.02 * inch], style_rows=result_status_styles(data.results) + result_alignment_styles()),
    ]


def input_register_and_warnings(data: DetailedReportData, styles) -> list[Any]:
    values = first_intermediate(data.intermediate_values)
    parts: list[Any] = [PageBreak(), SectionBar("Input Register & Warnings"), Spacer(1, 10)]
    groups = input_register_groups(values, data)
    for row in range(0, len(groups), 2):
        left_title, left_rows = groups[row]
        right_title, right_rows = groups[row + 1] if row + 1 < len(groups) else ("", [["", "", "", ""]])
        parts.append(
            two_column(
                card(left_title, left_rows, header_rows=1, col_widths=[1.12 * inch, 0.82 * inch, 0.45 * inch, 0.94 * inch]),
                card(right_title, right_rows, header_rows=1, col_widths=[1.12 * inch, 0.82 * inch, 0.45 * inch, 0.94 * inch]),
            )
        )
        parts.append(Spacer(1, 7))
    if data.options.include_warnings:
        parts.append(two_column(warning_card("Critical Warnings", data.critical_warnings), warning_card("Informational Warnings", data.informational_warnings)))
    return parts


def symbols_and_methodology(data: DetailedReportData, styles) -> list[Any]:
    methodology = [
        ["Step", "Reviewer Flow"],
        ["1", "Confirm scenario inputs and trusted-result freshness."],
        ["2", "Review key geometry, pressure, soil, and loading assumptions."],
        ["3", "Check stored stress results, allowables, utilization, and controlling condition."],
        ["4", "Review coefficient lookup/interpolation traceability and appendix plots."],
        ["5", "Verify applicability against governing standards and project requirements."],
    ]
    return [
        PageBreak(),
        SectionBar("Symbols & Methodology"),
        Spacer(1, 10),
        two_column(
            card("Symbol Legend", symbol_rows(data.calculation.calculation_type), header_rows=1, col_widths=[0.62 * inch, 1.95 * inch, 0.76 * inch]),
            card("Methodology", methodology, header_rows=1, col_widths=[0.55 * inch, 2.78 * inch]),
        ),
        Spacer(1, 8),
        card("Traceability Boundary", [["Source of Truth", "Engineering formulas, pass/fail logic, warnings, and calculated values are produced by the calculation engine. This report formats stored results for review and does not independently recalculate design formulas."]], col_widths=[1.3 * inch, 5.42 * inch]),
    ]


def detailed_formula_trace(data: DetailedReportData, styles) -> list[Any]:
    parts: list[Any] = [PageBreak(), SectionBar("Detailed Formula Trace"), Spacer(1, 10)]
    for index, equation in enumerate(data.equations, start=1):
        block = [formula_card(equation, index), Spacer(1, 7)]
        parts.append(KeepTogether(block))
    return parts


def intermediate_values_dashboard(data: DetailedReportData, styles) -> list[Any]:
    values = first_intermediate(data.intermediate_values)
    sections = intermediate_sections(values, data.calculation.calculation_type)
    parts: list[Any] = [PageBreak(), SectionBar("Intermediate Values"), Spacer(1, 10)]
    for row in range(0, len(sections), 2):
        left_title, left_rows = sections[row]
        right_title, right_rows = sections[row + 1] if row + 1 < len(sections) else ("", [["Value", ""]])
        parts.append(
            two_column(
                card(left_title, left_rows, header_rows=1, col_widths=[1.25 * inch, 1.28 * inch, 0.8 * inch], style_rows=dashboard_card_styles()),
                card(right_title, right_rows, header_rows=1, col_widths=[1.25 * inch, 1.28 * inch, 0.8 * inch], style_rows=dashboard_card_styles()),
            )
        )
        parts.append(Spacer(1, 8))
    return parts


def dashboard_card_styles() -> list[tuple]:
    return [
        ("FONTSIZE", (0, 1), (-1, -1), 8.2),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
    ]


def coefficient_lookup_summary(data: DetailedReportData, styles) -> list[Any]:
    plots = report_plots(data)
    values = first_intermediate(data.intermediate_values)
    rows = [["Coeff.", "Figure", "Input x", "Lower", "Upper", "Selected", "Method", "Appendix"]]
    for index, plot in enumerate(plots, start=1):
        rows.append(
            [
                coefficient_name(plot),
                clean_text(plot.figure_label or plot.figure_id),
                lookup_value(plot, "Input x") or clean_lookup_value(plot.x_value),
                lookup_value(plot, "Lower bound"),
                lookup_value(plot, "Upper bound"),
                used_coefficient_display(plot, values),
                lookup_status(plot),
                f"Fig. A-{index}" if data.options.include_appendix_plots else MISSING,
            ]
        )
    if len(rows) == 1:
        rows.append(["No lookup traces", MISSING, MISSING, MISSING, MISSING, MISSING, "No interpolation traces were available.", MISSING])
    return [
        PageBreak(),
        SectionBar("Coefficient Lookup Summary"),
        Spacer(1, 8),
        Paragraph("Compact lookup/interpolation register. Full-size generated plots are provided in the appendix when enabled.", styles["Note"]),
        Spacer(1, 8),
        card("Lookup Summary", rows, header_rows=1, col_widths=[0.58 * inch, 1.15 * inch, 0.82 * inch, 0.72 * inch, 0.72 * inch, 0.82 * inch, 0.95 * inch, 0.96 * inch], style_rows=lookup_alignment_styles()),
    ]


def appendix_full_size_plots(data: DetailedReportData, styles) -> list[Any]:
    plots = report_plots(data)
    values = first_intermediate(data.intermediate_values)
    parts: list[Any] = [PageBreak(), SectionBar("Appendix Full-Size Plots"), Spacer(1, 8), Paragraph(PLOT_NOTICE, styles["Note"]), Spacer(1, 8)]
    if not plots:
        parts.append(card("Appendix Full-Size Plots", [["Plot Status", "No interpolation traces were available for appendix plots."]], col_widths=[1.35 * inch, 5.37 * inch]))
        return parts
    for index, plot in enumerate(plots, start=1):
        parts.extend(plot_block(plot, styles, index, values))
    return parts


def references_page(data: DetailedReportData, styles) -> list[Any]:
    rows = [
        ["Used Source Workbooks", used_source_workbooks(data.calculation.calculation_type)],
        ["Application", APP_VERSION],
        ["Engine", ENGINE_VERSION],
        ["Standards", STANDARDS_VERSION],
        ["Generated", format_timestamp(data.generated_at)],
        ["Report Type", "Detailed Scenario Report"],
        ["Scenario Name", data.scenario.scenario_name or "Base Case"],
        ["Engineering Disclaimer", "This report is for engineering documentation and review. Verify applicability, assumptions, lookup data, and governing standard requirements before use."],
    ]
    traceability = [
        ["Stored Results", "Displayed values are formatted from stored calculation-engine outputs."],
        ["Lookup Plots", "Generated plots and digitized underlays are reviewer traceability aids and do not replace the governing standard."],
        ["Review", "Independent engineering checking remains required before design or construction use."],
    ]
    return [
        PageBreak(),
        SectionBar("References"),
        Spacer(1, 10),
        card("References", rows, col_widths=[1.35 * inch, 5.37 * inch]),
        Spacer(1, 10),
        card("Traceability Notes", traceability, col_widths=[1.35 * inch, 5.37 * inch]),
    ]


def used_source_workbooks(calculation_type: str) -> str:
    key = calculation_type.lower()
    workbook = SOURCE_WORKBOOKS.get(key)
    return workbook or ", ".join(SOURCE_WORKBOOKS.values())


def get_styles():
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "Helvetica"
    styles["Normal"].fontSize = 8.3
    styles["Normal"].leading = 10
    styles.add(ParagraphStyle("HeaderRight", parent=styles["Normal"], fontSize=9.2, leading=10.5, textColor=TEXT, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("HeaderKicker", parent=styles["Normal"], fontSize=7.0, leading=8.2, textColor=TEXT, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("Note", parent=styles["Italic"], fontSize=7.4, leading=8.7, textColor=MUTED))
    styles.add(ParagraphStyle("CenterNote", parent=styles["Normal"], fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=MUTED))
    return styles


def page_frame(canvas, doc, data: DetailedReportData) -> None:
    canvas.saveState()
    calc = data.calculation
    y = PAGE_HEIGHT - 42
    logo = hdr_logo_image()
    if logo:
        canvas.drawImage(logo, LEFT_MARGIN, y - 15, width=56, height=31, preserveAspectRatio=True, mask="auto")
    else:
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 25)
        canvas.drawString(LEFT_MARGIN, y - 7, "HDR")
    canvas.setFont("Helvetica-Bold", 9.2)
    canvas.drawString(LEFT_MARGIN + 66, y + 2, f"API RP 1102 {calc.calculation_type.upper()} LOADING CALCULATOR")
    canvas.setFont("Helvetica", 8.2)
    canvas.setFillColor(MUTED)
    canvas.drawString(LEFT_MARGIN + 66, y - 12, "GAS PIPELINE - TECHNICAL TOOL")
    canvas.setFillColor(TEXT)
    canvas.setFont("Helvetica", 6.9)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y + 16, "ENGINEERING CALCULATION PACKAGE")
    canvas.setFont("Helvetica", 11)
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y, f"API RP 1102 {calc.calculation_type} Loading Analysis")
    canvas.setFont("Helvetica", 8.2)
    date_text = format_date(calc.date)
    if date_text == MISSING:
        date_text = f"Date: {format_timestamp(data.generated_at).split(' ')[0]}"
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN, y - 13, f"Calc {calc.calc_number or MISSING} - Rev {calc.revision or '0'} - {date_text} - {calc.status or MISSING}")
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(0.9)
    canvas.line(LEFT_MARGIN, PAGE_HEIGHT - 69, PAGE_WIDTH - RIGHT_MARGIN, PAGE_HEIGHT - 69)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7.2)
    canvas.drawString(LEFT_MARGIN + 2, 24, f"API RP 1102 Loading Calculator - {data.scenario.scenario_name or 'Base Case'}")
    canvas.drawRightString(PAGE_WIDTH - RIGHT_MARGIN - 2, 24, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def two_column(left: Flowable, right: Flowable) -> Table:
    table = Table([[left, right]], colWidths=[3.36 * inch, 3.36 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return table


def card(title: str, rows: list[list[Any]], header_rows: int = 0, col_widths: list[float] | None = None, style_rows: list[tuple] | None = None) -> Table:
    width = max((len(row) for row in rows), default=1)
    body = [[Paragraph(escape(title), CARD_TITLE)] + [""] * (width - 1)]
    body.extend(normalize_rows(rows, header_rows=header_rows))
    table = Table(body, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    commands = [
        ("SPAN", (0, 0), (-1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY_DARK),
        ("BOX", (0, 0), (-1, -1), 0.65, LINE),
        ("INNERGRID", (0, 1), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]
    if len(body) > 1:
        commands.append(("ROWBACKGROUNDS", (0, 1 + header_rows), (-1, -1), [colors.white, SOFT]))
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
    normalized = []
    for row_index, row in enumerate(rows):
        padded = row + [""] * (width - len(row))
        normalized.append([cell_value(value, header=row_index < header_rows, label_cell=column_index == 0) for column_index, value in enumerate(padded)])
    return normalized


def cell_value(value: Any, *, header: bool = False, label_cell: bool = False) -> Any:
    if isinstance(value, Flowable):
        return value
    text = clean_display_text(value) if isinstance(value, str) else clean_text(value)
    style = HEADER_CELL if header else LABEL if label_cell else CELL
    return Paragraph(escape(text), style)


def clean_display_text(value: str) -> str:
    stripped = value.strip()
    if stripped in {"", "-", "None", "null"}:
        return MISSING
    return stripped


def status_badge(status: str) -> StatusBadge:
    return StatusBadge(status)


def normalized_status(status: Any) -> str:
    text = clean_text(status)
    if text in {"Pass", "Fail", "Needs Review", "Warning", "Trace"}:
        return text
    if text in {MISSING, "-", "N/A", "Not Calculated"}:
        return "Not Calculated" if text == "Not Calculated" else "N/A"
    return text


def status_palette(status: str):
    if status == "Pass":
        return GREEN, GREEN_BG, True
    if status == "Fail":
        return RED, RED_BG, True
    if status in {"Needs Review", "Warning"}:
        return AMBER, AMBER_BG, True
    if status == "Trace":
        return TRACE, TRACE_BG, False
    return NA, NA_BG, False


def status_colors(status: str):
    fg, bg, _solid = status_palette(normalized_status(status))
    return fg, bg


def metadata_rows(data: DetailedReportData) -> list[list[str]]:
    project = data.project
    calc = data.calculation
    scenario = data.scenario
    return [
        ["Project", project.project_name],
        ["Project No.", project.project_number],
        ["Client", project.client],
        ["Location", project.location],
        ["Crossing", calc.crossing_name],
        ["Calculation Type", calc.calculation_type],
        ["Scenario", scenario.scenario_name or "Base Case"],
        ["Prepared By", calc.prepared_by],
        ["Checked By", calc.checked_by],
    ]


def executive_metadata_rows(data: DetailedReportData) -> list[list[str]]:
    project = data.project
    calc = data.calculation
    scenario = data.scenario
    return [
        ["Project", project.project_name],
        ["Project No.", project.project_number],
        ["Crossing", calc.crossing_name],
        ["Calculation Type", calc.calculation_type],
        ["Scenario", scenario.scenario_name or "Base Case"],
        ["Prepared / Checked", f"{clean_text(calc.prepared_by)} / {clean_text(calc.checked_by)}"],
    ]


def purpose_rows(data: DetailedReportData) -> list[list[str]]:
    calc = data.calculation
    return [
        ["Basis", "API RP 1102, 7th Ed. (2007, R2024)"],
        ["Purpose", f"Check combined stress of buried gas pipeline crossing under internal pressure and external {calc.calculation_type.lower()} loading."],
        ["References", "49 CFR Part 192, ASME B31.8, source workbooks"],
        ["Notes", calc.notes or "Allowables per API RP 1102 tables and ASME B31.8 design factor."],
    ]


def executive_purpose_rows(data: DetailedReportData) -> list[list[str]]:
    calc = data.calculation
    return [
        ["Basis", "API RP 1102, 7th Ed. (2007, R2024)"],
        ["Purpose", f"Combined stress check for buried gas pipeline under internal pressure and {calc.calculation_type.lower()} loading."],
        ["References", "49 CFR Part 192, ASME B31.8, source workbooks"],
    ]


def timing_rows(data: DetailedReportData) -> list[list[str]]:
    return [
        ["Generated", format_timestamp(data.generated_at)],
        ["Scenario Calculated", format_timestamp(data.results.get("calculated_at"))],
        ["Application / Engine", f"{APP_VERSION} / {ENGINE_VERSION}"],
        ["Standards", STANDARDS_VERSION],
    ]


def executive_input_rows(values: dict[str, Any], calculation_type: str) -> list[list[str]]:
    keys = ["nps", "outside_diameter", "wall_thickness", "cover_depth", "bored_diameter", "operating_pressure"]
    keys += ["surface_pressure"] if calculation_type == "Railroad" else ["design_wheel_load"]
    return [[label(key), executive_value_with_unit(key, values.get(key))] for key in keys if key in values]


def executive_intermediate_rows(values: dict[str, Any], calculation_type: str) -> list[list[str]]:
    keys = ["SHi", "Seff", "allowable_effective", "SFG", "SFL"]
    keys += ["SHr"] if calculation_type == "Railroad" else ["SHh"]
    rows = [[label(key), executive_value_with_unit(key, values.get(key))] for key in keys if key in values]
    return rows[:4]


def input_register_groups(values: dict[str, Any], data: DetailedReportData) -> list[tuple[str, list[list[str]]]]:
    calculation_type = data.calculation.calculation_type
    groups = [
        ("Project / Scenario", input_group_rows(values, [], {"Calculation": calculation_type, "Scenario": data.scenario.scenario_name or "Base Case", "Status": data.calculation.status or MISSING})),
        ("Pipe Geometry", input_group_rows(values, ["nps", "outside_diameter", "wall_thickness", "cover_depth", "bored_diameter"])),
        ("Material / Design", input_group_rows(values, ["pipe_specification", "pipe_grade", "SMYS", "design_factor"])),
        ("Operating Conditions", input_group_rows(values, ["operating_pressure", "temperature"])),
        ("Soil / Installation", input_group_rows(values, ["soil_type", "soil_unit_weight", "soil_modulus", "installation_type"])),
    ]
    mode_keys = ["surface_pressure", "number_of_tracks", "track_spacing"] if calculation_type == "Railroad" else ["pavement_type", "axle_configuration", "design_wheel_load", "wheel_spacing"]
    groups.append((f"{calculation_type} Loading", input_group_rows(values, mode_keys)))
    return groups


def input_group_rows(values: dict[str, Any], keys: list[str], extras: dict[str, Any] | None = None) -> list[list[str]]:
    rows = [["Input", "Value", "Unit", "Notes"]]
    for name, extra_value in (extras or {}).items():
        rows.append([name, clean_text(extra_value), "", "Report metadata"])
    for key in keys:
        if key in values:
            rows.append([label(key), clean_number(values.get(key)), unit_for(key), note_for(key)])
    if len(rows) == 1:
        rows.append(["No values", MISSING, MISSING, "No stored inputs in this group."])
    return rows


def warning_card(title: str, warnings: list[dict[str, Any]]) -> Table:
    if not warnings:
        severity = "critical" if "Critical" in title else "informational"
        return card(f"{title}: None", [["Review Status", f"No {severity} warnings reported."]], col_widths=[0.9 * inch, 2.43 * inch])
    rows = [["Severity", "Message"]] + [[warning.get("severity"), warning.get("message")] for warning in warnings]
    return card(title, rows, header_rows=1, col_widths=[0.75 * inch, 2.58 * inch])


def symbol_rows(calculation_type: str) -> list[list[str]]:
    mode = [["KHe", "Earth load stiffness coefficient", "factor"], ["Be", "Burial factor", "factor"], ["Ee", "Excavation factor", "factor"], ["Fi", "Impact factor", "factor"], ["KHh", "Highway circumferential stiffness coefficient", "factor"], ["GHh", "Highway circumferential geometry factor", "factor"], ["KLh", "Highway longitudinal stiffness coefficient", "factor"], ["GLh", "Highway longitudinal geometry factor", "factor"]]
    if calculation_type == "Railroad":
        mode = [["KHr", "Railroad circumferential stiffness coefficient", "factor"], ["GHr", "Railroad circumferential geometry factor", "factor"], ["KLr", "Railroad longitudinal stiffness coefficient", "factor"], ["GLr", "Railroad longitudinal geometry factor", "factor"], ["Nh", "Double-track circumferential factor", "factor"], ["NL", "Double-track longitudinal factor", "factor"], ["Fi", "Impact factor", "factor"]]
    shared = [["D", "Pipe outside diameter", "in"], ["t", "Pipe wall thickness", "in"], ["H", "Cover depth", "ft"], ["Bd", "Bore diameter", "in"], ["SHi", "Internal pressure hoop stress", "psi"], ["SHe", "Earth load stress", "psi"], ["SHh", "Highway circumferential live-load stress", "psi"], ["SLh", "Highway longitudinal live-load stress", "psi"], ["Seff", "Effective stress", "psi"], ["SMYS", "Specified minimum yield strength", "psi"]]
    return [["Sym.", "Meaning", "Unit"]] + mode + shared


def formula_card(equation: EquationTrace, index: int) -> Table:
    trace_only = normalized_status(equation.status) == "Trace"
    rows: list[list[Any]] = [
        ["Equation", clean_equation_text(equation.equation)],
        ["Result Summary", formula_summary_table(equation, trace_only)],
        ["Substitution", clean_equation_text(equation.substitution)],
        ["Notes", formula_note(equation)],
    ]
    return card(f"{index}  {equation.equation_id} - {equation.title}".upper(), rows, col_widths=[1.18 * inch, 5.54 * inch])


def formula_summary_table(equation: EquationTrace, trace_only: bool) -> Table:
    if trace_only:
        rows: list[list[Any]] = [
            [formula_cell("Calculated Result", header=True), formula_cell("Compliance", header=True), formula_cell("Status", header=True)],
            [formula_cell(clean_equation_text(equation.result)), formula_cell("Trace item only; pass/fail compliance is evaluated in combined or fatigue checks."), status_badge(equation.status)],
        ]
        widths = [1.6 * inch, 2.95 * inch, 0.9 * inch]
    else:
        rows = [
            [formula_cell("Calculated Result", header=True), formula_cell("Allowable", header=True), formula_cell("Utilization", header=True), formula_cell("Status", header=True)],
            [formula_cell(clean_equation_text(equation.result)), formula_cell(clean_equation_text(equation.allowable)), formula_cell(clean_text(equation.utilization)), status_badge(equation.status)],
        ]
        widths = [1.75 * inch, 1.45 * inch, 1.0 * inch, 0.9 * inch]
    table = Table(rows, colWidths=widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3f7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.7),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, GRID),
                ("BOX", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def formula_cell(text: str, *, header: bool = False) -> Paragraph:
    return Paragraph(escape(text), HEADER_CELL if header else CELL)


def formula_note(equation: EquationTrace) -> str:
    if normalized_status(equation.status) == "Trace":
        return "Coefficient lookup details are summarized in the Coefficient Lookup Summary and appendix plots where available."
    return "Stored calculation-engine result. Rounded display values are shown for report readability."


def result_rows(results: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = [["Check", "Calculated (psi)", "Allowable (psi)", "Utilization", "Status"]]
    for check in results.get("checks", []):
        rows.append([check.get("name"), clean_number(check.get("calculated_psi"), 1), clean_number(check.get("allowable_psi"), 1), percent_from_fraction(check.get("utilization")), status_badge(check.get("result"))])
    return rows


def result_status_styles(results: dict[str, Any]) -> list[tuple]:
    commands: list[tuple] = []
    for row_index, check in enumerate(results.get("checks", []), start=2):
        color, background = status_colors(str(check.get("result", "")))
        commands.extend([("BACKGROUND", (4, row_index), (4, row_index), background), ("TEXTCOLOR", (4, row_index), (4, row_index), color)])
    return commands


def result_alignment_styles() -> list[tuple]:
    return [("ALIGN", (1, 2), (3, -1), "RIGHT")]


def lookup_alignment_styles() -> list[tuple]:
    return [
        ("ALIGN", (2, 2), (5, -1), "RIGHT"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]


def intermediate_sections(values: dict[str, Any], calculation_type: str) -> list[tuple[str, list[list[str]]]]:
    return [
        ("Internal Pressure", rows_for(values, ["SHi", "SHi_internal", "allowable_hoop"])),
        ("Earth Load", rows_for(values, ["Khe", "Be", "Ee", "SHe"])),
        (f"{calculation_type} Loading", rows_for(values, ["Fi", "KHh", "GHh", "KLh", "GLh", "SHh", "SLh", "KHr", "GHr", "KLr", "GLr", "Nh", "NL", "SHr", "SLr"])),
        ("Combined / Fatigue", rows_for(values, ["S1", "S2", "S3", "Seff", "allowable_effective", "SFG", "SFL", "allowable_girth", "allowable_longitudinal"])),
    ]


def rows_for(values: dict[str, Any], keys: list[str]) -> list[list[str]]:
    rows = [["Value", "Magnitude", "Unit"]]
    rows += [[label(key), value_display(key, values.get(key)), unit_for(key)] for key in keys if key in values]
    return rows if len(rows) > 1 else [["Value", "Magnitude", "Unit"], ["No values", "No stored values", ""]]


def plot_block(plot: PlotArtifact, styles, index: int, values: dict[str, Any]) -> list[Any]:
    heading = f"Figure A-{index}: {plot.title}"
    if plot.underlay_used:
        heading += " - API 1102 curve underlay"
    if plot.image_bytes:
        plot_content: list[list[Any]] = [[plot_image(plot, width=6.46 * inch, height=3.0 * inch)]]
    else:
        plot_content = [[Paragraph("Plot could not be generated. Lookup values used are listed below.", CELL)]]
    unique_note = unique_plot_note(plot.notes)
    block: list[Any] = [
        card(heading, plot_content, col_widths=[6.72 * inch]),
        Spacer(1, 3),
        card("Lookup Values", lookup_rows(plot, values), col_widths=[1.55 * inch, 5.17 * inch]),
    ]
    if unique_note:
        block.extend([Spacer(1, 3), Paragraph(unique_note, styles["Note"])])
    else:
        block.extend([Spacer(1, 3), Paragraph("Interpolation note: Linear interpolation from implemented lookup data.", styles["Note"])])
    if coefficient_name(plot) == "Fi":
        block.extend([Spacer(1, 2), Paragraph("Note: This figure is for reference only and is not used within the calculation — the API 1102 formula is used instead.", styles["Note"])])
    block.append(Spacer(1, 7))
    return [KeepTogether(block)]


def plot_image(plot: PlotArtifact, width: float, height: float) -> Image:
    return Image(BytesIO(plot.image_bytes or b""), width=width, height=height)


def coefficient_name(plot: PlotArtifact) -> str:
    haystack = f"{plot.table_name} {plot.figure_label or ''}".lower()
    figure = plot.figure_label or ""
    figure_match = re.search(r"\b(?:Figure|Fig\.)\s+\d+\s+([A-Za-z][A-Za-z0-9]*)\b", figure)
    if figure_match:
        return normalize_coefficient_token(figure_match.group(1))
    for token in ["KHe", "KHh", "GHh", "KLh", "GLh", "KHr", "GHr", "KLr", "GLr", "Fi", "Be", "Ee", "NH", "NL"]:
        if re.search(rf"(?<![a-z0-9]){re.escape(token.lower())}(?![a-z0-9])", haystack):
            return token
    return plot.table_name


def report_plots(data: DetailedReportData) -> list[PlotArtifact]:
    values = first_intermediate(data.intermediate_values)
    targets = coefficient_targets(values, data.calculation.calculation_type)
    if not targets:
        return data.plots
    best: dict[str, tuple[float, int, int, PlotArtifact]] = {}
    ordered_tokens = list(targets)
    for order, plot in enumerate(data.plots):
        token = coefficient_name(plot)
        if token not in targets:
            continue
        selected = selected_coefficient(plot)
        if selected is None:
            continue
        target = targets[token]
        difference = abs(selected - target)
        tolerance = coefficient_tolerance(target)
        if difference > tolerance:
            continue
        fallback_penalty = 1 if not plot.image_bytes else 0
        score = (difference, fallback_penalty, order, plot)
        if token not in best or score[:3] < best[token][:3]:
            best[token] = score
    filtered = [best[token][3] for token in ordered_tokens if token in best]
    return filtered or data.plots


def coefficient_targets(values: dict[str, Any], calculation_type: str) -> dict[str, float]:
    target_keys = [
        ("KHe", "Khe"),
        ("Be", "Be"),
        ("Ee", "Ee"),
        ("Fi", "Fi"),
    ]
    if calculation_type == "Railroad":
        target_keys += [("KHr", "KHr"), ("GHr", "GHr"), ("KLr", "KLr"), ("GLr", "GLr"), ("NH", "Nh"), ("NL", "NL")]
    else:
        target_keys += [("KHh", "KHh"), ("GHh", "GHh"), ("KLh", "KLh"), ("GLh", "GLh")]
    targets: dict[str, float] = {}
    for token, key in target_keys:
        number = optional_float(values.get(key))
        if number is not None:
            targets[token] = number
    return targets


def coefficient_tolerance(target: float) -> float:
    return max(abs(target) * 0.001, 0.01)


def selected_coefficient(plot: PlotArtifact) -> float | None:
    for key, value in plot.lookup_values:
        if key.lower() == "selected coefficient":
            return optional_float(value)
    return optional_float(plot.y_value)


def used_coefficient_display(plot: PlotArtifact, values: dict[str, Any]) -> str:
    token = coefficient_name(plot)
    target = target_for_coefficient(values, token)
    if target is not None:
        return clean_number(target, coefficient_digits(token))
    return lookup_value(plot, "Selected coefficient") or clean_lookup_value(plot.y_value)


def coefficient_digits(token: str) -> int:
    return {"KHe": 1, "Fi": 3, "Be": 3, "Ee": 3, "KHh": 3, "GHh": 3, "KLh": 3, "GLh": 3, "KHr": 3, "GHr": 3, "KLr": 3, "GLr": 3}.get(token, 3)


def target_for_coefficient(values: dict[str, Any], token: str) -> float | None:
    key = {"KHe": "Khe", "NH": "Nh"}.get(token, token)
    return optional_float(values.get(key))


def normalize_coefficient_token(token: str) -> str:
    mapping = {"khe": "KHe", "khh": "KHh", "ghh": "GHh", "klh": "KLh", "glh": "GLh", "khr": "KHr", "ghr": "GHr", "klr": "KLr", "glr": "GLr", "fi": "Fi", "be": "Be", "ee": "Ee", "nh": "NH", "nl": "NL"}
    return mapping.get(token.lower(), token)


def lookup_value(plot: PlotArtifact, label_text: str) -> str:
    for key, value in plot.lookup_values:
        if key.lower() == label_text.lower():
            return clean_lookup_value(value)
    return MISSING


def lookup_status(plot: PlotArtifact) -> str:
    if coefficient_name(plot) == "Fi":
        return "API 1102 formula"
    if not plot.image_bytes:
        return "Fallback"
    if plot.underlay_used:
        return "Underlay"
    return "Interpolated"


def unique_plot_note(note: str) -> str:
    if not note:
        return ""
    cleaned = note.replace("Generated coefficient plot based on implemented lookup data; verify against governing standard.", "").strip()
    cleaned = re.sub(r"(Plot placeholder:[^.]+\.?)(?:\s+\1)+", r"\1", cleaned)
    if cleaned.lower() == "linear interpolation from implemented lookup data.":
        return ""
    return cleaned


def maximum_utilization(results: dict[str, Any]) -> str:
    values = [float(check.get("utilization", 0)) for check in results.get("checks", []) if check.get("utilization") is not None]
    return percent_from_fraction(max(values)) if values else MISSING


def percent_from_fraction(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return MISSING


def clean_equation_text(text: Any) -> str:
    return clean_text(text)


def clean_text(value: Any) -> str:
    if value is None:
        return MISSING
    if isinstance(value, str):
        stripped = value.strip()
        if stripped in {"", "-", "None", "null"}:
            return MISSING
        if numeric_text(stripped):
            return clean_number(stripped)
        return stripped
    if isinstance(value, float | int):
        return clean_number(value)
    return str(value)


def clean_number(value: Any, digits: int = 3) -> str:
    try:
        number = float(value.replace(",", "")) if isinstance(value, str) else float(value)
    except (TypeError, ValueError):
        return value.strip() if isinstance(value, str) and value.strip() else MISSING
    if number.is_integer():
        return f"{number:,.0f}"
    rounded = f"{number:,.{digits}f}".rstrip("0").rstrip(".")
    return rounded


def optional_float(value: Any) -> float | None:
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def float_or(value: Any, fallback: float) -> float:
    number = optional_float(value)
    return fallback if number is None else number


def clean_lookup_value(value: Any) -> str:
    text = clean_text(value)
    if text == MISSING:
        return MISSING
    raw = str(value).strip() if value is not None else ""
    if "e" not in raw.lower() and numeric_text(raw):
        return raw
    try:
        number = float(raw.replace(",", ""))
    except ValueError:
        return text
    if number.is_integer():
        return f"{number:,.0f}"
    return f"{number:,.6f}".rstrip("0").rstrip(".")


def executive_value_with_unit(key: str, value: Any) -> str:
    number = value_display(key, value, executive=True)
    unit = unit_for(key)
    return f"{number} {unit}".strip() if unit and number != MISSING else number


def value_display(key: str, value: Any, *, executive: bool = False) -> str:
    if value is None:
        return MISSING
    if key in stress_keys():
        return clean_number(value, 1)
    if key in {"operating_pressure", "surface_pressure"}:
        return clean_number(value, 1 if key == "surface_pressure" else 0)
    if key in {"design_wheel_load"}:
        return clean_number(value, 0)
    if executive and key in {"outside_diameter", "bored_diameter", "cover_depth"}:
        return clean_number(value, 2)
    if key in {"wall_thickness"}:
        return clean_number(value, 3)
    return clean_number(value, 3)


def lookup_rows(plot: PlotArtifact, values: dict[str, Any] | None = None) -> list[list[str]]:
    rows = plot.lookup_values or [["Lookup Values", "No lookup values available."]]
    output: list[list[str]] = []
    for key, value in rows:
        if key.lower() == "interpolation note":
            continue
        if key.lower() == "selected coefficient" and values is not None:
            output.append([key, used_coefficient_display(plot, values)])
        elif key.lower() == "figure":
            output.append(["API Figure", clean_lookup_value(value)])
        else:
            output.append([key, clean_lookup_value(value)])
    # Inject additional input parameters from intermediate values
    name = coefficient_name(plot)
    extra = _additional_lookup_inputs(name, values)
    for label, val in extra:
        if not any(existing[0].lower().startswith(label.lower().split(" ")[0]) for existing in output):
            output.append([label, val])
    return output


def _additional_lookup_inputs(name: str, values: dict[str, Any] | None) -> list[list[str]]:
    """Return additional input rows to show in the lookup values card for a given coefficient.

    Only returns rows that provide genuinely new information beyond what is
    already shown as "Input x" in the base lookup_values list.
    """
    if values is None:
        return []
    extras: list[list[str]] = []
    if name == "Fi":
        # Show H (Cover Depth) explicitly alongside Input x
        h = values.get("cover_depth")
        if h is not None:
            extras.append(["H (Cover Depth)", f"{clean_number(h, 2)} ft"])
    elif name == "KHe":
        e_prime = values.get("e_prime")
        tw_d = values.get("tw_d")
        if e_prime is not None:
            extras.append(["E' (Soil Modulus)", f"{clean_number(e_prime, 0)} psi"])
        if tw_d is not None:
            extras.append(["tw/D", clean_number(tw_d, 4)])
    elif name in {"KHh", "KLh", "KHr", "KLr"}:
        er = values.get("er")
        tw_d = values.get("tw_d")
        if er is not None:
            extras.append(["Er", f"{clean_number(er, 0)} psi"])
        if tw_d is not None:
            extras.append(["tw/D", clean_number(tw_d, 4)])
    elif name in {"GHh", "GLh", "GHr", "GLr"}:
        # Depth band (H) is the curve selector; Input x is outside diameter
        h = values.get("cover_depth")
        if h is not None:
            extras.append(["H (Cover Depth)", f"{clean_number(h, 2)} ft"])
    return extras


def numeric_text(value: str) -> bool:
    if "%" in value:
        return False
    if not re.fullmatch(r"[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?", value):
        return False
    try:
        float(value.replace(",", ""))
    except ValueError:
        return False
    return True


def value_with_unit(key: str, value: Any) -> str:
    number = value_display(key, value)
    unit = unit_for(key)
    return f"{number} {unit}".strip() if unit and number != MISSING else number


def unit_for(key: str) -> str:
    if key in {"outside_diameter", "wall_thickness", "bored_diameter", "wheel_spacing"}:
        return "in"
    if key in {"cover_depth"}:
        return "ft"
    if key in {"operating_pressure"}:
        return "psig"
    if key in {"surface_pressure", "SHi", "SHi_internal", "allowable_hoop", "SHe", "SHh", "SLh", "SHr", "SLr", "S1", "S2", "S3", "Seff", "allowable_effective", "SFG", "SFL", "allowable_girth", "allowable_longitudinal", "SMYS"}:
        return "psi"
    if key in {"design_wheel_load"}:
        return "lb"
    if key in {"soil_unit_weight"}:
        return "pcf"
    return ""


def stress_keys() -> set[str]:
    return {"SHi", "SHi_internal", "allowable_hoop", "SHe", "SHh", "SLh", "SHr", "SLr", "S1", "S2", "S3", "Seff", "allowable_effective", "SFG", "SFL", "allowable_girth", "allowable_longitudinal", "SMYS"}


def note_for(key: str) -> str:
    notes = {
        "cover_depth": "Cover from grade to pipe.",
        "bored_diameter": "Used where casing/bore geometry is modeled.",
        "design_wheel_load": "Highway loading input.",
        "surface_pressure": "Railroad loading input.",
        "soil_type": "Standards lookup category.",
        "wall_thickness": "Selected or custom wall.",
    }
    return notes.get(key, "")


def format_timestamp(value: Any) -> str:
    text = clean_text(value)
    if text == MISSING:
        return MISSING
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except ValueError:
        return text


def format_date(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return clean_text(value)


def label(key: str) -> str:
    special = {
        "nps": "NPS",
        "SMYS": "SMYS",
        "SHi": "SHi",
        "SHe": "SHe",
        "SHh": "SHh",
        "SLh": "SLh",
        "SHr": "SHr",
        "SLr": "SLr",
        "Seff": "Seff",
        "SFG": "SFG",
        "SFL": "SFL",
        "KHh": "KHh",
        "GHh": "GHh",
        "KLh": "KLh",
        "GLh": "GLh",
        "KHr": "KHr",
        "GHr": "GHr",
        "KLr": "KLr",
        "GLr": "GLr",
        "Nh": "Nh",
        "NL": "NL",
        "Fi": "Fi",
        "Khe": "KHe",
        "Be": "Be",
        "Ee": "Ee",
    }
    return special.get(key, key.replace("_", " ").title())
