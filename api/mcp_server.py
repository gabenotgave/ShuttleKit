"""MCP SSE server entry: ``python mcp_server.py`` (run from the ``api/`` directory)."""

from shuttlekit.mcp_server import mcp

if __name__ == "__main__":
    mcp.run(transport="sse")
