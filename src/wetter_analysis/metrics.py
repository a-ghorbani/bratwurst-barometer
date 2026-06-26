"""Metric computation for Germany temperature plots."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import HOT_DAY_THRESHOLDS_C
from .data import (
    download_station_archive,
    list_historical_station_archives,
    read_station_daily_max_temperature,
)


@dataclass(frozen=True)
class ProcessingSummary:
    station_files_considered: int
    station_files_with_data: int
    station_days_parsed: int
    start_year: int
    end_year: int

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([self.__dict__])


def period_label(start_year: int, end_year: int) -> str:
    return f"{start_year}-{str(end_year)[-2:]}"


def station_archives_for_period(raw_dir: Path, start_year: int, end_year: int) -> pd.DataFrame:
    index = list_historical_station_archives(raw_dir)
    return index[
        (index["start"].dt.year <= end_year) & (index["end"].dt.year >= start_year)
    ].copy()


def compute_station_temperature_metrics(
    raw_dir: Path,
    start_year: int,
    end_year: int,
    max_stations: int | None = None,
) -> tuple[pd.DataFrame, ProcessingSummary]:
    """Compute annual station-day extreme and hot-day threshold metrics.

    `unique_dates_over_Xc` is a national calendar-day count: a date is counted
    once if at least one included German DWD station reports `TXK > X`.
    `station_days_over_Xc` counts all station-date observations above threshold.
    """

    archives = station_archives_for_period(raw_dir, start_year, end_year)
    archives = archives.sort_values(["station_id", "start", "end"])
    if max_stations is not None:
        archives = archives.head(max_stations)

    annual_chunks: list[pd.DataFrame] = []
    p95_chunks: list[pd.DataFrame] = []
    hot_dates_by_threshold = {
        threshold: {year: set() for year in range(start_year, end_year + 1)}
        for threshold in HOT_DAY_THRESHOLDS_C
    }

    station_files_with_data = 0
    station_days_parsed = 0

    for row in archives.itertuples(index=False):
        archive_path = download_station_archive(raw_dir, row.filename)
        txk = read_station_daily_max_temperature(archive_path, start_year, end_year)
        if txk.empty:
            continue

        station_files_with_data += 1
        station_days_parsed += len(txk)
        p95_chunks.append(txk[["year", "txk"]])

        grouped = txk.groupby("year")["txk"]
        annual_data = {
            "annual_stationday_txk_max_c": grouped.max(),
            "station_day_count": grouped.size(),
        }

        for threshold in HOT_DAY_THRESHOLDS_C:
            hot = txk[txk["txk"] > float(threshold)]
            annual_data[f"station_days_over_{threshold}c"] = hot.groupby("year").size()
            for year, dates in hot.groupby("year")["date"]:
                hot_dates_by_threshold[threshold][int(year)].update(dates.tolist())

        annual = pd.DataFrame(annual_data).reset_index()
        annual["source_station_files"] = 1
        annual_chunks.append(annual)

        if station_files_with_data % 100 == 0:
            print(
                f"Processed {station_files_with_data}/{len(archives)} station files "
                f"({station_days_parsed:,} station-days)",
                file=sys.stderr,
            )

    if not annual_chunks or not p95_chunks:
        raise RuntimeError("No station daily TXK observations were parsed.")

    combined = pd.concat(annual_chunks, ignore_index=True)
    agg_spec = {
        "annual_stationday_txk_max_c": ("annual_stationday_txk_max_c", "max"),
        "station_day_count": ("station_day_count", "sum"),
        "source_station_files": ("source_station_files", "sum"),
    }
    for threshold in HOT_DAY_THRESHOLDS_C:
        agg_spec[f"station_days_over_{threshold}c"] = (
            f"station_days_over_{threshold}c",
            "sum",
        )

    annual = combined.groupby("year").agg(**agg_spec)
    all_txk = pd.concat(p95_chunks, ignore_index=True)
    annual["annual_stationday_txk_p95_c"] = all_txk.groupby("year")["txk"].quantile(0.95)

    for threshold in HOT_DAY_THRESHOLDS_C:
        annual[f"unique_dates_over_{threshold}c"] = pd.Series(
            {
                year: len(dates)
                for year, dates in hot_dates_by_threshold[threshold].items()
            }
        )

    annual = annual.reset_index()
    ordered_columns = [
        "year",
        "annual_stationday_txk_max_c",
        "annual_stationday_txk_p95_c",
        "station_day_count",
        "source_station_files",
    ]
    for threshold in HOT_DAY_THRESHOLDS_C:
        ordered_columns.extend(
            [f"station_days_over_{threshold}c", f"unique_dates_over_{threshold}c"]
        )
    annual = annual[ordered_columns]

    summary = ProcessingSummary(
        station_files_considered=len(archives),
        station_files_with_data=station_files_with_data,
        station_days_parsed=station_days_parsed,
        start_year=start_year,
        end_year=end_year,
    )
    return annual, summary


def combine_annual_metrics(
    annual_mean: pd.DataFrame,
    station_metrics: pd.DataFrame,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    annual_mean = annual_mean[
        (annual_mean["year"] >= start_year) & (annual_mean["year"] <= end_year)
    ].copy()
    if annual_mean.empty:
        raise RuntimeError(f"No DWD annual mean data for {start_year}-{end_year}.")
    return annual_mean.merge(station_metrics, on="year", how="left").sort_values("year")


def summarize_periods(
    annual_metrics: pd.DataFrame,
    period_start_year: int,
    baseline_start_year: int,
    baseline_end_year: int,
) -> pd.DataFrame:
    """Summarize complete 10-year periods anchored at `period_start_year`."""

    frame = annual_metrics[annual_metrics["year"] >= period_start_year].copy()
    frame["period_start"] = period_start_year + (
        (frame["year"] - period_start_year) // 10
    ) * 10
    frame["period_end"] = frame["period_start"] + 9
    frame["period"] = [
        period_label(int(start), int(end))
        for start, end in zip(frame["period_start"], frame["period_end"])
    ]

    agg_spec = {
        "years": ("year", "count"),
        "mean_annual_mean_c": ("annual_mean_c", "mean"),
        "mean_stationday_txk_p95_c": ("annual_stationday_txk_p95_c", "mean"),
        "max_stationday_txk_c": ("annual_stationday_txk_max_c", "max"),
    }
    for threshold in HOT_DAY_THRESHOLDS_C:
        agg_spec[f"total_unique_dates_over_{threshold}c"] = (
            f"unique_dates_over_{threshold}c",
            "sum",
        )
        agg_spec[f"total_station_days_over_{threshold}c"] = (
            f"station_days_over_{threshold}c",
            "sum",
        )

    summary = (
        frame.groupby(["period_start", "period_end", "period"])
        .agg(**agg_spec)
        .round(2)
        .reset_index()
    )
    summary = summary[summary["years"] == 10].copy()

    baseline = frame[
        (frame["year"] >= baseline_start_year) & (frame["year"] <= baseline_end_year)
    ]
    if baseline.empty:
        baseline = frame

    summary["mean_annual_mean_anomaly_c"] = (
        summary["mean_annual_mean_c"] - baseline["annual_mean_c"].mean()
    ).round(2)
    summary["mean_stationday_txk_p95_anomaly_c"] = (
        summary["mean_stationday_txk_p95_c"]
        - baseline["annual_stationday_txk_p95_c"].mean()
    ).round(2)
    return summary
