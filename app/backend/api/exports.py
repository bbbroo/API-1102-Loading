from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.backend.database.models import ExportRecord
from app.backend.database.session import get_db
from app.backend.exports.csv import render_csv
from app.backend.exports.json_package import render_json
from app.backend.exports.pdf import render_pdf
from app.backend.reporting.models import ReportOptions
from app.backend.reporting.pdf import render_detailed_pdf
from app.backend.reporting.service import DetailedReportBlocked, build_detailed_report_data
from app.backend.services.import_export_service import calculation_package, import_project_package, project_package, scenario_package

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/project/{project_id}.json")
def export_json(project_id: int, db: Session = Depends(get_db)):
    try:
        package = project_package(db, project_id)
        content = render_json(package)
    except ValueError:
        raise HTTPException(404, "Project not found")
    record_export(db, project_id, None, "json", f"project-{project_id}.hdr1102.json")
    return Response(content, media_type="application/json", headers={"Content-Disposition": f"attachment; filename=project-{project_id}.hdr1102.json"})


@router.get("/project/{project_id}.csv")
def export_csv(project_id: int, db: Session = Depends(get_db)):
    try:
        content = render_csv(project_package(db, project_id))
    except ValueError:
        raise HTTPException(404, "Project not found")
    record_export(db, project_id, None, "csv", f"project-{project_id}.csv")
    return Response(content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=project-{project_id}.csv"})


@router.get("/project/{project_id}.pdf")
def export_pdf(project_id: int, db: Session = Depends(get_db)):
    try:
        content = render_pdf(project_package(db, project_id))
    except ValueError:
        raise HTTPException(404, "Project not found")
    record_export(db, project_id, None, "pdf", f"project-{project_id}.pdf")
    return Response(content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=project-{project_id}.pdf"})


@router.get("/calculation/{calculation_id}.json")
def export_calculation_json(calculation_id: int, db: Session = Depends(get_db)):
    try:
        package = calculation_package(db, calculation_id)
    except ValueError:
        raise HTTPException(404, "Calculation not found")
    project_id = package["project"]["id"]
    record_export(db, project_id, None, "json", f"calculation-{calculation_id}.hdr1102.json", calculation_id=calculation_id)
    return Response(render_json(package), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=calculation-{calculation_id}.hdr1102.json"})


@router.get("/calculation/{calculation_id}.csv")
def export_calculation_csv(calculation_id: int, db: Session = Depends(get_db)):
    try:
        package = calculation_package(db, calculation_id)
    except ValueError:
        raise HTTPException(404, "Calculation not found")
    project_id = package["project"]["id"]
    record_export(db, project_id, None, "csv", f"calculation-{calculation_id}.csv", calculation_id=calculation_id)
    return Response(render_csv(package), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=calculation-{calculation_id}.csv"})


@router.get("/calculation/{calculation_id}.pdf")
def export_calculation_pdf(calculation_id: int, db: Session = Depends(get_db)):
    try:
        package = calculation_package(db, calculation_id)
    except ValueError:
        raise HTTPException(404, "Calculation not found")
    project_id = package["project"]["id"]
    record_export(db, project_id, None, "pdf", f"calculation-{calculation_id}.pdf", calculation_id=calculation_id)
    return Response(render_pdf(package), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=calculation-{calculation_id}.pdf"})


@router.get("/scenario/{scenario_id}.json")
def export_scenario_json(scenario_id: int, db: Session = Depends(get_db)):
    try:
        package = scenario_package(db, scenario_id)
    except ValueError:
        raise HTTPException(404, "Scenario not found")
    project_id = package["project"]["id"]
    calculation_id = package["calculations"][0]["id"]
    record_export(db, project_id, scenario_id, "json", f"scenario-{scenario_id}.hdr1102.json", calculation_id=calculation_id)
    return Response(render_json(package), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=scenario-{scenario_id}.hdr1102.json"})


@router.get("/scenario/{scenario_id}.csv")
def export_scenario_csv(scenario_id: int, db: Session = Depends(get_db)):
    try:
        package = scenario_package(db, scenario_id)
    except ValueError:
        raise HTTPException(404, "Scenario not found")
    project_id = package["project"]["id"]
    calculation_id = package["calculations"][0]["id"]
    record_export(db, project_id, scenario_id, "csv", f"scenario-{scenario_id}.csv", calculation_id=calculation_id)
    return Response(render_csv(package), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=scenario-{scenario_id}.csv"})


@router.get("/scenario/{scenario_id}.pdf")
def export_scenario_pdf(scenario_id: int, db: Session = Depends(get_db)):
    try:
        package = scenario_package(db, scenario_id)
    except ValueError:
        raise HTTPException(404, "Scenario not found")
    project_id = package["project"]["id"]
    calculation_id = package["calculations"][0]["id"]
    record_export(db, project_id, scenario_id, "pdf", f"scenario-{scenario_id}.pdf", calculation_id=calculation_id)
    return Response(render_pdf(package), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=scenario-{scenario_id}.pdf"})


@router.post("/scenario/{scenario_id}/detailed.pdf")
def export_scenario_detailed_pdf(scenario_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        options = ReportOptions.from_payload(payload.get("report_options"))
        data = build_detailed_report_data(
            db,
            scenario_id,
            project_id=int(payload.get("project_id")),
            calculation_id=int(payload.get("calculation_id")),
            options=options,
        )
    except (TypeError, ValueError) as exc:
        if isinstance(exc, DetailedReportBlocked):
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Detailed PDF generation is blocked.",
                    "issues": [issue.__dict__ for issue in exc.issues],
                    "recovery_action": "Recalculate Scenario",
                },
            )
        raise HTTPException(status_code=400, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    filename = f"scenario-{scenario_id}-detailed.pdf"
    return Response(
        render_detailed_pdf(data),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/records")
def export_records(calculation_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(ExportRecord)
    if calculation_id:
        query = query.filter(ExportRecord.calculation_id == calculation_id)
    return [
        {
            "id": record.id,
            "calculation_id": record.calculation_id,
            "scenario_id": record.scenario_id,
            "export_type": record.export_type,
            "file_name": record.file_name,
            "exported_at": record.exported_at,
        }
        for record in query.order_by(ExportRecord.exported_at.desc()).limit(25).all()
    ]


@router.post("/import")
def import_json(package: dict, db: Session = Depends(get_db)):
    try:
        project = import_project_package(db, package)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return {"project_id": project.id, "project_name": project.project_name}


def record_export(db: Session, project_id: int, scenario_id: int | None, export_type: str, file_name: str, calculation_id: int | None = None) -> None:
    if calculation_id is None:
        package = project_package(db, project_id)
        first_calc = next(iter(package.get("calculations", [])), None)
        calculation_id = first_calc["id"] if first_calc else None
    if calculation_id is None:
        return
    db.add(ExportRecord(calculation_id=calculation_id, scenario_id=scenario_id, export_type=export_type, file_name=file_name))
    db.commit()
