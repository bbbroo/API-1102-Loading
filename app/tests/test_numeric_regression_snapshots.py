from __future__ import annotations

import pytest

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.tests.helpers import rounded_values


# These are current-engine regression snapshots, not independent engineering verification.
# They exist to make accidental formula or lookup drift visible during ordinary test runs.
SNAPSHOT_KEYS = ["SHi", "SHe", "SHh", "SLh", "SHr", "SLr", "Seff", "allowable_hoop", "allowable_effective", "Khe", "Be", "Ee", "Fi"]

HIGHWAY_SNAPSHOTS = {
    "default": {"SHi": 25500.0, "SHe": 2907.641411, "SHh": 1480.924005, "SLh": 1005.647653, "Seff": 26754.361091, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2790.529412, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.47622},
    "shallow_cover": {"SHi": 25500.0, "SHe": 712.426475, "SHh": 1855.353013, "SLh": 1176.653777, "Seff": 25127.503485, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2790.529412, "Be": 0.261153, "Ee": 1.104108, "Fi": 1.5},
    "high_pressure": {"SHi": 76500.0, "SHe": 2907.641411, "SHh": 1480.924005, "SLh": 1005.647653, "Seff": 72675.980263, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2790.529412, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.47622},
    "rigid_single_axle": {"SHi": 25500.0, "SHe": 2907.641411, "SHh": 1039.608651, "SLh": 705.964652, "Seff": 26393.047705, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2790.529412, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.47622},
    "no_pavement_shallow_cover": {"SHi": 25500.0, "SHe": 1997.272456, "SHh": 2040.888314, "SLh": 1294.319155, "Seff": 26421.852934, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2790.529412, "Be": 0.732136, "Ee": 1.104108, "Fi": 1.5},
    "nps24_thick_wall": {"SHi": 12793.176972, "SHe": 867.608399, "SHh": 699.207773, "SLh": 621.996419, "Seff": 13002.817823, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 674.45, "Be": 0.797846, "Ee": 0.9674, "Fi": 1.47622},
    "dense_soil": {"SHi": 25500.0, "SHe": 2216.265532, "SHh": 988.711684, "SLh": 676.647767, "Seff": 25736.448318, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 1897.960784, "Be": 0.955576, "Ee": 1.104108, "Fi": 1.47622},
    "soft_soil": {"SHi": 25500.0, "SHe": 2727.50359, "SHh": 2040.398257, "SLh": 1483.325703, "Seff": 27036.937527, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 3141.176471, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.47622},
}

RAILROAD_SNAPSHOTS = {
    "default": {"SHi": 20400.0, "SHe": 3273.004308, "SHr": 11885.98005, "SLr": 11066.189118, "Seff": 31153.505099, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3141.176471, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.726392},
    "high_surface_pressure": {"SHi": 20400.0, "SHe": 3273.004308, "SHr": 25653.194354, "SLr": 23883.861406, "Seff": 43598.134752, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3141.176471, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.726392},
    "low_cover": {"SHi": 20400.0, "SHe": 801.947211, "SHr": 12048.516243, "SLr": 11217.514986, "Seff": 29177.360694, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3141.176471, "Be": 0.261153, "Ee": 1.104108, "Fi": 1.75},
    "nps24_thick_wall": {"SHi": 10234.541578, "SHe": 867.608399, "SHr": 4799.70594, "SLr": 6623.019786, "Seff": 14334.464129, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 674.45, "Be": 0.797846, "Ee": 0.9674, "Fi": 1.726392},
    "soft_soil": {"SHi": 20400.0, "SHe": 2727.50359, "SHr": 11885.98005, "SLr": 11066.189118, "Seff": 30684.556568, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3141.176471, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.726392},
    "dense_soil": {"SHi": 20400.0, "SHe": 2216.265532, "SHr": 6414.307253, "SLr": 5170.505837, "Seff": 25572.347342, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 1897.960784, "Be": 0.955576, "Ee": 1.104108, "Fi": 1.726392},
    "one_track": {"SHi": 20400.0, "SHe": 3273.004308, "SHr": 11885.98005, "SLr": 11066.189118, "Seff": 31153.505099, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3141.176471, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.726392},
    "two_track": {"SHi": 20400.0, "SHe": 3273.004308, "SHr": 11885.98005, "SLr": 11066.189118, "Seff": 31153.505099, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3141.176471, "Be": 1.065847, "Ee": 1.104108, "Fi": 1.726392},
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
