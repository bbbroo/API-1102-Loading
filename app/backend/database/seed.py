from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Project, Scenario
from app.backend.services.calculation_service import run_scenario
from app.backend.services.helpers import dumps
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY, DEFAULT_SHARED_RAILROAD


def seed_if_empty(db: Session) -> None:
    if db.query(Project).count():
        return
    project = Project(
        project_name="Example Project - Highway and Railroad Crossings",
        project_number="EX-1102-001",
        client="HDR Internal",
        location="Rosemont, IL",
        description="Single first-run example project with one sample highway crossing calculation and one sample railroad crossing calculation.",
    )
    db.add(project)
    db.flush()
    highway = Calculation(
        project_id=project.id,
        calc_number="CALC-1102-001",
        crossing_name="Sample Highway Crossing",
        calculation_type="Highway",
        road_highway="Sample Highway",
        prepared_by="Example Engineer",
        checked_by="Example Checker",
        reviewer="",
        date=date.today(),
        revision="0",
        status="Draft",
    )
    railroad = Calculation(
        project_id=project.id,
        calc_number="CALC-1102-002",
        crossing_name="Sample Railroad Crossing",
        calculation_type="Railroad",
        railroad_route="Sample Railroad Route",
        prepared_by="Example Engineer",
        checked_by="Example Checker",
        date=date.today(),
        revision="0",
        status="Draft",
    )
    db.add_all([highway, railroad])
    db.flush()
    s1 = Scenario(calculation_id=highway.id, scenario_name="Base Case", shared_inputs_json=dumps(DEFAULT_SHARED_HIGHWAY), highway_inputs_json=dumps({"pavement_type": "Flexible", "axle_configuration": "Tandem Axle"}))
    s2 = Scenario(calculation_id=railroad.id, scenario_name="Base Case", shared_inputs_json=dumps(DEFAULT_SHARED_RAILROAD), railroad_inputs_json=dumps({"number_of_tracks": 2, "surface_pressure": 13.9}))
    db.add_all([s1, s2])
    db.commit()
    run_scenario(db, s1)
    run_scenario(db, s2)
