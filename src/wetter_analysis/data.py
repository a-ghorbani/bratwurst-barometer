"""Readers for DWD Climate Data Center files."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from .config import ANNUAL_MEAN_URL, HISTORICAL_KL_URL
from .download import download_file, download_text


def read_annual_mean_temperature(raw_dir: Path) -> pd.DataFrame:
    """Read DWD Germany-wide annual mean air temperature.

    Returns columns:
    - `year`
    - `annual_mean_c`
    """

    path = raw_dir / "regional_averages_tm_year.txt"
    download_file(ANNUAL_MEAN_URL, path)

    frame = pd.read_csv(path, sep=";", skiprows=1)
    frame.columns = [str(column).strip() for column in frame.columns]
    frame = frame.rename(columns={"Jahr": "year", "Deutschland": "annual_mean_c"})
    frame = frame[["year", "annual_mean_c"]].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["annual_mean_c"] = pd.to_numeric(frame["annual_mean_c"], errors="coerce")
    return frame.dropna().astype({"year": int}).sort_values("year")


def list_historical_station_archives(raw_dir: Path) -> pd.DataFrame:
    """List DWD daily KL historical station zip files from the directory index."""

    path = raw_dir / "historical_kl_index.html"
    if not path.exists():
        path.write_text(download_text(HISTORICAL_KL_URL), encoding="utf-8")

    html_text = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    pattern = re.compile(
        r'href="(tageswerte_KL_(\d{5})_(\d{8})_(\d{8})_hist\.zip)"'
    )
    for filename, station_id, start, end in pattern.findall(html_text):
        rows.append(
            {
                "filename": filename,
                "station_id": int(station_id),
                "start": pd.to_datetime(start, format="%Y%m%d"),
                "end": pd.to_datetime(end, format="%Y%m%d"),
            }
        )

    if not rows:
        raise RuntimeError("No historical DWD station archives found in index.")

    return pd.DataFrame(rows).sort_values(["station_id", "start", "end"])


def download_station_archive(raw_dir: Path, filename: str) -> Path:
    path = raw_dir / "daily_kl_historical" / filename
    download_file(HISTORICAL_KL_URL + filename, path)
    return path


def read_station_daily_max_temperature(
    archive_path: Path,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    """Read daily maximum air temperature (`TXK`) from one DWD KL archive."""

    with zipfile.ZipFile(archive_path) as archive:
        product_names = [
            name
            for name in archive.namelist()
            if name.startswith("produkt_klima_tag_") and name.endswith(".txt")
        ]
        if not product_names:
            return pd.DataFrame(columns=["station_id", "date", "year", "txk"])

        with archive.open(product_names[0]) as handle:
            text = io.TextIOWrapper(handle, encoding="latin1")
            frame = pd.read_csv(
                text,
                sep=";",
                usecols=["STATIONS_ID", "MESS_DATUM", " TXK"],
                skipinitialspace=False,
            )

    frame.columns = [column.strip().lower() for column in frame.columns]
    frame = frame.rename(
        columns={"stations_id": "station_id", "mess_datum": "date", "txk": "txk"}
    )
    frame["date"] = pd.to_datetime(
        frame["date"].astype(str), format="%Y%m%d", errors="coerce"
    )
    frame["txk"] = pd.to_numeric(frame["txk"], errors="coerce")
    frame = frame[(frame["date"].dt.year >= start_year) & (frame["date"].dt.year <= end_year)]

    # DWD uses -999 for missing values. The upper bound protects against corrupt rows
    # without excluding plausible German daily maximum temperatures.
    frame = frame[(frame["txk"] > -100) & (frame["txk"] < 60)]
    frame["year"] = frame["date"].dt.year
    return frame[["station_id", "date", "year", "txk"]].dropna()
