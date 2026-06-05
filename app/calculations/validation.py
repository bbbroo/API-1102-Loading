from __future__ import annotations

import math

from app.calculations.result_models import WarningMessage
from app.standards.dropdown_options import CALCULATION_STATUSES
from app.standards.pipe_dimensions import PIPE_DIMENSIONS, normalize_nps


def validate_shared_inputs(inputs: dict) -> list[WarningMessage]:
    warnings: list[WarningMessage] = []
    required = ["nps", "wall_thickness", "cover_depth", "bored_diameter", "operating_pressure", "soil_unit_weight"]
    for key in required:
        if inputs.get(key) in (None, ""):
            warnings.append(WarningMessage("required_missing", f"Required input missing: {key}", "error"))
    d = float(inputs.get("outside_diameter") or 0)
    tw = float(inputs.get("wall_thickness") or 0)
    bd = float(inputs.get("bored_diameter") or 0)
    h = float(inputs.get("cover_depth") or 0)
    if d <= 0:
        warnings.append(WarningMessage("diameter_invalid", "Pipe outside diameter must be positive.", "error"))
    if tw <= 0:
        warnings.append(WarningMessage("wall_invalid", "Wall thickness must be positive.", "error"))
    else:
        nps = normalize_nps(inputs.get("nps", ""))
        wall_options = [float(option) for option in PIPE_DIMENSIONS.get(nps, {}).get("wall_thickness_options", [])]
        if wall_options and not any(math.isclose(tw, option, rel_tol=0, abs_tol=1e-9) for option in wall_options):
            warnings.append(
                WarningMessage(
                    "wall_nonstandard",
                    "Wall thickness is not listed for the selected NPS standards table; the custom value is used in the calculation.",
                    "review",
                )
            )
    if bd and d and bd <= d:
        warnings.append(WarningMessage("bored_diameter_invalid", "Bored diameter must exceed pipe outside diameter.", "error"))
    if h and not (1 <= h <= 30):
        warnings.append(WarningMessage("cover_range", "Cover depth is outside workbook-supported range 1 to 30 ft.", "review"))
    pressure = float(inputs.get("operating_pressure") or 0)
    if pressure < 0:
        warnings.append(WarningMessage("pressure_invalid", "Operating pressure must be non-negative.", "error"))
    if pressure > 6000:
        warnings.append(WarningMessage("pressure_range", "Operating pressure is outside workbook-supported range 0 to 6000 psi.", "review"))
    gamma = float(inputs.get("soil_unit_weight") or 0)
    if gamma and not (50 <= gamma <= 200):
        warnings.append(WarningMessage("soil_weight_range", "Soil unit weight is outside workbook-supported range 50 to 200 pcf.", "review"))
    if inputs.get("status") and inputs["status"] not in CALCULATION_STATUSES:
        warnings.append(WarningMessage("status_invalid", "Status is not a supported documentation status.", "error"))
    return warnings
