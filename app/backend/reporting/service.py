from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.backend.database.models import Calculation, Project, Scenario
from app.backend.reporting.models import DetailedReportData, EquationTrace, ReportIssue, ReportOptions
from app.backend.reporting.plots import build_plot_artifacts
from app.backend.services.calculation_service import scenario_input_fingerprint
from app.backend.services.helpers import loads


class DetailedReportBlocked(ValueError):
    def __init__(self, issues: list[ReportIssue]):
        super().__init__("Detailed report generation is blocked")
        self.issues = issues


def build_detailed_report_data(
    db: Session,
    scenario_id: int,
    project_id: int,
    calculation_id: int,
    options: ReportOptions,
) -> DetailedReportData:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise LookupError("Scenario not found")
    calculation = scenario.calculation
    project = calculation.project if calculation else None
    if calculation is None or project is None:
        raise LookupError("Scenario is not linked to a calculation and project")
    if calculation.id != calculation_id or project.id != project_id:
        raise PermissionError("Report IDs do not match the selected scenario")

    results = loads(scenario.results_json, {})
    shared = loads(scenario.shared_inputs_json, {})
    highway = loads(scenario.highway_inputs_json, {})
    railroad = loads(scenario.railroad_inputs_json, {})
    warnings = loads(scenario.warnings_json, [])
    intermediate = loads(scenario.intermediate_values_json, {})
    issues = report_blocking_issues(calculation, results, shared, highway, railroad, warnings)
    if issues:
        raise DetailedReportBlocked(issues)

    critical, informational = split_warnings(warnings)
    return DetailedReportData(
        project=project,
        calculation=calculation,
        scenario=scenario,
        options=options,
        generated_at=datetime.now(timezone.utc).isoformat(),
        results=results,
        intermediate_values=intermediate,
        warnings=warnings,
        critical_warnings=critical,
        informational_warnings=informational,
        equations=build_equation_traces(calculation.calculation_type, results, first_intermediate(intermediate)),
        plots=build_plot_artifacts(results.get("interpolation", []), include=options.include_plots),
    )


def report_blocking_issues(
    calculation: Calculation,
    results: dict[str, Any],
    shared: dict[str, Any],
    highway: dict[str, Any],
    railroad: dict[str, Any],
    warnings: list[dict[str, Any]],
) -> list[ReportIssue]:
    issues: list[ReportIssue] = []
    if not results.get("checks"):
        issues.append(ReportIssue("not_calculated", "Scenario has not been calculated.", "results"))
    if not results.get("calculated_at"):
        issues.append(ReportIssue("not_calculated", "Scenario result timestamp is missing.", "results"))
    if not results.get("input_fingerprint"):
        issues.append(ReportIssue("stale_result", "Scenario result was created before detailed report freshness metadata existed. Recalculate Scenario.", "results"))
    else:
        expected = scenario_input_fingerprint(calculation.calculation_type, shared, highway, railroad)
        if results.get("input_fingerprint") != expected:
            issues.append(ReportIssue("inputs_changed", "Scenario inputs changed after the last trusted result. Recalculate Scenario.", "inputs"))

    error_warnings = [warning for warning in warnings if warning.get("severity") == "error"]
    for warning in error_warnings:
        issues.append(ReportIssue("required_inputs_missing", warning.get("message", "Required inputs are missing or invalid."), warning.get("code") or "inputs"))
    return issues


