from __future__ import annotations

import math
from typing import Iterable


EXPECTED_CHECK_NAMES = {
    "Barlow Stress",
    "Effective Stress",
    "Girth Weld Stress",
    "Longitudinal Weld Stress",
}
VALID_RESULT_STATUSES = {"Pass", "Fail", "Needs Review", "Not Calculated"}


def assert_finite_number(value, name: str) -> None:
    assert isinstance(value, (int, float)), f"{name} is not numeric: {value!r}"
    assert math.isfinite(float(value)), f"{name} is not finite: {value!r}"


def assert_finite_intermediates(result, keys: Iterable[str] | None = None) -> None:
    values = result.intermediate_values
    selected = keys or [key for key, value in values.items() if isinstance(value, (int, float))]
    for key in selected:
        assert key in values, f"Missing intermediate value: {key}"
        assert_finite_number(values[key], key)


def check_map(result):
    return {check.name: check for check in result.checks}


def warning_codes(result_or_warnings) -> set[str]:
    warnings = getattr(result_or_warnings, "warnings", result_or_warnings)
    return {warning.code if hasattr(warning, "code") else warning["code"] for warning in warnings}


def warning_by_code(result_or_warnings, code: str):
    warnings = getattr(result_or_warnings, "warnings", result_or_warnings)
    return [
        warning
        for warning in warnings
        if (warning.code if hasattr(warning, "code") else warning["code"]) == code
    ]


def utilization(check) -> float:
    calculated = getattr(check, "calculated_psi")
    allowable = getattr(check, "allowable_psi")
    return calculated / allowable


def assert_expected_checks(result) -> None:
    assert set(check_map(result)) == EXPECTED_CHECK_NAMES


def assert_valid_result_status(result) -> None:
    assert result.overall_result in VALID_RESULT_STATUSES


def rounded_values(result, keys: Iterable[str], digits: int = 6) -> dict[str, float]:
    values = result.intermediate_values
    return {key: round(float(values[key]), digits) for key in keys if key in values}
