from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class WarningMessage:
    code: str
    message: str
    severity: str = "warning"


@dataclass
class InterpolationTrace:
    table_name: str
    input_value: float
    lower_bound: float | None
    upper_bound: float | None
    interpolated_value: float
    extrapolated: bool = False
    warning: str | None = None


@dataclass
class StressCheck:
    name: str
    calculated_psi: float
    allowable_psi: float
    result: str = field(init=False)
    utilization: float = field(init=False)

    def __post_init__(self) -> None:
        self.utilization = self.calculated_psi / self.allowable_psi if self.allowable_psi else float("inf")
        self.result = "Pass" if self.calculated_psi <= self.allowable_psi else "Fail"


@dataclass
class CalculationResult:
    calculation_type: str
    checks: list[StressCheck]
    intermediate_values: dict[str, Any]
    warnings: list[WarningMessage]
    interpolation: list[InterpolationTrace]
    overall_result: str
    controlling_check: str | None
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize_checks(checks: list[StressCheck], warnings: list[WarningMessage]) -> tuple[str, str | None]:
    if not checks:
        return "Not Calculated", None
    controlling = max(checks, key=lambda c: c.utilization)
    if any(c.result == "Fail" for c in checks):
        failed = [c for c in checks if c.result == "Fail"]
        controlling = max(failed, key=lambda c: c.utilization)
        return "Fail", controlling.name
    if any(w.severity in {"error", "review"} for w in warnings):
        return "Needs Review", controlling.name
    return "Pass", controlling.name
