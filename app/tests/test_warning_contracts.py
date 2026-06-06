from __future__ import annotations

import pytest

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.calculations.shared import enrich_shared_inputs
from app.calculations.validation import validate_shared_inputs
from app.tests.helpers import warning_by_code, warning_codes


def warning_tuple(result_or_warnings, code: str):
    warning = warning_by_code(result_or_warnings, code)[0]
    return warning.code, warning.severity, warning.message


@pytest.mark.parametrize(
    "inputs, code, severity, substring",
    [
        ({"wall_thickness": 0}, "wall_invalid", "error", "positive"),
        ({"wall_thickness": 0.251}, "wall_nonstandard", "review", "not listed"),
        ({"bored_diameter": 12.75}, "bored_diameter_invalid", "error", "exceed"),
        ({"cover_depth": 31}, "cover_range", "review", "1 to 30 ft"),
        ({"operating_pressure": -14.731}, "pressure_invalid", "error", "below 0 psia"),
        ({"operating_pressure": 6000.1}, "pressure_range", "review", "-14.73 to 6000"),
        ({"soil_unit_weight": 49.9}, "soil_weight_range", "review", "50 to 200"),
    ],
)
def test_shared_validation_warning_contracts(inputs, code, severity, substring):
    shared = enrich_shared_inputs({**inputs})
    if code == "wall_invalid":
        shared["wall_thickness"] = 0
    warnings = validate_shared_inputs(shared)
    found_code, found_severity, message = warning_tuple(warnings, code)
    assert found_code == code
    assert found_severity == severity
    assert substring in message


def test_railroad_tracks_invalid_warning_contract():
    result = calculate_railroad({}, {"number_of_tracks": "bad"})
    code, severity, message = warning_tuple(result, "tracks_invalid")
    assert code == "tracks_invalid"
    assert severity == "error"
    assert "1 or 2" in message


def test_lookup_range_warning_contract():
    result = calculate_highway({"nps": "48"})
    code, severity, message = warning_tuple(result, "lookup_range")
    assert code == "lookup_range"
    assert severity == "review"
    assert "outside table range" in message


def test_no_false_positive_warnings_for_valid_shared_inputs():
    result = calculate_highway()
    codes = warning_codes(result)
    assert "wall_invalid" not in codes
    assert "wall_nonstandard" not in codes
    assert "bored_diameter_invalid" not in codes
    assert "cover_range" not in codes
    assert "pressure_invalid" not in codes
    assert "pressure_range" not in codes
    assert "soil_weight_range" not in codes
    assert "tracks_invalid" not in warning_codes(calculate_railroad({}, {"number_of_tracks": 2}))
