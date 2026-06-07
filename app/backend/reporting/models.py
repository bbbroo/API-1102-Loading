from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReportOptions:
    include_formula_trace: bool = True
    include_intermediates: bool = True
    include_plots: bool = True
    include_appendix_plots: bool = True
    include_warnings: bool = True

    @classmethod
    def from_payload(cls, payload: dict[str, Any] | None) -> "ReportOptions":
        data = payload or {}
        return cls(
            include_formula_trace=bool(data.get("include_formula_trace", True)),
            include_intermediates=bool(data.get("include_intermediates", True)),
            include_plots=bool(data.get("include_plots", True)),
            include_appendix_plots=bool(data.get("include_appendix_plots", True)),
            include_warnings=bool(data.get("include_warnings", True)),
        )


@dataclass
class ReportIssue:
    code: str
    message: str
    input_anchor: str | None = None


@dataclass
class EquationTrace:
    equation_id: str
    section: str
    title: str
    equation: str
    substitution: str
    result: str
    allowable: str
    utilization: str
    status: str


@dataclass
class PlotArtifact:
    title: str
    table_name: str
    image_bytes: bytes | None
    x_value: str
    y_value: str
    notes: str
    lookup_values: list[list[str]] = field(default_factory=list)
    figure_id: str | None = None
    figure_label: str | None = None
    underlay_used: bool = False


@dataclass
class DetailedReportData:
    project: Any
    calculation: Any
    scenario: Any
    options: ReportOptions
    generated_at: str
    results: dict[str, Any]
    intermediate_values: dict[str, Any]
    warnings: list[dict[str, Any]]
    critical_warnings: list[dict[str, Any]]
    informational_warnings: list[dict[str, Any]]
    equations: list[EquationTrace]
    plots: list[PlotArtifact]
