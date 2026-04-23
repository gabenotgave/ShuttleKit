"""
Start/stop ``mcp_server.py`` as a child of uvicorn when ``FEATURE_FLAGS_CHATBOT`` is enabled.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

from shuttlekit.feature_flags import is_chatbot_enabled

logger = logging.getLogger(__name__)

_process: subprocess.Popen | None = None


async def start_if_enabled() -> None:
    global _process
    if not is_chatbot_enabled():
        return
    api_dir = Path(__file__).resolve().parent.parent
    script = api_dir / "mcp_server.py"
    if not script.is_file():
        logger.warning("Embedded MCP skipped: %s not found", script)
        return
    try:
        _process = subprocess.Popen(
            [sys.executable, str(script)],
            cwd=str(api_dir),
        )
    except OSError as e:
        logger.error("Embedded MCP failed to start: %s", e)
        return

    await asyncio.sleep(0.25)
    if _process.poll() is not None:
        logger.error(
            "Embedded MCP exited immediately (code %s). "
            "Free MCP_PORT or run python mcp_server.py in another terminal.",
            _process.returncode,
        )
        _process = None


def stop() -> None:
    global _process
    if _process is None:
        return
    proc = _process
    _process = None
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
