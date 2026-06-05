from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ImportPackage(BaseModel):
    app_version: str | None = None
    calculation_engine_version: str | None = None
    standards_version: str | None = None
    project: dict[str, Any]
    calculations: list[dict[str, Any]] = []
