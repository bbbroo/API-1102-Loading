from __future__ import annotations

import pytest

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.tests.helpers import rounded_values


# These are current-engine regression snapshots, not independent engineering verification.
# They exist to make accidental formula or lookup drift visible during ordinary test runs.
SNAPSHOT_KEYS = ["SHi", "SHe", "SHh", "SLh", "SHr", "SLr", "Seff", "allowable_hoop", "allowable_effective", "Khe", "Be", "Ee", "Fi"]

HIGHWAY_SNAPSHOTS = {
    "default": {"SHi": 25500.0, "SHe": 2859.010936, "SHh": 1476.289403, "SLh": 1008.41028, "Seff": 26706.321139, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.478814},
    "shallow_cover": {"SHi": 25500.0, "SHe": 727.236876, "SHh": 1848.114123, "SLh": 1170.601225, "Seff": 25134.903282, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 0.271844, "Ee": 1.100937, "Fi": 1.500493},
    "high_pressure": {"SHi": 76500.0, "SHe": 2859.010936, "SHh": 1476.289403, "SLh": 1008.41028, "Seff": 72627.878079, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.478814},
    "rigid_single_axle": {"SHi": 25500.0, "SHe": 2859.010936, "SHh": 1036.355161, "SLh": 707.904017, "Seff": 26346.429534, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.478814},
    "no_pavement_shallow_cover": {"SHi": 25500.0, "SHe": 1958.038084, "SHh": 2034.261167, "SLh": 1288.507341, "Seff": 26381.812749, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 0.731923, "Ee": 1.100937, "Fi": 1.501479},
    "nps24_thick_wall": {"SHi": 12793.176972, "SHe": 869.572194, "SHh": 701.980939, "SLh": 625.741358, "Seff": 13006.597085, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 674.991357, "Be": 0.800989, "Ee": 0.96501, "Fi": 1.478814},
    "dense_soil": {"SHi": 25500.0, "SHe": 2204.689152, "SHh": 996.191103, "SLh": 680.599028, "Seff": 25732.494112, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 1892.854638, "Be": 0.955894, "Ee": 1.100937, "Fi": 1.478814},
    "soft_soil": {"SHi": 25500.0, "SHe": 2705.71158, "SHh": 2038.526788, "SLh": 1488.757819, "Seff": 27014.923821, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.478814},
}

RAILROAD_SNAPSHOTS = {
    "default": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 11618.32183, "SLr": 11122.400176, "Seff": 30905.264695, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.726397},
    "high_surface_pressure": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 25075.514741, "SLr": 24005.180237, "Seff": 43149.224806, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.726397},
    "low_cover": {"SHi": 20400.0, "SHe": 825.891169, "SHr": 11777.198514, "SLr": 11274.495296, "Seff": 28973.28988, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 0.271844, "Ee": 1.100937, "Fi": 1.750005},
    "nps24_thick_wall": {"SHi": 10234.541578, "SHe": 869.572194, "SHr": 4538.697948, "SLr": 6830.750883, "Seff": 14176.901025, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 674.991357, "Be": 0.800989, "Ee": 0.96501, "Fi": 1.726397},
    "soft_soil": {"SHi": 20400.0, "SHe": 2705.71158, "SHr": 11618.32183, "SLr": 11122.400176, "Seff": 30440.878823, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.726397},
    "dense_soil": {"SHi": 20400.0, "SHe": 2204.689152, "SHr": 6304.269062, "SLr": 5237.609668, "Seff": 25457.515747, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 1892.854638, "Be": 0.955894, "Ee": 1.100937, "Fi": 1.726397},
    "one_track": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 11618.32183, "SLr": 11122.400176, "Seff": 30905.264695, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.726397},
    "two_track": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 11618.32183, "SLr": 11122.400176, "Seff": 30905.264695, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.726397},
}


HIGHWAY_CASES = {
    "default": ({}, {}),
    "shallow_cover": ({"cover_depth": 1, "bored_diameter": 14.75}, {}),
    "high_pressure": ({"operating_pressure": 3000}, {}),
    "rigid_single_axle": ({}, {"pavement_type": "Rigid", "axle_configuration": "Single Axle"}),
    "no_pavement_shallow_cover": ({"cover_depth": 3}, {"pavement_type": "None", "axle_configuration": "Tandem Axle"}),
    "nps24_thick_wall": ({"nps": "24", "wall_thickness": 0.938, "bored_diameter": 26.0}, {}),
    "dense_soil": ({"soil_type": "Dense to very dense sands and gravels", "soil_unit_weight": 150}, {}),
    "soft_soil": ({"soil_type": "Soft to medium clays and silts with high plasticities", "soil_unit_weight": 100}, {}),
}

RAILROAD_CASES = {
    "default": ({}, {}),
    "high_surface_pressure": ({}, {"surface_pressure": 30}),
    "low_cover": ({"cover_depth": 1}, {}),
    "nps24_thick_wall": ({"nps": "24", "wall_thickness": 0.938, "bored_diameter": 26.0}, {}),
    "soft_soil": ({"soil_type": "Soft to medium clays and silts with high plasticities", "soil_unit_weight": 100}, {}),
    "dense_soil": ({"soil_type": "Dense to very dense sands and gravels", "soil_unit_weight": 150}, {}),
    "one_track": ({}, {"number_of_tracks": 1}),
    "two_track": ({}, {"number_of_tracks": 2}),
}


@pytest.mark.snapshot
@pytest.mark.parametrize("name", HIGHWAY_CASES)
def test_highway_numeric_regression_snapshots(name):
    shared, highway = HIGHWAY_CASES[name]
    actual = rounded_values(calculate_highway(shared, highway), SNAPSHOT_KEYS)
    assert actual == pytest.approx(HIGHWAY_SNAPSHOTS[name], abs=1e-6, rel=1e-9)


@pytest.mark.snapshot
@pytest.mark.parametrize("name", RAILROAD_CASES)
def test_railroad_numeric_regression_snapshots(name):
    shared, railroad = RAILROAD_CASES[name]
    actual = rounded_values(calculate_railroad(shared, railroad), SNAPSHOT_KEYS)
    assert actual == pytest.approx(RAILROAD_SNAPSHOTS[name], abs=1e-6, rel=1e-9)
