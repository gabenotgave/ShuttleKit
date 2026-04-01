from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shuttlekit.agent.shuttle_agent import invoke_shuttle_agent
from shuttlekit.services import (
    load_config,
    load_config_service,
    get_stops_service,
    get_routes_service,
    get_schedule_service,
    get_status_service,
    get_plan_service,
)


app = FastAPI(title="ShuttleKit API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        # Add your production frontend URL here after deployment
        # "https://your-frontend-domain.com",
    ],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Client-generated thread id")
    message: str = Field(..., min_length=1, description="User message")


class ChatResponse(BaseModel):
    session_id: str
    reply: str


def _load_config():
    try:
        return load_config()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule file not found")


@app.get("/api/config")
def get_config():
    try:
        return load_config_service()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Schedule file not found")


@app.get("/api/stops")
def get_stops():
    return get_stops_service(_load_config())


@app.get("/api/routes")
def get_routes():
    return get_routes_service(_load_config())


@app.get("/api/schedule")
def get_schedule():
    """Full timetable per route: stops in loop order with arrival lists (config-driven)."""
    return get_schedule_service(_load_config())


@app.get("/api/status")
def get_status():
    return get_status_service(_load_config())


@app.post("/api/chat", response_model=ChatResponse)
async def post_chat(body: ChatRequest):
    """
    Run one shuttle agent turn (MCP tools + LLM). Reuse `session_id` to continue the thread.
    """
    try:
        result = await invoke_shuttle_agent(body.session_id, body.message)
        return ChatResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Agent transport error (is the MCP server running?): {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Agent error: {e!s}",
        ) from e


@app.get("/api/plan")
def get_plan(
    from_lat: float = Query(...),
    from_lng: float = Query(...),
    to_lat: float = Query(...),
    to_lng: float = Query(...),
    time: str = Query(default=None, description="HH:MM — defaults to now"),
):
    return get_plan_service(
        _load_config(),
        from_lat=from_lat,
        from_lng=from_lng,
        to_lat=to_lat,
        to_lng=to_lng,
        time=time
    )
