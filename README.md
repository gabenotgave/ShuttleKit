# ShuttleKit

A campus shuttle planning API for Dickinson College. Given a user's coordinates and destination, ShuttleKit finds the nearest stops, computes walk times using the Haversine formula, and returns a full itinerary with walk and shuttle legs.

Built with FastAPI. Frontend (Vite) in progress.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js (for the frontend, coming soon)

### Installation

```bash
# Clone the repo
git clone https://github.com/gabenotgave/ShuttleKit.git
cd ShuttleKit

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
uvicorn api.main:app --reload
```

API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## API Reference

### `GET /api/plan`

Returns a step-by-step itinerary from a source coordinate to a destination coordinate.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_lat` | float | yes | Origin latitude |
| `from_lng` | float | yes | Origin longitude |
| `to_lat` | float | yes | Destination latitude |
| `to_lng` | float | yes | Destination longitude |
| `time` | string | no | Departure time as `HH:MM`. Defaults to current server time. |

#### Example request

```
GET /api/plan?from_lat=40.2009&from_lng=-77.1969&to_lat=40.1899&to_lng=-77.1946&time=06:10
```

#### Example response

```json
{
  "legs": [
    {
      "type": "walk",
      "description": "Walk to Drayer Hall",
      "duration_minutes": 1,
      "from": { "name": "Your location", "coords": [40.2009, -77.1969] },
      "to":   { "name": "Drayer Hall",   "coords": [40.2009, -77.1969] }
    },
    {
      "type": "shuttle",
      "description": "Safety Shuttle shuttle",
      "departs": "06:45",
      "arrives": "07:20",
      "wait_minutes": 35,
      "ride_minutes": 35,
      "from": { "name": "Drayer Hall", "coords": [40.2009, -77.1969] },
      "to":   { "name": "Walmart",     "coords": [40.1899, -77.1946] }
    },
    {
      "type": "walk",
      "description": "Walk to destination",
      "duration_minutes": 1,
      "from": { "name": "Walmart", "coords": [40.1899, -77.1946] },
      "to":   { "name": "Your destination", "coords": [40.1899, -77.1946] }
    }
  ],
  "total_minutes": 71,
  "arrives_at": "07:21"
}
```

If no trips remain tonight, the response will be:

```json
{ "message": "No more shuttle trips tonight" }
```

---

## Testing

Unit tests cover the geo and planning modules using pytest.

```bash
pytest tests/api/ -v
```

| Module | Coverage |
|--------|----------|
| `api/geo.py` | Haversine distance, walk time, nearest stop sorting |
| `api/planning.py` | Time parsing/formatting, loop generation, wrap-around logic |

---

## Configuration

Routes and stops are defined in `config.json` at the project root. Each stop requires:

- `id` — unique slug
- `name` — display name
- `coords` — `[lat, lng]`
- `arrivals` — list of `HH:MM` times (one per loop)

Loop interval and stop offsets are derived automatically from the arrivals data — no manual configuration needed.

---

## Project Structure

```
api/
  main.py        # FastAPI app and route handlers
  geo.py         # Haversine distance and nearest-stop logic
  planning.py    # Shuttle loop planning logic
web/             # Frontend (Vite, in progress)
tests/
  postman/       # Postman collection
  api/           # pytest unit tests (coming soon)
config.json      # Route and stop definitions
```

---

## License

MIT
