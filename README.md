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
uvicorn dashboard.app:app --reload
```

Open `http://127.0.0.1:8000`.

The dashboard refreshes data at startup and then every six hours. You can also trigger a refresh from the web UI.

## Optional CrewAI Workflow

The CrewAI workflow uses OpenRouter. Create a `.env` file with:

```text
OPENROUTER_API_KEY=your_key_here
```

Then run:

```bash
python crew/crew.py
```
