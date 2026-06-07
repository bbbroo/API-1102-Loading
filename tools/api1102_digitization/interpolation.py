from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


class DigitizedRangeError(ValueError):
    """Raised when interpolation is requested outside a digitized API graph range."""


@dataclass(frozen=True)
class InterpolationWarning:
    table_name: str
    input_value: float
    lower_bound: float
    upper_bound: float
    message: str


@dataclass(frozen=True)
class InterpolationResult:
    value: float | None
    warning: InterpolationWarning | None = None


def _ordered_points(table: Mapping[float, float] | Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
    items = table.items() if isinstance(table, Mapping) else table
    points = sorted((float(x), float(y)) for x, y in items)
    if len(points) < 2:
        raise ValueError("At least two digitized points are required for interpolation.")
    duplicate_x = [x for (x, _), (next_x, _) in zip(points, points[1:]) if x == next_x]
    if duplicate_x:
        raise ValueError(f"Duplicate x-values are not valid interpolation points: {duplicate_x}")
    return points


def linear_interpolate(
    table_name: str,
    table: Mapping[float, float] | Iterable[tuple[float, float]],
    x: float,
    *,
    on_out_of_range: str = "raise",
    tolerance: float = 1e-12,
) -> InterpolationResult:
    """Linearly interpolate between digitized points without silent extrapolation.

    Args:
        table_name: Human-readable table/curve name used in warnings.
        table: Mapping or iterable of ``(x, y)`` digitized points.
        x: Input x-value.
        on_out_of_range: ``"raise"`` to raise ``DigitizedRangeError`` or
            ``"warn"`` to return ``InterpolationResult(None, warning)``.
        tolerance: Numeric tolerance used for endpoint comparisons.
    """

    points = _ordered_points(table)
    x_value = float(x)
    xmin = points[0][0]
    xmax = points[-1][0]
    if x_value < xmin - tolerance or x_value > xmax + tolerance:
        warning = InterpolationWarning(
            table_name=table_name,
            input_value=x_value,
            lower_bound=xmin,
            upper_bound=xmax,
            message=f"{table_name} input {x_value} is outside digitized/API graph range {xmin} to {xmax}.",
        )
        if on_out_of_range == "warn":
            return InterpolationResult(None, warning)
        raise DigitizedRangeError(warning.message)
    if abs(x_value - xmin) <= tolerance:
        return InterpolationResult(points[0][1])
    if abs(x_value - xmax) <= tolerance:
        return InterpolationResult(points[-1][1])

    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 - tolerance <= x_value <= x1 + tolerance:
            if abs(x1 - x0) <= tolerance:
                return InterpolationResult(y0)
            fraction = (x_value - x0) / (x1 - x0)
            return InterpolationResult(y0 + fraction * (y1 - y0))

    # The earlier bounds check should make this unreachable unless floating-point
    # precision places x into a tiny gap at a segment boundary.
    warning = InterpolationWarning(
        table_name=table_name,
        input_value=x_value,
        lower_bound=xmin,
        upper_bound=xmax,
        message=f"{table_name} input {x_value} could not be bracketed by digitized points.",
    )
    if on_out_of_range == "warn":
        return InterpolationResult(None, warning)
    raise DigitizedRangeError(warning.message)

