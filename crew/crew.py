import os
import csv
from io import StringIO

import requests
from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

REQUEST_TIMEOUT = 15

llm = LLM(
    model="openrouter/anthropic/claude-haiku-4-5",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


def get_text(url: str) -> str:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def csv_rows(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    header_index = next(
        index for index, line in enumerate(lines) if "," in line and not line.lower().startswith("land-ocean:")
    )
    return list(csv.DictReader(StringIO("\n".join(lines[header_index:]))))


@tool("Get CO2 Levels")
def get_co2_levels(input: str = "") -> str:
    """Fetch the latest atmospheric CO2 levels from NOAA Mauna Loa."""
    text = get_text("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv")
    lines = [line for line in text.strip().split("\n") if not line.startswith("#")]
    latest = lines[-1].split(",")
    co2_value = latest[4].strip()
    return f"Latest CO2 level: {co2_value} ppm (NOAA Mauna Loa)"


@tool("Get Temperature Anomaly")
def get_temperature_anomaly(input: str = "") -> str:
    """Fetch global temperature anomaly data from NASA GISS."""
    text = get_text("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv")
    lines = [line for line in text.strip().split("\n") if not line.startswith("#")]
    latest = lines[-1].split(",")
    year = latest[0].strip()
    jan = latest[1].strip()
    return f"NASA GISS temperature anomaly - Year: {year}, Jan: {jan} C above baseline"


@tool("Get Sea Level Data")
def get_sea_level(input: str = "") -> str:
    """Fetch global mean sea level rise data."""
    text = get_text("https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv")
    rows = csv_rows(text)
    latest = next(
        row for row in reversed(rows) if row.get("NOAA Adjusted Sea Level") or row.get("CSIRO Adjusted Sea Level")
    )
    year = latest["Year"]
    level = latest.get("NOAA Adjusted Sea Level") or latest["CSIRO Adjusted Sea Level"]
    return f"Sea level rise - Year: {year}, Level: {level} inches above 1993 baseline"


@tool("Get Solar Data")
def get_solar_data(input: str = "") -> str:
    """Fetch solar irradiance data from NASA POWER."""
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
    values = response.json()["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
    valid_values = [value for value in values.values() if value != -999]
    avg = round(sum(valid_values) / len(valid_values), 2)
    return f"NASA POWER solar irradiance 2024 avg: {avg} kWh/m2/day"


data_collector = Agent(
    role="Climate Data Collector",
    goal="Collect the latest climate data from all available sources",
    backstory="You are a specialist in retrieving real-time climate data from NASA and NOAA APIs.",
    tools=[get_co2_levels, get_temperature_anomaly, get_sea_level, get_solar_data],
    llm=llm,
    verbose=True,
)

analyst = Agent(
    role="Climate Data Analyst",
    goal="Analyze climate data and identify key trends and anomalies",
    backstory="You are an expert climate scientist who interprets raw data into meaningful insights.",
    llm=llm,
    verbose=True,
)

reporter = Agent(
    role="Climate Report Writer",
    goal="Write a clear, concise climate briefing for a general audience",
    backstory="You specialize in translating complex climate science into plain English daily briefings.",
    llm=llm,
    verbose=True,
)

collect_task = Task(
    description="Use all available tools to collect the latest CO2, temperature, sea level, and solar data.",
    expected_output="A summary of the latest raw climate data from all four sources.",
    agent=data_collector,
)

analyze_task = Task(
    description="Analyze the collected climate data. Identify any concerning trends, record values, or notable changes.",
    expected_output="A bullet point analysis of key climate trends and what they mean.",
    agent=analyst,
)

report_task = Task(
    description=(
        "Write a daily climate briefing in plain English based on the analysis. "
        "Keep it under 200 words. Make it informative and accessible."
    ),
    expected_output="A 150-200 word daily climate briefing ready for publication.",
    agent=reporter,
)

climate_crew = Crew(
    agents=[data_collector, analyst, reporter],
    tasks=[collect_task, analyze_task, report_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    result = climate_crew.kickoff()
    print("\n===== CLIMATE BRIEFING =====\n")
    print(result)
