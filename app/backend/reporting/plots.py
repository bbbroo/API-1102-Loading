from __future__ import annotations

import json
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from app.backend.reporting.models import PlotArtifact

DISCLAIMER = "Generated coefficient plot based on implemented lookup data; verify against governing standard."

ROOT = Path(__file__).resolve().parents[3]
DIGITIZED_DIR = ROOT / "Refs" / "digitized_api_1102"
MANIFEST_PATH = DIGITIZED_DIR / "viewer_manifest.json"

FACTOR_ALIASES = {
    "khe": "KHe",
    "earth khe": "KHe",
    "burial": "Be",
    "burial factor": "Be",
    "excavation": "Ee",
    "excavation factor": "Ee",
    "impact": "Fi",
    "impact factor": "Fi",
    "khh": "KHh",
    "ghh": "GHh",
    "klh": "KLh",
    "glh": "GLh",
    "khr": "KHr",
    "ghr": "GHr",
    "klr": "KLr",
    "glr": "GLr",
    "nh": "NH",
    "nh factor": "NH",
    "nl": "NL",
    "nl factor": "NL",
}


def build_plot_artifacts(interpolation: list[dict[str, Any]], include: bool = True) -> list[PlotArtifact]:
    if not include:
        return []
    return [build_plot(trace) for trace in interpolation]


def build_plot(trace: dict[str, Any]) -> PlotArtifact:
    table_name = str(trace.get("table_name") or "Lookup table")
    input_value = trace.get("input_value")
    y_value = trace.get("interpolated_value")
    lower = trace.get("lower_bound")
    upper = trace.get("upper_bound")
    notes = trace.get("warning") or ("Clamped/interpolated outside source range." if trace.get("extrapolated") else "Linear interpolation from implemented lookup data.")
    figure = figure_for_trace(table_name)
    figure_label = figure_title(figure) if figure else None
    underlay_used = False
    try:
        if figure:
            image = draw_underlay_trace_plot(figure, table_name, float(input_value), float(y_value), bool(trace.get("extrapolated")))
            underlay_used = True
        else:
            image = draw_trace_plot(table_name, float(input_value), float(y_value), lower, upper, bool(trace.get("extrapolated")))
    except Exception as exc:
        image = None
        notes = f"Plot placeholder: {exc}"

    lookup_values = [
        ["Input x", fmt(input_value)],
        ["Lower bound", fmt(lower)],
        ["Upper bound", fmt(upper)],
        ["Selected coefficient", fmt(y_value)],
        ["Figure", figure_label or "No API graph underlay matched"],
        ["Interpolation note", notes],
    ]
    return PlotArtifact(
        title=f"{table_name} ({figure_label})" if figure_label else table_name,
        table_name=table_name,
        image_bytes=image,
        x_value=fmt(input_value),
        y_value=fmt(y_value),
        notes=f"{notes} {DISCLAIMER}",
        lookup_values=lookup_values,
        figure_id=str(figure.get("id")) if figure else None,
        figure_label=figure_label,
        underlay_used=underlay_used,
    )


@lru_cache(maxsize=1)
def graph_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"figures": []}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def figure_for_trace(table_name: str) -> dict[str, Any] | None:
    factor = factor_for_trace(table_name)
    if not factor:
        return None
    for figure in graph_manifest().get("figures", []):
        if str(figure.get("factor", "")).lower() == factor.lower():
            return figure
    return None


