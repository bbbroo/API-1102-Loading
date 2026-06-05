from fastapi.testclient import TestClient

from app.backend.main import app
from app.backend.database.models import Calculation, Project, Scenario
from app.backend.database.session import SessionLocal
from app.backend.services.helpers import dumps
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY


def test_api_health_and_dashboard():
    with TestClient(app) as client:
        assert client.get("/api/health").json()["ok"] is True
        summary = client.get("/api/dashboard/summary").json()
        assert summary["total_projects"] >= 1
        assert summary["total_calculations"] >= 1


def test_project_workflow_actions_and_calculation_parenting():
    with TestClient(app) as client:
        project = client.post(
            "/api/projects",
            json={
                "project_name": "Workflow Alignment Project",
                "project_number": "WF-1102",
                "client": "HDR",
                "location": "Omaha, NE",
                "description": "Project detail workflow test",
                "status": "Active",
            },
        ).json()

        projects = client.get("/api/projects").json()
        assert any(item["id"] == project["id"] for item in projects)

        calc = client.post(
            "/api/calculations",
            json={
                "project_id": project["id"],
                "calc_number": "CALC-WF-001",
                "crossing_name": "Workflow Crossing",
                "calculation_type": "Highway",
                "status": "Draft",
            },
        ).json()
        assert calc["project_id"] == project["id"]

        project_calcs = client.get(f"/api/calculations?project_id={project['id']}").json()
        assert [item["id"] for item in project_calcs] == [calc["id"]]

        clone = client.post(f"/api/projects/{project['id']}/duplicate").json()
        assert clone["id"] != project["id"]
        assert clone["project_name"].endswith("Copy")

        archived = client.post(f"/api/projects/{project['id']}/archive").json()
        assert archived["status"] == "Archived"

        assert client.delete(f"/api/projects/{clone['id']}").json()["ok"] is True


def test_calculation_create_initializes_mode_specific_base_case_results():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"project_name": "Mode Defaults Project", "status": "Active"}).json()

        for calculation_type in ("Highway", "Railroad"):
            calc = client.post(
                "/api/calculations",
                json={
                    "project_id": project["id"],
                    "calc_number": f"CALC-{calculation_type.upper()}",
                    "crossing_name": f"{calculation_type} Crossing",
                    "calculation_type": calculation_type,
                    "status": "Draft",
                },
            ).json()

            assert calc["calculation_type"] == calculation_type
            assert calc["overall_result"] in {"Pass", "Fail", "Needs Review"}

            scenarios = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()
            assert len(scenarios) == 1
            base = scenarios[0]
            assert base["scenario_name"] == "Base Case"
            assert base["results"]["calculation_type"] == calculation_type
            assert base["results"]["overall_result"] == calc["overall_result"]
            assert len(base["results"]["checks"]) == 4
            if calculation_type == "Railroad":
                assert base["railroad_inputs"]["number_of_tracks"] == 2
                assert base["railroad_inputs"]["surface_pressure"] == 13.9
            else:
                assert base["highway_inputs"]["pavement_type"] == "Flexible"
                assert base["highway_inputs"]["axle_configuration"] == "Tandem Axle"


def test_calculation_api_rejects_combined_mode():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"project_name": "Invalid Mode Project", "status": "Active"}).json()

        rejected_create = client.post(
            "/api/calculations",
            json={
                "project_id": project["id"],
                "calc_number": "CALC-BAD",
                "crossing_name": "Invalid Crossing",
                "calculation_type": "Highway + Railroad",
                "status": "Draft",
            },
        )
        assert rejected_create.status_code == 422

        calc = client.post(
            "/api/calculations",
            json={
                "project_id": project["id"],
                "calc_number": "CALC-GOOD",
                "crossing_name": "Valid Crossing",
                "calculation_type": "Highway",
                "status": "Draft",
            },
        ).json()
        rejected_patch = client.patch(f"/api/calculations/{calc['id']}", json={"calculation_type": "Highway + Railroad"})
        assert rejected_patch.status_code == 422


def test_type_switch_seeds_missing_mode_inputs_and_recalculates():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"project_name": "Type Switch Project", "status": "Active"}).json()
        calc = client.post(
            "/api/calculations",
            json={"project_id": project["id"], "calc_number": "CALC-SWITCH", "crossing_name": "Switch Crossing", "calculation_type": "Highway", "status": "Draft"},
        ).json()
        base = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()[0]
        client.patch(f"/api/scenarios/{base['id']}", json={"shared_inputs": {**base["shared_inputs"], "cover_depth": 5}})

        patched = client.patch(f"/api/calculations/{calc['id']}", json={"calculation_type": "Railroad"}).json()
        assert patched["calculation_type"] == "Railroad"

        scenario = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()[0]
        assert scenario["shared_inputs"]["cover_depth"] == 5
        assert scenario["railroad_inputs"]["number_of_tracks"] == 2
        assert scenario["railroad_inputs"]["surface_pressure"] == 13.9
        assert scenario["results"]["calculation_type"] == "Railroad"


