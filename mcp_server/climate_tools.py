import asyncio
import csv
from io import StringIO
from typing import Any

import requests
from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("climate-tools")

REQUEST_TIMEOUT = 15


def get_text(url: str, params: dict[str, Any] | None = None) -> str:
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def parse_csv(text: str) -> list[dict[str, str]]:
    lines = [
        line for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    header_index = next(
        index for index, line in enumerate(lines)
        if "," in line
    )

    csv_text = "\n".join(lines[header_index:])
    return list(csv.DictReader(StringIO(csv_text)))


def text_response(message: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=message)]


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_co2_levels",
            description="Get the latest atmospheric CO2 level from NOAA Mauna Loa.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_temperature_anomaly",
            description="Get the latest global temperature anomaly from NASA GISS.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_sea_level",
            description="Get the latest global mean sea level rise data.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_solar_data",
            description="Get average 2024 solar irradiance data from NASA POWER.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]):
    try:
        if name == "get_co2_levels":
            return get_co2_levels()

        if name == "get_temperature_anomaly":
            return get_temperature_anomaly()

        if name == "get_sea_level":
            return get_sea_level()

        if name == "get_solar_data":
            return get_solar_data()

        return text_response(f"Unknown tool: {name}")

    except requests.RequestException as error:
        return text_response(f"Network error while running {name}: {error}")

    except Exception as error:
        return text_response(f"Error while running {name}: {error}")


def get_co2_levels() -> list[types.TextContent]:
    url = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv"
    text = get_text(url)
    rows = parse_csv(text)

    latest = next(
        row for row in reversed(rows)
        if row.get("average") and row["average"].strip() not in {"", "-999.99"}
    )

    date = latest.get("date", "unknown date")
    co2_value = latest["average"].strip()

    return text_response(
        f"Latest CO2 level: {co2_value} ppm on {date} "
        f"(NOAA Mauna Loa weekly average)."
    )


def get_temperature_anomaly() -> list[types.TextContent]:
    url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
    text = get_text(url)
    rows = parse_csv(text)

    month_columns = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ]

    latest_row = None
    latest_month = None
    latest_value = None

    for row in reversed(rows):
        year = row.get("Year", "").strip()

        if not year or not year.isdigit():
            continue

        for month in reversed(month_columns):
            value = row.get(month, "").strip()

            if value and value != "***":
                latest_row = row
                latest_month = month
                latest_value = value
                break

        if latest_row:
            break

    if not latest_row or not latest_month or not latest_value:
        return text_response("Could not find a valid NASA GISS temperature anomaly value.")

    year = latest_row["Year"].strip()

    return text_response(
        f"NASA GISS latest global temperature anomaly: {latest_value} C "
        f"for {latest_month} {year}."
    )


def get_sea_level() -> list[types.TextContent]:
    url = "https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv"
    text = get_text(url)
    rows = parse_csv(text)

    latest = next(
        row for row in reversed(rows)
        if row.get("NOAA Adjusted Sea Level") or row.get("CSIRO Adjusted Sea Level")
    )

    year = latest.get("Year", "unknown year")
    level = (
        latest.get("NOAA Adjusted Sea Level")
        or latest.get("CSIRO Adjusted Sea Level")
        or "unknown"
    )

    return text_response(
        f"Sea level rise: {level} inches in {year} "
        f"relative to the dataset baseline."
    )


def get_solar_data() -> list[types.TextContent]:
    url = "https://power.larc.nasa.gov/api/temporal/monthly/point"

    params = {
        "parameters": "ALLSKY_SFC_SW_DWN",
        "community": "RE",
        "longitude": -90,
        "latitude": 38,
        "start": 2024,
        "end": 2024,
        "format": "JSON",
    }

    data = get_json(url, params=params)

    values = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]

    valid_values = [
        value for value in values.values()
        if isinstance(value, int | float) and value != -999
    ]

    if not valid_values:
        return text_response("Could not find valid NASA POWER solar irradiance values.")

    average = round(sum(valid_values) / len(valid_values), 2)

    return text_response(
        f"NASA POWER solar irradiance 2024 average near latitude 38, longitude -90: "
        f"{average} kWh/m2/day."
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())