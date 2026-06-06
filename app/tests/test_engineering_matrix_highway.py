from __future__ import annotations

import pytest

from app.calculations.highway import DEFAULT_HIGHWAY_INPUTS, calculate_highway
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY
from app.standards.pipe_dimensions import PIPE_DIMENSIONS
from app.standards.soil_properties import SOIL_PROPERTIES
from app.tests.helpers import (
    assert_expected_checks,
    assert_finite_intermediates,
    assert_finite_number,
    assert_valid_result_status,
    check_map,
    utilization,
    warning_codes,
)


NPS_VALUES = ["6", "8", "12", "16", "24", "36", "48"]
COVERS = [1, 3, 6, 8, 10, 14, 30]
PRESSURES = [-14.73, 0, 100, 800, 1000, 1440, 3000, 6000]
PAVEMENTS = ["Flexible", "Rigid", "None"]
AXLES = ["Single Axle", "Tandem Axle"]
SOILS = list(SOIL_PROPERTIES)


def wall_cases(nps: str) -> list[float]:
    options = [float(value) for value in PIPE_DIMENSIONS[nps]["wall_thickness_options"]]
    custom = round(options[0] + 0.013, 3)
    if custom in options:
        custom = round(options[0] + 0.017, 3)
    return [options[0], options[len(options) // 2], options[-1], custom]


def highway_cases():
    cases = []
    for index in range(168):
        nps = NPS_VALUES[index % len(NPS_VALUES)]
        pipe = PIPE_DIMENSIONS[nps]
        wall = wall_cases(nps)[(index // len(NPS_VALUES)) % 4]
        cases.append(
            {
                "shared": {
                    **DEFAULT_SHARED_HIGHWAY,
                    "nps": nps,
                    "wall_thickness": wall,
                    "bored_diameter": float(pipe["outside_diameter"]) + 2.0,
                    "cover_depth": COVERS[index % len(COVERS)],
                    "operating_pressure": PRESSURES[(index // 3) % len(PRESSURES)],
                    "soil_type": SOILS[(index // 5) % len(SOILS)],
                },
                "highway": {
                    "pavement_type": PAVEMENTS[(index // 7) % len(PAVEMENTS)],
                    "axle_configuration": AXLES[(index // 11) % len(AXLES)],
                },
                "custom_wall": wall not in [float(value) for value in pipe["wall_thickness_options"]],
            }
        )
    return cases


@pytest.mark.parametrize("case", highway_cases())
def test_highway_engineering_matrix_cases(case):
    result = calculate_highway(case["shared"], case["highway"])
    assert_expected_checks(result)
    assert_valid_result_status(result)
    assert_finite_intermediates(result)
    for check in result.checks:
        assert_finite_number(check.calculated_psi, f"{check.name} calculated")
        assert_finite_number(check.allowable_psi, f"{check.name} allowable")
    assert result.to_dict() == calculate_highway(case["shared"], case["highway"]).to_dict() | {"calculated_at": result.calculated_at}
    codes = warning_codes(result)
    if case["custom_wall"]:
        assert "wall_nonstandard" in codes
    if case["shared"]["operating_pressure"] < -14.73:
        assert "pressure_invalid" in codes
    if not 1 <= case["shared"]["cover_depth"] <= 30:
        assert "cover_range" in codes


def test_highway_default_case_contract():
    result = calculate_highway()
    assert result.calculation_type == "Highway"
    assert result.overall_result == "Pass"
    assert result.controlling_check == "Effective Stress"
    assert_expected_checks(result)
    assert warning_codes(result) == set()


def test_highway_high_pressure_failure_contract():
    result = calculate_highway({"operating_pressure": 6000})
    assert result.overall_result == "Fail"
    assert check_map(result)["Barlow Stress"].result == "Fail"


def test_highway_thicker_wall_reduces_barlow_utilization():
    thin = calculate_highway({"wall_thickness": 0.25})
    thick = calculate_highway({"wall_thickness": 0.5})
    assert utilization(check_map(thick)["Barlow Stress"]) < utilization(check_map(thin)["Barlow Stress"])


def test_highway_cover_increase_reduces_live_load_trend():
    shallow = calculate_highway({"cover_depth": 3})
    deep = calculate_highway({"cover_depth": 10})
    assert deep.intermediate_values["SHh"] < shallow.intermediate_values["SHh"]
    assert deep.intermediate_values["SLh"] < shallow.intermediate_values["SLh"]


def test_highway_pavement_and_axle_options_change_live_load():
    values = {
        (pavement, axle): calculate_highway({}, {"pavement_type": pavement, "axle_configuration": axle}).intermediate_values["SHh"]
        for pavement in PAVEMENTS
        for axle in AXLES
    }
    assert len(set(values.values())) > 1
    assert calculate_highway({}, {"pavement_type": "bad", "axle_configuration": "bad"}).intermediate_values["pavement_type"] == DEFAULT_HIGHWAY_INPUTS["pavement_type"]
