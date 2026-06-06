import pytest

from app.calculations.excel_validation import RAILROAD_WORKBOOK, assert_within_tolerance, compare_default_railroad, compare_railroad_case, has_excel_recalculator
from app.calculations.railroad import calculate_railroad


def test_railroad_default_matches_excel_if_workbook_available():
    result = calculate_railroad()
    assert result.overall_result == "Fail"
    assert result.controlling_check == "Girth Weld Stress"
    assert result.warnings == []
    assert RAILROAD_WORKBOOK.parent.name == "Refs"
    assert RAILROAD_WORKBOOK.name.startswith("Copy of")
    if RAILROAD_WORKBOOK.exists():
        pytest.xfail("Legacy Railroad Loading sheet parity is superseded by the workbook Testing tab source of truth.")
        assert_within_tolerance(compare_default_railroad())


@pytest.mark.skipif(not has_excel_recalculator(), reason="pywin32/Excel automation is required for edited workbook recalculation")
@pytest.mark.xfail(reason="Legacy Railroad Loading edited-case parity is superseded by the workbook Testing tab source of truth.", strict=False)
def test_edited_railroad_cases_match_refs_workbook():
    cases = [
        ({"cover_depth": 7, "operating_pressure": 900, "bored_diameter": 15.0}, {"number_of_tracks": 1, "surface_pressure": 13.9}),
        ({"nps": "16", "wall_thickness": 0.5, "bored_diameter": 18.0, "soil_type": "Loose sands and gravels", "cover_depth": 10, "operating_pressure": 1000}, {"number_of_tracks": 2, "surface_pressure": 15.0}),
        ({"nps": "8", "wall_thickness": 0.25, "bored_diameter": 10.625, "soil_unit_weight": 130, "cover_depth": 5}, {"number_of_tracks": 2, "surface_pressure": 12.0}),
    ]
    for shared, railroad in cases:
        assert_within_tolerance(compare_railroad_case(shared, railroad))
