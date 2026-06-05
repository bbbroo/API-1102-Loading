from __future__ import annotations

from app.calculations.result_models import InterpolationTrace


def bounds(values: list[float], x: float) -> tuple[float | None, float | None, bool]:
    ordered = sorted(float(v) for v in values)
    lower = max((v for v in ordered if v <= x), default=None)
    upper = min((v for v in ordered if v >= x), default=None)
    extrapolated = lower is None or upper is None
    if lower is None:
        lower = ordered[0]
        upper = ordered[1] if len(ordered) > 1 else ordered[0]
    if upper is None:
        lower = ordered[-2] if len(ordered) > 1 else ordered[-1]
        upper = ordered[-1]
    return lower, upper, extrapolated


def linear(table_name: str, table: dict[float, float], x: float, warn_extrapolation: bool = True) -> tuple[float, InterpolationTrace]:
    lower, upper, extrapolated = bounds(list(table.keys()), float(x))
    y1 = float(table[lower])
    y2 = float(table[upper])
    if lower == upper:
        y = y1
    else:
        y = y1 + (float(x) - lower) * (y2 - y1) / (upper - lower)
    warning = f"{table_name} input {x} is outside table range {min(table)} to {max(table)}." if extrapolated and warn_extrapolation else None
    return y, InterpolationTrace(table_name, float(x), lower, upper, y, extrapolated, warning)


def by_nearest_key(table_name: str, table: dict[float, float], x: float) -> tuple[float, InterpolationTrace]:
    key = min(table.keys(), key=lambda k: abs(float(k) - float(x)))
    y = float(table[key])
    trace = InterpolationTrace(table_name, float(x), key, key, y, False, None)
    return y, trace


def two_step(table_name: str, nested: dict[float, dict[float, float]], outer_x: float, inner_x: float) -> tuple[float, list[InterpolationTrace]]:
    traces: list[InterpolationTrace] = []
    outer_values: dict[float, float] = {}
    for outer_key, inner_table in nested.items():
        y, trace = linear(f"{table_name} @ {outer_key}", inner_table, inner_x)
        traces.append(trace)
        outer_values[outer_key] = y
    y, trace = linear(table_name, outer_values, outer_x)
    traces.append(trace)
    return y, traces
