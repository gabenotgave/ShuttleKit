import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

from .geo import nearest_stops, walk_minutes
from .planning import fmt_hhmm, parse_hhmm, plan_shuttle


def _config_path() -> Path:
    # api/config.json — package lives in api/shuttlekit/
    return Path(__file__).resolve().parent.parent / "config.json"


def _disruptions_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "disruptions.json"


def load_disruptions() -> list[dict]:
    path = _disruptions_path()
    if not path.exists():
        return []
    with open(path) as f:
        return list(json.load(f).get("disruptions", []))


def save_disruptions(disruptions: list[dict]) -> None:
    path = _disruptions_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"disruptions": disruptions}, f, indent=2)


def _parse_local_dt(s: str, tz: ZoneInfo) -> datetime:
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=tz)


def _cancelled_run_indices_for_route(
    route: dict, items: list[dict], tz: ZoneInfo, day: date
) -> set[int]:
    # Must match plan_shuttle: loop index k is the k-th departure at route["stops"][0].
    stops = route["stops"]
    if not stops:
        return set()
    n = min(len(s["arrivals"]) for s in stops)
    cancelled: set[int] = set()
    anchor = stops[0]
    for i in range(n):
        h, m = map(int, anchor["arrivals"][i].split(":"))
        anchor_dt = datetime.combine(day, time(h, m), tzinfo=tz)
        for d in items:
            if d.get("kind", "cancellation") != "cancellation":
                continue
            rid = d.get("route_id")
            if rid is not None and rid != route["id"]:
                continue
            start = _parse_local_dt(d["start_local"], tz)
            end = _parse_local_dt(d["end_local"], tz)
            if start <= anchor_dt <= end:
                cancelled.add(i)
    return cancelled


def _config_with_effective_routes(
    config: dict, items: list[dict], tz: ZoneInfo, day: date
) -> dict:
    if not items:
        return config
    routes: list[dict] = []
    for route in config["routes"]:
        cancelled = _cancelled_run_indices_for_route(route, items, tz, day)
        new_stops = [
            {
                **stop,
                "arrivals": [
                    a for j, a in enumerate(stop["arrivals"]) if j not in cancelled
                ],
            }
            for stop in route["stops"]
        ]
        routes.append({**route, "stops": new_stops})
    return {**config, "routes": routes}


def _disruption_alerts(items: list[dict], tz: ZoneInfo, now: datetime) -> dict:
    active: list[dict] = []
    upcoming: list[dict] = []
    horizon = now + timedelta(hours=24)
    for d in items:
        if d.get("kind", "cancellation") != "cancellation":
            continue
        start = _parse_local_dt(d["start_local"], tz)
        end = _parse_local_dt(d["end_local"], tz)
        row = {
            "id": d.get("id", ""),
            "route_id": d.get("route_id"),
            "message": d.get("message", ""),
            "start_local": d["start_local"],
            "end_local": d["end_local"],
        }
        if start <= now <= end:
            active.append(row)
        elif now < start <= horizon:
            upcoming.append(row)
    return {"active": active, "upcoming": upcoming}


def add_disruption_row(
    *,
    route_id: str | None,
    start_local: str,
    end_local: str,
    message: str,
    kind: str = "cancellation",
) -> dict:
    items = load_disruptions()
    row = {
        "id": str(uuid.uuid4()),
        "route_id": route_id,
        "start_local": start_local,
        "end_local": end_local,
        "message": message.strip(),
        "kind": kind,
    }
    items.append(row)
    save_disruptions(items)
    return row


def delete_disruption_row(disruption_id: str) -> bool:
    items = load_disruptions()
    n = len(items)
    items = [d for d in items if d.get("id") != disruption_id]
    if len(items) == n:
        return False
    save_disruptions(items)
    return True


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
    """Campus name, IANA timezone, current local time, and disruption summary for prompts."""
    tz = ZoneInfo(config["timezone"])
    now = datetime.now(tz)
    items = load_disruptions()
    alerts = _disruption_alerts(items, tz, now)
    parts: list[str] = []
    for a in alerts["active"]:
        msg = (a.get("message") or "").strip() or "Cancellation"
        rid = a.get("route_id")
        scope = f" route={rid}" if rid else " (all routes)"
        parts.append(f"ACTIVE{scope}: {msg} ({a['start_local']}–{a['end_local']})")
    for u in alerts["upcoming"]:
        msg = (u.get("message") or "").strip() or "Cancellation"
        rid = u.get("route_id")
        scope = f" route={rid}" if rid else " (all routes)"
        parts.append(f"UPCOMING{scope}: {msg} ({u['start_local']}–{u['end_local']})")
    disruption_note = (
        "; ".join(parts)
        if parts
        else "No active or upcoming disruptions in the next 24 hours."
    )
    return {
        "campus": config["campus"],
        "timezone": config["timezone"],
        # 12-hour clock so the agent context matches “reply in AM/PM” instructions
        "now_local": now.strftime("%A, %Y-%m-%d %I:%M:%S %p %Z"),
        "disruption_note": disruption_note,
    }


def get_disruptions_public(config: dict) -> dict:
    """Active + upcoming (24h) for the site banner; same window as agent alerts."""
    tz = ZoneInfo(config["timezone"])
    now = datetime.now(tz)
    return _disruption_alerts(load_disruptions(), tz, now)


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


