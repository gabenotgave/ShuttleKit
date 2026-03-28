import sys
from pathlib import Path
import pytest

# Add parent directory to path so we can import from api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from geo import haversine_meters, walk_minutes, nearest_stops


# Known coords from config.json
DRAYER = (40.2009, -77.1969)
WALMART = (40.1899, -77.1946)


class TestHaversineMeters:
    def test_same_point_is_zero(self):
        assert haversine_meters(40.0, -77.0, 40.0, -77.0) == 0.0

    def test_known_distance_approximate(self):
        dist = haversine_meters(*DRAYER, *WALMART)
        # Roughly 1.25 km between these two coords
        assert 1200 < dist < 1400

    def test_symmetrical(self):
        a_to_b = haversine_meters(*DRAYER, *WALMART)
        b_to_a = haversine_meters(*WALMART, *DRAYER)
        assert abs(a_to_b - b_to_a) < 0.001

    def test_returns_float(self):
        assert isinstance(haversine_meters(*DRAYER, *WALMART), float)


class TestWalkMinutes:
    def test_same_point_is_zero(self):
        assert walk_minutes(40.0, -77.0, 40.0, -77.0) == 0

    def test_rounds_up(self):
        result = walk_minutes(40.2009, -77.1969, 40.2010, -77.1970)
        assert result >= 1

    def test_known_distance(self):
        # ~1.25 km at 80 m/min = ~15.6 min → rounds up to 16
        result = walk_minutes(*DRAYER, *WALMART)
        assert result == 16

    def test_returns_int(self):
        assert isinstance(walk_minutes(*DRAYER, *WALMART), int)


class TestNearestStops:
    STOPS = [
        {"id": "a", "name": "Stop A", "coords": [40.2009, -77.1969]},
        {"id": "b", "name": "Stop B", "coords": [40.1899, -77.1946]},
        {"id": "c", "name": "Stop C", "coords": [40.2018, -77.1986]},
    ]

    def test_nearest_is_first(self):
        result = nearest_stops(self.STOPS, 40.2009, -77.1969)
        assert result[0]["id"] == "a"

    def test_returns_all_stops(self):
        result = nearest_stops(self.STOPS, 40.2009, -77.1969)
        assert len(result) == 3

    def test_sorted_by_distance(self):
        result = nearest_stops(self.STOPS, 40.2009, -77.1969)
        assert result[0]["id"] == "a"

    def test_empty_list(self):
        assert nearest_stops([], 40.0, -77.0) == []
