from __future__ import annotations

import fitz
from fastapi.testclient import TestClient

from app.backend.database.models import Scenario
from app.backend.database.session import SessionLocal
from app.backend.main import app
from app.backend.reporting.models import ReportOptions
from app.backend.reporting.pdf import HDR_LOGO_SVG, PipelineSchematic
from app.backend.reporting.plots import build_plot, factor_for_trace, figure_for_trace
from app.backend.reporting.service import build_detailed_report_data
from app.backend.services.helpers import dumps, loads


def create_report_fixture(client: TestClient, calculation_type: str = "Highway"):
    project = client.post("/api/projects", json={"project_name": "Detailed Report Project", "project_number": "DR-001", "status": "Active"}).json()
    calc = client.post(
        "/api/calculations",
        json={"project_id": project["id"], "calc_number": "DR-CALC-001", "crossing_name": "Detailed Crossing", "calculation_type": calculation_type, "status": "Draft"},
    ).json()
    scenario = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()[0]
    return project, calc, scenario


def detailed_payload(project, calc):
    return {
        "project_id": project["id"],
        "calculation_id": calc["id"],
        "report_options": {
            "include_formula_trace": True,
            "include_intermediates": True,
            "include_plots": True,
            "include_appendix_plots": True,
            "include_warnings": True,
        },
    }


def detailed_payload_with_options(project, calc, **options):
    payload = detailed_payload(project, calc)
    payload["report_options"].update(options)
    return payload


