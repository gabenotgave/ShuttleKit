import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from shuttlekit.geo import geocode_addresses
from shuttlekit.services import (
    load_config,
    get_schedule_service,
    get_plan_service,
)


load_dotenv()

# Default 8001 so uvicorn (main:app) can use 8000 without clashing.
_mcp_port = int(os.getenv("MCP_PORT", "8001"))

mcp = FastMCP("ShuttleKit", port=_mcp_port)
_config = load_config()


@mcp.tool()
def get_schedule() -> dict:
    """
    Single source for shuttle data: campus name, whether service is active right now,
    per-day operating hours, timezone, every stop (id, name, coordinates, route ids),
    and every route with its timetable. Each route includes `runs`: each run is one
    full loop in stop order — all `arrival` times in one run are the same physical
    trip. Use `stops` to match user language to stop ids and to read coordinates.
    Each stop has `arrivals` (24h) and `arrivals_12` (US 12-hour); each `runs` entry
    lists `arrival` + `arrival_12` per stop; `hours` includes `start_12` / `end_12`.
    Prefer those `*_12` fields for user-facing times. `quick_next` reflects **today**
    after cancellations (next arrival hints). Full `routes` / `runs` / `arrivals_12` are
    the recurring weekly timetable—use them for any day unless `disruption_alerts` says
    otherwise. `get_trip` applies cancellations for the requested trip time.
    `disruption_alerts`: active/upcoming windows (optional `route_id`, `message`).
    """
    return get_schedule_service(_config, apply_disruptions=True)


@mcp.tool()
def get_trip(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
    time: str = "",
) -> dict:
    """
    Plan a shuttle trip between two lat/lng points. Returns walk + shuttle + walk
    legs with wait time, ride duration, and arrival. `time` is optional query time
    in HH:MM (24-hour); omit or pass empty for now.

    For shuttle stops by name, get coordinates from `get_schedule` → `stops` (by id).
    For street addresses or off-network places, use `get_coords_by_addresses` first.
    """
    return get_plan_service(
        _config,
        from_lat=from_lat,
        from_lng=from_lng,
        to_lat=to_lat,
        to_lng=to_lng,
        time=time,
    )


@mcp.tool()
def get_coords_by_addresses(addresses: list[str]) -> dict:
    """
    Geocode free-text addresses or place names to [lat, lng]. Use for locations
    that are not shuttle stops. For stop names on the shuttle, use `get_schedule`
    and match against `stops` instead — geocoding can return unrelated global hits.
    """
    return geocode_addresses(addresses)


if __name__ == "__main__":
    mcp.run(transport="sse")