def test_parent_calculation_uses_worst_scenario_and_updates_after_delete():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"project_name": "Scenario Summary Project", "status": "Active"}).json()
        calc = client.post(
            "/api/calculations",
            json={"project_id": project["id"], "calc_number": "CALC-SUMMARY", "crossing_name": "Summary Crossing", "calculation_type": "Highway", "status": "Draft"},
        ).json()
        base = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()[0]
        failed = client.post(
            "/api/scenarios",
            json={
                "calculation_id": calc["id"],
                "scenario_name": "High Pressure",
                "description": "",
                "shared_inputs": {**base["shared_inputs"], "operating_pressure": 3000},
                "highway_inputs": base["highway_inputs"],
                "railroad_inputs": base["railroad_inputs"],
            },
        ).json()

        summarized = client.get(f"/api/calculations/{calc['id']}").json()
        assert summarized["overall_result"] == "Fail"
        assert summarized["controlling_check"] == "High Pressure: Barlow Stress"

        assert client.delete(f"/api/scenarios/{failed['id']}").json()["ok"] is True
        resummarized = client.get(f"/api/calculations/{calc['id']}").json()
        assert resummarized["overall_result"] == "Pass"
        assert resummarized["controlling_check"] == "Effective Stress"


def test_delete_calculation_removes_it_from_project_and_cascades_scenarios():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"project_name": "Delete Calculation Project", "status": "Active"}).json()
        calc = client.post(
            "/api/calculations",
            json={"project_id": project["id"], "calc_number": "CALC-DELETE", "crossing_name": "Delete Crossing", "calculation_type": "Highway", "status": "Draft"},
        ).json()
        scenarios = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()
        assert len(scenarios) == 1

        assert client.delete(f"/api/calculations/{calc['id']}").json()["ok"] is True
        assert client.get(f"/api/calculations/{calc['id']}").status_code == 404
        assert client.get(f"/api/calculations?project_id={project['id']}").json() == []

        with SessionLocal() as db:
            assert db.query(Scenario).filter(Scenario.calculation_id == calc["id"]).count() == 0


def test_opening_stale_legacy_scenario_refreshes_results():
    with TestClient(app) as client:
        with SessionLocal() as db:
            project = Project(project_name="Legacy Stale Project", status="Active")
            db.add(project)
            db.flush()
            calc = Calculation(project_id=project.id, calc_number="CALC-STALE", crossing_name="Stale Crossing", calculation_type="Highway", status="Draft")
            db.add(calc)
            db.flush()
            scenario = Scenario(calculation_id=calc.id, scenario_name="Base Case", shared_inputs_json=dumps(DEFAULT_SHARED_HIGHWAY))
            db.add(scenario)
            db.commit()
            calc_id = calc.id

        scenarios = client.get(f"/api/scenarios?calculation_id={calc_id}").json()
        assert scenarios[0]["results"]["overall_result"] == "Pass"
        assert len(scenarios[0]["results"]["checks"]) == 4
        refreshed_calc = client.get(f"/api/calculations/{calc_id}").json()
        assert refreshed_calc["overall_result"] == "Pass"


def test_partial_updates_scenario_crud_and_export_records():
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"project_name": "Patch Project", "status": "Active"}).json()
        patched_project = client.patch(f"/api/projects/{project['id']}", json={"client": "HDR Internal"}).json()
        assert patched_project["client"] == "HDR Internal"

        calc = client.post(
            "/api/calculations",
            json={"project_id": project["id"], "calc_number": "CALC-PATCH", "crossing_name": "Patch Crossing", "calculation_type": "Highway", "status": "Draft"},
        ).json()
        patched_calc = client.patch(f"/api/calculations/{calc['id']}", json={"prepared_by": "Engineer A", "status": "Issued"}).json()
        assert patched_calc["prepared_by"] == "Engineer A"
        assert patched_calc["status"] == "Issued"

        scenarios = client.get(f"/api/scenarios?calculation_id={calc['id']}").json()
        base = scenarios[0]
        patched_scenario = client.patch(f"/api/scenarios/{base['id']}", json={"scenario_name": "Reduced Cover", "shared_inputs": {**base["shared_inputs"], "cover_depth": 5}}).json()
        assert patched_scenario["scenario_name"] == "Reduced Cover"
        assert patched_scenario["shared_inputs"]["cover_depth"] == 5
        assert patched_scenario["results"]["overall_result"] in {"Pass", "Fail", "Needs Review", "Not Calculated"}

        duplicate = client.post(f"/api/scenarios/{base['id']}/duplicate").json()
        assert duplicate["scenario_name"].endswith("Copy")
        assert client.delete(f"/api/scenarios/{duplicate['id']}").json()["ok"] is True

        assert client.get(f"/api/exports/calculation/{calc['id']}.json").status_code == 200
        assert client.get(f"/api/exports/scenario/{base['id']}.csv").status_code == 200
        records = client.get(f"/api/exports/records?calculation_id={calc['id']}").json()
        assert len(records) >= 2
        assert {record["export_type"] for record in records} >= {"json", "csv"}
