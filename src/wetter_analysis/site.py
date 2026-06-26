"""Generate a static GitHub Pages site from the analysis outputs."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

import pandas as pd

INTERACTIVE_DEFAULT_START_YEAR = 1956


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

JSON_FILES = ["annual_temperature_metrics.json", "decade_temperature_metrics.json"]


def copy_assets(output_dir: Path, docs_dir: Path) -> None:
    assets_dir = docs_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for filename in SVG_FILES + CSV_FILES + JSON_FILES:
        source = output_dir / filename
        if source.exists():
            shutil.copy2(source, assets_dir / filename)


def write_json_assets(output_dir: Path, annual: pd.DataFrame, periods: pd.DataFrame) -> None:
    annual_records = annual.where(pd.notnull(annual), None).to_dict(orient="records")
    period_records = periods.where(pd.notnull(periods), None).to_dict(orient="records")
    (output_dir / "annual_temperature_metrics.json").write_text(
        json.dumps(annual_records, separators=(",", ":")),
        encoding="utf-8",
    )
    (output_dir / "decade_temperature_metrics.json").write_text(
        json.dumps(period_records, separators=(",", ":")),
        encoding="utf-8",
    )


def generate_site(output_dir: Path, docs_dir: Path) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)

    annual = pd.read_csv(output_dir / "annual_temperature_metrics.csv")
    periods = pd.read_csv(output_dir / "decade_temperature_metrics.csv")
    processing = pd.read_csv(output_dir / "station_processing_summary.csv").iloc[0]
    write_json_assets(output_dir, annual, periods)
    copy_assets(output_dir, docs_dir)

    hottest = annual.loc[annual["annual_stationday_txk_max_c"].idxmax()]
    warmest = annual.loc[annual["annual_mean_c"].idxmax()]
    latest_period = periods.tail(1).iloc[0]

    static_chart_sections = [
        (
            "Static period chart",
            "SVG export of the 10-year hot-day threshold comparison.",
            "decade_days_over_thresholds.svg",
        ),
        (
            "Static anomaly chart",
            "SVG export of 10-year temperature anomalies.",
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
    static_cards = "\n".join(
        f"""
        <section class="chart static-chart">
          <div class="chart-copy">
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(description)}</p>
          </div>
          <img src="assets/{filename}" alt="{html.escape(title)} chart" loading="lazy">
        </section>
        """
        for title, description, filename in static_chart_sections
    )

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Germany Temperature Trends</title>
  <link rel="stylesheet" href="styles.css">
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
</head>
<body>
  <main>
    <header class="hero">
      <p class="eyebrow">DWD Climate Data Center analysis</p>
      <h1>Germany temperature trends, {int(annual['year'].min())}-{int(annual['year'].max())}</h1>
      <p class="lede">Interactive annual and 10-year heat metrics computed from public DWD data. The full dataset starts in {int(annual['year'].min())}; charts open on {INTERACTIVE_DEFAULT_START_YEAR}-{int(annual['year'].max())} by default.</p>
      <div class="stats">
        <div><strong>{int(processing['station_files_with_data'])}</strong><span>station files with data</span></div>
        <div><strong>{int(processing['station_days_parsed']):,}</strong><span>station-days parsed</span></div>
        <div><strong>{int(warmest['year'])}</strong><span>warmest annual mean: {warmest['annual_mean_c']:.2f} C</span></div>
        <div><strong>{int(hottest['year'])}</strong><span>hottest station-day: {hottest['annual_stationday_txk_max_c']:.1f} C</span></div>
      </div>
    </header>

    <section class="chart">
      <div class="chart-copy">
        <h2>Hot-day thresholds by 10-year period</h2>
        <p>Compare periods from 1906 onward, with one bar per threshold. Use the legend to isolate 35, 40, 41, or 42 C.</p>
      </div>
      <div id="period-thresholds" class="plot" aria-label="Interactive hot-day thresholds by 10-year period"></div>
    </section>

    <section class="chart">
      <div class="chart-copy">
        <h2>Annual heat extremes</h2>
        <p>Zoom, pan, or use the range buttons. The full series is loaded from 1906, while the initial view starts in 1956.</p>
      </div>
      <div id="annual-extremes" class="plot" aria-label="Interactive annual heat extremes"></div>
    </section>

    <section class="chart">
      <div class="chart-copy">
        <h2>Annual hot-day thresholds</h2>
        <p>Calendar days per year where at least one DWD station exceeded each daily maximum temperature threshold.</p>
      </div>
      <div id="annual-thresholds" class="plot" aria-label="Interactive annual hot-day thresholds"></div>
    </section>

    <section class="chart">
      <div class="chart-copy">
        <h2>Annual mean temperature</h2>
        <p>DWD Germany-wide annual mean air temperature, shown separately from station extremes.</p>
      </div>
      <div id="annual-mean" class="plot" aria-label="Interactive annual mean temperature"></div>
    </section>

    {static_cards}

    <section class="notes">
      <h2>Methodology</h2>
      <p>Germany-wide annual mean temperature comes from DWD's regional annual air-temperature series. Station heat-extreme metrics are computed from DWD daily KL observations using <code>TXK</code>, the daily maximum air temperature.</p>
      <p>The 10-year chart uses fixed periods from {html.escape(str(periods.iloc[0]['period']))} through {html.escape(str(latest_period['period']))}. A day above a threshold is counted once per calendar date if at least one included station exceeds that threshold.</p>
      <p>Station coverage changes over time, so early-period extreme counts are best read as observed station-network counts rather than a perfectly homogeneous national climatology.</p>
      <p>Latest 10-year period: <strong>{html.escape(str(latest_period['period']))}</strong>, mean annual temperature {latest_period['mean_annual_mean_c']:.2f} C, TXK p95 {latest_period['mean_stationday_txk_p95_c']:.2f} C.</p>
      <p><a href="assets/annual_temperature_metrics.csv">Annual CSV</a> · <a href="assets/decade_temperature_metrics.csv">10-year period CSV</a></p>
    </section>
  </main>
  <script src="site.js"></script>
</body>
</html>
"""
    (docs_dir / "index.html").write_text(html_text, encoding="utf-8")
    (docs_dir / "styles.css").write_text(STYLES_CSS, encoding="utf-8")
    (docs_dir / "site.js").write_text(SITE_JS, encoding="utf-8")


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

