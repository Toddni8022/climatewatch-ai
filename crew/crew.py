import os
import requests
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

load_dotenv()

llm = LLM(
    model="openrouter/anthropic/claude-haiku-4-5",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# ── Climate Data Tools ──────────────────────────────────────────────

@tool("Get CO2 Levels")
def get_co2_levels(input: str = "") -> str:
    """Fetches the latest atmospheric CO2 levels from NOAA Mauna Loa"""
    url = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv"
    response = requests.get(url)
    lines = [l for l in response.text.strip().split("\n") if not l.startswith("#")]
    latest = lines[-1].split(",")
    co2_value = latest[4].strip()
    return f"Latest CO2 level: {co2_value} ppm (NOAA Mauna Loa)"

@tool("Get Temperature Anomaly")
def get_temperature_anomaly(input: str = "") -> str:
    """Fetches global temperature anomaly data from NASA GISS"""
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
    response = requests.get(url)
    lines = [l for l in response.text.strip().split("\n") if not l.startswith("#")]
    latest = lines[-1].split(",")
    year = latest[0].strip()
    jan = latest[1].strip()
    return f"NASA GISS Temperature Anomaly - Year: {year}, Jan: {jan}C above baseline"

@tool("Get Sea Level Data")
def get_sea_level(input: str = "") -> str:
    """Fetches global mean sea level rise data"""
    url = "https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv"
    response = requests.get(url)
    lines = response.text.strip().split("\n")
    latest = lines[-1].split(",")
    year = latest[0].strip()
    level = latest[1].strip()
    return f"Sea Level Rise - Year: {year}, Level: {level} inches above 1993 baseline"

@tool("Get Solar Data")
def get_solar_data(input: str = "") -> str:
    """Fetches solar irradiance data from NASA Power"""
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=-90&latitude=38&start=2024&end=2024&format=JSON"
    response = requests.get(url)
    data = response.json()
    values = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    avg = round(sum(values.values()) / len(values), 2)
    return f"NASA Power Solar Irradiance 2024 avg: {avg} kWh/m2/day"

# ── Agents ──────────────────────────────────────────────────────────

data_collector = Agent(
    role="Climate Data Collector",
    goal="Collect the latest climate data from all available sources",
    backstory="You are a specialist in retrieving real-time climate data from NASA and NOAA APIs.",
    tools=[get_co2_levels, get_temperature_anomaly, get_sea_level, get_solar_data],
    llm=llm,
    verbose=True
)

analyst = Agent(
    role="Climate Data Analyst",
    goal="Analyze climate data and identify key trends and anomalies",
    backstory="You are an expert climate scientist who interprets raw data into meaningful insights.",
    llm=llm,
    verbose=True
)

reporter = Agent(
    role="Climate Report Writer",
    goal="Write a clear, concise climate briefing for a general audience",
    backstory="You specialize in translating complex climate science into plain English daily briefings.",
    llm=llm,
    verbose=True
)

# ── Tasks ────────────────────────────────────────────────────────────

collect_task = Task(
    description="Use all available tools to collect the latest CO2, temperature, sea level, and solar data.",
    expected_output="A summary of the latest raw climate data from all four sources.",
    agent=data_collector
)

analyze_task = Task(
    description="Analyze the collected climate data. Identify any concerning trends, record values, or notable changes.",
    expected_output="A bullet point analysis of key climate trends and what they mean.",
    agent=analyst
)

report_task = Task(
    description="Write a daily climate briefing in plain English based on the analysis. Keep it under 200 words. Make it informative and accessible.",
    expected_output="A 150-200 word daily climate briefing ready for publication.",
    agent=reporter
)

# ── Crew ─────────────────────────────────────────────────────────────

climate_crew = Crew(
    agents=[data_collector, analyst, reporter],
    tasks=[collect_task, analyze_task, report_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    result = climate_crew.kickoff()
    print("\n===== CLIMATE BRIEFING =====\n")
    print(result)