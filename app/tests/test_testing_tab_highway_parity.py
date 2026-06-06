from __future__ import annotations

import pytest

from app.calculations.highway import calculate_highway
from app.tests.spreadsheet_case_loader import (
    HIGHWAY_OUTPUT_MAPPINGS,
    assert_cached_outputs_available,
    assert_outputs_match,
    load_highway_testing_cases,
    output_value,
)


HIGHWAY_TESTING_CASES = load_highway_testing_cases()
HIGHWAY_PARITY_CASES = (
    HIGHWAY_TESTING_CASES
    if any(any(output_value(case, mapping) not in (None, "") for mapping in HIGHWAY_OUTPUT_MAPPINGS) for case in HIGHWAY_TESTING_CASES)
    else [HIGHWAY_TESTING_CASES[0]]
)


@pytest.mark.workbook
@pytest.mark.parametrize("case", HIGHWAY_PARITY_CASES, ids=lambda case: case.case_id)
def test_highway_testing_tab_case_matches_spreadsheet(case):
    assert_cached_outputs_available(HIGHWAY_TESTING_CASES, HIGHWAY_OUTPUT_MAPPINGS)
    result = calculate_highway(case.shared_inputs, case.mode_inputs)
    failures = assert_outputs_match(case, result, HIGHWAY_OUTPUT_MAPPINGS)
    assert not failures, "\n\n".join(failures[:5])
