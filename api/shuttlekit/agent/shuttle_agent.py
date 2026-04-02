"""
Shared shuttle agent: MCP tools + LangChain create_agent + thread memory.
Used by the CLI (`chatbot.py`) and FastAPI (`/api/chat`).
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import AsyncExitStack
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, wrap_model_call
from langchain.agents.middleware.types import ModelRequest
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    trim_messages,
)
from langgraph.checkpoint.memory import MemorySaver

from shuttlekit.services import get_agent_prompt_context, load_config

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.sse import sse_client

from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME", "").strip()
PROVIDER = os.getenv("PROVIDER", "").strip()
MCP_SSE_URL = os.getenv("MCP_SSE_URL", "http://127.0.0.1:8001/sse").strip()

# In-memory thread retention (MemorySaver): drop checkpoints older than this (wall clock, UTC).
def _retention_delta() -> timedelta:
    hours = float(os.getenv("CHAT_THREAD_RETENTION_HOURS", "24"))
    return timedelta(hours=max(hours, 0.01))


def _prune_interval_seconds() -> float | None:
    """Seconds between prune runs; None disables the background loop (set env to 0)."""
    raw = float(os.getenv("CHAT_PRUNE_INTERVAL_SECONDS", "3600"))
    if raw <= 0:
        return None
    return max(raw, 10.0)


# thread_id -> last activity (UTC). Used only with the process-local MemorySaver.
_thread_last_activity: dict[str, datetime] = {}


def get_chat_model_display() -> str:
    """Human-readable model label for API responses and UI disclaimers."""
    if MODEL_NAME and PROVIDER:
        return f"{MODEL_NAME} ({PROVIDER})"
    if MODEL_NAME:
        return MODEL_NAME
    if PROVIDER:
        return f"(model not set) · provider: {PROVIDER}"
    return "Not configured (set MODEL_NAME and PROVIDER in the API environment)"

SYSTEM_PROMPT = """You are a helpful assistant for the campus shuttle (ShuttleKit).

You have three tools: `get_schedule` (everything about stops, routes, timetables, live running status, and campus name), `get_coords_by_addresses` (geocode off-network places), and `get_trip` (walk + shuttle legs between two coordinates). Call tools when needed—do not guess times, stops, or paths from memory.

`get_schedule` includes US 12-hour labels everywhere: each stop has **`arrivals_12`** parallel to **`arrivals`**; each `runs[]` stop has **`arrival_12`** next to **`arrival`**; service **`hours`** include **`start_12`** / **`end_12`**. When speaking to the user in 12-hour form, **copy those `*_12` strings**—do not convert `HH:MM` yourself.

**`quick_next`** is a small hint only: per route and stop id, **`next_arrival_12`**, **`next_arrival_24`**, and **`run_index_for_next`** for the first arrival at that stop at or after the reference time. Use that for the single “next shuttle” headline. For “all remaining times tonight” at a stop, filter that stop’s **`arrivals` / `arrivals_12`** using the same clock as context (or list `arrivals_12` entries at indices **≥** the `run_index_for_next` slot if you align by index). For one full loop as a table, use **`routes[].runs[run_index]`** and the **`arrival_12`** fields—**one `run.index` for the whole table.**

If you must answer in 24-hour only, still use **one** `run.index` for a whole trip—never mix loops.

Do not infer where the vehicle is by projecting from the clock or simulating motion. Do not state that the shuttle “just left,” “is at,” or “was at” a stop unless that follows from schedule times compared to the current time or from explicit live status—never contradict schedule times you just showed, including in follow-up turns in the same conversation unless the user asks for a later loop or you re-fetch the schedule.

Stop names: match against `get_schedule` → `stops` (by id and name) before geocoding. Use `get_coords_by_addresses` only for addresses or places clearly not on the shuttle network. Do not geocode shuttle stop names when `stops` can identify them.

Geocoding disambiguation: when geocoding is appropriate but the first result looks wrong (wrong country/region, a distant or irrelevant hit, or nonsense for a campus building or local address), retry once with a refined query: append the campus name from the context block below, e.g. original phrase plus ", " and that exact Campus line. If the user already gave a city or state, you may combine campus with that. Do not chain many speculative geocode calls—one targeted retry is usually enough unless the user asks to try another wording.

Trip “planning” vs showing the schedule: for “when,” “next,” or “what time,” answer from the schedule (and stops as needed) first—clear and minimal. Offer a fuller step-by-step or ordered trip plan mainly when the user asks how to get from A to B, which stop order to use, or similar routing questions; still ground the plan in resolved stops and schedule data, not guessed positions.

When you state any time to the user (schedules, arrivals, departures, service windows, trip times, or relative to “now”), always phrase it in 12-hour clock with AM or PM (e.g. 6:00 PM, 11:30 AM). Do not use 24-hour or military-style times (e.g. 18:00, 23:30) unless the user explicitly asks for that format.

