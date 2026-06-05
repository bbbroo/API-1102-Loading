from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProjectBase(BaseModel):
    project_name: str = ""
    project_number: str = ""
    client: str = ""
    location: str = ""
    description: str = ""
    status: str = "Active"


class ProjectCreate(ProjectBase):
    pass


class ProjectPatch(BaseModel):
    project_name: str | None = None
    project_number: str | None = None
    client: str | None = None
    location: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
