"""MCP adapter. Tool schemas and execution are owned by the shared registry."""

import asyncio
import json

from .core import Toolkit


def serve(toolkit: Toolkit) -> None:
    from mcp import types
    from mcp.server.lowlevel import Server
    from mcp.server.stdio import stdio_server

    server = Server("project-zomboid-toolkit")

    @server.list_tools()
    async def list_tools():
        return [types.Tool(**schema) for schema in toolkit.schemas()]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            result = await asyncio.to_thread(toolkit.call, name, arguments)
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))],
                isError=isinstance(result, dict) and result.get("ok") is False,
            )
        except (OSError, ValueError) as exc:
            return types.CallToolResult(isError=True, content=[types.TextContent(
                type="text", text=json.dumps({"error": {"message": str(exc)}}))])

    async def run():
        async with stdio_server() as (read, write):
            await server.run(read, write, server.create_initialization_options())

    asyncio.run(run())
