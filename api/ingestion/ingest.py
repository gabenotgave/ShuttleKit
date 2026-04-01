import litellm
import os
import json
import base64
import argparse
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

load_dotenv()


def _ingestion_model() -> str | None:
    return os.getenv("INGESTION_MODEL") or os.getenv("MODEL")


def _route_ingestion_api_key(model: str | None, api_key: str | None) -> None:
    """Map INGESTION_API_KEY into the env var LiteLLM reads for the chosen provider."""
    if not api_key:
        return
    m = (model or "").strip().lower()
    if m.startswith("openai/") or m.startswith("gpt-") or m.startswith("o1") or m.startswith("o3"):
        os.environ["OPENAI_API_KEY"] = api_key
    elif m.startswith("anthropic/") or "claude" in m:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif m.startswith("groq/"):
        os.environ["GROQ_API_KEY"] = api_key
    elif m.startswith("gemini/") or m.startswith("vertex_ai/") or ("/" in m and m.split("/")[0] == "gemini"):
        os.environ["GEMINI_API_KEY"] = api_key
    else:
        # Default matches previous single-provider behavior (Gemini vision)
        os.environ["GEMINI_API_KEY"] = api_key


_route_ingestion_api_key(_ingestion_model(), os.getenv("INGESTION_API_KEY"))

MODEL = _ingestion_model()
PROMPT = """You are a JSON extraction engine. You receive a campus safety shuttle schedule. Return ONLY a single valid JSON object — no markdown fences, no commentary, no preamble, no explanation. Raw JSON only.

The output MUST follow this EXACT schema. Do not add, remove, or rename any fields. You MUST leave campus as an empty string:

{
  "campus": "",
  "timezone": "<IANA timezone string, e.g. America/New_York>",
  "routes": [
    {
      "id": "<kebab-case slug from route name, e.g. safety-shuttle>",
      "name": "<Route name as printed on the schedule>",
      "color": "<Hex color if visible, otherwise null>",
      "stops": [
        {
          "id": "<kebab-case slug from stop name, e.g. drayer-hall>",
          "name": "<Stop name exactly as printed>",
          "coords": [0.0, 0.0],
          "arrivals": ["HH:MM", "HH:MM"]
        }
      ]
    }
  ],
  "hours": {
    "<lowercase full day name>": { "start": "HH:MM", "end": "HH:MM" }
  }
}

Rules:
1. STOPS: List in the order the shuttle visits them based on the first departure cycle.
2. ARRIVALS: Every scheduled time as a flat array in 24-hour "HH:MM" format. Convert AM/PM. Expand ranges into individual times.
3. COORDS: You MUST populate coords with [latitude, longitude] for every stop. Use your best knowledge of the campus and stop name to estimate coordinates in decimal degrees. Never leave coords as an empty array — always provide your best guess. Round to 4 decimal places.
4. CAMPUS: Leave as empty string "".
5. ROUTES: Separate object for each named route. If only one unnamed route, use id "safety-shuttle" and name "Safety Shuttle".
6. COLOR: Hex color if the document uses one for the route, otherwise null.
7. HOURS: Every operating day as a separate key using full lowercase day name. "start" is earliest departure, "end" is last arrival. Omit days with no service.
8. OUTPUT: ONLY the JSON object. No text before or after. No markdown. No code fences."""


def extract_schedule(filename):
    # Support both relative path from api/ and from ingestion/ directory
    if os.path.exists(filename):
        filepath = filename
    elif os.path.exists(os.path.join("ingestion", filename)):
        filepath = os.path.join("ingestion", filename)
    else:
        filepath = filename  # Let it fail with clear error
    
    ext = filename.lower().rsplit('.', 1)[-1]

    mime_types = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp',
    }

    if ext not in mime_types:
        raise ValueError(f"Unsupported file type: {ext}")

    if not MODEL:
        raise ValueError(
            "Set INGESTION_MODEL (or legacy MODEL) in .env — e.g. gemini/gemini-1.5-flash or openai/gpt-4o"
        )

    with open(filepath, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    response = litellm.completion(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime_types[ext]};base64,{b64}"}}
            ]
        }]
    )

    text = response.choices[0].message.content.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]

    return json.loads(text.strip())


