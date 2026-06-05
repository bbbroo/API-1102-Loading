from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.standards.metadata import APP_VERSION, ENGINE_VERSION, SOURCE_WORKBOOKS, STANDARDS_VERSION


def render_pdf(package: dict[str, Any]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36, pageCompression=0)
    styles = getSampleStyleSheet()
    story = []
    project = package["project"]
    story.append(Paragraph("HDR", styles["Title"]))
    story.append(Paragraph("API RP 1102 Loading Calculator", styles["Title"]))
    story.append(Paragraph("Engineering Calculation Package", styles["Heading2"]))
    story.append(Paragraph(f"Export scope: {package.get('export_scope', 'project')} | Standards: {STANDARDS_VERSION} | Exported: {package.get('export_timestamp', '')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(_section("Project & Calculation", [[k.replace("_", " ").title(), str(v or "")] for k, v in project.items() if k in {"project_name", "project_number", "client", "location", "status"}]))
    for calc in package.get("calculations", []):
        story.append(Spacer(1, 10))
        story.append(_section("Calculation Metadata", [[k.replace("_", " ").title(), str(calc.get(k) or "")] for k in ["calc_number", "crossing_name", "calculation_type", "prepared_by", "checked_by", "reviewer", "revision", "status", "review_comments"]]))
        for scenario in calc.get("scenarios", []):
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"Scenario: {scenario.get('scenario_name', 'Base Case')}", styles["Heading3"]))
            story.append(_section("Inputs & Assumptions", input_rows(scenario)))
            story.append(_section("Intermediate Calculations", intermediate_rows(scenario)))
            story.append(Paragraph("Pipeline Cross-Section Schematic", styles["Heading3"]))
            story.append(Paragraph("Loading surface, cover depth, bore diameter, and pipe geometry are shown in the app report preview and are derived from current scenario inputs.", styles["Normal"]))
            story.append(Spacer(1, 8))
            checks = scenario.get("results", {}).get("checks", [])
            rows = [["Check", "Calculated (psi)", "Allowable (psi)", "Utilization", "Result"]]
            rows += [[c["name"], f"{c['calculated_psi']:.1f}", f"{c['allowable_psi']:.1f}", f"{c['utilization']:.1%}", c["result"]] for c in checks]
            story.append(_table(rows))
            warnings = scenario.get("warnings", [])
            if warnings:
                story.append(Paragraph("Warnings", styles["Heading3"]))
                story.append(_table([["Severity", "Message"]] + [[w.get("severity", ""), w.get("message", "")] for w in warnings]))
    story.append(Spacer(1, 14))
    story.append(Paragraph("References", styles["Heading3"]))
    story.append(Paragraph(", ".join(SOURCE_WORKBOOKS.values()), styles["Normal"]))
    story.append(Paragraph(f"App version {APP_VERSION} | Calculation engine {ENGINE_VERSION} | Standards {STANDARDS_VERSION}", styles["Normal"]))
    story.append(Paragraph("This tool is intended to support engineering calculations and documentation. It does not replace engineering judgment, applicable codes, standards, client requirements, or independent checking.", styles["Italic"]))
    doc.build(story)
    return buffer.getvalue()


def input_rows(scenario: dict[str, Any]) -> list[list[str]]:
    shared = scenario.get("shared_inputs", {})
    highway = scenario.get("highway_inputs", {})
    railroad = scenario.get("railroad_inputs", {})
    rows = []
    for key in ["nps", "wall_thickness", "cover_depth", "bored_diameter", "operating_pressure", "installation_temperature", "operating_temperature", "soil_unit_weight"]:
        if key in shared:
            rows.append([key.replace("_", " ").title(), str(shared.get(key))])
    for key, value in {**highway, **railroad}.items():
        rows.append([key.replace("_", " ").title(), str(value)])
    return rows or [["Inputs", "See JSON export for full scenario input package."]]


def intermediate_rows(scenario: dict[str, Any]) -> list[list[str]]:
    values = scenario.get("intermediate_values", {})
    if "highway" in values or "railroad" in values:
        values = values.get("highway") or values.get("railroad") or {}
    keys = ["SHi", "SHi_internal", "SHe", "Fi", "Khe", "Be", "Ee", "S1", "S2", "S3", "Seff", "allowable_hoop", "allowable_effective", "allowable_girth", "allowable_longitudinal"]
    rows = []
    for key in keys:
        if key in values:
            value = values[key]
            rows.append([key, f"{value:.3f}" if isinstance(value, float) else str(value)])
    return rows or [["Intermediate Values", "Run calculation to populate intermediate results."]]


def _section(title: str, rows: list[list[str]]):
    return _table([[title, ""]] + rows)


def _table(rows: list[list[str]]):
    table = Table(rows, hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4b5563")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d1d5db")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    return table