def pdf_text(content: bytes) -> str:
    doc = fitz.open(stream=content, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def pdf_page_texts(content: bytes) -> list[str]:
    doc = fitz.open(stream=content, filetype="pdf")
    return [page.get_text() for page in doc]


def test_detailed_pdf_endpoint_returns_pdf():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        response = client.post(f"/api/reports/scenario/{scenario['id']}/detailed.pdf", json=detailed_payload(project, calc))
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
        text = pdf_text(response.content)
        pages = pdf_page_texts(response.content)
        upper = text.upper()
        for expected in [
            "API RP 1102 Highway Loading Analysis",
            "Project & Calculation",
            "Purpose & References",
            "Inputs & Assumptions",
            "Pipeline Cross-Section Schematic",
            "Results Summary",
            "Effective Stress",
            "Coefficient Lookup Summary",
            "References",
            "Barlow Stress",
            "Girth Weld Stress",
            "Longitudinal Weld Stress",
            "Source",
            "Workbooks",
            "Application",
            "Engine",
        ]:
            assert expected in text
        for expected in ["OVERALL RESULT", "CONTROLLING CHECK", "MAXIMUM UTILIZATION"]:
            assert expected in upper
        for expected in [
            "EXECUTIVE CALCULATION SHEET",
            "INPUT REGISTER & WARNINGS",
            "SYMBOLS & METHODOLOGY",
            "DETAILED FORMULA TRACE",
            "INTERMEDIATE VALUES",
            "APPENDIX FULL-SIZE PLOTS",
        ]:
            assert expected in upper
        for expected_value in ["25,500", "26,699.1", "46,800", "54.5%", "57.0%", "11.6%", "8.9%"]:
            assert expected_value in text
        assert 12 <= len(pages) <= 18
        assert "PAGE 2 - INPUT REGISTER & WARNINGS" in pages[1]
        assert "This report supports engineering documentation" not in pages[1]
        assert "Executive Metrics" not in text
        assert "Report Metadata" in text
        assert "psig" in text
        assert "D=12.75 in" in text
        assert "1e+04" not in text
        assert "0.01961" in text
        assert "0.0175" in text
        assert "2,744.4" in text
        assert "Be\nFigure 4 Be" in text
        assert "Ee\nFigure 5 Ee" in text
        assert "Fi\nFigure 7 Fi" in text
        assert text.count("KHe\nFigure 3 KHe") == 1
        assert text.count("KHh\nFigure 14 KHh") == 1
        assert text.count("KLh\nFigure 16 KLh") == 1
        assert "KHe @ 200" not in text
        assert "KHe @ 1000" not in text
        assert "KHe @ 2000" not in text
        assert "Highway KHh @ 5000" not in text
        assert "Highway KHh @ 20000" not in text
        assert "Highway KLh @ 5000" not in text
        assert "Highway KLh @ 20000" not in text
        assert "S3=-1,000.0 psi" in text
        assert "S3=—1,000.0 psi" not in text
        assert "SFG=- psi" not in text
        assert "SFL=- psi" not in text
        assert "SFG=1,002.4 psi" in text
        assert "SFL=1,467.5 psi" in text
        assert "Trace item only" in text
        assert "Trace  Pass" not in text
        assert "T\nTrace" not in text
        assert "Interpolation note: Linear interpolation from implemented lookup data." in text
        assert "Figure Figure" not in text
        for page_text in pages:
            assert page_text.count("Plot placeholder: Selected point is outside calibrated graph range") <= 1
        assert HDR_LOGO_SVG.name == "hdr-logo.svg"
        assert HDR_LOGO_SVG.parts[-4:] == ("frontend", "src", "assets", "hdr-logo.svg")
        assert HDR_LOGO_SVG.exists()
        schematic = PipelineSchematic({}, "Highway")
        assert schematic.diagram_width == 565
        assert schematic.diagram_height == 360


def test_detailed_pdf_export_alias_returns_pdf():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        response = client.post(f"/api/exports/scenario/{scenario['id']}/detailed.pdf", json=detailed_payload(project, calc))
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")


def test_detailed_pdf_options_control_optional_sections():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        response = client.post(
            f"/api/reports/scenario/{scenario['id']}/detailed.pdf",
            json=detailed_payload_with_options(
                project,
                calc,
                include_formula_trace=False,
                include_intermediates=False,
                include_plots=False,
                include_appendix_plots=False,
            ),
        )
        assert response.status_code == 200
        upper = pdf_text(response.content).upper()
        assert "DETAILED FORMULA TRACE" not in upper
        assert "INTERMEDIATE VALUES" not in upper
        assert "COEFFICIENT LOOKUP SUMMARY" not in upper
        assert "APPENDIX FULL-SIZE PLOTS" not in upper


def test_detailed_report_data_has_equation_traces_and_plots_for_modes():
    with TestClient(app) as client:
        for calculation_type, prefix in [("Highway", "HWY"), ("Railroad", "RR")]:
            project, calc, scenario = create_report_fixture(client, calculation_type)
            with SessionLocal() as db:
                data = build_detailed_report_data(db, scenario["id"], project["id"], calc["id"], ReportOptions())
            assert data.equations
            assert any(equation.equation_id.startswith("GEN-EQ") for equation in data.equations)
            assert any(equation.equation_id.startswith(f"{prefix}-EQ") for equation in data.equations)
            assert data.results.get("interpolation")
            assert data.plots


def test_detailed_pdf_blocks_not_calculated():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        with SessionLocal() as db:
            row = db.get(Scenario, scenario["id"])
            row.results_json = dumps({})
            row.intermediate_values_json = dumps({})
            row.warnings_json = dumps([])
            db.commit()
        response = client.post(f"/api/reports/scenario/{scenario['id']}/detailed.pdf", json=detailed_payload(project, calc))
        assert response.status_code == 409
        assert "not_calculated" in response.text
        assert "Recalculate Scenario" in response.text


def test_detailed_pdf_blocks_legacy_missing_fingerprint():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        with SessionLocal() as db:
            row = db.get(Scenario, scenario["id"])
            results = loads(row.results_json, {})
            results.pop("input_fingerprint", None)
            row.results_json = dumps(results)
            db.commit()
        response = client.post(f"/api/reports/scenario/{scenario['id']}/detailed.pdf", json=detailed_payload(project, calc))
        assert response.status_code == 409
        assert "stale_result" in response.text


def test_detailed_pdf_blocks_changed_input_fingerprint_mismatch():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        with SessionLocal() as db:
            row = db.get(Scenario, scenario["id"])
            shared = loads(row.shared_inputs_json, {})
            shared["cover_depth"] = float(shared.get("cover_depth", 6)) + 1
            row.shared_inputs_json = dumps(shared)
            db.commit()
        response = client.post(f"/api/reports/scenario/{scenario['id']}/detailed.pdf", json=detailed_payload(project, calc))
        assert response.status_code == 409
        assert "inputs_changed" in response.text


def test_detailed_pdf_blocks_required_input_error_warning():
    with TestClient(app) as client:
        project, calc, scenario = create_report_fixture(client)
        with SessionLocal() as db:
            row = db.get(Scenario, scenario["id"])
            row.warnings_json = dumps([{"code": "required_missing", "message": "Required input missing: cover_depth", "severity": "error"}])
            db.commit()
        response = client.post(f"/api/reports/scenario/{scenario['id']}/detailed.pdf", json=detailed_payload(project, calc))
        assert response.status_code == 409
        assert "required_inputs_missing" in response.text
        assert "cover_depth" in response.text


def test_plot_generation_fallback_includes_lookup_values(monkeypatch):
    def raise_plot(*args, **kwargs):
        raise RuntimeError("plot backend unavailable")

    monkeypatch.setattr("app.backend.reporting.plots.draw_trace_plot", raise_plot)
    artifact = build_plot({"table_name": "Fallback Table", "input_value": 3.5, "lower_bound": 3, "upper_bound": 4, "interpolated_value": 1.25})
    assert artifact.image_bytes is None
    assert "Plot placeholder" in artifact.notes
    assert ["Selected coefficient", "1.25"] in artifact.lookup_values


def test_plot_generation_uses_api_curve_underlay_for_known_trace():
    artifact = build_plot({"table_name": "Highway GHh", "input_value": 12.75, "lower_bound": 12.0, "upper_bound": 18.0, "interpolated_value": 0.6})
    assert artifact.image_bytes
    assert artifact.underlay_used
    assert artifact.figure_id == "15"
    assert "Figure 15 GHh" in (artifact.figure_label or "")


def test_manifest_mapping_covers_report_trace_factors():
    expected = {
        "Highway earth Khe": "KHe",
        "Highway burial factor": "Be",
        "Railroad excavation factor": "Ee",
        "Highway impact factor": "Fi",
        "Highway KHh @ 5000.0": "KHh",
        "Highway GHh": "GHh",
        "Highway KLh": "KLh",
        "Highway GLh": "GLh",
        "Railroad KHr": "KHr",
        "Railroad GHr": "GHr",
        "Railroad KLr": "KLr",
        "Railroad GLr": "GLr",
        "Railroad Nh factor": "NH",
        "Railroad NL factor": "NL",
    }
    for table_name, factor in expected.items():
        assert factor_for_trace(table_name) == factor
        assert figure_for_trace(table_name)
