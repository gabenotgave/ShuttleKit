# ShuttleKit API

FastAPI backend for the ShuttleKit campus shuttle planning system.

Application code lives under **`shuttlekit/`** (routes, services, geo/planning, feature flags, embedded MCP spawn, MCP server module, LangGraph agent). **`main.py`** at this directory only re-exports `app` for `uvicorn main:app`.

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

When **`FEATURE_FLAGS_CHATBOT`** is enabled (default **true** when unset; see `.env.example`), **`uvicorn main:app` also runs `mcp_server.py`** via **`shuttlekit/embedded_mcp.py`**. Stop uvicorn to stop both. If the chatbot feature is off, MCP is not started and **`/api/chat*`** returns **404**.

- Default **port `8001`** (`MCP_PORT` in `.env`). Keep **uvicorn on 8000** so they do not clash.
- **`MCP_SSE_URL`** (default `http://127.0.0.1:8001/sse`) is what the LangGraph agent uses; it must match where MCP is listening.

Implementation: **`shuttlekit/mcp_server.py`** (three tools: `get_schedule`, `get_trip`, `get_coords_by_addresses`). Root **`mcp_server.py`** imports and runs it.

**Feature flags:** **`GET /api/features`** returns `{"chatbot": bool}` from `FEATURE_FLAGS_CHATBOT` only (no arbitrary env leakage).

Full explanation, env table, production notes, and troubleshooting: **[SETUP.md — MCP server and chat assistant](../SETUP.md#mcp-server-and-chat-assistant)**.

## Configuration

Edit `config.json` to customize routes, stops, schedules, and operating hours for your campus.

## Testing

```bash
pytest tests/api/ -v
```

## Deployment

See [SETUP.md](../SETUP.md) in the root directory for deployment guides.
