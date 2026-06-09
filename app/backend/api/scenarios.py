from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Scenario
from app.backend.database.session import get_db
from app.backend.schemas.scenario import ScenarioCreate, ScenarioPatch
from app.backend.services.calculation_defaults import merged_mode_inputs
from app.backend.services.calculation_service import run_scenario, update_calculation_summary
from app.backend.services.helpers import dumps, loads
from app.standards.metadata import ENGINE_VERSION

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def scenario_payload(s: Scenario) -> dict:
    return {
        "id": s.id,
        "calculation_id": s.calculation_id,
        "scenario_name": s.scenario_name,
        "description": s.description,
        "shared_inputs": loads(s.shared_inputs_json, {}),
        "highway_inputs": loads(s.highway_inputs_json, {}),
        "railroad_inputs": loads(s.railroad_inputs_json, {}),
        "results": loads(s.results_json, {}),
        "intermediate_values": loads(s.intermediate_values_json, {}),
        "warnings": loads(s.warnings_json, []),
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


@router.get("")
def list_scenarios(calculation_id: int, db: Session = Depends(get_db)):
    scenarios = db.query(Scenario).filter(Scenario.calculation_id == calculation_id).all()
    for scenario in scenarios:
        results = loads(scenario.results_json, {})
        if not results.get("checks") or results.get("engine_version") != ENGINE_VERSION:
            run_scenario(db, scenario)
    scenarios = db.query(Scenario).filter(Scenario.calculation_id == calculation_id).all()
    return [scenario_payload(s) for s in scenarios]


@router.post("")
def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)):
    calculation_type = "Highway"
    if payload.calculation_id:
        calc = db.get(Calculation, payload.calculation_id)
        calculation_type = calc.calculation_type if calc else calculation_type
    shared, highway, railroad = merged_mode_inputs(calculation_type, payload.shared_inputs, payload.highway_inputs, payload.railroad_inputs)
    s = Scenario(calculation_id=payload.calculation_id, scenario_name=payload.scenario_name, description=payload.description, shared_inputs_json=dumps(shared), highway_inputs_json=dumps(highway), railroad_inputs_json=dumps(railroad))
    db.add(s)
    db.commit()
    db.refresh(s)
    run_scenario(db, s)
    return scenario_payload(s)


@router.put("/{scenario_id}")
def update_scenario(scenario_id: int, payload: ScenarioCreate, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Scenario not found")
    s.scenario_name = payload.scenario_name
    s.description = payload.description
    s.shared_inputs_json = dumps(payload.shared_inputs)
    s.highway_inputs_json = dumps(payload.highway_inputs)
    s.railroad_inputs_json = dumps(payload.railroad_inputs)
    run_scenario(db, s)
    return scenario_payload(s)


@router.patch("/{scenario_id}")
def patch_scenario(scenario_id: int, payload: ScenarioPatch, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Scenario not found")
    values = payload.model_dump(exclude_unset=True)
    if "calculation_id" in values:
        s.calculation_id = values["calculation_id"]
    if "scenario_name" in values:
        s.scenario_name = values["scenario_name"]
    if "description" in values:
        s.description = values["description"]
    if "shared_inputs" in values:
        s.shared_inputs_json = dumps(values["shared_inputs"])
    if "highway_inputs" in values:
        s.highway_inputs_json = dumps(values["highway_inputs"])
    if "railroad_inputs" in values:
        s.railroad_inputs_json = dumps(values["railroad_inputs"])
    run_scenario(db, s)
    return scenario_payload(s)


@router.post("/{scenario_id}/duplicate")
def duplicate_scenario(scenario_id: int, db: Session = Depends(get_db)):
    source = db.get(Scenario, scenario_id)
    if not source:
        raise HTTPException(404, "Scenario not found")
    clone = Scenario(calculation_id=source.calculation_id, scenario_name=f"{source.scenario_name} Copy", description=source.description, shared_inputs_json=source.shared_inputs_json, highway_inputs_json=source.highway_inputs_json, railroad_inputs_json=source.railroad_inputs_json, results_json=source.results_json, intermediate_values_json=source.intermediate_values_json, warnings_json=source.warnings_json)
    db.add(clone)
    db.commit()
    db.refresh(clone)
    if clone.calculation:
        update_calculation_summary(db, clone.calculation)
        db.commit()
    return scenario_payload(clone)


@router.post("/{scenario_id}/calculate")
def calculate_scenario(scenario_id: int, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Scenario not found")
    run_scenario(db, s)
    return scenario_payload(s)


@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    s = db.get(Scenario, scenario_id)
    if not s:
        raise HTTPException(404, "Scenario not found")
    calc = s.calculation
    db.delete(s)
    db.flush()
    if calc:
        update_calculation_summary(db, calc)
    db.commit()
    return {"ok": True}
