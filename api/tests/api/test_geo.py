import sys
from pathlib import Path
import pytest

# Add parent directory to path so we can import from api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from unittest.mock import MagicMock, patch

from shuttlekit.geo import haversine_meters, walk_minutes, nearest_stops, geocode_addresses


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


class TestGeocodeAddresses:
    def _make_location(self, lat, lng):
        loc = MagicMock()
        loc.latitude = lat
        loc.longitude = lng
        return loc

    @patch("shuttlekit.geo.Nominatim")
    @patch("shuttlekit.geo.RateLimiter")
    def test_returns_coords_for_known_address(self, mock_rl, mock_nom):
        mock_rl.return_value = lambda q: self._make_location(40.2009, -77.1969)
        result = geocode_addresses(["Drayer Hall, Dickinson College"])
        assert result["Drayer Hall, Dickinson College"] == [40.2009, -77.1969]

    @patch("shuttlekit.geo.Nominatim")
    @patch("shuttlekit.geo.RateLimiter")
    def test_returns_none_for_unresolved_address(self, mock_rl, mock_nom):
        mock_rl.return_value = lambda q: None
        result = geocode_addresses(["totally fake address xyzzy"])
        assert result["totally fake address xyzzy"] is None

    @patch("shuttlekit.geo.Nominatim")
    @patch("shuttlekit.geo.RateLimiter")
    def test_handles_multiple_addresses(self, mock_rl, mock_nom):
        locations = {
            "Address A": self._make_location(40.1, -77.1),
            "Address B": self._make_location(40.2, -77.2),
        }
        mock_rl.return_value = lambda q: locations.get(q)
        result = geocode_addresses(["Address A", "Address B"])
        assert result["Address A"] == [40.1, -77.1]
        assert result["Address B"] == [40.2, -77.2]

    @patch("shuttlekit.geo.Nominatim")
    @patch("shuttlekit.geo.RateLimiter")
    def test_returns_none_on_exception(self, mock_rl, mock_nom):
        def raise_exc(q):
            raise Exception("network error")
        mock_rl.return_value = raise_exc
        result = geocode_addresses(["Some Address"])
        assert result["Some Address"] is None

    @patch("shuttlekit.geo.Nominatim")
    @patch("shuttlekit.geo.RateLimiter")
    def test_empty_input(self, mock_rl, mock_nom):
        result = geocode_addresses([])
        assert result == {}

    @patch("shuttlekit.geo.Nominatim")
    @patch("shuttlekit.geo.RateLimiter")
    def test_coords_rounded_to_4_decimal_places(self, mock_rl, mock_nom):
        mock_rl.return_value = lambda q: self._make_location(40.123456789, -77.987654321)
        result = geocode_addresses(["Some Address"])
        lat, lng = result["Some Address"]
        assert lat == round(40.123456789, 4)
        assert lng == round(-77.987654321, 4)
