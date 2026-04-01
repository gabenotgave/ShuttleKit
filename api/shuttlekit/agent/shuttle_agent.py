"""
Shared shuttle agent: MCP tools + LangChain create_agent + thread memory.
Used by the CLI (`chatbot.py`) and FastAPI (`/api/chat`).
"""

from __future__ import annotations

import os
from contextlib import AsyncExitStack

from langchain.agents import create_agent
from langchain.agents.middleware import dynamic_prompt, wrap_model_call
from langchain.agents.middleware.types import ModelRequest
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, trim_messages
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

SYSTEM_PROMPT = """You are a helpful assistant for the campus shuttle (ShuttleKit).

Ground answers in the provided tools: live status, stops, routes, schedules, trip plans, and geocoding. Call tools when the user asks about times, locations, routes, or whether the shuttle is running—do not guess times, stops, or paths from memory.

If the user names a place or address instead of coordinates, use the geocoding tools before planning a trip. If they refer to a stop by name, resolve it with stop lookup tools first.

Be concise and clear. If data is missing or tools fail, say so and suggest what the user can try next."""

# Checkpoints store the graph `messages` list as-is: `AIMessage` already carries
# `tool_calls`; tool outputs are the following `ToolMessage`s. Nothing extra to save.
_checkpointer = MemorySaver()


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
        )

    return shuttle_system_prompt


@wrap_model_call
async def trim_history_for_model(request: ModelRequest, handler):
    trimmed = trim_messages(
        list(request.messages),
        max_tokens=4000,
        strategy="last",
        token_counter="approximate",
        include_system=True,
    )
    return await handler(request.override(messages=trimmed))


def _final_reply(messages: list) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content:
            return str(m.content)
    return ""


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

    return {
        "session_id": session_id,
        "reply": _final_reply(messages),
    }
