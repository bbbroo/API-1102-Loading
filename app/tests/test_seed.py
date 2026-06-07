from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.backend.database.models import Base, Calculation, Project, Scenario
from app.backend.database.seed import seed_if_empty


def test_first_run_seed_creates_one_example_project_with_highway_and_railroad_calculations():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = Session()
    try:
        seed_if_empty(db)

        projects = db.query(Project).all()
        calculations = db.query(Calculation).all()
        scenarios = db.query(Scenario).all()

        assert len(projects) == 1
        assert projects[0].project_name == "Example Project - Highway and Railroad Crossings"
        assert len(calculations) == 2
        assert {calc.calculation_type for calc in calculations} == {"Highway", "Railroad"}
        assert {calc.crossing_name for calc in calculations} == {"Sample Highway Crossing", "Sample Railroad Crossing"}
        assert {calc.project_id for calc in calculations} == {projects[0].id}
        assert len(scenarios) == 2
        assert {scenario.scenario_name for scenario in scenarios} == {"Base Case"}
        assert all(scenario.results_json and scenario.results_json != "{}" for scenario in scenarios)

        seed_if_empty(db)
        assert db.query(Project).count() == 1
        assert db.query(Calculation).count() == 2
    finally:
        db.close()
