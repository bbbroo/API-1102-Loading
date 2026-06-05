from __future__ import annotations

import csv
import io
from typing import Any


def render_csv(package: dict[str, Any]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Section", "Name", "Value", "Unit", "Result"])
    writer.writerow(["Package", "app_version", package.get("app_version", ""), "", ""])
    writer.writerow(["Package", "calculation_engine_version", package.get("calculation_engine_version", ""), "", ""])
    writer.writerow(["Package", "standards_version", package.get("standards_version", ""), "", ""])
    writer.writerow(["Package", "schema_version", package.get("schema_version", ""), "", ""])
    writer.writerow(["Package", "export_scope", package.get("export_scope", "project"), "", ""])
    writer.writerow(["Package", "export_timestamp", package.get("export_timestamp", ""), "", ""])
    project = package["project"]
    for key, value in project.items():
        writer.writerow(["Project", key, value, "", ""])
    for calc in package.get("calculations", []):
        for key, value in calc.items():
            if key != "scenarios":
                writer.writerow(["Calculation", key, value, "", ""])
        for scenario in calc.get("scenarios", []):
            writer.writerow(["Scenario", "scenario_name", scenario.get("scenario_name"), "", ""])
            writer.writerow(["Scenario", "description", scenario.get("description", ""), "", ""])
            for section, values in [
                ("Shared Inputs", scenario.get("shared_inputs", {})),
                ("Highway Inputs", scenario.get("highway_inputs", {})),
                ("Railroad Inputs", scenario.get("railroad_inputs", {})),
                ("Intermediate", scenario.get("intermediate_values", {})),
            ]:
                for key, value in flatten(values).items():
                    writer.writerow([section, key, value, "", ""])
            results = scenario.get("results", {})
            writer.writerow(["Results", "overall_result", results.get("overall_result", ""), "", ""])
            writer.writerow(["Results", "controlling_check", results.get("controlling_check", ""), "", ""])
            for check in results.get("checks", []):
                writer.writerow(["Stress Check", check["name"], check["calculated_psi"], "psi", check["result"]])
                writer.writerow(["Stress Check Allowable", check["name"], check["allowable_psi"], "psi", check["utilization"]])
            for warning in scenario.get("warnings", []):
                writer.writerow(["Warning", warning.get("code"), warning.get("message"), "", warning.get("severity")])
    return output.getvalue().encode("utf-8")


def flatten(values: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in values.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(flatten(value, name))
        elif isinstance(value, list):
            out[name] = "; ".join(str(item) for item in value)
        else:
            out[name] = value
    return out
