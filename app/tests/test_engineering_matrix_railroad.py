from __future__ import annotations

import pytest

from app.calculations.railroad import calculate_railroad
from app.calculations.shared import DEFAULT_SHARED_RAILROAD
from app.standards.pipe_dimensions import PIPE_DIMENSIONS
from app.standards.soil_properties import SOIL_PROPERTIES
from app.tests.helpers import (
    assert_expected_checks,
    assert_finite_intermediates,
    assert_finite_number,
    assert_valid_result_status,
    warning_codes,
)


NPS_VALUES = ["6", "8", "12", "16", "24", "36", "48"]
COVERS = [1, 3, 6, 8, 10, 14, 30]
PRESSURES = [-14.73, 0, 100, 800, 1000, 1440, 3000, 6000]
SURFACE_PRESSURES = [5, 10, 13.9, 15, 20, 30]
TRACKS = [1, 2]
SOILS = list(SOIL_PROPERTIES)


def railroad_cases():
    cases = []
    for index in range(144):
        nps = NPS_VALUES[index % len(NPS_VALUES)]
        options = [float(value) for value in PIPE_DIMENSIONS[nps]["wall_thickness_options"]]
        cases.append(
            {
                "shared": {
                    **DEFAULT_SHARED_RAILROAD,
                    "nps": nps,
                    "wall_thickness": options[(index // 7) % len(options)],
                    "bored_diameter": float(PIPE_DIMENSIONS[nps]["outside_diameter"]) + 2.0,
                    "cover_depth": COVERS[index % len(COVERS)],
                    "operating_pressure": PRESSURES[(index // 3) % len(PRESSURES)],
                    "soil_type": SOILS[(index // 5) % len(SOILS)],
                },
                "railroad": {
                    "surface_pressure": SURFACE_PRESSURES[(index // 11) % len(SURFACE_PRESSURES)],
                    "number_of_tracks": TRACKS[(index // 13) % len(TRACKS)],
                },
            }
        )
    return cases


@pytest.mark.parametrize("case", railroad_cases())
def test_railroad_engineering_matrix_cases(case):
    result = calculate_railroad(case["shared"], case["railroad"])
    assert_expected_checks(result)
    assert_valid_result_status(result)
    assert_finite_intermediates(result)
    for check in result.checks:
        assert_finite_number(check.calculated_psi, f"{check.name} calculated")
        assert_finite_number(check.allowable_psi, f"{check.name} allowable")
    repeated = calculate_railroad(case["shared"], case["railroad"])
    assert [check.calculated_psi for check in result.checks] == [check.calculated_psi for check in repeated.checks]
    higher_surface = calculate_railroad(case["shared"], {**case["railroad"], "surface_pressure": case["railroad"]["surface_pressure"] + 1})
    assert higher_surface.intermediate_values["SHr"] > result.intermediate_values["SHr"]
    assert higher_surface.intermediate_values["SLr"] > result.intermediate_values["SLr"]


@pytest.mark.parametrize("bad_track", [0, 3, "bad"])
def test_railroad_invalid_matrix_track_count_warning_contract(bad_track):
    result = calculate_railroad({}, {"number_of_tracks": bad_track})
    assert "tracks_invalid" in warning_codes(result)
    assert result.intermediate_values["number_of_tracks"] == 2


def test_railroad_default_case_contract():
    result = calculate_railroad()
    assert result.calculation_type == "Railroad"
    assert result.overall_result == "Fail"
    assert result.controlling_check == "Girth Weld Stress"
    assert_expected_checks(result)
    assert warning_codes(result) == set()


def test_railroad_high_surface_pressure_increases_live_load_stress():
    low = calculate_railroad({}, {"surface_pressure": 5})
    high = calculate_railroad({}, {"surface_pressure": 30})
    assert high.intermediate_values["SHr"] > low.intermediate_values["SHr"]
    assert high.intermediate_values["SLr"] > low.intermediate_values["SLr"]


def test_railroad_invalid_track_count_warning_contract():
    result = calculate_railroad({}, {"number_of_tracks": "bad"})
    assert "tracks_invalid" in warning_codes(result)
    assert result.intermediate_values["number_of_tracks"] == 2


def test_railroad_one_track_uses_api_single_track_factors():
    one = calculate_railroad({}, {"number_of_tracks": 1})
    two = calculate_railroad({}, {"number_of_tracks": 2})
    assert one.intermediate_values["number_of_tracks"] == 1
    assert two.intermediate_values["number_of_tracks"] == 2
    assert one.intermediate_values["Nh"] == 1.0
    assert one.intermediate_values["NL"] == 1.0
    assert two.intermediate_values["Nh"] > one.intermediate_values["Nh"]
    assert two.intermediate_values["NL"] > one.intermediate_values["NL"]
    assert one.intermediate_values["SHr"] < two.intermediate_values["SHr"]
    assert one.intermediate_values["SLr"] < two.intermediate_values["SLr"]


def test_railroad_geometry_uses_ten_foot_curve_through_ten_feet():
    eight = calculate_railroad({"cover_depth": 8})
    ten = calculate_railroad({"cover_depth": 10})
    just_over_ten = calculate_railroad({"cover_depth": 10.1})
    assert eight.intermediate_values["GHr"] == pytest.approx(ten.intermediate_values["GHr"])
    assert eight.intermediate_values["GLr"] == pytest.approx(ten.intermediate_values["GLr"])
    assert just_over_ten.intermediate_values["GHr"] != pytest.approx(ten.intermediate_values["GHr"])
    assert just_over_ten.intermediate_values["GLr"] != pytest.approx(ten.intermediate_values["GLr"])


def test_railroad_cover_increase_reduces_live_load_trend():
    shallow = calculate_railroad({"cover_depth": 3})
    deep = calculate_railroad({"cover_depth": 14})
    assert deep.intermediate_values["SHr"] < shallow.intermediate_values["SHr"]
    assert deep.intermediate_values["SLr"] < shallow.intermediate_values["SLr"]


@pytest.mark.parametrize(
    ("cover_depth", "impact_factor"),
    [(0, 1.75), (5, 1.75), (6, 1.72), (30, 1.0), (40, 1.0)],
)
def test_railroad_impact_factor_uses_api_linear_rule(cover_depth, impact_factor):
    result = calculate_railroad({"cover_depth": cover_depth})
    assert result.intermediate_values["Fi"] == pytest.approx(impact_factor)
