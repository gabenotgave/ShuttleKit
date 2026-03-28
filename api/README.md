# ShuttleKit API

FastAPI backend for the ShuttleKit campus shuttle planning system.

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (optional, only needed for schedule ingestion)
cp .env.example .env
# Edit .env with your API key

# Run the server
uvicorn main:app --reload
```

API will be available at `http://localhost:8000`

Interactive docs at `http://localhost:8000/docs`

## Configuration

Edit `config.json` to customize routes, stops, schedules, and operating hours for your campus.

## Testing

```bash
pytest tests/ -v
```

## Deployment

See [SETUP.md](../SETUP.md) in the root directory for deployment guides.
