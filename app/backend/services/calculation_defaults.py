from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.calculations.highway import DEFAULT_HIGHWAY_INPUTS
from app.calculations.railroad import DEFAULT_RAILROAD_INPUTS
from app.calculations.shared import DEFAULT_SHARED_HIGHWAY, DEFAULT_SHARED_RAILROAD


def mode_defaults(calculation_type: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if calculation_type == "Railroad":
        return deepcopy(DEFAULT_SHARED_RAILROAD), {}, deepcopy(DEFAULT_RAILROAD_INPUTS)
    return deepcopy(DEFAULT_SHARED_HIGHWAY), deepcopy(DEFAULT_HIGHWAY_INPUTS), {}


def merged_mode_inputs(
    calculation_type: str,
    shared_inputs: dict[str, Any] | None = None,
    highway_inputs: dict[str, Any] | None = None,
    railroad_inputs: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    shared_defaults, highway_defaults, railroad_defaults = mode_defaults(calculation_type)
    return (
        {**shared_defaults, **(shared_inputs or {})},
        {**highway_defaults, **(highway_inputs or {})},
        {**railroad_defaults, **(railroad_inputs or {})},
    )
