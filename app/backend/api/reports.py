from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.backend.database.session import get_db
from app.backend.reporting.models import ReportOptions
from app.backend.reporting.pdf import render_detailed_pdf
from app.backend.reporting.service import DetailedReportBlocked, build_detailed_report_data

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/scenario/{scenario_id}/detailed.pdf")
def detailed_scenario_pdf(scenario_id: int, payload: dict, db: Session = Depends(get_db)):
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
