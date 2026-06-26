# Germany temperature trends

Reproducible plots and CSV metrics for temperature trends and hot-day extremes
in Germany, built from public Deutscher Wetterdienst (DWD) Climate Data Center
data.

The publication build covers `1956-2025` and summarizes complete 10-year
periods:

```text
1956-65, 1966-75, 1976-85, 1986-95, 1996-05, 2006-15, 2016-25
```

## What it generates

CSV files in `outputs/`:

- `annual_temperature_metrics.csv`: annual Germany-wide mean temperature,
  annual station-day maximum temperature, annual station-day 95th percentile,
  and hot-day threshold counts.
- `decade_temperature_metrics.csv`: complete 10-year period summaries.
- `station_processing_summary.csv`: station-file and station-day coverage.

SVG charts in `outputs/`:

- `decade_days_over_thresholds.svg`: one grouped bar set per 10-year period,
  comparing `TXK > 35 C`, `> 40 C`, `> 41 C`, and `> 42 C`.
- `decade_temperature_anomalies.svg`: 10-year period anomalies for annual mean
  temperature and annual 95th-percentile station-day maximum temperature.
- `annual_heat_extremes.svg`: annual hottest station-day and annual p95.
- `annual_mean_temperature.svg`: DWD Germany-wide annual mean temperature.
- `days_over_thresholds.svg`: annual comparison of the hot-day thresholds.
- `days_over_35c.svg`, `days_over_40c.svg`, `days_over_41c.svg`,
  `days_over_42c.svg`: individual threshold charts.

GitHub Pages site:

- `docs/index.html`
- `docs/styles.css`
- `docs/assets/*`

Configure GitHub Pages to publish from the repository's `docs/` directory.

## Quick start

```sh
python3 -m pip install -r requirements.txt
python3 germany_temperature_plots.py
python3 scripts/verify_outputs.py
```

The default command builds the publication dataset for `1956-2025`, writes
charts and CSVs under `outputs/`, and copies site assets into `docs/`.

For an installed CLI:

```sh
python3 -m pip install -e .
wetter-analysis
```

## Reproducibility

Raw DWD files are cached under `data/raw/`. The cache is ignored by git because
the station archive is large and can be rebuilt from DWD.

To force a fresh download:

```sh
rm -rf data/raw
python3 germany_temperature_plots.py
```

Useful options:

```sh
python3 germany_temperature_plots.py --start-year 1881
python3 germany_temperature_plots.py --start-year 1976 --end-year 2025
python3 germany_temperature_plots.py --no-site
```

`--max-stations` exists only for fast local debugging and should not be used
for published results.

## Data sources

- DWD CDC Germany regional annual mean air temperature:
  `regional_averages_DE/annual/air_temperature_mean/regional_averages_tm_year.txt`
- DWD CDC German daily station climate observations, historical KL product:
  `observations_germany/climate/daily/kl/historical/tageswerte_KL_*_hist.zip`

The annual mean temperature series starts in `1881`. Daily station archives go
back earlier for a few stations, but station coverage is sparse in early years.

## Metric definitions

- `annual_mean_c`: DWD Germany-wide regional annual mean air temperature.
- `annual_stationday_txk_max_c`: hottest daily maximum air temperature observed
  by any included DWD station in a year.
- `annual_stationday_txk_p95_c`: 95th percentile across all station-day `TXK`
  values in a year.
- `unique_dates_over_35c`, `unique_dates_over_40c`, `unique_dates_over_41c`,
  `unique_dates_over_42c`: count of calendar dates where at least one station
  reported `TXK` above that threshold.
- `station_days_over_35c`, `station_days_over_40c`, `station_days_over_41c`,
  `station_days_over_42c`: count of all station-date observations above that
  threshold.

## Interpretation notes

Station coverage changes over time. The "unique calendar dates above threshold"
metric is less sensitive to station-count changes than station-day counts, but
early-period extremes are still observed station-network counts rather than a
perfectly homogeneous gridded national climatology.

The `> 42 C` chart is expected to be zero for the current publication build:
the hottest parsed station-day maximum is `41.2 C`.
