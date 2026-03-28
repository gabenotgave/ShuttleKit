# ShuttleKit

A campus shuttle planning system with a FastAPI backend and Next.js frontend. Given a user's coordinates and destination, ShuttleKit finds the nearest stops, computes walk times using the Haversine formula, and returns a full itinerary with walk and shuttle legs displayed on an interactive map.

---

## Features

- Real-time trip planning with walk + shuttle legs
- Interactive Google Maps display with labeled pins
- Shuttle status indicator (active/inactive based on schedule)
- Configurable campus, routes, stops, and hours via `config.json`
- RESTful API with FastAPI
- Modern Next.js frontend with TypeScript and Tailwind CSS

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)
- Google Maps API key

### Installation

```bash
# Clone the repo
git clone https://github.com/gabenotgave/ShuttleKit.git
cd ShuttleKit

# Backend setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd web
npm install
```

### Configuration

1. **Backend environment** — Copy `.env.example` to `.env` and add your API key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env`:
   ```
   INGESTION_API_KEY=your_api_key_here
   MODEL=gemini/gemini-1.5-flash
   ```

2. **Frontend environment** — Copy `web/.env.local.example` to `web/.env.local`:
   ```bash
   cp web/.env.local.example web/.env.local
   ```
   Edit `web/.env.local`:
   ```
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```

3. **Campus configuration** — Update `config.json` with your campus name, timezone, routes, stops, and hours.

### Running the Application

**Backend (API):**
```bash
uvicorn api.main:app --reload
```
API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**Frontend:**
```bash
cd web
npm run dev
```
Frontend available at `http://localhost:3000`.

---

## API Reference

### `GET /api/config`

Returns campus configuration.

**Response:**
```json
{
  "campus": "Dickinson College",
  "map_center": { "lat": 40.2009, "lng": -77.1969 }
}
```

### `GET /api/status`

Returns shuttle operational status based on current day/time.

**Response:**
```json
{
  "active": true,
  "message": "The shuttle is currently running"
}
```

### `GET /api/stops`

Returns all stops with their routes.

**Response:**
```json
{
  "drayer-hall": {
    "id": "drayer-hall",
    "name": "DRAYER HALL",
    "coords": [40.201, -77.197],
    "routes": ["safety-shuttle"]
  }
}
```

### `GET /api/routes`

Returns all routes with their paths for map display.

**Response:**
```json
[
  {
    "id": "safety-shuttle",
    "name": "Safety Shuttle",
    "color": null,
    "path": [[40.201, -77.197], [40.2002, -77.1986], ...]
  }
]
```

### `GET /api/plan`

Returns a step-by-step itinerary from origin to destination.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_lat` | float | yes | Origin latitude |
| `from_lng` | float | yes | Origin longitude |
| `to_lat` | float | yes | Destination latitude |
| `to_lng` | float | yes | Destination longitude |
| `time` | string | no | Departure time as `HH:MM` (24-hour). Defaults to current time. |

**Example request:**
```
GET /api/plan?from_lat=40.2009&from_lng=-77.1969&to_lat=40.1894&to_lng=-77.1943&time=18:10
```

**Example response:**
```json
{
  "legs": [
    {
      "type": "walk",
      "description": "Walk to DRAYER HALL",
      "duration_minutes": 1,
      "from": { "name": "Your location", "coords": [40.2009, -77.1969] },
      "to": { "name": "DRAYER HALL", "coords": [40.201, -77.197] }
    },
    {
      "type": "shuttle",
      "description": "Safety Shuttle shuttle",
      "departs": "18:45",
      "arrives": "19:20",
      "wait_minutes": 35,
      "ride_minutes": 35,
      "from": { "name": "DRAYER HALL", "coords": [40.201, -77.197] },
      "to": { "name": "WALMART", "coords": [40.1894, -77.1943] }
    },
    {
      "type": "walk",
      "description": "Walk to destination",
      "duration_minutes": 1,
      "from": { "name": "WALMART", "coords": [40.1894, -77.1943] },
      "to": { "name": "Your destination", "coords": [40.1894, -77.1943] }
    }
  ],
  "total_minutes": 37,
  "arrives_at": "19:21"
}
```

**Error response:**
```json
{ "message": "No more shuttle trips tonight" }
```

---

## Schedule Ingestion

ShuttleKit includes an automated ingestion tool that extracts shuttle schedules from images or PDFs using LLM vision models and optionally geocodes stop locations.

### Prerequisites

- Python dependencies: `litellm`, `geopy`, `python-dotenv`
- API key for a vision-capable model (e.g., Gemini, GPT-4 Vision)

### Setup

1. Install additional dependencies:
   ```bash
   pip install litellm geopy python-dotenv
   ```

2. Configure your API key in `.env` (see Configuration section above)

3. Place your schedule file (PDF, PNG, JPG, WEBP) in the `ingestion/` folder.

### Usage

```bash
python ingestion/ingest.py <filename> --campus "Campus Name" --location "City, State" [--geocode]
```

**Arguments:**
- `filename` — Schedule file in `ingestion/` folder (e.g., `schedule.png`)
- `--campus` — Full campus name (e.g., `"Dickinson College"`)
- `--location` — City/region for geocoding anchor (e.g., `"Carlisle, PA"`)
- `--geocode` — (Optional) Enable geocoding to refine stop coordinates via OpenStreetMap

**Example:**
```bash
python ingestion/ingest.py schedule.pdf --campus "Dickinson College" --location "Carlisle, PA" --geocode
```

**Output:**
- Generates/overwrites `config.json` with extracted routes, stops, times, and coordinates
- Without `--geocode`: Uses LLM-estimated coordinates
- With `--geocode`: Attempts to geocode each stop via Nominatim (OpenStreetMap)

**Important:** Always review the generated `config.json` for accuracy. The LLM may misinterpret schedules, and geocoding may return incorrect locations. Manual verification is recommended.

---

## Testing

Unit tests cover the geo and planning modules using pytest.

```bash
pytest tests/api/ -v
```

**Coverage:**
- `api/geo.py` — Haversine distance, walk time, nearest stop sorting
- `api/planning.py` — Time parsing/formatting, loop generation, wrap-around logic

---

## Configuration

Routes, stops, and hours are defined in `config.json` at the project root.

**Structure:**
```json
{
  "campus": "Your Campus Name",
  "timezone": "America/New_York",
  "routes": [
    {
      "id": "route-id",
      "name": "Route Name",
      "color": "#3b82f6",
      "stops": [
        {
          "id": "stop-id",
          "name": "STOP NAME",
          "coords": [lat, lng],
          "arrivals": ["18:00", "18:45", "19:30", ...]
        }
      ]
    }
  ],
  "hours": {
    "monday": { "start": "18:00", "end": "23:50" },
    "tuesday": { "start": "18:00", "end": "23:50" }
  }
}
```

**Notes:**
- All times use 24-hour format (`HH:MM`)
- Loop interval and stop offsets are derived automatically from arrivals
- Frontend fetches campus name and map center from the API

---

## Project Structure

```
api/
  main.py        # FastAPI app and endpoints
  geo.py         # Haversine distance and nearest-stop logic
  planning.py    # Shuttle loop planning logic
web/
  app/           # Next.js app router pages
  components/    # React components (map, search, itinerary, navbar)
  lib/           # API client and utilities
  public/        # Static assets
tests/
  api/           # pytest unit tests
  postman/       # Postman collection
config.json      # Route and stop definitions
```

---

## License

MIT
