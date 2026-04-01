import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from shuttlekit.geo import geocode_addresses
from shuttlekit.services import (
    load_config,
    get_stops_service,
    get_routes_service,
    get_schedule_service,
    get_status_service,
    get_plan_service,
)


load_dotenv()

# Default 8001 so uvicorn (main:app) can use 8000 without clashing.
_mcp_port = int(os.getenv("MCP_PORT", "8001"))

mcp = FastMCP("ShuttleKit", port=_mcp_port)
_config = load_config()


@mcp.tool()
def get_status() -> dict:
    """
    Check whether the shuttle is currently running. Returns active (bool) and a
    human-readable message. Call this first when a user asks if the shuttle is
    running, available, or operating right now.
    """
    return get_status_service(_config)


@mcp.tool()
def get_stops() -> dict:
    """
    Get all shuttle stops, keyed by stop ID. Each stop includes its name,
    coordinates [lat, lng], and which route IDs serve it. Use this to look up
    stop IDs or coordinates when a user refers to a stop by name, or to list
    all available stops.
    """
    return get_stops_service(_config)


@mcp.tool()
def get_routes() -> dict:
    """
    Get all shuttle routes with their IDs, names, colors, and ordered path
    coordinates. Use this when a user asks about available routes, route names,
    or wants to know where a route goes.
    """
    return get_routes_service(_config)


@mcp.tool()
def get_schedule() -> dict:
    """
    Get the full shuttle timetable — all routes with their stops and every
    scheduled arrival time in HH:MM (24-hour) format. Also includes operating
    hours per day and the campus timezone. Use this when a user asks what time
    the shuttle arrives somewhere, how often it runs, or what the full schedule is.
    """
    return get_schedule_service(_config)


@mcp.tool()
def get_trip(
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
    time: str) -> dict:
    """
    Plan a shuttle trip between two locations given as coordinates. Returns a
    multi-leg itinerary with walk and shuttle segments, including departure time,
    wait time, ride duration, and estimated arrival. The time parameter is optional
    in HH:MM 24-hour format and defaults to now if omitted.

    This tool requires lat/lng coordinates — if the user provides an address or
    place name instead, call get_coords_by_addresses first to resolve coordinates.
    If they refer to a stop by name, call get_stops first to find its coordinates.
    """
    return get_plan_service(
        _config,
        from_lat=from_lat,
        from_lng=from_lng,
        to_lat=to_lat,
        to_lng=to_lng,
        time=time
    )


@mcp.tool()
def get_coords_by_stops(stop_ids: list[str]) -> dict:
    """
    Look up full stop details (name, coordinates, routes) for a list of stop IDs.
    Use this when you already know the stop ID and need its coordinates to pass
    to get_trip, or to confirm details about a specific stop.
    """
    stops_data = get_stops_service(_config)
    result = {}
    for stop_id in stop_ids:
        if stop_id in stops_data:
            result[stop_id] = stops_data[stop_id]
    return result


@mcp.tool()
def get_coords_by_addresses(addresses: list[str]) -> dict:
    """
    Geocode a list of free-text addresses or place names into coordinates.
    Returns a mapping of address -> [lat, lng], or null if a location could not
    be resolved. Use this when a user provides a location by name or address
    rather than coordinates, before calling get_trip.
    """
    return geocode_addresses(addresses)


if __name__ == "__main__":
    mcp.run(transport="sse")
