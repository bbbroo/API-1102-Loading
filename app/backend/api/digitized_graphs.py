from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/digitized-graphs", tags=["digitized-graphs"])

ROOT = Path(__file__).resolve().parents[3]
DIGITIZED_DIR = ROOT / "Refs" / "digitized_api_1102"
MANIFEST_PATH = DIGITIZED_DIR / "viewer_manifest.json"


def numeric(value: str) -> float | str:
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def read_curve_points(filename: str) -> dict[str, list[dict[str, Any]]]:
    path = DIGITIZED_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Digitized CSV not found: {filename}")
    curves: dict[str, list[dict[str, Any]]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            curve_name = row["curve_name"]
            curves.setdefault(curve_name, []).append(
                {
                    "x_value": numeric(row["x_value"]),
                    "y_value": numeric(row["y_value"]),
                    "point_type": row["notes"].split(" | ", 1)[0].replace("point_type=", ""),
                    "notes": row["notes"],
                }
            )
    for points in curves.values():
        points.sort(key=lambda item: float(item["x_value"]))
    return curves


@router.get("")
def digitized_graphs():
    if not MANIFEST_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Digitized graph viewer manifest not found. Run tools/api1102_digitization/digitize_api1102.py.",
        )
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    figures = []
    for figure in manifest.get("figures", []):
        item = dict(figure)
        curve_points = read_curve_points(item["filename"])
        item["curves"] = [
            {
                **curve,
                "points": curve_points.get(curve["curve_name"], []),
            }
            for curve in item.get("curves", [])
        ]
        figures.append(item)
    return {
        "schema_version": manifest.get("schema_version", 1),
        "source": manifest.get("source"),
        "digitization_method": manifest.get("digitization_method"),
        "figures": figures,
    }
