
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
    xaxis: { title: '10-year period' },
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