Be concise and clear. If data is missing or tools fail, say so and suggest what the user can try next."""

# Checkpoints store the graph `messages` list as-is: `AIMessage` already carries
# `tool_calls`; tool outputs are the following `ToolMessage`s. Nothing extra to save.
_checkpointer = MemorySaver()


def touch_thread(session_id: str) -> None:
    """Mark a thread as recently used (call after a successful turn or when serving existing history)."""
    _thread_last_activity[session_id] = datetime.now(timezone.utc)


def prune_stale_chat_threads() -> None:
    """
    Remove LangGraph checkpoints for threads whose last activity is older than the retention window.
    Safe to call from a background task; operates only on in-memory state.
    """
    cutoff = datetime.now(timezone.utc) - _retention_delta()
    stale = [tid for tid, ts in _thread_last_activity.items() if ts < cutoff]
    for tid in stale:
        try:
            _checkpointer.delete_thread(tid)
        except Exception:
            logger.exception("Failed to delete stale chat thread %r", tid)
        _thread_last_activity.pop(tid, None)


async def run_chat_prune_loop() -> None:
    """Background loop for the FastAPI lifespan (no external cron)."""
    interval = _prune_interval_seconds()
    if interval is None:
        return
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(prune_stale_chat_threads)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Chat thread prune task failed")


def shuttle_system_prompt_middleware(schedule_config: dict):
    @dynamic_prompt
    def shuttle_system_prompt(request: ModelRequest) -> str:
        ctx = get_agent_prompt_context(schedule_config)
        return (
            f"{SYSTEM_PROMPT}\n\n"
            "Context for this turn (interpret schedules and 'now' in the campus timezone):\n"
            f"- Campus: {ctx['campus']}\n"
            f"- Current local time: {ctx['now_local']}\n"
            f"- IANA timezone: {ctx['timezone']}\n"
            "- Geocoding: use the Campus line above to disambiguate vague or odd place names "
            "(append it after a comma when refining a geocode query).\n"
        )

    return shuttle_system_prompt


@wrap_model_call
async def trim_history_for_model(request: ModelRequest, handler):
    trimmed = trim_messages(
        list(request.messages),
        max_tokens=50000,
        strategy="last",
        token_counter="approximate",
        include_system=True,
    )
    return await handler(request.override(messages=trimmed))


def _stringify_ai_content(content: Any) -> str:
    """
    Gemini and some providers return AIMessage.content as structured blocks, e.g.
    [{'type': 'text', 'text': '...'}]. str() on that would leak Python repr to users.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        if "text" in content and content["text"] is not None:
            return str(content["text"])
        return str(content)
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if text is not None:
                    parts.append(str(text))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _final_reply(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            return _stringify_ai_content(m.content)
    return ""


def _message_to_payload(m: BaseMessage) -> dict[str, Any]:
    """JSON-friendly dict for API history (roles aligned with common chat UIs)."""
    role_map = {"human": "user", "ai": "assistant", "tool": "tool", "system": "system"}
    role = role_map.get(m.type, m.type)
    payload: dict[str, Any] = {"role": role}

    if isinstance(m, AIMessage):
        payload["content"] = _stringify_ai_content(m.content) if m.content else ""
        tool_calls = getattr(m, "tool_calls", None) or []
        if tool_calls:
            payload["tool_calls"] = tool_calls
        return payload

    if isinstance(m, ToolMessage):
        payload["name"] = m.name
        c = m.content
        payload["content"] = c if isinstance(c, str) else _stringify_ai_content(c)
        return payload

    if isinstance(m, (HumanMessage, SystemMessage)):
        c = m.content
        payload["content"] = c if isinstance(c, str) else _stringify_ai_content(c)
        return payload

    c = getattr(m, "content", None)
    payload["content"] = (
        c if isinstance(c, str) else _stringify_ai_content(c) if c is not None else ""
    )
    return payload


def get_chat_history_for_session(session_id: str) -> dict[str, Any]:
    """
    Load the LangGraph checkpoint for `session_id` and return all messages in the thread.

    Uses the same in-process MemorySaver as ``invoke_shuttle_agent`` (not persisted across
    API restarts).
    """
    config = {"configurable": {"thread_id": session_id}}
    tup = _checkpointer.get_tuple(config)
    if tup is None:
        return {"session_id": session_id, "messages": []}

    touch_thread(session_id)

    checkpoint = tup.checkpoint
    channel_values = checkpoint.get("channel_values") or {}
    raw_messages = channel_values.get("messages")
    if not raw_messages:
        return {"session_id": session_id, "messages": []}

    out: list[dict[str, Any]] = []
    for m in raw_messages:
        if isinstance(m, BaseMessage):
            out.append(_message_to_payload(m))
        else:
            out.append({"role": "unknown", "content": str(m)})

    return {"session_id": session_id, "messages": out}


async def invoke_shuttle_agent(session_id: str, user_message: str) -> dict:
    """
    Run one agent turn (model ↔ tools loop until done).

    Returns the assistant’s final text for this turn. Thread state remains in the
    checkpointer for future turns; a separate endpoint can load history by `session_id` later.
    """
    text = user_message.strip()
    if not text:
        raise ValueError("message must not be empty")

    model = init_chat_model(MODEL_NAME, model_provider=PROVIDER)
    app_config = load_config()
    thread_config = {"configurable": {"thread_id": session_id}}

    async with AsyncExitStack() as stack:
        sse_transport = await stack.enter_async_context(sse_client(MCP_SSE_URL))
        mcp_session = await stack.enter_async_context(ClientSession(*sse_transport))
        await mcp_session.initialize()

        tools = await load_mcp_tools(mcp_session)

        agent = create_agent(
            model,
            tools,
            checkpointer=_checkpointer,
            middleware=[
                shuttle_system_prompt_middleware(app_config),
                trim_history_for_model,
            ],
        )

        response = await agent.ainvoke(
            {"messages": [("user", text)]},
            config=thread_config,
        )
        messages = list(response["messages"])

    touch_thread(session_id)

    return {
        "session_id": session_id,
        "reply": _final_reply(messages),
        "model_display": get_chat_model_display(),
    }
