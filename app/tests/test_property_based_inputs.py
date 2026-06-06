from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY, DEFAULT_SHARED_RAILROAD
from app.standards.pipe_dimensions import PIPE_DIMENSIONS
from app.standards.soil_properties import SOIL_PROPERTIES
from app.tests.helpers import assert_expected_checks, assert_finite_intermediates, assert_valid_result_status, warning_codes


VALID_NPS = list(PIPE_DIMENSIONS)
VALID_SOILS = list(SOIL_PROPERTIES)
VALID_PAVEMENTS = ["Flexible", "Rigid", "None"]
VALID_AXLES = ["Single Axle", "Tandem Axle"]


@st.composite
def valid_shared(draw, defaults):
    nps = draw(st.sampled_from(VALID_NPS))
    pipe = PIPE_DIMENSIONS[nps]
    od = float(pipe["outside_diameter"])
    wall = draw(st.sampled_from([float(value) for value in pipe["wall_thickness_options"]]))
    return {
        **defaults,
        "nps": nps,
        "wall_thickness": wall,
        "cover_depth": draw(st.floats(min_value=1, max_value=30, allow_nan=False, allow_infinity=False)),
        "bored_diameter": draw(st.floats(min_value=od + 0.1, max_value=od + 24, allow_nan=False, allow_infinity=False)),
        "operating_pressure": draw(st.floats(min_value=-14.73, max_value=6000, allow_nan=False, allow_infinity=False)),
        "soil_unit_weight": draw(st.floats(min_value=50, max_value=200, allow_nan=False, allow_infinity=False)),
        "soil_type": draw(st.sampled_from(VALID_SOILS)),
    }


@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    shared=valid_shared(DEFAULT_SHARED_HIGHWAY),
    pavement=st.sampled_from(VALID_PAVEMENTS),
    axle=st.sampled_from(VALID_AXLES),
)
def test_highway_valid_inputs_are_finite_and_warning_clean(shared, pavement, axle):
    result = calculate_highway(shared, {"pavement_type": pavement, "axle_configuration": axle})
    assert_expected_checks(result)
    assert_finite_intermediates(result)
    assert_valid_result_status(result)
    assert all(check.allowable_psi > 0 for check in result.checks)
    assert not [warning for warning in result.warnings if warning.severity == "error"]


@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(shared=valid_shared(DEFAULT_SHARED_RAILROAD), surface_pressure=st.floats(min_value=1, max_value=50, allow_nan=False, allow_infinity=False), tracks=st.sampled_from([1, 2]))
def test_railroad_valid_inputs_are_finite_and_warning_clean(shared, surface_pressure, tracks):
    result = calculate_railroad(shared, {"surface_pressure": surface_pressure, "number_of_tracks": tracks})
    assert_expected_checks(result)
    assert_finite_intermediates(result)
    assert_valid_result_status(result)
    assert all(check.allowable_psi > 0 for check in result.checks)
    assert not [warning for warning in result.warnings if warning.severity == "error"]


@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    pressure=st.one_of(st.floats(min_value=-10000, max_value=-14.731, allow_nan=False, allow_infinity=False), st.floats(min_value=6000.1, max_value=10000, allow_nan=False, allow_infinity=False)),
    cover=st.one_of(st.floats(min_value=0.01, max_value=0.99, allow_nan=False, allow_infinity=False), st.floats(min_value=30.01, max_value=80, allow_nan=False, allow_infinity=False)),
    soil_weight=st.one_of(st.floats(min_value=1, max_value=49.9, allow_nan=False, allow_infinity=False), st.floats(min_value=200.1, max_value=400, allow_nan=False, allow_infinity=False)),
)
def test_highway_invalid_numeric_inputs_emit_expected_warnings(pressure, cover, soil_weight):
    result = calculate_highway({"operating_pressure": pressure, "cover_depth": cover, "soil_unit_weight": soil_weight, "bored_diameter": 12.75})
    codes = warning_codes(result)
    assert "cover_range" in codes
    assert "soil_weight_range" in codes
    assert "bored_diameter_invalid" in codes
    assert "pressure_invalid" in codes or "pressure_range" in codes


@pytest.mark.property
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(track=st.one_of(st.integers().filter(lambda value: value not in {1, 2}), st.text(min_size=1).filter(lambda value: value not in {"1", "2"})))
def test_railroad_invalid_tracks_emit_warning_and_normalize(track):
    result = calculate_railroad({}, {"number_of_tracks": track})
    assert "tracks_invalid" in warning_codes(result)
    assert result.intermediate_values["number_of_tracks"] == 2


def test_invalid_dropdown_inputs_normalize_to_current_defaults():
    highway = calculate_highway({"soil_type": "bad"}, {"pavement_type": "bad", "axle_configuration": "bad"})
    railroad = calculate_railroad({"soil_type": "bad"}, {"number_of_tracks": 2})
    assert highway.intermediate_values["soil_type"] == "Loose sands and gravels"
    assert highway.intermediate_values["pavement_type"] == "Flexible"
    assert highway.intermediate_values["axle_configuration"] == "Tandem Axle"
    assert railroad.intermediate_values["soil_type"] == "Loose sands and gravels"
