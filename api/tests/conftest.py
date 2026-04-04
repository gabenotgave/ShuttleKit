"""Pytest: do not spawn MCP as a subprocess (avoids MCP_PORT conflicts)."""

import pytest


@pytest.fixture(autouse=True)
def _no_embedded_mcp_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    async def noop_start() -> None:
        return None

    def noop_stop() -> None:
        pass

    monkeypatch.setattr("shuttlekit.main._embedded_mcp_start", noop_start)
    monkeypatch.setattr("shuttlekit.main._embedded_mcp_stop", noop_stop)
