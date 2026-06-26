"""Command-line entry point for the Germany temperature analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import (
    DEFAULT_BASELINE_END_YEAR,
    DEFAULT_BASELINE_START_YEAR,
    DEFAULT_PERIOD_START_YEAR,
    AnalysisConfig,
)
from .data import read_annual_mean_temperature
from .metrics import (
    combine_annual_metrics,
    compute_station_temperature_metrics,
    summarize_periods,
)
from .notes import write_notes
from .site import generate_site
from .svg import render_all_charts


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Germany temperature metrics, SVG charts, and a static site."
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=1956,
        help="First year to include. Default: 1956.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Last complete year to include. Defaults to latest DWD annual mean year.",
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--docs-dir", type=Path, default=Path("docs"))
    parser.add_argument(
        "--period-start-year",
        type=int,
        default=DEFAULT_PERIOD_START_YEAR,
        help="Anchor year for complete 10-year periods. Default: 1956.",
    )
    parser.add_argument(
        "--baseline-start-year",
        type=int,
        default=DEFAULT_BASELINE_START_YEAR,
        help="First baseline year for anomaly plots. Default: 1976.",
    )
    parser.add_argument(
        "--baseline-end-year",
        type=int,
        default=DEFAULT_BASELINE_END_YEAR,
        help="Last baseline year for anomaly plots. Default: 2005.",
    )
    parser.add_argument(
        "--max-stations",
        type=int,
        default=None,
        help="Debug option: limit station archives processed. Do not use for publication.",
    )
    parser.add_argument(
        "--no-site",
        action="store_true",
        help="Skip GitHub Pages site generation under docs/.",
    )
    return parser.parse_args(argv)


def config_from_args(args: argparse.Namespace) -> AnalysisConfig:
    annual_mean = read_annual_mean_temperature(args.raw_dir)
    latest_year = int(annual_mean["year"].max())
    end_year = args.end_year or latest_year
    if args.start_year > end_year:
        raise ValueError("--start-year must be less than or equal to --end-year")
    return AnalysisConfig(
        start_year=args.start_year,
        end_year=end_year,
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        docs_dir=args.docs_dir,
        period_start_year=args.period_start_year,
        baseline_start_year=args.baseline_start_year,
        baseline_end_year=args.baseline_end_year,
        max_stations=args.max_stations,
        build_site=not args.no_site,
    )


def run(config: AnalysisConfig) -> None:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.raw_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Building metrics for {config.start_year}-{config.end_year}",
        file=sys.stderr,
    )
    annual_mean = read_annual_mean_temperature(config.raw_dir)
    station_metrics, processing = compute_station_temperature_metrics(
        config.raw_dir,
        config.start_year,
        config.end_year,
        max_stations=config.max_stations,
    )
    annual = combine_annual_metrics(
        annual_mean, station_metrics, config.start_year, config.end_year
    )
    periods = summarize_periods(
        annual,
        period_start_year=config.period_start_year,
        baseline_start_year=config.baseline_start_year,
        baseline_end_year=config.baseline_end_year,
    )

    annual.to_csv(config.output_dir / "annual_temperature_metrics.csv", index=False)
    periods.to_csv(config.output_dir / "decade_temperature_metrics.csv", index=False)
    processing.to_frame().to_csv(
        config.output_dir / "station_processing_summary.csv", index=False
    )
    render_all_charts(config.output_dir, annual, periods)
    write_notes(config.output_dir / "notes.md", annual, periods, processing)

    if config.build_site:
        generate_site(config.output_dir, config.docs_dir)
        print(f"Wrote GitHub Pages site to {config.docs_dir}", file=sys.stderr)

    print(f"Wrote outputs to {config.output_dir}", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = config_from_args(args)
    run(config)
