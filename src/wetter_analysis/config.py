"""Project configuration and constants."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ANNUAL_MEAN_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/regional_averages_DE/"
    "annual/air_temperature_mean/regional_averages_tm_year.txt"
)

HISTORICAL_KL_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/historical/"
)

HOT_DAY_THRESHOLDS_C = (35, 40, 41, 42)
DEFAULT_PERIOD_START_YEAR = 1956
DEFAULT_BASELINE_START_YEAR = 1976
DEFAULT_BASELINE_END_YEAR = 2005


@dataclass(frozen=True)
class AnalysisConfig:
    """Runtime settings for one analysis run."""

    start_year: int
    end_year: int
    raw_dir: Path = Path("data/raw")
    output_dir: Path = Path("outputs")
    docs_dir: Path = Path("docs")
    period_start_year: int = DEFAULT_PERIOD_START_YEAR
    baseline_start_year: int = DEFAULT_BASELINE_START_YEAR
    baseline_end_year: int = DEFAULT_BASELINE_END_YEAR
    max_stations: int | None = None
    build_site: bool = True
