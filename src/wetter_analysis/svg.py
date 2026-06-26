"""Simple SVG chart rendering.

The project writes SVG directly to keep the publication workflow lightweight:
only pandas is needed for data processing, and the charts work on GitHub Pages
without a JavaScript plotting runtime.
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import HOT_DAY_THRESHOLDS_C


@dataclass(frozen=True)
class PlotStyle:
    width: int = 1120
    height: int = 650
    margin_left: int = 82
    margin_right: int = 34
    margin_top: int = 62
    margin_bottom: int = 78

    @property
    def plot_width(self) -> int:
        return self.width - self.margin_left - self.margin_right

    @property
    def plot_height(self) -> int:
        return self.height - self.margin_top - self.margin_bottom


THRESHOLD_SERIES = [
    ("> 35 C", "unique_dates_over_35c", "#d97706"),
    ("> 40 C", "unique_dates_over_40c", "#dc2626"),
    ("> 41 C", "unique_dates_over_41c", "#7f1d1d"),
    ("> 42 C", "unique_dates_over_42c", "#374151"),
]


def nice_ticks(min_value: float, max_value: float, count: int = 6) -> list[float]:
    if min_value == max_value:
        if min_value == 0:
            return [0, 1]
        return [min_value - 1, min_value, min_value + 1]

    span = max_value - min_value
    raw_step = span / max(1, count - 1)
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = min([1, 2, 2.5, 5, 10], key=lambda value: abs(value * magnitude - raw_step))
    step *= magnitude
    start = math.floor(min_value / step) * step
    end = math.ceil(max_value / step) * step

    ticks = []
    value = start
    while value <= end + step * 0.5:
        ticks.append(round(value, 6))
        value += step
    return ticks


def svg_header(style: PlotStyle, title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{style.width}" height="{style.height}" viewBox="0 0 {style.width} {style.height}">',
        "<style>",
        "text{font-family:Inter,Segoe UI,Arial,sans-serif;fill:#1f2933}",
        ".title{font-size:26px;font-weight:700}.subtitle{font-size:14px;fill:#52606d}",
        ".axis{stroke:#52606d;stroke-width:1}.grid{stroke:#d9e2ec;stroke-width:1}",
        ".tick{font-size:12px;fill:#52606d}.legend{font-size:13px;fill:#334e68}",
        "</style>",
        f'<rect width="{style.width}" height="{style.height}" fill="#fbfcfe"/>',
        f'<text x="{style.margin_left}" y="34" class="title">{html.escape(title)}</text>',
        f'<text x="{style.margin_left}" y="55" class="subtitle">{html.escape(subtitle)}</text>',
    ]


def add_axes(
    parts: list[str],
    style: PlotStyle,
    x_labels: list[str],
    y_min: float,
    y_max: float,
    y_label: str,
) -> None:
    x0, y0 = style.margin_left, style.margin_top
    x1, y1 = style.width - style.margin_right, style.height - style.margin_bottom
    parts.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" class="axis"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" class="axis"/>')

    for tick in nice_ticks(y_min, y_max, 7):
        y = y0 + (y_max - tick) / (y_max - y_min) * style.plot_height
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.1f}" text-anchor="end" class="tick">{tick:g}</text>')

    group_width = style.plot_width / len(x_labels)
    for index, label in enumerate(x_labels):
        x = x0 + group_width * (index + 0.5)
        parts.append(f'<line x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y1 + 6}" class="axis"/>')
        parts.append(f'<text x="{x:.1f}" y="{y1 + 24}" text-anchor="middle" class="tick">{html.escape(label)}</text>')

    parts.append(
        f'<text transform="translate(22 {style.margin_top + style.plot_height / 2:.1f}) rotate(-90)" '
        f'text-anchor="middle" class="tick">{html.escape(y_label)}</text>'
    )


def scale_line_points(
    x_values: list[int],
    y_values: list[float],
    style: PlotStyle,
    y_min: float,
    y_max: float,
) -> list[tuple[float, float]]:
    x_min, x_max = min(x_values), max(x_values)
    points = []
    for x_value, y_value in zip(x_values, y_values):
        x = style.margin_left + (x_value - x_min) / (x_max - x_min) * style.plot_width
        y = style.margin_top + (y_max - y_value) / (y_max - y_min) * style.plot_height
        points.append((x, y))
    return points


def render_line_plot(
    path: Path,
    frame: pd.DataFrame,
    title: str,
    subtitle: str,
    series: list[tuple[str, str, str]],
    y_label: str,
) -> None:
    style = PlotStyle()
    years = frame["year"].astype(int).tolist()
    values: list[float] = []
    for _, column, _ in series:
        values.extend(frame[column].dropna().astype(float).tolist())

    y_ticks = nice_ticks(min(values), max(values), 7)
    y_min, y_max = min(y_ticks), max(y_ticks)
    parts = svg_header(style, title, subtitle)

    year_ticks = _year_axis_labels(years)
    add_year_axes(parts, style, years, year_ticks, y_min, y_max, y_label)

    for index, (label, column, color) in enumerate(series):
        clean = frame[["year", column]].dropna()
        points = scale_line_points(
            clean["year"].astype(int).tolist(),
            clean[column].astype(float).tolist(),
            style,
            y_min,
            y_max,
        )
        point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        parts.append(f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="3"/>')
        for x, y in points:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.8" fill="{color}"/>')
        legend_y = 90 + 22 * index
        parts.append(f'<rect x="{style.width - 310}" y="{legend_y - 10}" width="14" height="4" fill="{color}"/>')
        parts.append(f'<text x="{style.width - 288}" y="{legend_y - 5}" class="legend">{html.escape(label)}</text>')

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def _year_axis_labels(years: list[int]) -> list[int]:
    first, last = min(years), max(years)
    first_decade = int(math.ceil(first / 10) * 10)
    labels = [first] + list(range(first_decade, last + 1, 10))
    if labels[-1] != last:
        labels.append(last)
    return sorted(set(labels))


def add_year_axes(
    parts: list[str],
    style: PlotStyle,
    years: list[int],
    year_ticks: list[int],
    y_min: float,
    y_max: float,
    y_label: str,
) -> None:
    x0, y0 = style.margin_left, style.margin_top
    x1, y1 = style.width - style.margin_right, style.height - style.margin_bottom
    parts.append(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" class="axis"/>')
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" class="axis"/>')

    for tick in nice_ticks(y_min, y_max, 7):
        y = y0 + (y_max - tick) / (y_max - y_min) * style.plot_height
        parts.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" class="grid"/>')
        parts.append(f'<text x="{x0 - 10}" y="{y + 4:.1f}" text-anchor="end" class="tick">{tick:g}</text>')

    first, last = min(years), max(years)
    for year in year_ticks:
        x = x0 + (year - first) / (last - first) * style.plot_width
        parts.append(f'<line x1="{x:.1f}" y1="{y1}" x2="{x:.1f}" y2="{y1 + 6}" class="axis"/>')
        parts.append(f'<text x="{x:.1f}" y="{y1 + 24}" text-anchor="middle" class="tick">{year}</text>')

    parts.append(
        f'<text transform="translate(22 {style.margin_top + style.plot_height / 2:.1f}) rotate(-90)" '
        f'text-anchor="middle" class="tick">{html.escape(y_label)}</text>'
    )


def render_bar_plot(
    path: Path,
    frame: pd.DataFrame,
    title: str,
    subtitle: str,
    column: str,
    y_label: str,
) -> None:
    style = PlotStyle()
    years = frame["year"].astype(int).tolist()
    values = frame[column].fillna(0).astype(float).tolist()
    y_ticks = nice_ticks(0, max(values) if values else 1, 6)
    y_min, y_max = min(y_ticks), max(y_ticks)
    parts = svg_header(style, title, subtitle)
    add_year_axes(parts, style, years, _year_axis_labels(years), y_min, y_max, y_label)

    bar_width = max(3, style.plot_width / len(years) * 0.72)
    baseline_y = style.margin_top + (y_max - 0) / (y_max - y_min) * style.plot_height
    for year, value in zip(years, values):
        x = style.margin_left + (year - min(years)) / (max(years) - min(years)) * style.plot_width
        y = style.margin_top + (y_max - value) / (y_max - y_min) * style.plot_height
        height = max(0, baseline_y - y)
        fill = "#c2410c" if value > 0 else "#cbd5e1"
        parts.append(
            f'<rect x="{x - bar_width / 2:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{height:.1f}" fill="{fill}"/>'
        )

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def render_threshold_comparison_plot(path: Path, frame: pd.DataFrame) -> None:
    style = PlotStyle()
    years = frame["year"].astype(int).tolist()
    values: list[float] = []
    for _, column, _ in THRESHOLD_SERIES:
        values.extend(frame[column].fillna(0).astype(float).tolist())

    y_ticks = nice_ticks(0, max(values) if values else 1, 7)
    y_min, y_max = min(y_ticks), max(y_ticks)
    parts = svg_header(
        style,
        "Germany annual hot-day thresholds",
        "Calendar days per year where at least one DWD station exceeded each TXK threshold",
    )
    add_year_axes(parts, style, years, _year_axis_labels(years), y_min, y_max, "days")

    for index, (label, column, color) in enumerate(THRESHOLD_SERIES):
        clean = frame[["year", column]].copy()
        clean[column] = clean[column].fillna(0)
        points = scale_line_points(
            clean["year"].astype(int).tolist(),
            clean[column].astype(float).tolist(),
            style,
            y_min,
            y_max,
        )
        point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        parts.append(f'<polyline points="{point_text}" fill="none" stroke="{color}" stroke-width="2.6"/>')
        legend_y = 90 + 22 * index
        parts.append(f'<rect x="{style.width - 230}" y="{legend_y - 10}" width="14" height="4" fill="{color}"/>')
        parts.append(f'<text x="{style.width - 208}" y="{legend_y - 5}" class="legend">{html.escape(label)}</text>')

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def render_period_threshold_comparison_plot(path: Path, periods: pd.DataFrame) -> None:
    style = PlotStyle()
    labels = periods["period"].astype(str).tolist()
    series = [
        (label, f"total_{column}", color)
        for label, column, color in THRESHOLD_SERIES
    ]
    values: list[float] = []
    for _, column, _ in series:
        values.extend(periods[column].fillna(0).astype(float).tolist())

    y_ticks = nice_ticks(0, max(values) if values else 1, 7)
    y_min, y_max = min(y_ticks), max(y_ticks)
    parts = svg_header(
        style,
        "Germany hot-day thresholds by 10-year period",
        "Total calendar days where at least one DWD station exceeded each TXK threshold",
    )
    add_axes(parts, style, labels, y_min, y_max, "days per 10-year period")

    x0 = style.margin_left
    y1 = style.height - style.margin_bottom
    group_width = style.plot_width / len(labels)
    bar_width = min(30, group_width * 0.16)
    offsets = [-1.8 * bar_width, -0.6 * bar_width, 0.6 * bar_width, 1.8 * bar_width]
    for index, _label in enumerate(labels):
        center = x0 + group_width * (index + 0.5)
        for offset, (_, column, color) in zip(offsets, series):
            value = float(periods.iloc[index][column])
            y = style.margin_top + (y_max - value) / (y_max - y_min) * style.plot_height
            height = max(0, y1 - y)
            parts.append(
                f'<rect x="{center + offset - bar_width / 2:.1f}" y="{y:.1f}" '
                f'width="{bar_width:.1f}" height="{height:.1f}" fill="{color}"/>'
            )

    for index, (label, _, color) in enumerate(series):
        legend_y = 88 + index * 22
        parts.append(f'<rect x="{style.width - 230}" y="{legend_y - 10}" width="14" height="10" fill="{color}"/>')
        parts.append(f'<text x="{style.width - 208}" y="{legend_y}" class="legend">{html.escape(label)}</text>')

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def render_period_anomaly_plot(path: Path, periods: pd.DataFrame) -> None:
    style = PlotStyle()
    labels = periods["period"].astype(str).tolist()
    mean_values = periods["mean_annual_mean_anomaly_c"].astype(float).tolist()
    p95_values = periods["mean_stationday_txk_p95_anomaly_c"].astype(float).tolist()
    values = mean_values + p95_values + [0.0]
    y_ticks = nice_ticks(min(values), max(values), 7)
    y_min, y_max = min(y_ticks), max(y_ticks)
    parts = svg_header(
        style,
        "Germany 10-year temperature anomalies",
        "Period means relative to the 1976-2005 baseline",
    )
    add_axes(parts, style, labels, y_min, y_max, "degrees C vs baseline")

    x0 = style.margin_left
    y1 = style.height - style.margin_bottom
    zero_y = style.margin_top + (y_max - 0) / (y_max - y_min) * style.plot_height
    parts.append(
        f'<line x1="{x0}" y1="{zero_y:.1f}" x2="{style.width - style.margin_right}" '
        f'y2="{zero_y:.1f}" stroke="#334e68" stroke-width="1.5"/>'
    )

    group_width = style.plot_width / len(labels)
    bar_width = min(42, group_width * 0.28)
    series = [
        ("Annual mean temperature anomaly", mean_values, "#0f766e"),
        ("TXK p95 anomaly", p95_values, "#2563eb"),
    ]
    for index, _label in enumerate(labels):
        center = x0 + group_width * (index + 0.5)
        for offset, (_series_label, values_for_series, color) in zip(
            [-bar_width * 0.62, bar_width * 0.62], series
        ):
            value = values_for_series[index]
            y = style.margin_top + (y_max - value) / (y_max - y_min) * style.plot_height
            rect_y = min(y, zero_y)
            height = abs(zero_y - y)
            parts.append(
                f'<rect x="{center + offset - bar_width / 2:.1f}" y="{rect_y:.1f}" '
                f'width="{bar_width:.1f}" height="{height:.1f}" fill="{color}"/>'
            )

    for index, (label, _values, color) in enumerate(series):
        legend_y = 88 + index * 22
        parts.append(f'<rect x="{style.width - 360}" y="{legend_y - 10}" width="14" height="10" fill="{color}"/>')
        parts.append(f'<text x="{style.width - 338}" y="{legend_y}" class="legend">{html.escape(label)}</text>')

    # Keep x-axis labels above long anomaly bars when values are negative.
    parts.append(f'<line x1="{x0}" y1="{y1}" x2="{style.width - style.margin_right}" y2="{y1}" class="axis"/>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def render_all_charts(output_dir: Path, annual: pd.DataFrame, periods: pd.DataFrame) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    render_line_plot(
        output_dir / "annual_mean_temperature.svg",
        annual,
        "Germany annual mean temperature",
        "DWD Germany regional annual mean air temperature, complete years",
        [("Annual mean", "annual_mean_c", "#0f766e")],
        "degrees C",
    )
    render_line_plot(
        output_dir / "annual_heat_extremes.svg",
        annual,
        "Germany station heat extremes",
        "DWD station-day TXK: annual maximum and 95th percentile",
        [
            ("Annual hottest station-day TXK", "annual_stationday_txk_max_c", "#b91c1c"),
            ("Annual station-day TXK p95", "annual_stationday_txk_p95_c", "#2563eb"),
        ],
        "degrees C",
    )
    for threshold in HOT_DAY_THRESHOLDS_C:
        render_bar_plot(
            output_dir / f"days_over_{threshold}c.svg",
            annual,
            f"Germany days over {threshold} C",
            f"Calendar days per year where at least one DWD station reported TXK > {threshold} C",
            f"unique_dates_over_{threshold}c",
            "days",
        )
    render_threshold_comparison_plot(output_dir / "days_over_thresholds.svg", annual)
    render_period_threshold_comparison_plot(
        output_dir / "decade_days_over_thresholds.svg", periods
    )
    render_period_anomaly_plot(output_dir / "decade_temperature_anomalies.svg", periods)
