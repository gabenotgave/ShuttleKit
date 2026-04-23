import math
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in meters between two coordinates."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def walk_minutes(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    WALK_SPEED_MPM = 80  # meters per minute
    return math.ceil(haversine_meters(lat1, lng1, lat2, lng2) / WALK_SPEED_MPM)


def nearest_stops(all_stops: list, lat: float, lng: float) -> list:
    """Return stops sorted by distance to the given coordinates."""
    return sorted(all_stops, key=lambda s: haversine_meters(lat, lng, s["coords"][0], s["coords"][1]))


def geocode_addresses(addresses: list[str]) -> dict:
    """Return a mapping of address -> [lat, lng] for each address using Nominatim."""
    geolocator = Nominatim(user_agent="shuttlekit-chatbot")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    result = {}
    for address in addresses:
        try:
            location = geocode(address)
            if location:
                result[address] = [round(location.latitude, 4), round(location.longitude, 4)]
            else:
                result[address] = None
        except Exception:
            result[address] = None

    return result
