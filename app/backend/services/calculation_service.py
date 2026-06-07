from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Scenario
from app.backend.services.calculation_defaults import merged_mode_inputs
from app.backend.services.helpers import dumps, loads
from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad

RESULT_PRIORITY = {"Fail": 4, "Needs Review": 3, "Pass": 2, "Not Calculated": 1}


def seed_scenario_for_mode(scenario: Scenario, calculation_type: str) -> Scenario:
    shared, highway, railroad = merged_mode_inputs(
        calculation_type,
        loads(scenario.shared_inputs_json, {}),
        loads(scenario.highway_inputs_json, {}),
        loads(scenario.railroad_inputs_json, {}),
    )
    scenario.shared_inputs_json = dumps(shared)
    scenario.highway_inputs_json = dumps(highway)
    scenario.railroad_inputs_json = dumps(railroad)
    return scenario


def run_scenario(db: Session, scenario: Scenario) -> Scenario:
    calc = db.get(Calculation, scenario.calculation_id)
    if calc:
        seed_scenario_for_mode(scenario, calc.calculation_type)
    shared = loads(scenario.shared_inputs_json, {})
    highway_inputs = loads(scenario.highway_inputs_json, {})
    railroad_inputs = loads(scenario.railroad_inputs_json, {})
    if calc and calc.calculation_type == "Railroad":
        result = calculate_railroad(shared, railroad_inputs)
    else:
        result = calculate_highway(shared, highway_inputs)
    payload = result.to_dict()
    payload["input_fingerprint"] = scenario_input_fingerprint(
        calc.calculation_type if calc else payload.get("calculation_type", "Highway"),
        shared,
        highway_inputs,
        railroad_inputs,
    )
    scenario.results_json = dumps(payload)
    scenario.intermediate_values_json = dumps(payload["intermediate_values"])
    scenario.warnings_json = dumps(payload["warnings"])
    if calc:
        update_calculation_summary(db, calc)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


def refresh_calculation(db: Session, calc: Calculation) -> Calculation:
    for scenario in db.query(Scenario).filter(Scenario.calculation_id == calc.id).all():
        run_scenario(db, scenario)
    db.refresh(calc)
    return calc


def update_calculation_summary(db: Session, calc: Calculation) -> Calculation:
    scenarios = db.query(Scenario).filter(Scenario.calculation_id == calc.id).all()
    if not scenarios:
        calc.overall_result = "Not Calculated"
        calc.controlling_check = ""
        db.add(calc)
        return calc

    ranked = []
    for scenario in scenarios:
        result = loads(scenario.results_json, {})
        status = result.get("overall_result") or "Not Calculated"
        ranked.append((RESULT_PRIORITY.get(status, 0), _controlling_utilization(result), scenario, result))

    _, _, controlling_scenario, controlling_result = max(ranked, key=lambda item: (item[0], item[1]))
    calc.overall_result = controlling_result.get("overall_result") or "Not Calculated"
    controlling_check = controlling_result.get("controlling_check") or ""
    calc.controlling_check = (
        f"{controlling_scenario.scenario_name}: {controlling_check}"
        if controlling_check and len(scenarios) > 1
        else controlling_check
    )
    db.add(calc)
    return calc


def _controlling_utilization(result: dict) -> float:
    checks = result.get("checks") or []
    if not checks:
        return 0.0
    failed = [check for check in checks if check.get("result") == "Fail"]
    controlling_checks = failed or checks
    return max(float(check.get("utilization") or 0.0) for check in controlling_checks)


def scenario_input_fingerprint(
    calculation_type: str,
    shared_inputs: dict[str, Any],
    highway_inputs: dict[str, Any],
    railroad_inputs: dict[str, Any],
) -> str:
    mode = "Railroad" if calculation_type == "Railroad" else "Highway"
    payload = {
        "calculation_type": mode,
        "shared_inputs": shared_inputs,
        "mode_inputs": railroad_inputs if mode == "Railroad" else highway_inputs,
    }
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
