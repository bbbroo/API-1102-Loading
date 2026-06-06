from __future__ import annotations

import time

import pytest

from app.calculations.highway import calculate_highway
from app.calculations.railroad import calculate_railroad


@pytest.mark.slow
def test_250_mixed_calculations_complete_within_generous_runtime():
    start = time.perf_counter()
    for index in range(125):
        calculate_highway({"nps": "12", "cover_depth": 1 + (index % 30), "operating_pressure": 100 + index})
        calculate_railroad({"nps": "12", "cover_depth": 1 + (index % 30), "operating_pressure": 100 + index}, {"surface_pressure": 5 + (index % 20), "number_of_tracks": 1 + (index % 2)})
    elapsed = time.perf_counter() - start
    assert elapsed < 10
