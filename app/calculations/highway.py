from __future__ import annotations

from typing import Any

from app.calculations.interpolation import linear, two_step
from app.calculations.result_models import CalculationResult, summarize_checks
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY, base_stresses, checks_from_values, enrich_shared_inputs, trace_warnings
from app.calculations.validation import validate_shared_inputs
from app.standards import highway_tables as tables

DEFAULT_HIGHWAY_INPUTS = {"pavement_type": "Flexible", "axle_configuration": "Tandem Axle"}


def _depth_band_highway(cover: float) -> str:
    if cover < 6:
        return "3"
    if cover < 8:
        return "6"
    if cover < 10:
        return "8"
    return "10"


def _pavement_factor_case(shared: dict[str, Any]) -> str:
    if float(shared["cover_depth"]) < 4 and float(shared["outside_diameter"]) <= 12:
        return "shallow_small"
    return "standard"


def _highway_glh(shared: dict[str, Any], band: str):
    table = tables.GL_BY_DEPTH.get(band, tables.GL_BY_DEPTH["6"])
    outside_diameter = float(shared["outside_diameter"])
    cover_depth = float(shared["cover_depth"])
    if band == "8" and outside_diameter in table and cover_depth in table:
        return linear("Highway GLh workbook fallback", table, cover_depth, warn_extrapolation=False)
    return linear("Highway GLh", table, outside_diameter)


def calculate_highway(shared_inputs: dict[str, Any] | None = None, highway_inputs: dict[str, Any] | None = None) -> CalculationResult:
    shared = enrich_shared_inputs({**DEFAULT_SHARED_HIGHWAY, **(shared_inputs or {})})
    highway = {**DEFAULT_HIGHWAY_INPUTS, **(highway_inputs or {})}
    warnings = validate_shared_inputs(shared)
    traces = []

    khe, more = two_step("Highway earth Khe", tables.EARTH_KHE_BY_E_PRIME, shared["e_prime"], shared["tw_d"])
    traces.extend(more)
    burial_table = tables.BURIAL_A_BY_H_BD if shared["e_prime"] < 1000 else tables.BURIAL_B_BY_H_BD
    be, t = linear("Highway burial factor", burial_table, shared["h_bd"])
    traces.append(t)
    ee, t = linear("Highway excavation factor", tables.EXCAVATION_BY_BD_D, shared["bd_d"])
    traces.append(t)
    she = khe * be * ee * (shared["soil_unit_weight"] / (12**3)) * shared["outside_diameter"]

    fi, t = linear("Highway impact factor", tables.IMPACT_BY_COVER, shared["cover_depth"])
    traces.append(t)
    khh, more = two_step("Highway KHh", tables.KH_BY_ER, shared["er"], shared["tw_d"])
    traces.extend(more)
    klh, more = two_step("Highway KLh", tables.KL_BY_ER, shared["er"], shared["tw_d"])
    traces.extend(more)
    band = _depth_band_highway(shared["cover_depth"])
    ghh, t = linear("Highway GHh", tables.GH_BY_DEPTH.get(band, tables.GH_BY_DEPTH["6"]), shared["outside_diameter"])
    traces.append(t)
    glh, t = _highway_glh(shared, band)
    traces.append(t)
    pavement_type = highway.get("pavement_type") if highway.get("pavement_type") in {"Flexible", "None", "Rigid"} else DEFAULT_HIGHWAY_INPUTS["pavement_type"]
    axle_configuration = highway.get("axle_configuration") if highway.get("axle_configuration") in {"Single Axle", "Tandem Axle"} else DEFAULT_HIGHWAY_INPUTS["axle_configuration"]
    pavement_factor_case = _pavement_factor_case(shared)
    factors = tables.PAVEMENT_AXLE_FACTORS[pavement_factor_case][(pavement_type, axle_configuration)]
    wheel_load = float(highway.get("design_wheel_load") or factors["wheel_load"])
    r = float(highway.get("pavement_factor") or factors["R"])
    l = float(highway.get("axle_factor") or factors["L"])
    shh = khh * ghh * r * l * fi * wheel_load / (12**2)
    slh = klh * glh * r * l * fi * wheel_load / (12**2)

    values = base_stresses(shared, shh, slh, she)
    checks = checks_from_values(values, slh, shh)
    warnings.extend(trace_warnings(traces))
    overall, controlling = summarize_checks(checks, warnings)
    intermediate = {
        **shared,
        **values,
        "Khe": khe,
        "Be": be,
        "Ee": ee,
        "SHe": she,
        "Fi": fi,
        "KHh": khh,
        "GHh": ghh,
        "R": r,
        "L": l,
        "SHh": shh,
        "KLh": klh,
        "GLh": glh,
        "SLh": slh,
        "design_wheel_load": wheel_load,
        "pavement_type": pavement_type,
        "axle_configuration": axle_configuration,
        "pavement_factor_case": pavement_factor_case,
    }
    return CalculationResult("Highway", checks, intermediate, warnings, traces, overall, controlling)