def factor_for_trace(table_name: str) -> str | None:
    normalized = table_name.lower().replace("_", " ")
    for token, factor in sorted(FACTOR_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if token in normalized:
            return factor
    return None


def figure_title(figure: dict[str, Any] | None) -> str | None:
    if not figure:
        return None
    return f"{figure.get('figure')} {figure.get('factor')}".strip()


def draw_underlay_trace_plot(figure: dict[str, Any], table_name: str, x_value: float, y_value: float, extrapolated: bool) -> bytes:
    underlay = underlay_path(figure)
    if not underlay.exists():
        raise FileNotFoundError(f"API graph underlay not found for {figure_title(figure)}")
    image = Image.open(underlay).convert("RGB")
    image = ImageEnhance.Contrast(image).enhance(0.78)
    image = ImageEnhance.Brightness(image).enhance(1.08)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    marker = graph_point_to_image(figure, x_value, y_value)
    if marker is None:
        raise ValueError(f"Selected point is outside calibrated graph range for {figure_title(figure)}")
    x_px, y_px = marker
    draw_crosshair(draw, image.size, x_px, y_px)
    draw.ellipse([x_px - 8, y_px - 8, x_px + 8, y_px + 8], fill="#1570ef", outline="#0f172a", width=3)
    label = f"x={x_value:g}, y={y_value:g}"
    badge = label_box(draw, label, font, x_px, y_px, image.size)
    draw.rounded_rectangle(badge, radius=6, fill="#ffffff", outline="#263746", width=2)
    draw.text((badge[0] + 8, badge[1] + 6), label, fill="#111827", font=font)
    caption = f"{figure_title(figure)} - {table_name[:78]}"
    draw.rectangle([0, 0, image.width, 30], fill="#263746")
    draw.text((12, 9), caption, fill="#ffffff", font=font)
    footer = "clamped/extrapolated" if extrapolated else "interpolated from implemented lookup data"
    draw.rectangle([0, image.height - 28, image.width, image.height], fill="#f8fafc", outline="#d1d5db")
    draw.text((12, image.height - 20), footer, fill="#b54708" if extrapolated else "#027a48", font=font)
    return image_bytes(image)


def underlay_path(figure: dict[str, Any]) -> Path:
    underlay_url = str(figure.get("underlay_url") or "")
    filename = underlay_url.rsplit("/", 1)[-1]
    return DIGITIZED_DIR / "graph_underlays" / filename


def graph_point_to_image(figure: dict[str, Any], x_value: float, y_value: float) -> tuple[float, float] | None:
    x_page_coord = graph_value_to_page(figure["calibrations"]["x"], x_value)
    y_page_coord = graph_value_to_page(figure["calibrations"]["y"], y_value)
    if x_page_coord is None or y_page_coord is None:
        return None
    page_x = 0.0
    page_y = 0.0
    if figure["calibrations"]["x"]["page_coordinate"] == "page_x":
        page_x = x_page_coord
    else:
        page_y = x_page_coord
    if figure["calibrations"]["y"]["page_coordinate"] == "page_y":
        page_y = y_page_coord
    else:
        page_x = y_page_coord
    clip_x0, clip_y0 = figure["clip_pdf_points"][:2]
    scale = float(figure.get("render_scale") or 1)
    return (page_x - clip_x0) * scale, (page_y - clip_y0) * scale


def graph_value_to_page(calibration: dict[str, Any], value: float) -> float | None:
    ticks = sorted(calibration.get("ticks", []), key=lambda item: float(item["value"]))
    if not ticks:
        return None
    if value < float(ticks[0]["value"]) or value > float(ticks[-1]["value"]):
        return None
    for tick in ticks:
        if abs(float(tick["value"]) - value) < 1e-10:
            return float(tick["page_coord"])
    for left, right in zip(ticks, ticks[1:]):
        left_value = float(left["value"])
        right_value = float(right["value"])
        if left_value <= value <= right_value:
            ratio = (value - left_value) / (right_value - left_value)
            return float(left["page_coord"]) + ratio * (float(right["page_coord"]) - float(left["page_coord"]))
    return None


def draw_crosshair(draw: ImageDraw.ImageDraw, size: tuple[int, int], x_px: float, y_px: float) -> None:
    width, height = size
    draw.line([(0, y_px), (width, y_px)], fill="#d92d20", width=4)
    draw.line([(x_px, 0), (x_px, height)], fill="#d92d20", width=4)


def label_box(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, x_px: float, y_px: float, size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = size
    bbox = draw.textbbox((0, 0), text, font=font)
    label_width = bbox[2] - bbox[0] + 16
    label_height = bbox[3] - bbox[1] + 12
    left = int(min(max(x_px + 14, 8), width - label_width - 8))
    top = int(min(max(y_px - label_height - 14, 38), height - label_height - 34))
    return left, top, left + label_width, top + label_height


def draw_trace_plot(table_name: str, x_value: float, y_value: float, lower: Any, upper: Any, extrapolated: bool) -> bytes:
    width, height = 640, 360
    margin = 52
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    axis = (margin, height - margin, width - 28, 46)
    draw.rectangle([0, 0, width - 1, height - 1], outline="#d1d5db")
    draw.rectangle([0, 0, width, 34], fill="#263746")
    draw.text((18, 12), table_name[:82], fill="#ffffff", font=font)
    draw.line([(axis[0], axis[1]), (axis[2], axis[1]), (axis[0], axis[1]), (axis[0], axis[3])], fill="#344054", width=2)
    lb = float(lower if lower is not None else x_value)
    ub = float(upper if upper is not None else x_value)
    x_min = min(lb, ub, x_value)
    x_max = max(lb, ub, x_value)
    if x_min == x_max:
        x_min -= 1
        x_max += 1
    y_min = min(0.0, y_value * 0.8)
    y_max = max(1.0, y_value * 1.2)
    x_px = axis[0] + (x_value - x_min) / (x_max - x_min) * (axis[2] - axis[0])
    y_px = axis[1] - (y_value - y_min) / (y_max - y_min) * (axis[1] - axis[3])
    draw.line([(axis[0], y_px), (axis[2], y_px)], fill="#d92d20", width=2)
    draw.line([(x_px, axis[1]), (x_px, axis[3])], fill="#d92d20", width=2)
    draw.ellipse([x_px - 5, y_px - 5, x_px + 5, y_px + 5], fill="#1570ef", outline="#0f172a")
    draw.text((axis[0], axis[1] + 12), f"x={x_value:g}", fill="#344054", font=font)
    draw.text((axis[0] + 112, axis[1] + 12), f"y={y_value:g}", fill="#344054", font=font)
    draw.text((axis[0] + 224, axis[1] + 12), "clamped/extrapolated" if extrapolated else "interpolated", fill="#b54708" if extrapolated else "#027a48", font=font)
    return image_bytes(image)


def image_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def fmt(value: Any) -> str:
    try:
        return f"{float(value):.4g}"
    except (TypeError, ValueError):
        return "-"
