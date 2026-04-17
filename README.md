\# ClimateWatch AI



Real-time climate intelligence platform powered by MCP, CrewAI, and NASA/NOAA APIs.



\## What It Does

\- Pulls live CO2, temperature, sea level, and solar data from NASA and NOAA

\- Routes data through a 3-agent CrewAI pipeline (collector, analyst, report writer)

\- Serves findings to a FastAPI web dashboard with AI-generated daily briefings

\- Auto-refreshes every 6 hours via APScheduler



\## Tech Stack

\- MCP SDK — custom climate data tool server

\- CrewAI — multi-agent orchestration

\- Claude Haiku via OpenRouter — LLM backbone

\- FastAPI + Jinja2 — web dashboard

\- NASA GISS, NOAA, CSIRO, NASA Power — live data sources



\## Run It

pip install crewai crewai-tools fastapi uvicorn jinja2 apscheduler requests python-dotenv

uvicorn dashboard.app:app --reload

