import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from shuttlekit.services import get_schedule_service


MINIMAL_CONFIG = {
    "campus": "Test U",
    "timezone": "America/New_York",
    "hours": {"monday": {"start": "18:00", "end": "23:50"}},
    "routes": [
        {
            "id": "loop-a",
            "name": "Loop A",
            "stops": [
                {"id": "a", "name": "A", "coords": [0, 0], "arrivals": ["20:00", "21:00"]},
                {"id": "b", "name": "B", "coords": [0, 0], "arrivals": ["20:30", "21:30"]},
            ],
        }
    ],
}


def test_get_schedule_includes_stops_status_and_runs():
    out = get_schedule_service(MINIMAL_CONFIG)
    assert out["campus"] == "Test U"
    assert "quick_next" in out and "per_route" in out["quick_next"]
    assert "active" in out["status"]
    assert "a" in out["stops"] and out["stops"]["a"]["coords"] == [0, 0]
    route = out["routes"][0]
    assert len(route["runs"]) == 2
    assert [s["arrival"] for s in route["runs"][0]["stops"]] == ["20:00", "20:30"]
    assert [s["arrival_12"] for s in route["runs"][0]["stops"]] == ["8:00 PM", "8:30 PM"]
    assert [s["arrival"] for s in route["runs"][1]["stops"]] == ["21:00", "21:30"]
    assert route["stops"][0]["arrivals_12"] == ["8:00 PM", "9:00 PM"]
    assert out["hours"]["monday"]["start_12"] == "6:00 PM"
    assert out["hours"]["monday"]["end_12"] == "11:50 PM"


def test_quick_next_lean_and_arrivals_12_for_lists():
    """Next after 20:25 at B is 8:30 PM; 19:20 displays as 7:20 PM in arrivals_12."""
    fixed = datetime(2026, 4, 1, 20, 25, 0, tzinfo=ZoneInfo("America/New_York"))
    with patch("shuttlekit.services.datetime") as mock_dt:
        mock_dt.now.return_value = fixed
        out = get_schedule_service(MINIMAL_CONFIG)
    by_stop = out["quick_next"]["per_route"][0]["by_stop_id"]
    assert by_stop["b"]["next_arrival_24"] == "20:30"
    assert by_stop["b"]["next_arrival_12"] == "8:30 PM"
    assert set(by_stop["b"].keys()) == {"stop_name", "next_arrival_24", "next_arrival_12", "run_index_for_next"}

    one_slot = {
        "campus": "X",
        "timezone": "America/New_York",
        "hours": {"wednesday": {"start": "18:00", "end": "23:50"}},
        "routes": [
            {
                "id": "r1",
                "name": "R",
                "stops": [
                    {
                        "id": "w",
                        "name": "W",
                        "coords": [0, 0],
                        "arrivals": ["19:20", "20:50"],
                    },
                ],
            }
        ],
    }
    fixed2 = datetime(2026, 4, 1, 18, 0, 0, tzinfo=ZoneInfo("America/New_York"))
    with patch("shuttlekit.services.datetime") as mock_dt:
        mock_dt.now.return_value = fixed2
        out2 = get_schedule_service(one_slot)
    w = out2["quick_next"]["per_route"][0]["by_stop_id"]["w"]
    assert w["next_arrival_12"] == "7:20 PM"
    assert out2["routes"][0]["stops"][0]["arrivals_12"] == ["7:20 PM", "8:50 PM"]
