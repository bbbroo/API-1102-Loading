from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.calculations.shared import enrich_shared_inputs
from app.calculations.validation import validate_shared_inputs
from app.standards.pipe_dimensions import PIPE_DIMENSIONS
from app.standards.soil_properties import SOIL_PROPERTIES


def test_invalid_geometry_warnings():
    warnings = validate_shared_inputs({"outside_diameter": 12.75, "wall_thickness": 0, "bored_diameter": 12.0, "cover_depth": 40, "operating_pressure": -1, "soil_unit_weight": 20})
    codes = {w.code for w in warnings}
    assert "wall_invalid" in codes
    assert "bored_diameter_invalid" in codes
    assert "cover_range" in codes
    assert "pressure_invalid" in codes


def test_edited_highway_inputs_recalculate_and_normalize_invalid_options():
    result = calculate_highway(
        {"nps": "16", "wall_thickness": 0.5, "soil_type": "Not a Soil"},
        {"pavement_type": "Not Pavement", "axle_configuration": "Not Axle"},
    )
    assert result.intermediate_values["nps"] == "16"
    assert result.intermediate_values["outside_diameter"] == 16.0
    assert result.intermediate_values["soil_type"] == "Loose sands and gravels"
    assert result.intermediate_values["pavement_type"] == "Flexible"
    assert result.intermediate_values["axle_configuration"] == "Tandem Axle"
    assert result.overall_result in {"Pass", "Fail", "Needs Review"}


def test_highway_pipe_dimensions_match_workbook_range():
    assert list(PIPE_DIMENSIONS) == [
        "1/4",
        "3/8",
        "1/2",
        "3/4",
        "1",
        "1-1/4",
        "1-1/2",
        "2",
        "2-1/2",
        "3",
        "3-1/2",
        "4",
        "4-1/2",
        "5",
        "6",
        "8",
        "10",
        "12",
        "14",
        "16",
        "18",
        "20",
        "24",
        "26",
        "30",
        "36",
        "42",
        "48",
    ]
    assert PIPE_DIMENSIONS["48"]["outside_diameter"] == 48.0
    assert 1.312 in PIPE_DIMENSIONS["12"]["wall_thickness_options"]


def test_valid_edited_highway_pipe_sizes_do_not_raise_false_lookup_or_geometry_warnings():
    for nps, wall_thickness, bored_diameter in (("8", 0.188, 10.625), ("16", 0.5, 18.0)):
        result = calculate_highway({"nps": nps, "wall_thickness": wall_thickness, "bored_diameter": bored_diameter})
        codes = {warning.code for warning in result.warnings}
        assert "bored_diameter_invalid" not in codes
        assert "lookup_range" not in codes


def test_nonstandard_wall_thickness_is_preserved_and_warned():
    shared = enrich_shared_inputs({"nps": "12", "wall_thickness": 0.377})
    assert shared["wall_thickness"] == 0.377
    assert shared["tw_d"] == 0.377 / 12.75

    warnings = validate_shared_inputs(shared)
    warning = next(item for item in warnings if item.code == "wall_nonstandard")
    assert warning.severity == "review"


def test_standard_wall_thickness_does_not_warn():
    shared = enrich_shared_inputs({"nps": "12", "wall_thickness": 0.375})
    codes = {warning.code for warning in validate_shared_inputs(shared)}
    assert "wall_nonstandard" not in codes


def test_custom_wall_thickness_changes_calculated_outputs():
    standard = calculate_highway({"nps": "12", "wall_thickness": 0.375})
    custom = calculate_highway({"nps": "12", "wall_thickness": 0.377})

    assert custom.intermediate_values["wall_thickness"] == 0.377
    assert custom.intermediate_values["tw_d"] != standard.intermediate_values["tw_d"]
    assert custom.intermediate_values["SHi"] != standard.intermediate_values["SHi"]
    assert any(warning.code == "wall_nonstandard" for warning in custom.warnings)


def test_highway_soil_and_pavement_options_match_workbook():
    assert len(SOIL_PROPERTIES) == 6
    soil_result = calculate_highway({"soil_type": "Dense to very dense sands and gravels"})
    assert soil_result.intermediate_values["e_prime"] == 2000.0
    assert soil_result.intermediate_values["er"] == 20000.0

    single_axle = calculate_highway({"cover_depth": 6.0}, {"pavement_type": "Flexible", "axle_configuration": "Single Axle"})
    assert single_axle.intermediate_values["design_wheel_load"] == 12000.0
    assert single_axle.intermediate_values["L"] == 0.65

    shallow_none = calculate_highway(
        {"nps": "10", "wall_thickness": 0.25, "cover_depth": 3.0, "bored_diameter": 12.75},
        {"pavement_type": "None", "axle_configuration": "Single Axle"},
    )
    assert shallow_none.intermediate_values["pavement_factor_case"] == "shallow_small"
    assert shallow_none.intermediate_values["R"] == 1.2
    assert shallow_none.intermediate_values["L"] == 0.8


def test_edited_railroad_inputs_recalculate_and_validate_tracks():
    result = calculate_railroad({"cover_depth": 7, "operating_pressure": 900}, {"number_of_tracks": "bad", "surface_pressure": 15.0})
    assert result.intermediate_values["cover_depth"] == 7.0
    assert result.intermediate_values["operating_pressure"] == 900.0
    assert result.intermediate_values["surface_pressure"] == 15.0
    assert result.intermediate_values["number_of_tracks"] == 2
    assert any(w.code == "tracks_invalid" for w in result.warnings)