.plot {
  width: 100%;
  min-height: 560px;
  border: 1px solid var(--line);
  background: #fff;
}

.static-chart {
  background: linear-gradient(180deg, transparent, rgba(238, 243, 248, .45));
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
  .plot { min-height: 460px; }
}
"""


SITE_JS = """
const DEFAULT_START_YEAR = 1956;
const THRESHOLD_SERIES = [
  { label: '> 35 C', annual: 'unique_dates_over_35c', period: 'total_unique_dates_over_35c', color: '#d97706' },
  { label: '> 40 C', annual: 'unique_dates_over_40c', period: 'total_unique_dates_over_40c', color: '#dc2626' },
  { label: '> 41 C', annual: 'unique_dates_over_41c', period: 'total_unique_dates_over_41c', color: '#7f1d1d' },
  { label: '> 42 C', annual: 'unique_dates_over_42c', period: 'total_unique_dates_over_42c', color: '#374151' },
];

const commonLayout = {
  paper_bgcolor: '#ffffff',
  plot_bgcolor: '#ffffff',
  margin: { l: 64, r: 24, t: 36, b: 64 },
  font: { family: 'Inter, Segoe UI, Arial, sans-serif', color: '#1f2933' },
  hovermode: 'x unified',
  legend: { orientation: 'h', x: 0, y: 1.16 },
};

const config = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
};

function rangeButtons(maxYear) {
  return [
    { count: 20, label: '20y', step: 'year', stepmode: 'backward' },
    { count: 50, label: '50y', step: 'year', stepmode: 'backward' },
    { count: maxYear - DEFAULT_START_YEAR, label: '1956+', step: 'year', stepmode: 'backward' },
    { label: 'all', step: 'all' },
  ];
}

