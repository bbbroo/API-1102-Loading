from __future__ import annotations

from datetime import date as dt_date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


VALID_CALCULATION_TYPES = {"Highway", "Railroad"}


def validate_calculation_type(value: str | None) -> str | None:
    if value is None:
        return value
    if value not in VALID_CALCULATION_TYPES:
        raise ValueError("calculation_type must be Highway or Railroad")
    return value


class CalculationBase(BaseModel):
    project_id: int
    calc_number: str = ""
    crossing_name: str = ""
    calculation_type: str = "Highway"
    road_highway: str = ""
    railroad_route: str = ""
    prepared_by: str = ""
    checked_by: str = ""
    reviewer: str = ""
    date: dt_date | None = None
    revision: str = "0"
    status: str = "Draft"
    review_comments: str = ""
    notes: str = ""


class CalculationCreate(CalculationBase):
    @field_validator("calculation_type")
    @classmethod
    def calculation_type_is_supported(cls, value: str) -> str:
        return validate_calculation_type(value) or "Highway"


class CalculationPatch(BaseModel):
    project_id: int | None = None
    calc_number: str | None = None
    crossing_name: str | None = None
    calculation_type: str | None = None
    road_highway: str | None = None
    railroad_route: str | None = None
    prepared_by: str | None = None
    checked_by: str | None = None
    reviewer: str | None = None
    date: dt_date | None = None
    revision: str | None = None
    status: str | None = None
    review_comments: str | None = None
    notes: str | None = None

    @field_validator("calculation_type")
    @classmethod
    def calculation_type_is_supported(cls, value: str | None) -> str | None:
        return validate_calculation_type(value)


class CalculationRead(CalculationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    overall_result: str = "Not Calculated"
    controlling_check: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
