import sys
from pathlib import Path
import pytest

# Add parent directory to path so we can import from api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from planning import parse_hhmm, fmt_hhmm, plan_shuttle


class TestParseHhmm:
    def test_midnight(self):
        assert parse_hhmm("00:00") == 0

    def test_noon(self):
        assert parse_hhmm("12:00") == 720

    def test_with_minutes(self):
        assert parse_hhmm("06:45") == 405

    def test_end_of_day(self):
        assert parse_hhmm("23:59") == 1439


class TestFmtHhmm:
    def test_midnight(self):
        assert fmt_hhmm(0) == "00:00"

    def test_noon(self):
        assert fmt_hhmm(720) == "12:00"

    def test_with_minutes(self):
        assert fmt_hhmm(405) == "06:45"

    def test_roundtrip(self):
        assert fmt_hhmm(parse_hhmm("09:30")) == "09:30"


# Minimal route fixture matching config.json structure
ROUTE = {
    "id": "test-route",
    "name": "Test Route",
    "stops": [
        {"id": "stop-a", "name": "Stop A", "coords": [0, 0], "arrivals": ["06:00", "06:45", "07:30"]},
        {"id": "stop-b", "name": "Stop B", "coords": [0, 0], "arrivals": ["06:10", "06:55", "07:40"]},
        {"id": "stop-c", "name": "Stop C", "coords": [0, 0], "arrivals": ["06:20", "07:05", "07:50"]},
    ],
}

STOP_A = ROUTE["stops"][0]  # offset 0
STOP_B = ROUTE["stops"][1]  # offset 10
STOP_C = ROUTE["stops"][2]  # offset 20


class TestPlanShuttle:
    def test_returns_trips_after_query_time(self):
        # Query at 06:05 — first loop departs stop-b at 06:10, should be included
        result = plan_shuttle(ROUTE, STOP_B, STOP_C, parse_hhmm("06:05"))
        assert len(result) > 0
        assert result[0]["departs"] == parse_hhmm("06:10")

    def test_excludes_past_departures(self):
        # Query at 07:00 — only the 07:40 departure from stop-b remains
        result = plan_shuttle(ROUTE, STOP_B, STOP_C, parse_hhmm("07:00"))
        assert all(t["departs"] > parse_hhmm("07:00") for t in result)

    def test_no_trips_after_last_departure(self):
        result = plan_shuttle(ROUTE, STOP_A, STOP_B, parse_hhmm("08:00"))
        assert result == []

    def test_wrap_around(self):
        # from stop-c (offset 20) to stop-a (offset 0) — wraps, arrives in next loop
        result = plan_shuttle(ROUTE, STOP_C, STOP_A, parse_hhmm("06:00"))
        # loop 0: departs 360+20=380, arrives 360+0+45=405
        assert result[0]["departs"] == 380
        assert result[0]["arrives"] == 405

    def test_normal_trip_arrives_after_departs(self):
        result = plan_shuttle(ROUTE, STOP_A, STOP_C, parse_hhmm("05:50"))
        assert result[0]["arrives"] > result[0]["departs"]
