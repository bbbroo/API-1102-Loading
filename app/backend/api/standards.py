from __future__ import annotations

from fastapi import APIRouter

from app.standards.design_factors import DESIGN_FACTORS
from app.standards.dropdown_options import (
    AXLE_CONFIGURATIONS,
    CALCULATION_STATUSES,
    CALCULATION_TYPES,
    CLASS_LOCATIONS,
    PAVEMENT_TYPES,
    PIPELINE_LOCATIONS,
    PIPE_MATERIALS,
    PIPE_SPECIFICATIONS,
    PROJECT_STATUSES,
    SOIL_TYPES,
    TRACK_COUNTS,
)
from app.standards.fatigue_limits import fatigue_limits
from app.standards.highway_tables import PAVEMENT_AXLE_FACTORS
from app.standards.material_properties import MATERIAL_PROPERTIES
from app.standards.metadata import READ_ONLY_NOTICE, SOURCE_WORKBOOKS, STANDARDS_VERSION
from app.standards.pipe_dimensions import PIPE_DIMENSIONS
from app.standards.pipe_grades import PIPE_GRADES, WELD_SEAM_FACTORS
from app.standards.soil_properties import SOIL_PROPERTIES

router = APIRouter(prefix="/standards", tags=["standards"])


@router.get("")
def standards_index():
    return {
        "notice": READ_ONLY_NOTICE,
        "version": STANDARDS_VERSION,
        "source_workbooks": SOURCE_WORKBOOKS,
        "sections": ["pipe_dimensions", "pipe_grades", "soil_properties", "design_factors", "material_properties", "fatigue_limits", "dropdown_options", "highway_loading_tables", "railroad_loading_tables"],
    }


@router.get("/tables")
def tables():
    return {
        "notice": READ_ONLY_NOTICE,
        "pipe_dimensions": PIPE_DIMENSIONS,
        "pipe_grades": PIPE_GRADES,
        "weld_seam_factors": WELD_SEAM_FACTORS,
        "soil_properties": SOIL_PROPERTIES,
        "design_factors": DESIGN_FACTORS,
        "material_properties": MATERIAL_PROPERTIES,
        "fatigue_limit_examples": {"API 5L X42 ERW": fatigue_limits(42000, "Electric Resistance Welded", 12.75), "API 5L X65 ERW": fatigue_limits(65000, "Electric Resistance Welded", 12.75)},
        "dropdown_options": {
            "calculation_statuses": CALCULATION_STATUSES,
            "calculation_types": CALCULATION_TYPES,
            "project_statuses": PROJECT_STATUSES,
            "pipe_specifications": PIPE_SPECIFICATIONS,
            "pipe_materials": PIPE_MATERIALS,
            "pipeline_locations": PIPELINE_LOCATIONS,
            "class_locations": CLASS_LOCATIONS,
            "soil_types": SOIL_TYPES,
            "pavement_types": PAVEMENT_TYPES,
            "axle_configurations": AXLE_CONFIGURATIONS,
            "track_counts": TRACK_COUNTS,
        },
        "highway_loading_tables": {
            "pavement_axle_factors": {
                case: {f"{pavement_type} {axle_configuration}": values for (pavement_type, axle_configuration), values in factors.items()}
                for case, factors in PAVEMENT_AXLE_FACTORS.items()
            }
        },
    }
