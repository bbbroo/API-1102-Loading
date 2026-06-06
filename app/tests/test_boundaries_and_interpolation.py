from __future__ import annotations

import pytest

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY
from app.standards.pipe_dimensions import PIPE_DIMENSIONS
from app.tests.helpers import assert_expected_checks, assert_finite_intermediates, warning_codes


HIGHWAY_COVER_POINTS = [1.00, 3.00, 4.00, 5.99, 6.00, 6.01, 7.99, 8.00, 8.01, 9.99, 10.00, 10.01, 30.00]
RAILROAD_COVER_POINTS = [1.00, 3.00, 5.99, 6.00, 6.01, 7.99, 8.00, 8.01, 9.99, 10.00, 10.01, 13.99, 14.00, 14.01, 30.00]


@pytest.mark.parametrize("cover", HIGHWAY_COVER_POINTS)
def test_highway_cover_transition_points_are_finite_and_deterministic(cover):
    result = calculate_highway({"cover_depth": cover})
    repeated = calculate_highway({"cover_depth": cover})
    assert_expected_checks(result)
    assert_finite_intermediates(result)
    assert warning_codes(result) == warning_codes(repeated)


@pytest.mark.parametrize("cover", RAILROAD_COVER_POINTS)
def test_railroad_cover_transition_points_are_finite_and_deterministic(cover):
    result = calculate_railroad({"cover_depth": cover})
    repeated = calculate_railroad({"cover_depth": cover})
    assert_expected_checks(result)
    assert_finite_intermediates(result)
    assert warning_codes(result) == warning_codes(repeated)


@pytest.mark.parametrize("delta, expects_warning", [(0, True), (-0.01, True), (0.01, False), (24, False), (240, False)])
def test_bored_diameter_boundary_behavior(delta, expects_warning):
    od = PIPE_DIMENSIONS["12"]["outside_diameter"]
    result = calculate_highway({"bored_diameter": od + delta})
    assert_expected_checks(result)
    assert_finite_intermediates(result)
    assert ("bored_diameter_invalid" in warning_codes(result)) is expects_warning


@pytest.mark.parametrize("wall", [0.001, 0, 10])
def test_wall_thickness_extreme_current_behavior_contract(wall):
    result = calculate_highway({"wall_thickness": wall})
    assert_expected_checks(result)
    assert_finite_intermediates(result)
    # TODO: calculation entrypoints currently normalize zero wall thickness before validation,
    # and allow very small or larger-than-radius custom wall values with at most nonstandard review.
    if wall > 0 and wall not in DEFAULT_SHARED_HIGHWAY.values():
        assert "wall_nonstandard" in warning_codes(result)


def test_wall_thickness_zero_is_currently_normalized_before_warning_contract():
    result = calculate_highway({"nps": "12", "wall_thickness": 0})
    assert result.intermediate_values["wall_thickness"] == PIPE_DIMENSIONS["12"]["wall_thickness_options"][0]
    assert "wall_invalid" not in warning_codes(result)
