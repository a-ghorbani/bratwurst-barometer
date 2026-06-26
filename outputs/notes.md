# Germany temperature plot notes

Period: 1906-2025

Station data coverage:

- Historical DWD KL station zip files considered: 1285
- Station files with usable TXK data in period: 1145
- Parsed station-days in period: 16,564,675

Metric definitions:

- `annual_mean_c`: DWD Germany-wide regional annual mean air temperature.
- `annual_stationday_txk_max_c`: hottest daily maximum temperature observed by
  any included DWD station in that year.
- `annual_stationday_txk_p95_c`: 95th percentile across all station-day daily
  maximum temperatures (`TXK`) in that year.
- `unique_dates_over_35c`, `unique_dates_over_40c`, `unique_dates_over_41c`, `unique_dates_over_42c`: count of calendar dates in the year where at least one
  included German station reported `TXK` above that threshold.
- `station_days_over_35c`, `station_days_over_40c`, `station_days_over_41c`, `station_days_over_42c`: count of station-date observations above each
  threshold.

Quick read:

- Warmest Germany-wide annual mean in this period: 2024
  at 10.89 C.
- Hottest station-day maximum in this period: 2019
  at 41.2 C.
- Latest 10-year period row in the summary (2016-25): mean
  annual temperature 10.15 C, average
  annual TXK p95 28.65 C.

Important interpretation notes:

- DWD station coverage changes over time. Counts based on "at least one station"
  are less sensitive to the number of stations than station-day counts, but the
  early decades still have less dense observation coverage than recent decades.
- `TXK > 42 C` is zero in this run because the highest parsed station-day
  maximum is 41.2 C.
