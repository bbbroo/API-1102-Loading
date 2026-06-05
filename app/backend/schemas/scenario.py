from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScenarioBase(BaseModel):
    calculation_id: int
    scenario_name: str = "Base Case"
    description: str = ""
    shared_inputs: dict[str, Any] = Field(default_factory=dict)
    highway_inputs: dict[str, Any] = Field(default_factory=dict)
    railroad_inputs: dict[str, Any] = Field(default_factory=dict)


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioPatch(BaseModel):
    calculation_id: int | None = None
    scenario_name: str | None = None
    description: str | None = None
    shared_inputs: dict[str, Any] | None = None
    highway_inputs: dict[str, Any] | None = None
    railroad_inputs: dict[str, Any] | None = None


class ScenarioRead(ScenarioBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    results: dict[str, Any] = Field(default_factory=dict)
    intermediate_values: dict[str, Any] = Field(default_factory=dict)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None
