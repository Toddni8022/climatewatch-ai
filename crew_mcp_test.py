import sys
from pathlib import Path

from crewai import Agent, Task, Crew
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

PROJECT_DIR = Path(__file__).resolve().parent

server_params = StdioServerParameters(
    command=sys.executable,
    args=["-m", "mcp_server.climate_tools"],
    cwd=str(PROJECT_DIR),
)

with MCPServerAdapter(server_params) as tools:

    print("Connected MCP tools:")
    for tool in tools:
        print(tool.name)

    agent = Agent(
        role="Climate Research Analyst",
        goal="Answer climate questions using real data",
        backstory=(
            "You analyze climate measurements using "
            "tools provided by an MCP server."
        ),
        tools=tools,
        verbose=True,
    )

    task = Task(
        description=(
            "Find the latest atmospheric CO2 measurement "
            "using the available MCP tools. "
            "Explain the result and identify its source. "
            "Do not invent a measurement date."
        ),
        expected_output="A short climate data report.",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )

    result = crew.kickoff()

    print("\nFINAL RESULT:")
    print(result)