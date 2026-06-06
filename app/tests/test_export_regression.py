from __future__ import annotations

from fastapi.testclient import TestClient

from app.backend.main import app


def create_export_fixture(client: TestClient):
    project = client.post(
        "/api/projects",
        json={
            "project_name": "Export Regression Project",
            "project_number": "EXP-1102",
            "client": "HDR",
            "location": "Omaha, NE",
            "description": "Export regression coverage",
            "status": "Active",
        },
    ).json()
    calc = client.post(
        "/api/calculations",
        json={
            "project_id": project["id"],
            "calc_number": "CALC-EXPORT-001",
            "crossing_name": "Export Crossing",
            "calculation_type": "Highway",
            "status": "Draft",
        },
    ).json()
    base = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()[0]
    high_pressure = client.post(
        "/api/scenarios",
        json={
            "calculation_id": calc["id"],
            "scenario_name": "High Pressure",
            "description": "High pressure export scenario",
            "shared_inputs": {**base["shared_inputs"], "operating_pressure": 3000},
            "highway_inputs": base["highway_inputs"],
            "railroad_inputs": base["railroad_inputs"],
        },
    ).json()
    return project, calc, base, high_pressure


def assert_scenario_result_shape(scenario):
    assert scenario["shared_inputs"]
    assert scenario["highway_inputs"]
    assert scenario["results"]
    assert scenario["intermediate_values"]
    assert "warnings" in scenario
    assert scenario["results"]["checks"]


def test_project_json_export_contains_full_calculation_package():
    with TestClient(app) as client:
        project, calc, _, _ = create_export_fixture(client)
        response = client.get(f"/api/exports/project/{project['id']}.json")
        assert response.status_code == 200
        package = response.json()
        assert package["project"]["project_name"] == project["project_name"]
        assert package["calculations"]
        exported_calc = next(item for item in package["calculations"] if item["id"] == calc["id"])
        assert len(exported_calc["scenarios"]) >= 2
        for scenario in exported_calc["scenarios"]:
            assert_scenario_result_shape(scenario)


def test_calculation_json_export_contains_only_selected_calculation_with_scenarios():
    with TestClient(app) as client:
        project, calc, _, _ = create_export_fixture(client)
        other = client.post("/api/calculations", json={"project_id": project["id"], "calc_number": "OTHER", "crossing_name": "Other", "calculation_type": "Railroad", "status": "Draft"}).json()
        response = client.get(f"/api/exports/calculation/{calc['id']}.json")
        assert response.status_code == 200
        package = response.json()
        assert [item["id"] for item in package["calculations"]] == [calc["id"]]
        assert other["id"] not in [item["id"] for item in package["calculations"]]
        assert package["calculations"][0]["scenarios"]


def test_scenario_json_export_contains_only_selected_scenario_with_checks():
    with TestClient(app) as client:
        _, _, base, high_pressure = create_export_fixture(client)
        response = client.get(f"/api/exports/scenario/{high_pressure['id']}.json")
        assert response.status_code == 200
        package = response.json()
        scenarios = package["calculations"][0]["scenarios"]
        assert [scenario["id"] for scenario in scenarios] == [high_pressure["id"]]
        assert base["id"] not in [scenario["id"] for scenario in scenarios]
        assert scenarios[0]["results"]["checks"]


def test_calculation_and_scenario_csv_exports_contain_key_strings():
    with TestClient(app) as client:
        _, calc, base, _ = create_export_fixture(client)
        for url in [f"/api/exports/calculation/{calc['id']}.csv", f"/api/exports/scenario/{base['id']}.csv"]:
            response = client.get(url)
            assert response.status_code == 200
            text = response.text
            for expected in ["Highway", "scenario_name", "overall_result", "controlling_check", "Barlow Stress", "Effective Stress", "Girth Weld Stress", "Longitudinal Weld Stress"]:
                assert expected in text


def test_calculation_pdf_export_smoke_contract():
    with TestClient(app) as client:
        _, calc, _, _ = create_export_fixture(client)
        response = client.get(f"/api/exports/calculation/{calc['id']}.pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF")
