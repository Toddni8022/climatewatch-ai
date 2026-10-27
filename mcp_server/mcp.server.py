from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("RackMind")

BASE_DIR = Path(__file__).resolve().parent


@mcp.tool()
def get_network_logs() -> str:
    """Read RackMind's network switch logs."""
    path = BASE_DIR / "data" / "switch.log"

    if not path.is_file():
        return "Network log file not found."

    return path.read_text(encoding="utf-8")


@mcp.tool()
def get_temperature_data() -> str:
    """Read RackMind's rack temperature data."""
    path = BASE_DIR / "data" / "rack_temperature.csv"

    if not path.is_file():
        return "Temperature data file not found."

    return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()