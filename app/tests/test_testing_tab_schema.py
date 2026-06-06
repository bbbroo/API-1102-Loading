from __future__ import annotations

import pytest

from app.tests.spreadsheet_case_loader import (
    HIGHWAY_INPUT_ALIASES,
    HIGHWAY_OUTPUT_MAPPINGS,
    RAILROAD_INPUT_ALIASES,
    RAILROAD_OUTPUT_MAPPINGS,
    SHARED_INPUT_ALIASES,
    assert_cached_outputs_available,
    assert_no_spreadsheet_errors,
    assert_required_headers,
    load_highway_testing_cases,
    load_railroad_testing_cases,
)


@pytest.mark.workbook
def test_highway_testing_tab_schema_and_row_count():
    cases = load_highway_testing_cases()
    assert len(cases) == 168
    assert cases[0].workbook_path.exists()
    assert_required_headers(cases, SHARED_INPUT_ALIASES | HIGHWAY_INPUT_ALIASES, HIGHWAY_OUTPUT_MAPPINGS)
    assert_no_spreadsheet_errors(cases, HIGHWAY_OUTPUT_MAPPINGS)
    assert_cached_outputs_available(cases, HIGHWAY_OUTPUT_MAPPINGS)


@pytest.mark.workbook
def test_railroad_testing_tab_schema_and_row_count():
    cases = load_railroad_testing_cases()
    assert len(cases) == 144
    assert cases[0].workbook_path.exists()
    assert_required_headers(cases, SHARED_INPUT_ALIASES | RAILROAD_INPUT_ALIASES, RAILROAD_OUTPUT_MAPPINGS)
    assert_no_spreadsheet_errors(cases, RAILROAD_OUTPUT_MAPPINGS)
    assert_cached_outputs_available(cases, RAILROAD_OUTPUT_MAPPINGS)
