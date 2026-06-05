from __future__ import annotations

from typing import Any

from app.calculations.interpolation import bounds, linear, two_step
from app.calculations.result_models import CalculationResult, WarningMessage, summarize_checks
from app.calculations.shared import DEFAULT_SHARED_RAILROAD, base_stresses, checks_from_values, enrich_shared_inputs, trace_warnings
from app.calculations.validation import validate_shared_inputs
from app.standards import railroad_tables as tables

DEFAULT_RAILROAD_INPUTS = {"number_of_tracks": 2, "surface_pressure": 13.9}


def _depth_band_rail(cover: float) -> str:
    if cover <= 6:
        return "6"
    if cover <= 8:
        return "10"
    return "14"


def _railroad_glr(shared: dict[str, Any], band: str):
    table = tables.GL_BY_DEPTH[band]
    lower, upper, _ = bounds(list(table.keys()), float(shared["outside_diameter"]))
    segment = {lower: table[lower], upper: table[upper]}
    return linear("Railroad GLr workbook forecast", segment, float(shared["cover_depth"]), warn_extrapolation=False)


def calculate_railroad(shared_inputs: dict[str, Any] | None = None, railroad_inputs: dict[str, Any] | None = None) -> CalculationResult:
    shared = enrich_shared_inputs({**DEFAULT_SHARED_RAILROAD, **(shared_inputs or {})})
    rail = {**DEFAULT_RAILROAD_INPUTS, **(railroad_inputs or {})}
    warnings = validate_shared_inputs(shared)
    traces = []
    try:
        number_of_tracks = int(rail.get("number_of_tracks", 2))
    except (TypeError, ValueError):
        warnings.append(WarningMessage("tracks_invalid", "Number of tracks must be 1 or 2.", "error"))
        number_of_tracks = 2
    if number_of_tracks not in {1, 2}:
        warnings.append(WarningMessage("tracks_invalid", "Number of tracks must be 1 or 2.", "error"))
        number_of_tracks = 2

    khe, more = two_step("Railroad earth Khe", tables.EARTH_KHE_BY_E_PRIME, shared["e_prime"], shared["tw_d"])
    traces.extend(more)
    burial_table = tables.BURIAL_A_BY_H_BD if shared["e_prime"] < 1000 else tables.BURIAL_B_BY_H_BD
    be, t = linear("Railroad burial factor", burial_table, shared["h_bd"])
    traces.append(t)
    ee, t = linear("Railroad excavation factor", tables.EXCAVATION_BY_BD_D, shared["bd_d"])
    traces.append(t)
    she = khe * be * ee * (shared["soil_unit_weight"] / (12**3)) * shared["outside_diameter"]
    fi, t = linear("Railroad impact factor", tables.IMPACT_BY_COVER, shared["cover_depth"])
    traces.append(t)
    khr, more = two_step("Railroad KHr", tables.KH_BY_ER, shared["er"], shared["tw_d"])
    traces.extend(more)
    klr, more = two_step("Railroad KLr", tables.KL_BY_ER, shared["er"], shared["tw_d"])
    traces.extend(more)
    band = _depth_band_rail(shared["cover_depth"])
    ghr, t = linear("Railroad GHr", tables.GH_BY_DEPTH[band], shared["outside_diameter"])
    traces.append(t)
    glr, t = _railroad_glr(shared, band)
    traces.append(t)
    double_track_band = "6" if shared["cover_depth"] <= 6 else ("10" if shared["cover_depth"] <= 10 else "14")
    nh, t = linear("Railroad Nh factor", tables.NH_BY_DEPTH[double_track_band], shared["outside_diameter"])
    traces.append(t)
    nl, t = linear("Railroad NL factor", tables.NL_BY_DEPTH[double_track_band], shared["outside_diameter"])
    traces.append(t)
    w = float(rail.get("surface_pressure", 13.9))
    shr = nh * khr * ghr * fi * w
    slr = klr * glr * nl * fi * w

    values = base_stresses(shared, shr, slr, she)
    checks = checks_from_values(values, slr / nl if nl else slr, shr / nh if nh else shr)
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
        "Nh": nh,
        "KHr": khr,
        "GHr": ghr,
        "SHr": shr,
        "NL": nl,
        "KLr": klr,
        "GLr": glr,
        "SLr": slr,
        "surface_pressure": w,
        "number_of_tracks": number_of_tracks,
    }
    return CalculationResult("Railroad", checks, intermediate, warnings, traces, overall, controlling)
