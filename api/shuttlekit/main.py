import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shuttlekit.agent.shuttle_agent import (
    get_chat_history_for_session,
    get_chat_model_display,
    invoke_shuttle_agent,
    run_chat_prune_loop,
)
from shuttlekit.services import (
    load_config,
    load_config_service,
    get_stops_service,
    get_routes_service,
    get_schedule_service,
    get_status_service,
    get_plan_service,
)


@asynccontextmanager
async def _lifespan(_: FastAPI):
    prune_task = asyncio.create_task(run_chat_prune_loop())
    yield
    prune_task.cancel()
    try:
        await prune_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="ShuttleKit API", lifespan=_lifespan)


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
    model_display: str = Field(
        ...,
        description="Configured LLM label (MODEL_NAME / PROVIDER) for UI disclaimers",
    )


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[dict[str, Any]] = Field(
        ...,
        description="LangGraph thread messages (user / assistant / tool); in-memory only",
    )


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


@app.get("/api/chat/model")
def get_chat_model():
    """Model label for the assistant UI (same env as the agent; no LLM call)."""
    return {"model_display": get_chat_model_display()}


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(session_id: str = Query(..., min_length=1, description="Client thread id")):
    """Return all messages stored for this chat session (LangGraph MemorySaver checkpointer)."""
    return ChatHistoryResponse(**get_chat_history_for_session(session_id))


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