def _hhmm_to_12h_us(hhmm: str) -> str:
    """Schedule uses 24h 'HH:MM'; return US 12-hour with AM/PM (no leading zero on hour)."""
    h, mi = map(int, hhmm.split(":"))
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{mi:02d} {suffix}"


def _hours_with_12h(hours: dict) -> dict:
    """Add start_12 / end_12 next to existing HH:MM strings (additive)."""
    out: dict = {}
    for day, span in hours.items():
        out[day] = {
            **span,
            "start_12": _hhmm_to_12h_us(span["start"]),
            "end_12": _hhmm_to_12h_us(span["end"]),
        }
    return out


def _build_quick_next(config: dict, now: datetime, now_m: int) -> dict:
    """
    Lean hint: first upcoming arrival at each stop (>= now) plus run index.
    Full lists of times use `arrivals` / `arrivals_12` and `runs` with `arrival_12`.
    """
    per_route: list[dict] = []
    for route in config["routes"]:
        sorted_stops = sorted(route["stops"], key=lambda s: s["arrivals"][0])
        runs = _runs_for_route(sorted_stops)
        by_stop_id: dict[str, dict] = {}

        for j, stop in enumerate(sorted_stops):
            sid = stop["id"]
            next_run: dict | None = None
            for run in runs:
                arr = run["stops"][j]["arrival"]
                if parse_hhmm(arr) >= now_m:
                    next_run = run
                    break

            if next_run is None:
                by_stop_id[sid] = {
                    "stop_name": stop["name"],
                    "next_arrival_24": None,
                    "next_arrival_12": None,
                    "run_index_for_next": None,
                }
            else:
                arr_next = next_run["stops"][j]["arrival"]
                by_stop_id[sid] = {
                    "stop_name": stop["name"],
                    "next_arrival_24": arr_next,
                    "next_arrival_12": _hhmm_to_12h_us(arr_next),
                    "run_index_for_next": next_run["index"],
                }

        per_route.append(
            {
                "route_id": route["id"],
                "route_name": route["name"],
                "by_stop_id": by_stop_id,
            }
        )

    return {
        "as_of_local": now.strftime("%A, %Y-%m-%d %I:%M:%S %p %Z"),
        "as_of_hhmm_24": f"{now.hour:02d}:{now.minute:02d}",
        "per_route": per_route,
    }


def _runs_for_route(sorted_stops: list[dict]) -> list[dict]:
    """
    One entry per shuttle loop: same index across each stop's arrivals array is one
    physical trip. Exposed so agents cannot mix times from different loops.
    """
    if not sorted_stops:
        return []
    n = min(len(s["arrivals"]) for s in sorted_stops)
    runs: list[dict] = []
    for i in range(n):
        runs.append(
            {
                "index": i,
                "stops": [
                    {
                        "id": stop["id"],
                        "name": stop["name"],
                        "arrival": stop["arrivals"][i],
                        "arrival_12": _hhmm_to_12h_us(stop["arrivals"][i]),
                    }
                    for stop in sorted_stops
                ],
            }
        )
    return runs


def _schedule_payload(config: dict, now: datetime, now_m: int) -> dict:
    routes_out = []
    for route in config["routes"]:
        sorted_stops = sorted(route["stops"], key=lambda s: s["arrivals"][0])
        routes_out.append(
            {
                "id": route["id"],
                "name": route["name"],
                "color": route.get("color"),
                "stops": [
                    {
                        "id": stop["id"],
                        "name": stop["name"],
                        "arrivals": stop["arrivals"],
                        "arrivals_12": [
                            _hhmm_to_12h_us(a) for a in stop["arrivals"]
                        ],
                    }
                    for stop in sorted_stops
                ],
                "runs": _runs_for_route(sorted_stops),
            }
        )

    return {
        "campus": config["campus"],
        "timezone": config["timezone"],
        "hours": _hours_with_12h(config["hours"]),
        "status": get_status_service(config),
        "stops": get_stops_service(config),
        "routes": routes_out,
        "quick_next": _build_quick_next(config, now, now_m),
    }


def get_schedule_service(config: dict, *, apply_disruptions: bool = False) -> dict:
    """
    Static timetable by default (REST /schedule). When apply_disruptions=True (MCP),
    routes/hours stay the full weekly poster (date-specific cancellations must not
    shrink tomorrow's columns). `quick_next` uses today's effective timetable only;
    `get_plan_service` still skips cancelled loops for trip planning.
    """
    tz = ZoneInfo(config["timezone"])
    now = datetime.now(tz)
    now_m = now.hour * 60 + now.minute
    if apply_disruptions:
        items = load_disruptions()
        out = _schedule_payload(config, now, now_m)
        out["disruption_alerts"] = _disruption_alerts(items, tz, now)
        if items:
            eff = _config_with_effective_routes(config, items, tz, now.date())
            out["quick_next"] = _build_quick_next(eff, now, now_m)
        return out
    return _schedule_payload(config, now, now_m)


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

    disruptions = load_disruptions()
    cancelled = _cancelled_run_indices_for_route(
        matched_route, disruptions, tz, now.date()
    )
    upcoming = plan_shuttle(
        matched_route,
        from_stop,
        to_stop,
        query_minutes,
        service_end_minutes,
        cancelled_run_indices=cancelled,
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
