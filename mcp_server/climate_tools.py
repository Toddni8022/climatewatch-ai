
import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("climate-tools")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_co2_levels",
            description="Get the latest atmospheric CO2 levels from NOAA Mauna Loa",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get_temperature_anomaly",
            description="Get global temperature anomaly data from NASA GISS",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get_sea_level",
            description="Get global mean sea level rise data",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        types.Tool(
            name="get_solar_data",
            description="Get solar irradiance data from NASA Power",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_co2_levels":
        url = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_weekly_mlo.csv"
        response = requests.get(url)
        lines = [l for l in response.text.strip().split("\n") if not l.startswith("#")]
        latest = lines[-1].split(",")
        co2_value = latest[4].strip()
        return [types.TextContent(type="text", text=f"Latest CO2 level: {co2_value} ppm (NOAA Mauna Loa)")]

    elif name == "get_temperature_anomaly":
        url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
        response = requests.get(url)
        lines = [l for l in response.text.strip().split("\n") if not l.startswith("#")]
        latest = lines[-1].split(",")
        year = latest[0].strip()
        jan = latest[1].strip()
        return [types.TextContent(type="text", text=f"NASA GISS Temperature Anomaly - Year: {year}, Jan: {jan}°C above baseline")]

    elif name == "get_sea_level":
        url = "https://raw.githubusercontent.com/datasets/sea-level-rise/master/data/epa-sea-level.csv"
        response = requests.get(url)
        lines = response.text.strip().split("\n")
        latest = lines[-1].split(",")
        year = latest[0].strip()
        level = latest[1].strip()
        return [types.TextContent(type="text", text=f"Sea Level Rise - Year: {year}, Level: {level} inches above 1993 baseline")]

    elif name == "get_solar_data":
        url = "https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude=-90&latitude=38&start=2024&end=2024&format=JSON"
        response = requests.get(url)
        data = response.json()
        values = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]
        avg = round(sum(values.values()) / len(values), 2)
        return [types.TextContent(type="text", text=f"NASA Power Solar Irradiance 2024 avg: {avg} kWh/m²/day")]

    return [types.TextContent(type="text", text="Tool not found")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())