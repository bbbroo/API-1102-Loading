from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Scenario
from app.backend.database.session import get_db
from app.backend.schemas.calculation import CalculationCreate, CalculationPatch, CalculationRead
from app.backend.services.calculation_defaults import merged_mode_inputs
from app.backend.services.calculation_service import refresh_calculation, run_scenario
from app.backend.services.helpers import dumps

router = APIRouter(prefix="/calculations", tags=["calculations"])


@router.get("", response_model=list[CalculationRead])
def list_calculations(project_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Calculation)
    if project_id:
        query = query.filter(Calculation.project_id == project_id)
    return query.order_by(Calculation.updated_at.desc()).all()


@router.post("", response_model=CalculationRead)
def create_calculation(payload: CalculationCreate, db: Session = Depends(get_db)):
    calc = Calculation(**payload.model_dump())
    db.add(calc)
    db.flush()
    shared, highway, railroad = merged_mode_inputs(payload.calculation_type)
    scenario = Scenario(
        calculation_id=calc.id,
        scenario_name="Base Case",
        shared_inputs_json=dumps(shared),
        highway_inputs_json=dumps(highway),
        railroad_inputs_json=dumps(railroad),
    )
    db.add(scenario)
    db.flush()
    run_scenario(db, scenario)
    db.refresh(calc)
    return calc


@router.get("/{calculation_id}", response_model=CalculationRead)
def get_calculation(calculation_id: int, db: Session = Depends(get_db)):
    calc = db.get(Calculation, calculation_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    return calc


@router.put("/{calculation_id}", response_model=CalculationRead)
def update_calculation(calculation_id: int, payload: CalculationCreate, db: Session = Depends(get_db)):
    calc = db.get(Calculation, calculation_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    previous_type = calc.calculation_type
    for key, value in payload.model_dump().items():
        setattr(calc, key, value)
    db.commit()
    db.refresh(calc)
    if calc.calculation_type != previous_type:
        refresh_calculation(db, calc)
    return calc


@router.patch("/{calculation_id}", response_model=CalculationRead)
def patch_calculation(calculation_id: int, payload: CalculationPatch, db: Session = Depends(get_db)):
    calc = db.get(Calculation, calculation_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    previous_type = calc.calculation_type
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(calc, key, value)
    db.commit()
    db.refresh(calc)
    if calc.calculation_type != previous_type:
        refresh_calculation(db, calc)
    return calc


@router.post("/{calculation_id}/duplicate", response_model=CalculationRead)
def duplicate_calculation(calculation_id: int, db: Session = Depends(get_db)):
    source = db.get(Calculation, calculation_id)
    if not source:
        raise HTTPException(404, "Calculation not found")
    clone = Calculation(project_id=source.project_id, calc_number=f"{source.calc_number}-COPY", crossing_name=source.crossing_name, calculation_type=source.calculation_type, road_highway=source.road_highway, railroad_route=source.railroad_route, prepared_by=source.prepared_by, checked_by=source.checked_by, reviewer=source.reviewer, date=source.date, revision=source.revision, status=source.status, review_comments=source.review_comments, notes=source.notes, overall_result=source.overall_result, controlling_check=source.controlling_check)
    db.add(clone)
    db.flush()
    for scenario in source.scenarios:
        db.add(Scenario(calculation_id=clone.id, scenario_name=scenario.scenario_name, description=scenario.description, shared_inputs_json=scenario.shared_inputs_json, highway_inputs_json=scenario.highway_inputs_json, railroad_inputs_json=scenario.railroad_inputs_json, results_json=scenario.results_json, intermediate_values_json=scenario.intermediate_values_json, warnings_json=scenario.warnings_json))
    db.commit()
    db.refresh(clone)
    return clone


@router.post("/{calculation_id}/calculate")
def calculate(calculation_id: int, db: Session = Depends(get_db)):
    calc = db.get(Calculation, calculation_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    scenarios = []
    for scenario in calc.scenarios:
        scenarios.append(run_scenario(db, scenario))
    return {"calculation_id": calculation_id, "scenario_count": len(scenarios), "overall_result": calc.overall_result, "controlling_check": calc.controlling_check}


@router.delete("/{calculation_id}")
def delete_calculation(calculation_id: int, db: Session = Depends(get_db)):
    calc = db.get(Calculation, calculation_id)
    if not calc:
        raise HTTPException(404, "Calculation not found")
    db.delete(calc)
    db.commit()
    return {"ok": True}
