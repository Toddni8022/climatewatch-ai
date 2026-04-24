from __future__ import annotations

import csv
import logging
import threading
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
REQUEST_TIMEOUT = 15
REFRESH_INTERVAL_HOURS = 6

logger = logging.getLogger("climatewatch.dashboard")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@dataclass
class ClimateData:
    co2: str = "Loading..."
    temperature_year: str = "..."
    temperature_anomaly: str = "..."
    sea_level_year: str = "..."
    sea_level_level: str = "..."
    solar: str = "Loading..."
    briefing: str = "Generating..."
    last_updated: str = "Never"
    status: str = "warming_up"
    error: str = ""


climate_data = ClimateData()
data_lock = threading.Lock()
refresh_lock = threading.Lock()
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
scheduler = BackgroundScheduler()


def fetch_csv_rows(url: str) -> list[dict[str, str]]:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    lines = [line for line in response.text.splitlines() if line.strip() and not line.startswith("#")]
    header_index = next(
        index for index, line in enumerate(lines) if "," in line and not line.lower().startswith("land-ocean:")
    )
    text = "\n".join(lines[header_index:])
    return list(csv.DictReader(StringIO(text)))


def fetch_co2() -> str:
    rows = fetch_csv_rows("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv")
    latest = rows[-1]
    return latest.get("average") or latest.get("value") or list(latest.values())[4]


def fetch_temperature() -> tuple[str, str]:
    rows = fetch_csv_rows("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv")
    latest = rows[-1]
    return latest["Year"], latest["Jan"]


def fetch_sea_level() -> tuple[str, str]:
    rows = fetch_csv_rows(
        "https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv"
    )
    for row in reversed(rows):
        level = row.get("NOAA Adjusted Sea Level") or row.get("CSIRO Adjusted Sea Level")
        if level:
            return row["Year"], level
    raise ValueError("No sea-level readings found")


def fetch_solar() -> str:
    response = requests.get(
        "https://power.larc.nasa.gov/api/temporal/monthly/point",
        params={
            "parameters": "ALLSKY_SFC_SW_DWN",
            "community": "RE",
            "longitude": -90,
            "latitude": 38,
            "start": 2024,
            "end": 2024,
            "format": "JSON",
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    values: dict[str, float] = response.json()["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    valid_values = [value for value in values.values() if value != -999]
    return f"{sum(valid_values) / len(valid_values):.2f}"


def build_briefing(co2: str, temp_year: str, temp_anomaly: str, sea_year: str, sea_level: str, solar: str) -> str:
    return (
        f"CO2 is currently {co2} ppm at NOAA Mauna Loa. "
        f"NASA GISS reports a January temperature anomaly of {temp_anomaly} C for {temp_year}. "
        f"Global mean sea level is {sea_level} inches above the 1993 baseline as of {sea_year}. "
        f"NASA POWER shows average 2024 solar irradiance near St. Louis at {solar} kWh/m2/day."
    )


def snapshot() -> dict[str, Any]:
    with data_lock:
        return asdict(climate_data)


def refresh_data() -> bool:
    if not refresh_lock.acquire(blocking=False):
        logger.info("Refresh already running")
        return False

    try:
        logger.info("Refreshing climate data")
        co2 = fetch_co2()
        temp_year, temp_anomaly = fetch_temperature()
        sea_year, sea_level = fetch_sea_level()
        solar = fetch_solar()

        with data_lock:
            climate_data.co2 = co2
            climate_data.temperature_year = temp_year
            climate_data.temperature_anomaly = temp_anomaly
            climate_data.sea_level_year = sea_year
            climate_data.sea_level_level = sea_level
            climate_data.solar = solar
            climate_data.briefing = build_briefing(co2, temp_year, temp_anomaly, sea_year, sea_level, solar)
            climate_data.last_updated = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            climate_data.status = "ready"
            climate_data.error = ""

        logger.info("Climate data refresh complete")
        return True
    except Exception as exc:
        logger.exception("Climate data refresh failed")
        with data_lock:
            climate_data.status = "error"
            climate_data.error = str(exc)
        return False
    finally:
        refresh_lock.release()


def refresh_in_background() -> None:
    thread = threading.Thread(target=refresh_data, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.add_job(
        refresh_in_background,
        "interval",
        hours=REFRESH_INTERVAL_HOURS,
        id="climate_data_refresh",
        replace_existing=True,
    )
    scheduler.start()
    refresh_in_background()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="ClimateWatch AI", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"data": snapshot()})


@app.get("/api/data")
async def get_data():
    return snapshot()


@app.post("/api/refresh")
async def manual_refresh():
    refresh_in_background()
    return {"status": "started"}