def round_coords(coords):
    """Round a [lat, lon] pair to 4 decimal places, or return [] if empty."""
    if coords and len(coords) == 2:
        return [round(coords[0], 4), round(coords[1], 4)]
    return []


def geocode_stops(config, location):
    campus = config["campus"]
    geolocator = Nominatim(user_agent="shuttle-schedule-geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.1)

    location_result = geolocator.geocode(location)
    if location_result:
        center_lat = location_result.latitude
        center_lon = location_result.longitude
        OFFSET = 0.045
        viewbox = (
            (center_lon - OFFSET, center_lat + OFFSET),
            (center_lon + OFFSET, center_lat - OFFSET),
        )
        print(f"Anchored geocoding to {location} ({center_lat:.4f}, {center_lon:.4f})")
    else:
        viewbox = None
        center_lat = center_lon = None
        print(f"Warning: Could not resolve location '{location}', geocoding without anchor")

    unique_stops = {}
    for route in config["routes"]:
        for stop in route["stops"]:
            if stop["id"] not in unique_stops:
                unique_stops[stop["id"]] = stop["name"]

    print(f"Geocoding {len(unique_stops)} unique stops near {campus}...")
    coords_cache = {}

    for stop_id, stop_name in unique_stops.items():
        queries = [
            f"{stop_name}, {campus}, {location}",
            f"{stop_name}, {location}",
            f"{stop_name}, {campus}",
        ]

        location_found = None
        for query in queries:
            try:
                location_found = geocode(
                    query,
                    viewbox=viewbox,
                    bounded=True,
                ) if viewbox else geocode(query)
            except Exception:
                pass
            if location_found:
                break

        if not location_found and viewbox:
            for query in queries:
                try:
                    location_found = geocode(query)
                except Exception:
                    pass
                if location_found:
                    break

        if location_found:
            coords_cache[stop_id] = round_coords([location_found.latitude, location_found.longitude])
            print(f"   {stop_name} → ({coords_cache[stop_id][0]}, {coords_cache[stop_id][1]}) [geocoded]")
        else:
            print(f"   {stop_name} — not found, keeping LLM coords")

    # Override with geocoded coords where found; round LLM coords for the rest
    for route in config["routes"]:
        for stop in route["stops"]:
            if stop["id"] in coords_cache:
                stop["coords"] = coords_cache[stop["id"]]
            else:
                stop["coords"] = round_coords(stop["coords"])

    found = sum(1 for c in coords_cache.values() if c)
    total = len(unique_stops)
    llm_only = total - found
    print(f"\nGeocoded {found}/{total} stops ({llm_only} using LLM coordinates)\n")
    return config


def run(filename, campus, location, do_geocode):
    print("Extracting schedule from image...")
    config = extract_schedule(filename)
    config["campus"] = campus
    print(f"  Found {sum(len(r['stops']) for r in config['routes'])} stops\n")

    if do_geocode:
        config = geocode_stops(config, location)
    else:
        # Round LLM-provided coords, keep them intact
        for route in config["routes"]:
            for stop in route["stops"]:
                stop["coords"] = round_coords(stop["coords"])
        print("Skipping geocoding; keeping LLM coordinates (use --geocode to refine)\n")

    output_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Done! Saved to {os.path.abspath(output_path)}")

    print("Please review the data in config.json to ensure accuracy. You can modify the file to make any corrections.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract shuttle schedule from image/PDF")
    parser.add_argument("file", help="Schedule file path (e.g. ingestion/schedule.png)")
    parser.add_argument("--campus", required=True, help="College name (e.g. 'Dickinson College')")
    parser.add_argument("--location", required=True, help="City/region anchor (e.g. 'Carlisle, PA')")
    parser.add_argument("--geocode", action="store_true", help="Enable geocoding to refine coordinates")
    args = parser.parse_args()

    run(args.file, args.campus, args.location, args.geocode)