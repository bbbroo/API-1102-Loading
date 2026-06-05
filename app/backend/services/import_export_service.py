from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Project, Scenario
from app.backend.services.helpers import dumps, loads
from app.backend.services.calculation_service import run_scenario
from app.standards.metadata import APP_VERSION, ENGINE_VERSION, STANDARDS_VERSION


VALID_IMPORTED_CALCULATION_TYPES = {"Highway", "Railroad"}


def normalize_calculation_type(value: Any) -> str:
    return value if value in VALID_IMPORTED_CALCULATION_TYPES else "Highway"


def project_package(db: Session, project_id: int) -> dict[str, Any]:
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError("Project not found")
    return {
        "app_version": APP_VERSION,
        "calculation_engine_version": ENGINE_VERSION,
        "standards_version": STANDARDS_VERSION,
        "schema_version": "1.0",
        "export_scope": "project",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "project": model_dict(project),
        "calculations": [_calculation_dict(calc) for calc in project.calculations],
    }


def calculation_package(db: Session, calculation_id: int) -> dict[str, Any]:
    calc = db.get(Calculation, calculation_id)
    if calc is None:
        raise ValueError("Calculation not found")
    project = calc.project
    return {
        "app_version": APP_VERSION,
        "calculation_engine_version": ENGINE_VERSION,
        "standards_version": STANDARDS_VERSION,
        "schema_version": "1.0",
        "export_scope": "calculation",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "project": model_dict(project),
        "calculations": [_calculation_dict(calc)],
    }


def scenario_package(db: Session, scenario_id: int) -> dict[str, Any]:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise ValueError("Scenario not found")
    calc = scenario.calculation
    return {
        "app_version": APP_VERSION,
        "calculation_engine_version": ENGINE_VERSION,
        "standards_version": STANDARDS_VERSION,
        "schema_version": "1.0",
        "export_scope": "scenario",
        "export_timestamp": datetime.now(timezone.utc).isoformat(),
        "project": model_dict(calc.project),
        "calculations": [{**model_dict(calc), "scenarios": [_scenario_dict(scenario)]}],
    }


def import_project_package(db: Session, package: dict[str, Any]) -> Project:
    if "project" not in package:
        raise ValueError("Import package must include a project object.")
    p = package["project"]
    project = Project(
        project_name=p.get("project_name", "Imported Project"),
        project_number=p.get("project_number", ""),
        client=p.get("client", ""),
        location=p.get("location", ""),
        description=p.get("description", ""),
        status=p.get("status", "Active"),
    )
    db.add(project)
    db.flush()
    for c in package.get("calculations", []):
        calc = Calculation(
            project_id=project.id,
            calc_number=c.get("calc_number", ""),
            crossing_name=c.get("crossing_name", ""),
            calculation_type=normalize_calculation_type(c.get("calculation_type", "Highway")),
            road_highway=c.get("road_highway", ""),
            railroad_route=c.get("railroad_route", ""),
            prepared_by=c.get("prepared_by", ""),
            checked_by=c.get("checked_by", ""),
            reviewer=c.get("reviewer", ""),
            revision=c.get("revision", "0"),
            status=c.get("status", "Draft"),
            review_comments=c.get("review_comments", ""),
            notes=c.get("notes", ""),
            overall_result=c.get("overall_result", "Not Calculated"),
            controlling_check=c.get("controlling_check", ""),
        )
        db.add(calc)
        db.flush()
        scenarios = c.get("scenarios", []) or [{"scenario_name": "Base Case"}]
        for s in scenarios:
            scenario = Scenario(
                calculation_id=calc.id,
                scenario_name=s.get("scenario_name", "Base Case"),
                description=s.get("description", ""),
                shared_inputs_json=dumps(s.get("shared_inputs", {})),
                highway_inputs_json=dumps(s.get("highway_inputs", {})),
                railroad_inputs_json=dumps(s.get("railroad_inputs", {})),
                results_json=dumps(s.get("results", {})),
                intermediate_values_json=dumps(s.get("intermediate_values", {})),
                warnings_json=dumps(s.get("warnings", [])),
            )
            db.add(scenario)
            db.flush()
            run_scenario(db, scenario)
    db.commit()
    db.refresh(project)
    return project


def _calculation_dict(calc: Calculation) -> dict[str, Any]:
    return {
        **model_dict(calc),
        "scenarios": [_scenario_dict(scenario) for scenario in calc.scenarios],
    }


def _scenario_dict(scenario: Scenario) -> dict[str, Any]:
    return {
        **model_dict(scenario),
        "shared_inputs": loads(scenario.shared_inputs_json, {}),
        "highway_inputs": loads(scenario.highway_inputs_json, {}),
        "railroad_inputs": loads(scenario.railroad_inputs_json, {}),
        "results": loads(scenario.results_json, {}),
        "intermediate_values": loads(scenario.intermediate_values_json, {}),
        "warnings": loads(scenario.warnings_json, []),
    }


def model_dict(model) -> dict[str, Any]:
    out = {}
    for col in model.__table__.columns:
        value = getattr(model, col.name)
        out[col.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return out
