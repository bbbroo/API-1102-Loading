from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from app.backend.database.models import Calculation, Project
from app.backend.database.session import get_db
from app.backend.services.helpers import loads

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _pipe_size_label(calc: Calculation) -> str:
    """Extract the pipe size label from the calculation's first scenario."""
    scenarios = calc.scenarios
    if scenarios:
        shared = loads(scenarios[0].shared_inputs_json, {})
        nps = shared.get("nps", "12")
        wall = shared.get("wall_thickness", 0.250)
        return f"NPS {nps} x {float(wall):.3f} in"
    return "NPS 12 x 0.250 in"


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    calcs = (
        db.query(Calculation)
        .options(selectinload(Calculation.scenarios))
        .order_by(Calculation.updated_at.desc())
        .all()
    )
    cutoff = datetime.utcnow() - timedelta(days=7)
    recent_activity = sum(1 for p in projects if p.updated_at and p.updated_at >= cutoff)

    return {
        "total_projects": len(projects),
        "total_calculations": len(calcs),
        "recent_activity": recent_activity,
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
                "pipe_size": _pipe_size_label(c),
            }
            for c in calcs
        ],
    }
