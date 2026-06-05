from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Project
from app.backend.database.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    calcs = db.query(Calculation).order_by(Calculation.updated_at.desc()).all()
    return {
        "total_projects": len(projects),
        "total_calculations": len(calcs),
        "passing_calculations": sum(1 for c in calcs if c.overall_result == "Pass"),
        "failing_calculations": sum(1 for c in calcs if c.overall_result == "Fail"),
        "by_status": {status: sum(1 for c in calcs if c.status == status) for status in sorted({c.status for c in calcs} | {"Draft"})},
        "recent": [
            {
                "id": c.id,
                "calc_number": c.calc_number,
                "project": c.project.project_name if c.project else "",
                "crossing_name": c.crossing_name,
                "calculation_type": c.calculation_type,
                "status": c.status,
                "result": c.overall_result,
                "modified_date": c.updated_at,
                "prepared_by": c.prepared_by,
                "checked_by": c.checked_by,
                "reviewer": c.reviewer,
                "pipe_size": "NPS 12 x 0.250 in",
            }
            for c in calcs[:20]
        ],
    }
