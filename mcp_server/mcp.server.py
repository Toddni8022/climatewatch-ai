"""Compatibility launcher for the ClimateWatch MCP server.

The canonical MCP tool definitions live in mcp_server/climate_tools.py.
Run from the project root: python -m mcp_server.climate_tools
"""

import asyncio

try:
    from mcp_server.climate_tools import main
except ModuleNotFoundError:
    # Allow direct execution: python mcp_server/mcp.server.py
    from climate_tools import main


if __name__ == "__main__":
    asyncio.run(main())
