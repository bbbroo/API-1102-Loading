import pytest

from app.calculations.excel_validation import HIGHWAY_WORKBOOK, assert_within_tolerance, compare_default_highway, compare_highway_case, has_excel_recalculator
from app.calculations.highway import calculate_highway


def test_highway_default_matches_excel_if_workbook_available():
    result = calculate_highway()
    assert result.overall_result == "Pass"
    assert result.controlling_check == "Effective Stress"
    assert HIGHWAY_WORKBOOK.parent.name == "Refs"
    assert HIGHWAY_WORKBOOK.name.startswith("Copy of")
    if HIGHWAY_WORKBOOK.exists():
        assert_within_tolerance(compare_default_highway())


@pytest.mark.skipif(not has_excel_recalculator(), reason="pywin32/Excel automation is required for edited workbook recalculation")
def test_edited_highway_cases_match_refs_workbook():
    cases = [
        ({"nps": "8", "wall_thickness": 0.188, "bored_diameter": 10.625, "cover_depth": 5, "operating_pressure": 900}, {"pavement_type": "Flexible", "axle_configuration": "Single Axle"}),
        ({"nps": "16", "wall_thickness": 0.5, "bored_diameter": 18.0, "soil_type": "Dense to very dense sands and gravels", "cover_depth": 8, "operating_pressure": 1200}, {"pavement_type": "None", "axle_configuration": "Tandem Axle"}),
        ({"nps": "12", "wall_thickness": 0.5, "bored_diameter": 15.0, "cover_depth": 10, "soil_unit_weight": 130}, {"pavement_type": "Rigid", "axle_configuration": "Single Axle"}),
    ]
    for shared, highway in cases:
        assert_within_tolerance(compare_highway_case(shared, highway))
