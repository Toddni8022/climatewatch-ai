import os
import sys
import threading
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
templates = Jinja2Templates(directory="dashboard/templates")
climate_data = {
    "co2": "Loading...",
    "temperature_year": "...",
    "temperature_anomaly": "...",
    "sea_level_year": "...",
    "sea_level_level": "...",
    "solar": "Loading...",
    "briefing": "Generating...",
    "last_updated": "Never"
}

def fetch_co2():
    r = requests.get("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv")
    lines = [l for l in r.text.strip().split("\n") if not l.startswith("#")]
    return lines[-1].split(",")[4].strip()

def fetch_temperature():
    r = requests.get("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv")
    lines = [l for l in r.text.strip().split("\n") if not l.startswith("#")]
    latest = lines[-1].split(",")
    return latest[0].strip(), latest[1].strip()

def fetch_sea_level():
    r = requests.get("https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv")
    lines = r.text.strip().split("\n")
    latest = lines[-1].split(",")
    return latest[0].strip(), latest[1].strip()

def fetch_solar():
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"
    params = "?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=-90&latitude=38&start=2024&end=2024&format=JSON"
    r = requests.get(url + params)
    values = r.json()["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    return round(sum(values.values()) / len(values), 2)

def refresh_data():
    try:
        co2 = fetch_co2()
        ty, ta = fetch_temperature()
        sy, sl = fetch_sea_level()
        solar = fetch_solar()
        climate_data["co2"] = co2
        climate_data["temperature_year"] = ty
        climate_data["temperature_anomaly"] = ta
        climate_data["sea_level_year"] = sy
        climate_data["sea_level_level"] = sl
        climate_data["solar"] = solar
        climate_data["briefing"] = "CO2: " + str(co2) + " ppm. Temp: " + str(ta) + "C above baseline in " + str(ty) + ". Sea level: " + str(sl) + " inches above 1993 baseline. Solar: " + str(solar) + " kWh/m2/day."
        climate_data["last_updated"] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        print("Refresh complete")
    except Exception as e:
        print("Error: " + str(e))

@app.on_event("startup")
async def startup_event():
    t = threading.Thread(target=refresh_data)
    t.daemon = True
    t.start()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"data": climate_data})

@app.get("/api/data")
async def get_data():
    return climate_data

@app.get("/api/refresh")
async def manual_refresh():
    t = threading.Thread(target=refresh_data)
    t.daemon = True
    t.start()
    return {"status": "started"}
