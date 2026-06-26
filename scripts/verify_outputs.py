#!/usr/bin/env python3
"""Verify generated analysis outputs before publishing."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import pandas as pd


EXPECTED_PERIODS = [
    "1906-15",
    "1916-25",
    "1926-35",
    "1936-45",
    "1946-55",
    "1956-65",
    "1966-75",
    "1976-85",
    "1986-95",
    "1996-05",
    "2006-15",
    "2016-25",
]

EXPECTED_FILES = [
    "annual_temperature_metrics.csv",
    "decade_temperature_metrics.csv",
    "station_processing_summary.csv",
    "annual_temperature_metrics.json",
    "decade_temperature_metrics.json",
    "annual_mean_temperature.svg",
    "annual_heat_extremes.svg",
    "days_over_35c.svg",
    "days_over_40c.svg",
    "days_over_41c.svg",
    "days_over_42c.svg",
    "days_over_thresholds.svg",
    "decade_days_over_thresholds.svg",
    "decade_temperature_anomalies.svg",
    "notes.md",
]


def fail(message: str) -> None:
    print(f"verify_outputs: {message}", file=sys.stderr)
    raise SystemExit(1)


def assert_no_invalid_numbers(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"\b(?:NaN|nan|inf|Infinity)\b", text):
        fail(f"{path} contains an invalid numeric literal")


def main() -> None:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("outputs")
    for filename in EXPECTED_FILES:
        path = output_dir / filename
        if not path.exists() or path.stat().st_size == 0:
            fail(f"missing or empty file: {path}")
        if path.suffix == ".svg":
            assert_no_invalid_numbers(path)

    annual = pd.read_csv(output_dir / "annual_temperature_metrics.csv")
    periods = pd.read_csv(output_dir / "decade_temperature_metrics.csv")
    processing = pd.read_csv(output_dir / "station_processing_summary.csv").iloc[0]

    if annual["year"].min() != 1906 or annual["year"].max() != 2025:
        fail("annual metrics must cover 1906-2025 for the interactive publication build")

    if periods["period"].tolist() != EXPECTED_PERIODS:
        fail("10-year periods do not match the requested 1906-15 ... 2016-25 sequence")

    if not (periods["years"] == 10).all():
        fail("all period rows must contain exactly 10 years")

    hottest = float(annual["annual_stationday_txk_max_c"].max())
    if not math.isclose(hottest, 41.2, abs_tol=0.05):
        fail(f"unexpected hottest station-day maximum: {hottest}")

    if annual["unique_dates_over_42c"].sum() != 0:
        fail("expected zero calendar days above 42 C in this dataset")

    if int(processing["station_days_parsed"]) < 10_000_000:
        fail("too few station-days parsed for the full publication build")

    print("verify_outputs: ok")


if __name__ == "__main__":
    main()
