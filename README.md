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

```bash
pip install -r requirements-dev.txt
pytest -q
```

Tests mock all external sources and verify CSV parsing, malformed upstream responses, briefing wording, and atomic snapshot publication. The dashboard identifies each upstream provider; the generated briefing is a deterministic summary, not a scientific forecast. Source schemas can change, so production deployments should monitor `/health` and preserve the last known good snapshot.
