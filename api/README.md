# ShuttleKit API

FastAPI backend for the ShuttleKit campus shuttle planning system.

Application code lives under **`shuttlekit/`** (routes, services, geo/planning, MCP server module, LangGraph agent). **`main.py`** at this directory only re-exports `app` for `uvicorn main:app`.

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

cp .env.example .env
# Edit .env: ingestion keys if needed; for chat, set MODEL_NAME, PROVIDER, provider keys, MCP_* (see below)

# Run the HTTP API
uvicorn main:app --reload
```

API will be available at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.

## MCP server (for `POST /api/chat`)

The shuttle assistant calls **MCP tools** (status, stops, routes, schedule, trip plan, geocoding) over **SSE**. Those tools are served by a **separate process** from uvicorn.

**Start MCP** (second terminal, same venv):

```bash
cd api   # repository: ShuttleKit/api
source .venv/bin/activate
python mcp_server.py
```

- Default **port `8001`** (`MCP_PORT` in `.env`). Keep **uvicorn on 8000** so they do not clash.
- **`MCP_SSE_URL`** (default `http://127.0.0.1:8001/sse`) is what the LangGraph agent uses; it must match where MCP is listening.

Implementation: **`shuttlekit/mcp_server.py`**. Root **`mcp_server.py`** delegates to it.

Full explanation, env table, production notes, and troubleshooting: **[SETUP.md — MCP server and chat assistant](../SETUP.md#mcp-server-and-chat-assistant)**.

## Configuration

Edit `config.json` to customize routes, stops, schedules, and operating hours for your campus.

## Testing

```bash
pytest tests/api/ -v
```

## Deployment

See [SETUP.md](../SETUP.md) in the root directory for deployment guides.
