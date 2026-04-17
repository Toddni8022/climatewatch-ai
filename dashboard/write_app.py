content = '''import os
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

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI()
templates = Jinja2Templates(directory="dashboard/templates")

climate_data = {
    "co2": "Loading...",
    "temperature_year": "...",
    "temperature_anomaly": "...",
    "sea_level_year": "...",
    "sea_level_level": "...",
    "solar": "Loading...",
    "briefing": "Generating briefing...",
    "last_updated": "Never"
}

def fetch_co2():
    url = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv"
    response = requests.get(url)
    lines = [l for l in response.text.strip().split("\\n") if not l.startswith("#")]
    latest = lines[-1].split(",")
    return latest[4].strip()

def fetch_temperature():
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
    response = requests.get(url)
    lines = [l for l in response.text.strip().split("\\n") if not l.startswith("#")]
    latest = lines[-1].split(",")
    return latest[0].strip(), latest[1].strip()

def fetch_sea_level():
    url = "https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv"
    response = requests.get(url)
    lines = response.text.strip().split("\\n")
    latest = lines[-1].split(",")
    return latest[0].strip(), latest[1].strip()

def fetch_solar():
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=-90&latitude=38&start=2024&end=2024&format=JSON"
    response = requests.get(url)
    data = response.json()
    values = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    return round(sum(values.values()) / len(values), 2)

def generate_briefing(co2, temp_year, temp_anomaly, sea_year, sea_level, solar):
    from crewai import Agent, Task, Crew, Process, LLM
    llm = LLM(
        model="openrouter/anthropic/claude-haiku-4-5",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
    reporter = Agent(
        role="Climate Report Writer",
        goal="Write a clear concise climate briefing",
        backstory="You translate climate data into plain English briefings.",
        llm=llm,
        verbose=False
    )
    desc = (
        "Write a daily climate briefing in plain English under 150 words using this data: "
        "CO2: " + str(co2) + " ppm. "
        "Temperature anomaly: " + str(temp_anomaly) + "C above baseline in " + str(temp_year) + ". "
        "Sea level: " + str(sea_level) + " inches above 1993 baseline as of " + str(sea_year) + ". "
        "Solar irradiance: " + str(solar) + " kWh/m2/day average. "
        "Make it informative and accessible to general readers."
    )
    report_task = Task(
        description=desc,
        expected_output="A 100-150 word plain English climate briefing.",
        agent=reporter
    )
    crew = Crew(agents=[reporter], tasks=[report_task], process=Process.sequential, verbose=False)
    result = crew.kickoff()
    return str(result)

def refresh_data():
    print("[" + str(datetime.now()) + "] Refreshing climate data...")
    try:
        co2 = fetch_co2()
        temp_year, temp_anomaly = fetch_temperature()
        sea_year, sea_level = fetch_sea_level()
        solar = fetch_solar()
        briefing = generate_briefing(co2, temp_year, temp_anomaly, sea_year, sea_level, solar)
        climate_data["co2"] = co2
        climate_data["temperature_year"] = temp_year
        climate_data["temperature_anomaly"] = temp_anomaly
        climate_data["sea_level_year"] = sea_year
        climate_data["sea_level_level"] = sea_level
        climate_data["solar"] = solar
        climate_data["briefing"] = briefing
        climate_data["last_updated"] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        print("Data refresh complete.")
    except Exception as e:
        print("Refresh error: " + str(e))

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_data, "interval", hours=6)
scheduler.start()

@app.on_event("startup")
async def startup_event():
    t = threading.Thread(target=refresh_data)
    t.daemon = True
    t.start()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"data": climate_data}
    )

@app.get("/api/data")
async def get_data():
    return climate_data

@app.get("/api/refresh")
async def manual_refresh():
    t = threading.Thread(target=refresh_data)
    t.daemon = True
    t.start()
    return {"status": "Refresh started"}
'''

with open("dashboard/app.py", "w") as f:
    f.write(content)

print("Done - app.py written successfully")