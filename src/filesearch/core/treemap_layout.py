"""Pure treemap layout helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(slots=True)
class TreemapRect:
    """Represents a laid-out treemap rectangle."""

    item: Any
    x: float
    y: float
    width: float
    height: float


def layout_treemap(
    items: Sequence[tuple[Any, float]],
    x: float,
    y: float,
    width: float,
    height: float,
) -> list[TreemapRect]:
    """Lay out *items* using a squarified treemap algorithm."""
    if width <= 0 or height <= 0:
        return []

    prepared = [
        (item, float(weight))
        for item, weight in items
        if weight is not None and float(weight) > 0.0
    ]
    if not prepared:
        return []

    ordered = [
        pair[1]
        for pair in sorted(
            enumerate(prepared),
            key=lambda indexed_pair: (-indexed_pair[1][1], indexed_pair[0]),
        )
    ]
    total_weight = sum(weight for _, weight in ordered)
    scale = (width * height) / total_weight if total_weight > 0 else 0.0
    scaled = [(item, weight * scale) for item, weight in ordered]

    rects: list[TreemapRect] = []
    row: list[tuple[Any, float]] = []
    remaining = list(scaled)
    current_x = x
    current_y = y
    remaining_width = width
    remaining_height = height

    while remaining:
        candidate = remaining[0]
        if not row:
            row.append(candidate)
            remaining.pop(0)
            continue

        short_side = min(remaining_width, remaining_height)
        if _worst_ratio(row + [candidate], short_side) <= _worst_ratio(row, short_side):
            row.append(candidate)
            remaining.pop(0)
            continue

        current_x, current_y, remaining_width, remaining_height = _layout_row(
            row,
            current_x,
            current_y,
            remaining_width,
            remaining_height,
            rects,
        )
        row = []

    if row:
        _layout_row(
            row,
            current_x,
            current_y,
            remaining_width,
            remaining_height,
            rects,
        )

    return rects


def _worst_ratio(row: Sequence[tuple[Any, float]], short_side: float) -> float:
    """Return the worst aspect ratio in *row*."""
    if not row or short_side <= 0:
        return float("inf")

    areas = [area for _, area in row]
    row_sum = sum(areas)
    max_area = max(areas)
    min_area = min(areas)
    if min_area <= 0 or row_sum <= 0:
        return float("inf")

    side_squared = short_side * short_side
    return max(
        (side_squared * max_area) / (row_sum * row_sum),
        (row_sum * row_sum) / (side_squared * min_area),
    )


def _layout_row(
    row: Sequence[tuple[Any, float]],
    x: float,
    y: float,
    width: float,
    height: float,
    rects: list[TreemapRect],
) -> tuple[float, float, float, float]:
    """Lay out a single row and return the remaining bounds."""
    row_area = sum(area for _, area in row)

    if width >= height:
        row_height = row_area / width if width > 0 else 0.0
        cursor_x = x
        for item, area in row:
            rect_width = area / row_height if row_height > 0 else 0.0
            rects.append(
                TreemapRect(
                    item=item,
                    x=cursor_x,
                    y=y,
                    width=max(0.0, rect_width),
                    height=max(0.0, row_height),
                )
            )
            cursor_x += rect_width
        return x, y + row_height, width, max(0.0, height - row_height)

    row_width = row_area / height if height > 0 else 0.0
    cursor_y = y
    for item, area in row:
        rect_height = area / row_width if row_width > 0 else 0.0
        rects.append(
            TreemapRect(
                item=item,
                x=x,
                y=cursor_y,
                width=max(0.0, row_width),
                height=max(0.0, rect_height),
            )
        )
        cursor_y += rect_height
    return x + row_width, y, max(0.0, width - row_width), height
