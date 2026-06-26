"""Generate a static GitHub Pages site from the analysis outputs."""

from __future__ import annotations

import html
import shutil
from pathlib import Path

import pandas as pd


SVG_FILES = [
    "decade_days_over_thresholds.svg",
    "decade_temperature_anomalies.svg",
    "annual_heat_extremes.svg",
    "annual_mean_temperature.svg",
    "days_over_thresholds.svg",
    "days_over_35c.svg",
    "days_over_40c.svg",
    "days_over_41c.svg",
    "days_over_42c.svg",
]

CSV_FILES = [
    "annual_temperature_metrics.csv",
    "decade_temperature_metrics.csv",
    "station_processing_summary.csv",
]


def copy_assets(output_dir: Path, docs_dir: Path) -> None:
    assets_dir = docs_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for filename in SVG_FILES + CSV_FILES:
        source = output_dir / filename
        if source.exists():
            shutil.copy2(source, assets_dir / filename)


def generate_site(output_dir: Path, docs_dir: Path) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    copy_assets(output_dir, docs_dir)

    annual = pd.read_csv(output_dir / "annual_temperature_metrics.csv")
    periods = pd.read_csv(output_dir / "decade_temperature_metrics.csv")
    processing = pd.read_csv(output_dir / "station_processing_summary.csv").iloc[0]

    hottest = annual.loc[annual["annual_stationday_txk_max_c"].idxmax()]
    warmest = annual.loc[annual["annual_mean_c"].idxmax()]
    latest_period = periods.tail(1).iloc[0]

    chart_sections = [
        (
            "Hot-day thresholds by 10-year period",
            "One total per period for days where at least one DWD station exceeded each threshold.",
            "decade_days_over_thresholds.svg",
        ),
        (
            "Temperature anomalies by 10-year period",
            "Germany-wide mean temperature and station-day TXK p95 relative to 1976-2005.",
            "decade_temperature_anomalies.svg",
        ),
        (
            "Annual station heat extremes",
            "Annual hottest station-day maximum and annual 95th percentile of station-day maximum temperature.",
            "annual_heat_extremes.svg",
        ),
        (
            "Annual mean temperature",
            "DWD Germany-wide regional annual mean air temperature.",
            "annual_mean_temperature.svg",
        ),
        (
            "Annual hot-day thresholds",
            "Year-by-year comparison of days exceeding 35, 40, 41, and 42 C.",
            "days_over_thresholds.svg",
        ),
    ]
    cards = "\n".join(
        f"""
        <section class="chart">
          <div class="chart-copy">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(description)}</p>
          </div>
          <img src="assets/{filename}" alt="{html.escape(title)} chart" loading="lazy">
        </section>
        """
        for title, description, filename in chart_sections
    )

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Germany Temperature Trends</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <main>
    <header class="hero">
      <p class="eyebrow">DWD Climate Data Center analysis</p>
      <h1>Germany temperature trends, {int(annual['year'].min())}-{int(annual['year'].max())}</h1>
      <p class="lede">Annual temperature and station heat-extreme metrics computed from public DWD data.</p>
      <div class="stats">
        <div><strong>{int(processing['station_files_with_data'])}</strong><span>station files with data</span></div>
        <div><strong>{int(processing['station_days_parsed']):,}</strong><span>station-days parsed</span></div>
        <div><strong>{int(warmest['year'])}</strong><span>warmest annual mean: {warmest['annual_mean_c']:.2f} C</span></div>
        <div><strong>{int(hottest['year'])}</strong><span>hottest station-day: {hottest['annual_stationday_txk_max_c']:.1f} C</span></div>
      </div>
    </header>

    {cards}

    <section class="notes">
      <h2>Methodology</h2>
      <p>Germany-wide annual mean temperature comes from DWD's regional annual air-temperature series. Station heat-extreme metrics are computed from DWD daily KL observations using <code>TXK</code>, the daily maximum air temperature.</p>
      <p>The main decade chart uses fixed 10-year periods from 1956-65 through 2016-25. A day above a threshold is counted once per calendar date if at least one included station exceeds that threshold.</p>
      <p>Station coverage changes over time, so early-period extreme counts are best read as observed station-network counts rather than a perfectly homogeneous national climatology.</p>
      <p>Latest 10-year period: <strong>{html.escape(str(latest_period['period']))}</strong>, mean annual temperature {latest_period['mean_annual_mean_c']:.2f} C, TXK p95 {latest_period['mean_stationday_txk_p95_c']:.2f} C.</p>
      <p><a href="assets/annual_temperature_metrics.csv">Annual CSV</a> · <a href="assets/decade_temperature_metrics.csv">10-year period CSV</a></p>
    </section>
  </main>
</body>
</html>
"""
    (docs_dir / "index.html").write_text(html_text, encoding="utf-8")
    (docs_dir / "styles.css").write_text(STYLES_CSS, encoding="utf-8")


STYLES_CSS = """
:root {
  color-scheme: light;
  --ink: #15202b;
  --muted: #52606d;
  --line: #d9e2ec;
  --paper: #fbfcfe;
  --band: #eef3f8;
  --accent: #0f766e;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: var(--paper);
}

main {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
}

.hero {
  padding: 54px 0 30px;
  border-bottom: 1px solid var(--line);
}

.eyebrow {
  margin: 0 0 10px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
}

h1 {
  max-width: 900px;
  margin: 0;
  font-size: clamp(34px, 5vw, 64px);
  line-height: 1.02;
  letter-spacing: 0;
}

.lede {
  max-width: 760px;
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 20px;
  line-height: 1.45;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-top: 30px;
  background: var(--line);
  border: 1px solid var(--line);
}

.stats div {
  min-height: 108px;
  padding: 18px;
  background: #fff;
}

.stats strong {
  display: block;
  font-size: 26px;
  line-height: 1.1;
}

.stats span {
  display: block;
  margin-top: 8px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.35;
}

.chart,
.notes {
  padding: 38px 0;
  border-bottom: 1px solid var(--line);
}

.chart-copy {
  max-width: 820px;
  margin-bottom: 18px;
}

h2 {
  margin: 0 0 8px;
  font-size: 26px;
  line-height: 1.2;
}

p {
  color: var(--muted);
  font-size: 16px;
  line-height: 1.6;
}

.chart img {
  display: block;
  width: 100%;
  height: auto;
  border: 1px solid var(--line);
  background: #fff;
}

a {
  color: #0b5cad;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: .92em;
}

@media (max-width: 820px) {
  main { width: min(100% - 22px, 1180px); }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 520px) {
  .stats { grid-template-columns: 1fr; }
  .hero { padding-top: 34px; }
}
"""
