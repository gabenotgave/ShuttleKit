import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .geo import nearest_stops, walk_minutes
from .planning import fmt_hhmm, parse_hhmm, plan_shuttle


def _config_path() -> Path:
    # api/config.json — package lives in api/shuttlekit/
    return Path(__file__).resolve().parent.parent / "config.json"


def load_config() -> dict:
    path = _config_path()
    with open(path) as f:
        return json.load(f)


def load_config_service() -> dict:
    config = load_config()
    all_stops = [s for r in config["routes"] for s in r["stops"]]
    avg_lat = sum(s["coords"][0] for s in all_stops) / len(all_stops)
    avg_lng = sum(s["coords"][1] for s in all_stops) / len(all_stops)
    return {
        "campus": config["campus"],
        "map_center": {"lat": avg_lat, "lng": avg_lng},
    }


def get_agent_prompt_context(config: dict) -> dict:
    """Campus name, IANA timezone, and current local time (for agent system prompts)."""
    tz = ZoneInfo(config["timezone"])
    now = datetime.now(tz)
    return {
        "campus": config["campus"],
        "timezone": config["timezone"],
        "now_local": now.strftime("%A, %Y-%m-%d %H:%M:%S %Z"),
    }


def get_stops_service(config: dict) -> dict:
    stopsMap = {}

    for route in config["routes"]:
        for stop in route["stops"]:
            if stop["id"] in stopsMap:
                stopsMap[stop["id"]]["routes"].append(route["id"])
            else:
                stopsMap[stop["id"]] = {
                    "id": stop["id"],
                    "name": stop["name"],
                    "coords": stop["coords"],
                    "routes": [route["id"]],
                }
    return stopsMap

def get_routes_service(config: dict) -> dict:
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


def get_schedule_service(config: dict) -> dict:
    routes_out = []
    for route in config["routes"]:
        sorted_stops = sorted(route["stops"], key=lambda s: s["arrivals"][0])
        routes_out.append({
            "id": route["id"],
            "name": route["name"],
            "color": route.get("color"),
            "stops": [
                {
                    "id": stop["id"],
                    "name": stop["name"],
                    "arrivals": stop["arrivals"],
                }
                for stop in sorted_stops
            ],
        })

    return {
        "timezone": config["timezone"],
        "hours": config["hours"],
        "routes": routes_out,
    }


def get_status_service(config: dict) -> dict:
    tz = ZoneInfo(config["timezone"])
    now = datetime.now(tz)
    day = now.strftime("%A").lower()

    hours = config["hours"]

    if day not in hours:
        return {"active": False, "message": "The shuttle will not be running today"}

    start_str = hours[day]["start"]
    end_str = hours[day]["end"]

    # Parse "HH:MM" strings into today's aware datetimes using the config timezone
    start_h, start_m = map(int, start_str.split(":"))
    end_h, end_m = map(int, end_str.split(":"))
    start_time = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end_time = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    if start_time <= now <= end_time:
        return {"active": True, "message": "The shuttle is currently running"}
    else:
        return {"active": False, "message": "The shuttle is not running right now"}


def get_plan_service(
    config: dict,
    from_lat: float,
    from_lng: float,
    to_lat: float,
    to_lng: float,
    time: str):
    tz = ZoneInfo(config["timezone"])

    now = datetime.now(tz)

    # Resolve query time
    if time:
        query_minutes = parse_hhmm(time)
    else:
        query_minutes = now.hour * 60 + now.minute

    day = now.strftime("%A").lower()
    hours = config.get("hours") or {}
    if day not in hours:
        return {"message": "No shuttle service today"}

    service_end_minutes = parse_hhmm(hours[day]["end"])

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

    upcoming = plan_shuttle(
        matched_route, from_stop, to_stop, query_minutes, service_end_minutes
    )

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
