from __future__ import annotations

import math
from typing import Any

from app.calculations.result_models import StressCheck, WarningMessage
from app.standards.design_factors import design_factor, temperature_derating
from app.standards.design_factors import DESIGN_FACTORS
from app.standards.fatigue_limits import fatigue_limits
from app.standards.material_properties import MATERIAL_PROPERTIES
from app.standards.pipe_dimensions import PIPE_DIMENSIONS, get_pipe, normalize_nps
from app.standards.pipe_grades import PIPE_GRADES, WELD_SEAM_FACTORS, joint_factor, smys
from app.standards.soil_properties import SOIL_PROPERTIES


DEFAULT_SHARED_HIGHWAY = {
    "nps": "12",
    "wall_thickness": 0.25,
    "pipe_specification": "API 5L",
    "pipe_grade": "X65",
    "pipeline_location": "Pipelines, mains, and service lines",
    "class_location": "1",
    "weld_seam_type": "Electric Resistance Welded",
    "pipe_material": "Steel",
    "operating_temperature": 70.0,
    "installation_temperature": 70.0,
    "operating_pressure": 1000.0,
    "soil_type": "Loose sands and gravels",
    "soil_unit_weight": 120.0,
    "cover_depth": 6.0,
    "bored_diameter": 14.75,
}

DEFAULT_SHARED_RAILROAD = {
    **DEFAULT_SHARED_HIGHWAY,
    "wall_thickness": 0.25,
    "pipe_grade": "X42",
    "operating_pressure": 800.0,
    "soil_type": "Soft to medium clays and silts with high plasticities",
}


def enrich_shared_inputs(inputs: dict[str, Any]) -> dict[str, float | str]:
    nps = normalize_nps(inputs.get("nps", "12"))
    if nps not in PIPE_DIMENSIONS:
        nps = "12"
    pipe = get_pipe(nps)
    pipe_material = _choice(inputs.get("pipe_material"), MATERIAL_PROPERTIES, "Steel")
    material = MATERIAL_PROPERTIES[pipe_material]
    soil_type = _choice(inputs.get("soil_type"), SOIL_PROPERTIES, "Loose sands and gravels")
    soil = SOIL_PROPERTIES[soil_type]
    d = float(pipe["outside_diameter"])
    wall_options = [float(option) for option in pipe.get("wall_thickness_options", [])]
    tw_input = float(inputs.get("wall_thickness", 0) or 0)
    if tw_input > 0:
        tw = tw_input
    else:
        tw = float(wall_options[0] if wall_options else 0.0)
    bd = float(inputs.get("bored_diameter", d + 2))
    cover = float(inputs.get("cover_depth", 0))
    specification = _choice(inputs.get("pipe_specification"), PIPE_GRADES, "API 5L")
    grade = _choice(inputs.get("pipe_grade"), PIPE_GRADES[specification], next(iter(PIPE_GRADES[specification])))
    weld = _choice(inputs.get("weld_seam_type"), WELD_SEAM_FACTORS, "Electric Resistance Welded")
    op_temp = float(inputs.get("operating_temperature", 70.0))
    pipeline_location = _choice(inputs.get("pipeline_location"), DESIGN_FACTORS, "Pipelines, mains, and service lines")
    class_location = _choice(str(inputs.get("class_location", "1")), DESIGN_FACTORS[pipeline_location], "1")
    return {
        **inputs,
        "nps": nps,
        "outside_diameter": d,
        "wall_thickness": tw,
        "bored_diameter": bd,
        "cover_depth": cover,
        "tw_d": tw / d if d else 0,
        "bd_d": bd / d if d else 0,
        "h_bd": cover * 12 / bd if bd else 0,
        "smys": float(inputs.get("smys") or smys(specification, grade)),
        "joint_factor": float(inputs.get("joint_factor") or joint_factor(weld)),
        "design_factor": float(inputs.get("design_factor") or design_factor(pipeline_location, class_location)),
        "temperature_derating_factor": float(inputs.get("temperature_derating_factor") or temperature_derating(op_temp)),
        "youngs_modulus": float(inputs.get("youngs_modulus") or material["youngs_modulus"]),
        "poisson_ratio": float(inputs.get("poisson_ratio") or material["poisson_ratio"]),
        "thermal_expansion": float(inputs.get("thermal_expansion") or material["thermal_expansion"]),
        "e_prime": float(inputs.get("e_prime") or soil["e_prime"]),
        "er": float(inputs.get("er") or soil["er"]),
        "soil_unit_weight": float(inputs.get("soil_unit_weight", 120.0)),
        "operating_pressure": float(inputs.get("operating_pressure", 0.0)),
        "installation_temperature": float(inputs.get("installation_temperature", 70.0)),
        "operating_temperature": op_temp,
        "pipe_specification": specification,
        "pipe_grade": grade,
        "weld_seam_type": weld,
        "pipe_material": pipe_material,
        "pipeline_location": pipeline_location,
        "class_location": class_location,
        "soil_type": soil_type,
    }


def _choice(value: Any, options: dict, default: str) -> str:
    text = str(value) if value not in (None, "") else default
    return text if text in options else default


def base_stresses(shared: dict[str, Any], live_circ: float, live_long: float, earth: float) -> dict[str, float]:
    p = shared["operating_pressure"]
    d = shared["outside_diameter"]
    tw = shared["wall_thickness"]
    shi = p * d / (2 * tw)
    allowable_hoop = shared["design_factor"] * shared["joint_factor"] * shared["temperature_derating_factor"] * shared["smys"]
    shi_internal = p * (d - tw) / (2 * tw)
    s1 = earth + live_circ + shi_internal
    s2 = live_long - shared["youngs_modulus"] * shared["thermal_expansion"] * (shared["operating_temperature"] - shared["installation_temperature"]) + shared["poisson_ratio"] * (earth + shi_internal)
    s3 = -p
    seff = math.sqrt(0.5 * ((s1 - s2) ** 2 + (s2 - s3) ** 2 + (s3 - s1) ** 2))
    allowable_effective = shared["smys"] * shared["design_factor"]
    fatigue = fatigue_limits(shared["smys"], str(shared.get("weld_seam_type", "Electric Resistance Welded")), d)
    allowable_girth = fatigue["girth"] * shared["design_factor"]
    allowable_longitudinal = fatigue["longitudinal"] * shared["design_factor"]
    return {
        "SHi": shi,
        "allowable_hoop": allowable_hoop,
        "SHi_internal": shi_internal,
        "S1": s1,
        "S2": s2,
        "S3": s3,
        "Seff": seff,
        "allowable_effective": allowable_effective,
        "fatigue_girth": fatigue["girth"],
        "fatigue_longitudinal": fatigue["longitudinal"],
        "allowable_girth": allowable_girth,
        "allowable_longitudinal": allowable_longitudinal,
    }


def checks_from_values(values: dict[str, float], girth_calculated: float, longitudinal_calculated: float) -> list[StressCheck]:
    return [
        StressCheck("Barlow Stress", values["SHi"], values["allowable_hoop"]),
        StressCheck("Effective Stress", values["Seff"], values["allowable_effective"]),
        StressCheck("Girth Weld Stress", girth_calculated, values["allowable_girth"]),
        StressCheck("Longitudinal Weld Stress", longitudinal_calculated, values["allowable_longitudinal"]),
    ]


def trace_warnings(traces) -> list[WarningMessage]:
    return [WarningMessage("lookup_range", t.warning, "review") for t in traces if t.warning]