def split_warnings(warnings: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    critical = [warning for warning in warnings if warning.get("severity") in {"error", "review"}]
    informational = [warning for warning in warnings if warning not in critical]
    return critical, informational


def first_intermediate(intermediate: dict[str, Any]) -> dict[str, Any]:
    return intermediate.get("highway") or intermediate.get("railroad") or intermediate


def build_equation_traces(calculation_type: str, results: dict[str, Any], values: dict[str, Any]) -> list[EquationTrace]:
    checks = results.get("checks") or []
    traces: list[EquationTrace] = [
        EquationTrace(
            "GEN-EQ-001",
            "Internal Pressure",
            "Barlow hoop stress",
            "S_Hi = P D / (2 t)",
            f"P={fmt(values.get('operating_pressure'))} psig, D={fmt(values.get('outside_diameter'), 2)} in, t={fmt(values.get('wall_thickness'), 3)} in",
            f"S_Hi={fmt(values.get('SHi'))} psi",
            f"Allowable={fmt(values.get('allowable_hoop'))} psi",
            utilization_for(checks, "Barlow Stress"),
            status_for(checks, "Barlow Stress"),
        ),
        EquationTrace(
            "GEN-EQ-002",
            "Combined Stresses",
            "Effective stress check",
            "S_eff = f(S1, S2, S3)",
            f"S1={fmt(values.get('S1'))} psi, S2={fmt(values.get('S2'))} psi, S3={fmt(values.get('S3'))} psi",
            f"S_eff={fmt(values.get('Seff'))} psi",
            f"Allowable={fmt(values.get('allowable_effective'))} psi",
            utilization_for(checks, "Effective Stress"),
            status_for(checks, "Effective Stress"),
        ),
    ]
    prefix = "RR" if calculation_type == "Railroad" else "HWY"
    mode_name = "railroad" if calculation_type == "Railroad" else "highway"
    traces.extend(
        [
            EquationTrace(
                f"{prefix}-EQ-001",
                f"{calculation_type} Loading",
                f"{calculation_type} circumferential live-load stress",
                f"S_H{mode_name[0]} = coefficient product x load",
                mode_substitution(calculation_type, values, "H"),
                f"S_H={fmt(values.get('SHr') if calculation_type == 'Railroad' else values.get('SHh'))} psi",
                "See combined and fatigue checks",
                "-",
                "Trace",
            ),
            EquationTrace(
                f"{prefix}-EQ-002",
                f"{calculation_type} Loading",
                f"{calculation_type} longitudinal live-load stress",
                f"S_L{mode_name[0]} = coefficient product x load",
                mode_substitution(calculation_type, values, "L"),
                f"S_L={fmt(values.get('SLr') if calculation_type == 'Railroad' else values.get('SLh'))} psi",
                "See fatigue checks",
                "-",
                "Trace",
            ),
            EquationTrace(
                f"{prefix}-EQ-003",
                "Fatigue / Welds",
                "Girth and longitudinal weld checks",
                "S_F <= allowable fatigue stress",
                weld_substitution(values, checks),
                weld_result(values, checks),
                weld_allowable(values, checks),
                f"{utilization_for(checks, 'Girth Weld Stress')} / {utilization_for(checks, 'Longitudinal Weld Stress')}",
                worst_status([status_for(checks, "Girth Weld Stress"), status_for(checks, "Longitudinal Weld Stress")]),
            ),
        ]
    )
    return traces


def weld_substitution(values: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    sfg = value_or_check(values, checks, "SFG", "Girth Weld Stress", "calculated_psi")
    sfl = value_or_check(values, checks, "SFL", "Longitudinal Weld Stress", "calculated_psi")
    if sfg is None and sfl is None:
        return "SFG/SFL: calculated weld stresses reported in Results Summary."
    return f"SFG={fmt_or_dash(sfg)} psi, SFL={fmt_or_dash(sfl)} psi"


def weld_result(values: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    sfg = value_or_check(values, checks, "SFG", "Girth Weld Stress", "calculated_psi")
    sfl = value_or_check(values, checks, "SFL", "Longitudinal Weld Stress", "calculated_psi")
    if sfg is None and sfl is None:
        return "Calculated weld stresses reported in Results Summary."
    return f"SFG={fmt_or_dash(sfg)} psi; SFL={fmt_or_dash(sfl)} psi"


def weld_allowable(values: dict[str, Any], checks: list[dict[str, Any]]) -> str:
    girth = value_or_check(values, checks, "allowable_girth", "Girth Weld Stress", "allowable_psi")
    longitudinal = value_or_check(values, checks, "allowable_longitudinal", "Longitudinal Weld Stress", "allowable_psi")
    return f"{fmt_or_dash(girth)} / {fmt_or_dash(longitudinal)} psi"


def value_or_check(values: dict[str, Any], checks: list[dict[str, Any]], key: str, check_name: str, check_key: str) -> Any:
    if values.get(key) is not None:
        return values.get(key)
    check = next((item for item in checks if item.get("name") == check_name), None)
    return check.get(check_key) if check else None


def fmt_or_dash(value: Any, digits: int = 1) -> str:
    return "—" if value is None else fmt(value, digits)


def mode_substitution(calculation_type: str, values: dict[str, Any], direction: str) -> str:
    if calculation_type == "Railroad":
        keys = ["Nh", "KHr", "GHr", "Fi", "surface_pressure"] if direction == "H" else ["KLr", "GLr", "NL", "Fi", "surface_pressure"]
        unit = "psi"
    else:
        keys = ["KHh", "GHh", "R", "L", "Fi", "design_wheel_load"] if direction == "H" else ["KLh", "GLh", "R", "L", "Fi", "design_wheel_load"]
        unit = "lb"
    parts = []
    for key in keys:
        suffix = f" {unit}" if key in {"surface_pressure", "design_wheel_load"} else ""
        parts.append(f"{key}={fmt(values.get(key), 3)}{suffix}")
    return ", ".join(parts)


def utilization_for(checks: list[dict[str, Any]], name: str) -> str:
    check = next((item for item in checks if item.get("name") == name), None)
    return f"{float(check.get('utilization', 0)) * 100:.1f}%" if check else "-"


def status_for(checks: list[dict[str, Any]], name: str) -> str:
    check = next((item for item in checks if item.get("name") == name), None)
    return check.get("result", "-") if check else "-"


def worst_status(statuses: list[str]) -> str:
    order = {"Fail": 3, "Needs Review": 2, "Pass": 1, "Trace": 0, "-": 0}
    return max(statuses, key=lambda status: order.get(status, 0))


def fmt(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "-"
