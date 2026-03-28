import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ShuttleKit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def load_config() -> dict:
    path = Path(__file__).parent.parent / "config.json"
    with open(path) as f:
        return json.load(f)


@app.get("/api/stops")
def get_stops():
    stopsMap = {}

    config = load_config()

    for route in config["routes"]:
        for stop in route["stops"]:
            if stop["id"] in stopsMap:
                stopsMap[stop["id"]["routes"].append(route["id"])]
            else:
                stopsMap[stop["id"]] = {
                    "id": stop["id"],
                    "name": stop["name"],
                    "coords": stop["coords"],
                    "routes": [route["id"]],
                }
    return stopsMap

print(get_stops())


@app.get("/api/routes")
def get_routes():

    try:
        config = load_config()
    except FileNotFoundError:
        return {"error": "Schedule file not found"}, 404
    
    routes = []
    for route in config["routes"]:
        sorted_stops = sorted(route["stops"], key=lambda s: s["arrivals"][0])
        routes.append({
            "id": route["id"],
            "name": route["name"],
            "color": route.get("color"),
            "path": [stop["coords"] for stop in sorted_stops]
        })
    return routes

@app.get("/api/status")
def get_status():
    
    config = load_config()
    tz = datetime.now().astimezone().tzinfo
    message = {}
    timeNow = datetime.now(tz)
    day = datetime.now().strftime("%A").lower()

    hours = config["hours"]

    if day is not hours:
        message = {"active": False, "message": "The bus will not be running today"}
        return message  
    
    start = config["hours"]["saturday"]["start"]
    end = config["hours"]["saturday"]["end"]

    if timeNow >= start and timeNow <= end: 
        message = {"active": True, "message": "The shuttle is currently running"}

    return message

print(get_status())



def parse_hhmm(s: str) -> int:
    """Return total minutes since midnight for a HH:MM string."""
    h, m = map(int, s.split(":"))
    return h * 60 + m


def fmt_hhmm(minutes: int) -> str:
    """Format total minutes since midnight as HH:MM."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@app.get("/api/plan")
def get_plan(
    from_stop_id: str = Query(..., alias="from"),
    to_stop_id: str = Query(..., alias="to"),
    time: str = Query(default=None, description="HH:MM — defaults to now"),
):
    if from_stop_id == to_stop_id:
        raise HTTPException(status_code=400, detail="Source and destination cannot be the same")

    config = load_config()
    tz = ZoneInfo(config["timezone"])

    # Resolve query time
    if time:
        query_minutes = parse_hhmm(time)
    else:
        now = datetime.now(tz)
        query_minutes = now.hour * 60 + now.minute

    # Find a route containing both stops
    matched_route = None
    from_stop = to_stop = None
    for route in config["routes"]:
        stops = route["stops"]
        stop_ids = [s["id"] for s in stops]
        if from_stop_id in stop_ids and to_stop_id in stop_ids:
            matched_route = route
            from_stop = stops[stop_ids.index(from_stop_id)]
            to_stop = stops[stop_ids.index(to_stop_id)]
            break

    if not matched_route:
        all_stop_ids = {s["id"] for r in config["routes"] for s in r["stops"]}
        if from_stop_id not in all_stop_ids:
            raise HTTPException(status_code=400, detail=f"Unknown stop: {from_stop_id}")
        if to_stop_id not in all_stop_ids:
            raise HTTPException(status_code=400, detail=f"Unknown stop: {to_stop_id}")
        raise HTTPException(status_code=400, detail="No route connects these two stops")

    # Derive loop parameters from the first stop's arrivals
    anchor_arrivals = matched_route["stops"][0]["arrivals"]
    first_dep = parse_hhmm(anchor_arrivals[0])
    last_dep = parse_hhmm(anchor_arrivals[-1])
    interval = parse_hhmm(anchor_arrivals[1]) - first_dep

    # Derive per-stop offsets relative to the anchor stop
    from_offset = parse_hhmm(from_stop["arrivals"][0]) - first_dep
    to_offset = parse_hhmm(to_stop["arrivals"][0]) - first_dep
    wraps = to_offset < from_offset  # passenger rides past loop start

    # Generate all departures after query time, take first two
    upcoming = []
    loop_start = first_dep
    while loop_start <= last_dep:
        # Set depart and arrive offset for specific stops
        departs = loop_start + from_offset
        arrives = loop_start + to_offset + (interval if wraps else 0)
        if departs > query_minutes:
            upcoming.append({
                "route": matched_route["name"],
                "departs": fmt_hhmm(departs),
                "arrives": fmt_hhmm(arrives),
                "wait_minutes": departs - query_minutes,
            })
        loop_start += interval

    if not upcoming:
        return {"message": "No more trips tonight"}

    result = {"from": from_stop["name"], "to": to_stop["name"], "next": upcoming[0]}
    if len(upcoming) >= 2:
        result["backup"] = upcoming[1]
    return result
