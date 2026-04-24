import asyncio
import csv
from io import StringIO

import requests
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("climate-tools")
REQUEST_TIMEOUT = 15


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


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_co2_levels",
            description="Get the latest atmospheric CO2 levels from NOAA Mauna Loa",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_temperature_anomaly",
            description="Get global temperature anomaly data from NASA GISS",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_sea_level",
            description="Get global mean sea level rise data",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="get_solar_data",
            description="Get solar irradiance data from NASA POWER",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_co2_levels":
        text = get_text("https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv")
        lines = [line for line in text.strip().split("\n") if not line.startswith("#")]
        latest = lines[-1].split(",")
        co2_value = latest[4].strip()
        return [types.TextContent(type="text", text=f"Latest CO2 level: {co2_value} ppm (NOAA Mauna Loa)")]

    if name == "get_temperature_anomaly":
        text = get_text("https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv")
        lines = [line for line in text.strip().split("\n") if not line.startswith("#")]
        latest = lines[-1].split(",")
        year = latest[0].strip()
        jan = latest[1].strip()
        return [
            types.TextContent(
                type="text",
                text=f"NASA GISS temperature anomaly - Year: {year}, Jan: {jan} C above baseline",
            )
        ]

    if name == "get_sea_level":
        text = get_text("https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv")
        rows = csv_rows(text)
        latest = next(
            row for row in reversed(rows) if row.get("NOAA Adjusted Sea Level") or row.get("CSIRO Adjusted Sea Level")
        )
        year = latest["Year"]
        level = latest.get("NOAA Adjusted Sea Level") or latest["CSIRO Adjusted Sea Level"]
        return [
            types.TextContent(
                type="text",
                text=f"Sea level rise - Year: {year}, Level: {level} inches above 1993 baseline",
            )
        ]

    if name == "get_solar_data":
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
        return [types.TextContent(type="text", text=f"NASA POWER solar irradiance 2024 avg: {avg} kWh/m2/day")]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
