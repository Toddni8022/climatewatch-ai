# ClimateWatch AI

ClimateWatch AI is a small FastAPI dashboard for live climate indicators from public NASA and NOAA data sources.

## What It Shows

- Atmospheric CO2 from NOAA Mauna Loa
- Global temperature anomaly from NASA GISS
- Global mean sea level rise from the CSIRO / EPA dataset
- Solar irradiance from NASA POWER
- A short plain-English climate briefing built from the latest readings

## Project Structure

```text
dashboard/    FastAPI web app and Jinja dashboard
crew/         Optional CrewAI agent workflow
mcp_server/   MCP climate data tool server
```

## Run The Dashboard

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn dashboard.app:app --reload --port 8000
```

Open `http://127.0.0.1:8000`.

Machine-readable endpoints:

- `GET /api/data` returns the current snapshot and source status.
- `GET /health` returns service and refresh health for deployment checks.
- `POST /api/refresh` starts a non-blocking source refresh.

The dashboard refreshes data at startup and then every six hours. You can also trigger a refresh from the web UI.

If port `8000` is already busy, use another port:

```bash
python -m uvicorn dashboard.app:app --reload --port 8001
```

## Optional CrewAI Workflow

CrewAI currently supports Python 3.10 through 3.13. If you are using Python 3.14, run the dashboard normally and use Python 3.13 for this optional agent workflow.

The CrewAI workflow uses OpenRouter. Create a `.env` file with:

```text
OPENROUTER_API_KEY=your_key_here
```

Then run:

```bash
pip install -r requirements-ai.txt
python crew/crew.py
```

## Optional MCP Server

```bash
pip install -r requirements-mcp.txt
python mcp_server/climate_tools.py
```

## Verification and Data Integrity

### CrewAI-to-MCP integration smoke test

`crew_mcp_test.py` launches the local MCP server over stdio using the same
Python interpreter, discovers its tools, and gives them to a CrewAI analyst.
The analyst is asked to retrieve atmospheric CO2, identify its source, and
avoid inventing a measurement date. The adapter closes the server when done.

This is separate from the OpenRouter workflow above. It uses CrewAI's default
OpenAI provider and requires `OPENAI_API_KEY` in the process environment. It
makes a paid model request and needs internet access to the data source.
Use Python 3.12, matching the successful Windows environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-integration.txt
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", (Read-Host "OpenAI API key" -AsSecureString)).Password
$env:OPENAI_MODEL_NAME = "gpt-4.1-mini"
.\.venv\Scripts\python.exe crew_mcp_test.py
Remove-Item Env:OPENAI_API_KEY
```

Run the script directly; it is a manual smoke test, outside the `tests/`
directory used by pytest. Do not commit credentials or console logs. `.env`
files and virtual environments are ignored; this script does not load `.env`.

The user's earlier successful run discovered `get_co2_levels`,
`get_temperature_anomaly`, `get_sea_level`, and `get_solar_data`, then called
`get_co2_levels` and generated a report with 426.73 ppm. That is historical
validation of the CO2 path only, not a current reading or validation of all
four tools. The measurement date was unknown and freshness was not verified.
The script was recovered from the user's original local file; the dependency
versions above reflect that environment, rather than a complete lockfile.

### Dashboard tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests mock all external sources and verify CSV parsing, malformed upstream responses, briefing wording, and atomic snapshot publication. The dashboard identifies each upstream provider; the generated briefing is a deterministic summary, not a scientific forecast. Source schemas can change, so production deployments should monitor `/health` and preserve the last known good snapshot.
