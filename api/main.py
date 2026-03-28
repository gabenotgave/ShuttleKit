import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Query
from datetime import datetime

from fastapi.middleware.cors import CORSMiddleware

from api.geo import nearest_stops, walk_minutes
from api.planning import fmt_hhmm, parse_hhmm, plan_shuttle


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



@app.get("/api/plan")
def get_plan(
    from_lat: float = Query(...),
    from_lng: float = Query(...),
    to_lat: float = Query(...),
    to_lng: float = Query(...),
    time: str = Query(default=None, description="HH:MM — defaults to now"),
):
    config = load_config()
    tz = ZoneInfo(config["timezone"])

    # Resolve query time
    if time:
        query_minutes = parse_hhmm(time)
    else:
        now = datetime.now(tz)
        query_minutes = now.hour * 60 + now.minute

    all_stops = [s for r in config["routes"] for s in r["stops"]]

    # Find nearest boarding stop; if nearest destination stop is the same, use second nearest
    from_ranked = nearest_stops(all_stops, from_lat, from_lng)
    from_stop = from_ranked[0]

    to_ranked = nearest_stops(all_stops, to_lat, to_lng)
    to_stop = to_ranked[0] if to_ranked[0]["id"] != from_stop["id"] else to_ranked[1]

    # Find a route containing both stops
    matched_route = None
    for route in config["routes"]:
        ids = [s["id"] for s in route["stops"]]
        if from_stop["id"] in ids and to_stop["id"] in ids:
            # Use the stop objects from this route (they carry arrivals)
            from_stop = route["stops"][ids.index(from_stop["id"])]
            to_stop = route["stops"][ids.index(to_stop["id"])]
            matched_route = route
            break

    if not matched_route:
        return {"message": "No route connects the nearest stops to your locations"}

    upcoming = plan_shuttle(matched_route, from_stop, to_stop, query_minutes)

    if not upcoming:
        return {"message": "No more shuttle trips tonight"}

    trip = upcoming[0]
    departs_min = trip["departs"]
    arrives_min = trip["arrives"]

    walk_to_min = walk_minutes(from_lat, from_lng, from_stop["coords"][0], from_stop["coords"][1])
    walk_from_min = walk_minutes(to_stop["coords"][0], to_stop["coords"][1], to_lat, to_lng)
    ride_min = arrives_min - departs_min
    total_min = (departs_min - query_minutes) + ride_min + walk_from_min
    arrives_at = fmt_hhmm(query_minutes + total_min)

    return {
        "legs": [
            {
                "type": "walk",
                "description": f"Walk to {from_stop['name']}",
                "duration_minutes": walk_to_min,
                "from": {"name": "Your location", "coords": [from_lat, from_lng]},
                "to": {"name": from_stop["name"], "coords": from_stop["coords"]},
            },
            {
                "type": "shuttle",
                "description": f"{matched_route['name']} shuttle",
                "departs": fmt_hhmm(departs_min),
                "arrives": fmt_hhmm(arrives_min),
                "wait_minutes": departs_min - query_minutes,
                "ride_minutes": ride_min,
                "from": {"name": from_stop["name"], "coords": from_stop["coords"]},
                "to": {"name": to_stop["name"], "coords": to_stop["coords"]},
            },
            {
                "type": "walk",
                "description": "Walk to destination",
                "duration_minutes": walk_from_min,
                "from": {"name": to_stop["name"], "coords": to_stop["coords"]},
                "to": {"name": "Your destination", "coords": [to_lat, to_lng]},
            },
        ],
        "total_minutes": total_min,
        "arrives_at": arrives_at,
    }
