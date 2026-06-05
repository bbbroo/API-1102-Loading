from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Project, Scenario
from app.backend.database.session import get_db
from app.backend.schemas.project import ProjectCreate, ProjectPatch, ProjectRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.updated_at.desc()).all()


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("/{project_id}/detail")
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    calculations = []
    for calc in project.calculations:
        calculations.append(
            {
                "id": calc.id,
                "project_id": calc.project_id,
                "calc_number": calc.calc_number,
                "crossing_name": calc.crossing_name,
                "calculation_type": calc.calculation_type,
                "status": calc.status,
                "overall_result": calc.overall_result,
                "controlling_check": calc.controlling_check,
                "revision": calc.revision,
                "updated_at": calc.updated_at,
                "scenario_count": len(calc.scenarios),
            }
        )
    return {
        "project": project,
        "calculation_count": len(calculations),
        "latest_modified": max([project.updated_at, *[calc.updated_at for calc in project.calculations]], default=project.updated_at),
        "result_summary": {
            "Pass": sum(1 for calc in project.calculations if calc.overall_result == "Pass"),
            "Fail": sum(1 for calc in project.calculations if calc.overall_result == "Fail"),
            "Needs Review": sum(1 for calc in project.calculations if calc.overall_result == "Needs Review"),
            "Not Calculated": sum(1 for calc in project.calculations if calc.overall_result == "Not Calculated"),
        },
        "recent_calculations": sorted(calculations, key=lambda calc: calc["updated_at"], reverse=True)[:5],
        "calculations": calculations,
    }


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectCreate, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for key, value in payload.model_dump().items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def patch_project(project_id: int, payload: ProjectPatch, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.post("/{project_id}/duplicate", response_model=ProjectRead)
def duplicate_project(project_id: int, db: Session = Depends(get_db)):
    source = db.get(Project, project_id)
    if not source:
        raise HTTPException(404, "Project not found")
    clone = Project(project_name=f"{source.project_name} Copy", project_number=source.project_number, client=source.client, location=source.location, description=source.description, status=source.status)
    db.add(clone)
    db.flush()
    for calc in source.calculations:
        c = Calculation(project_id=clone.id, calc_number=f"{calc.calc_number}-COPY", crossing_name=calc.crossing_name, calculation_type=calc.calculation_type, road_highway=calc.road_highway, railroad_route=calc.railroad_route, prepared_by=calc.prepared_by, checked_by=calc.checked_by, reviewer=calc.reviewer, date=calc.date, revision=calc.revision, status=calc.status, review_comments=calc.review_comments, notes=calc.notes, overall_result=calc.overall_result, controlling_check=calc.controlling_check)
        db.add(c)
        db.flush()
        for scenario in calc.scenarios:
            db.add(Scenario(calculation_id=c.id, scenario_name=scenario.scenario_name, description=scenario.description, shared_inputs_json=scenario.shared_inputs_json, highway_inputs_json=scenario.highway_inputs_json, railroad_inputs_json=scenario.railroad_inputs_json, results_json=scenario.results_json, intermediate_values_json=scenario.intermediate_values_json, warnings_json=scenario.warnings_json))
    db.commit()
    db.refresh(clone)
    return clone


@router.post("/{project_id}/archive", response_model=ProjectRead)
def archive_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    project.status = "Archived"
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}