function defaultRange(years) {
  return [Math.max(DEFAULT_START_YEAR, Math.min(...years)), Math.max(...years)];
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not load ${path}`);
  return response.json();
}

function plotAnnualMean(annual) {
  const years = annual.map(d => d.year);
  const trace = {
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Annual mean',
    x: years,
    y: annual.map(d => d.annual_mean_c),
    line: { color: '#0f766e', width: 3 },
    marker: { size: 5 },
    hovertemplate: '%{x}<br>%{y:.2f} C<extra></extra>',
  };
  Plotly.newPlot('annual-mean', [trace], {
    ...commonLayout,
    yaxis: { title: 'degrees C', gridcolor: '#e5edf5' },
    xaxis: {
      title: 'year',
      range: defaultRange(years),
      rangeslider: { visible: true, thickness: 0.08 },
      rangeselector: { buttons: rangeButtons(Math.max(...years)) },
    },
  }, config);
}

function plotAnnualExtremes(annual) {
  const years = annual.map(d => d.year);
  const traces = [
    {
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Annual hottest station-day TXK',
      x: years,
      y: annual.map(d => d.annual_stationday_txk_max_c),
      line: { color: '#b91c1c', width: 3 },
      marker: { size: 5 },
      hovertemplate: '%{x}<br>%{y:.1f} C<extra></extra>',
    },
    {
      type: 'scatter',
      mode: 'lines+markers',
      name: 'Annual station-day TXK p95',
      x: years,
      y: annual.map(d => d.annual_stationday_txk_p95_c),
      line: { color: '#2563eb', width: 3 },
      marker: { size: 5 },
      hovertemplate: '%{x}<br>%{y:.1f} C<extra></extra>',
    },
  ];
  Plotly.newPlot('annual-extremes', traces, {
    ...commonLayout,
    yaxis: { title: 'degrees C', gridcolor: '#e5edf5' },
    xaxis: {
      title: 'year',
      range: defaultRange(years),
      rangeslider: { visible: true, thickness: 0.08 },
      rangeselector: { buttons: rangeButtons(Math.max(...years)) },
    },
  }, config);
}

function plotAnnualThresholds(annual) {
  const years = annual.map(d => d.year);
  const traces = THRESHOLD_SERIES.map(series => ({
    type: 'scatter',
    mode: 'lines+markers',
    name: series.label,
    x: years,
    y: annual.map(d => d[series.annual]),
    line: { color: series.color, width: 3 },
    marker: { size: 5 },
    hovertemplate: '%{x}<br>%{y} days<extra></extra>',
  }));
  Plotly.newPlot('annual-thresholds', traces, {
    ...commonLayout,
    yaxis: { title: 'calendar days', gridcolor: '#e5edf5', rangemode: 'tozero' },
    xaxis: {
      title: 'year',
      range: defaultRange(years),
      rangeslider: { visible: true, thickness: 0.08 },
      rangeselector: { buttons: rangeButtons(Math.max(...years)) },
    },
  }, config);
}

function plotPeriodThresholds(periods) {
  const x = periods.map(d => d.period);
  const traces = THRESHOLD_SERIES.map(series => ({
    type: 'bar',
    name: series.label,
    x,
    y: periods.map(d => d[series.period]),
    marker: { color: series.color },
    hovertemplate: '%{x}<br>%{y} days<extra></extra>',
  }));
  Plotly.newPlot('period-thresholds', traces, {
    ...commonLayout,
    barmode: 'group',
    yaxis: { title: 'days per 10-year period', gridcolor: '#e5edf5', rangemode: 'tozero' },
    xaxis: { title: '10-year period', type: 'category', categoryorder: 'array', categoryarray: x },
  }, config);
}

async function main() {
  const [annual, periods] = await Promise.all([
    loadJson('assets/annual_temperature_metrics.json'),
    loadJson('assets/decade_temperature_metrics.json'),
  ]);
  plotPeriodThresholds(periods);
  plotAnnualExtremes(annual);
  plotAnnualThresholds(annual);
  plotAnnualMean(annual);
}

main().catch(error => {
  document.body.insertAdjacentHTML('beforeend', `<pre class="error">${error.message}</pre>`);
  console.error(error);
});
"""
