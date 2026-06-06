from __future__ import annotations

import pytest

from app.calculations.railroad import calculate_railroad
from app.tests.spreadsheet_case_loader import (
    RAILROAD_OUTPUT_MAPPINGS,
    assert_cached_outputs_available,
    assert_outputs_match,
    load_railroad_testing_cases,
    output_value,
)


RAILROAD_TESTING_CASES = load_railroad_testing_cases()
RAILROAD_PARITY_CASES = (
    RAILROAD_TESTING_CASES
    if any(any(output_value(case, mapping) not in (None, "") for mapping in RAILROAD_OUTPUT_MAPPINGS) for case in RAILROAD_TESTING_CASES)
    else [RAILROAD_TESTING_CASES[0]]
)


@pytest.mark.workbook
@pytest.mark.parametrize("case", RAILROAD_PARITY_CASES, ids=lambda case: case.case_id)
def test_railroad_testing_tab_case_matches_spreadsheet(case):
    assert_cached_outputs_available(RAILROAD_TESTING_CASES, RAILROAD_OUTPUT_MAPPINGS)
    result = calculate_railroad(case.shared_inputs, case.mode_inputs)
    failures = assert_outputs_match(case, result, RAILROAD_OUTPUT_MAPPINGS)
    assert not failures, "\n\n".join(failures[:5])
