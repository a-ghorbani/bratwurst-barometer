"""Markdown notes for generated outputs."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pandas as pd

from .config import HOT_DAY_THRESHOLDS_C
from .metrics import ProcessingSummary


def write_notes(
    path: Path,
    annual: pd.DataFrame,
    periods: pd.DataFrame,
    summary: ProcessingSummary,
) -> None:
    hottest = annual.loc[annual["annual_stationday_txk_max_c"].idxmax()]
    warmest_mean = annual.loc[annual["annual_mean_c"].idxmax()]
    latest_period = periods.tail(1).iloc[0]
    threshold_columns = ", ".join(
        f"`unique_dates_over_{threshold}c`" for threshold in HOT_DAY_THRESHOLDS_C
    )
    station_threshold_columns = ", ".join(
        f"`station_days_over_{threshold}c`" for threshold in HOT_DAY_THRESHOLDS_C
    )

    text = f"""# Germany temperature plot notes

Period: {int(annual['year'].min())}-{int(annual['year'].max())}

Station data coverage:

- Historical DWD KL station zip files considered: {summary.station_files_considered}
- Station files with usable TXK data in period: {summary.station_files_with_data}
- Parsed station-days in period: {summary.station_days_parsed:,}

Metric definitions:

- `annual_mean_c`: DWD Germany-wide regional annual mean air temperature.
- `annual_stationday_txk_max_c`: hottest daily maximum temperature observed by
  any included DWD station in that year.
- `annual_stationday_txk_p95_c`: 95th percentile across all station-day daily
  maximum temperatures (`TXK`) in that year.
- {threshold_columns}: count of calendar dates in the year where at least one
  included German station reported `TXK` above that threshold.
- {station_threshold_columns}: count of station-date observations above each
  threshold.

Quick read:

- Warmest Germany-wide annual mean in this period: {int(warmest_mean['year'])}
  at {warmest_mean['annual_mean_c']:.2f} C.
- Hottest station-day maximum in this period: {int(hottest['year'])}
  at {hottest['annual_stationday_txk_max_c']:.1f} C.
- Latest 10-year period row in the summary ({latest_period['period']}): mean
  annual temperature {latest_period['mean_annual_mean_c']:.2f} C, average
  annual TXK p95 {latest_period['mean_stationday_txk_p95_c']:.2f} C.

Important interpretation notes:

- DWD station coverage changes over time. Counts based on "at least one station"
  are less sensitive to the number of stations than station-day counts, but the
  early decades still have less dense observation coverage than recent decades.
- `TXK > 42 C` is zero in this run because the highest parsed station-day
  maximum is {hottest['annual_stationday_txk_max_c']:.1f} C.
"""
    path.write_text(textwrap.dedent(text), encoding="utf-8")
