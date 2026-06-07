from __future__ import annotations

import pytest

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad
from app.tests.helpers import rounded_values


# These are current-engine regression snapshots, not independent engineering verification.
# They exist to make accidental formula or lookup drift visible during ordinary test runs.
SNAPSHOT_KEYS = ["SHi", "SHe", "SHh", "SLh", "SHr", "SLr", "Seff", "allowable_hoop", "allowable_effective", "Khe", "Be", "Ee", "Fi"]

HIGHWAY_SNAPSHOTS = {
    "default": {"SHi": 25500.0, "SHe": 2859.010936, "SHh": 1467.490251, "SLh": 1002.399836, "Seff": 26699.114805, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.47},
    "shallow_cover": {"SHi": 25500.0, "SHe": 727.236876, "SHh": 1847.507017, "SLh": 1170.216683, "Seff": 25134.399802, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 0.271844, "Ee": 1.100937, "Fi": 1.5},
    "high_pressure": {"SHi": 76500.0, "SHe": 2859.010936, "SHh": 1467.490251, "SLh": 1002.399836, "Seff": 72620.702824, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.47},
    "rigid_single_axle": {"SHi": 25500.0, "SHe": 2859.010936, "SHh": 1030.178156, "SLh": 703.684685, "Seff": 26341.382366, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.47},
    "no_pavement_shallow_cover": {"SHi": 25500.0, "SHe": 1958.038084, "SHh": 2032.257719, "SLh": 1287.238351, "Seff": 26380.151339, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 2744.387442, "Be": 0.731923, "Ee": 1.100937, "Fi": 1.5},
    "nps24_thick_wall": {"SHi": 12793.176972, "SHe": 869.572194, "SHh": 697.796911, "SLh": 622.011742, "Seff": 13003.244847, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 674.991357, "Be": 0.800989, "Ee": 0.96501, "Fi": 1.47},
    "dense_soil": {"SHi": 25500.0, "SHe": 2204.689152, "SHh": 990.253489, "SLh": 676.542443, "Seff": 25727.641901, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 1892.854638, "Be": 0.955894, "Ee": 1.100937, "Fi": 1.47},
    "soft_soil": {"SHi": 25500.0, "SHe": 2705.71158, "SHh": 2026.376524, "SLh": 1479.884352, "Seff": 27005.027082, "allowable_hoop": 46800.0, "allowable_effective": 46800.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.47},
}

RAILROAD_SNAPSHOTS = {
    "default": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 11575.27061, "SLr": 11081.186573, "Seff": 30867.33109, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.72},
    "high_surface_pressure": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 24982.598438, "SLr": 23916.230015, "Seff": 43062.792045, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.72},
    "low_cover": {"SHi": 20400.0, "SHe": 825.891169, "SHr": 11777.164865, "SLr": 11274.463083, "Seff": 28973.259924, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 0.271844, "Ee": 1.100937, "Fi": 1.75},
    "nps24_thick_wall": {"SHi": 10234.541578, "SHe": 869.572194, "SHr": 4521.879986, "SLr": 6805.439813, "Seff": 14159.27124, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 674.991357, "Be": 0.800989, "Ee": 0.96501, "Fi": 1.72},
    "soft_soil": {"SHi": 20400.0, "SHe": 2705.71158, "SHr": 11575.27061, "SLr": 11081.186573, "Seff": 30402.870423, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.72},
    "dense_soil": {"SHi": 20400.0, "SHe": 2204.689152, "SHr": 6280.908848, "SLr": 5218.201917, "Seff": 25437.940246, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 1892.854638, "Be": 0.955894, "Ee": 1.100937, "Fi": 1.72},
    "one_track": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 10371.807313, "SLr": 10856.184703, "Seff": 29841.282908, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.72},
    "two_track": {"SHi": 20400.0, "SHe": 3246.853896, "SHr": 11575.27061, "SLr": 11081.186573, "Seff": 30867.33109, "allowable_hoop": 30240.0, "allowable_effective": 30240.0, "Khe": 3116.680998, "Be": 1.068711, "Ee": 1.100937, "Fi": 1.72},
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
