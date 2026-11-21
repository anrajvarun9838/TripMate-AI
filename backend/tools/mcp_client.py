"""MCP client: Tavily (web search), AviationStack (flights) and Weather."""

import os
import shutil
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from backend.config.settings import (
    AVIATION_STACK_API_KEY,
    TAVILY_API_KEY,
    WEATHER_MCP_URL,
    require_env,
)

UVX_COMMAND = shutil.which("uvx") or "uvx"


def _subprocess_env(**updates: str | None) -> dict[str, str]:
    """Copy the current environment and add the MCP API keys."""
    env = os.environ.copy()
    for key, value in updates.items():
        if value:
            env[key] = value
    return env


client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={TAVILY_API_KEY or ''}",
        },
        "aviationstack": {
            "transport": "stdio",
            "command": UVX_COMMAND,
            "args": ["aviationstack-mcp"],
            "env": _subprocess_env(AVIATION_STACK_API_KEY=AVIATION_STACK_API_KEY),
        },
        "weather": {
            "transport": "streamable_http",
            "url": WEATHER_MCP_URL or "http://localhost",  # real URL is checked before use
        },
    }
)


async def _get_server_tool(server_name: str, tool_name: str):
    """Load one tool from one MCP server so a broken server never affects others."""
    if server_name == "tavily":
        require_env("TAVILY_API_KEY", TAVILY_API_KEY)

    elif server_name == "aviationstack":
        require_env("AVIATION_STACK_API_KEY", AVIATION_STACK_API_KEY)
        if shutil.which("uvx") is None:
            raise RuntimeError(
                "uvx was not found. Install uv, reopen the terminal and run "
                "`uvx --version`."
            )

    elif server_name == "weather":
        require_env("WEATHER_MCP_URL", WEATHER_MCP_URL)

    tools = await client.get_tools(server_name=server_name)
    tool = next((item for item in tools if item.name == tool_name), None)

    if tool is None:
        available = ", ".join(sorted(item.name for item in tools)) or "none"
        raise RuntimeError(
            f"MCP tool '{tool_name}' was not found on server '{server_name}'. "
            f"Available tools: {available}"
        )

    return tool


async def get_all_tools() -> None:
    """Connection test: report every MCP server independently."""
    for server_name in ("tavily", "aviationstack", "weather"):
        try:
            tools = await client.get_tools(server_name=server_name)
            names = ", ".join(tool.name for tool in tools) or "no tools"
            print(f"{server_name}: OK -> {names}")
        except Exception as exc:
            print(f"{server_name}: FAILED -> {type(exc).__name__}: {exc}")


async def tavily_mcp_search(query: str):
    tool = await _get_server_tool("tavily", "tavily_search")
    return await tool.ainvoke({"query": query})


async def aviation_mcp_call(tool_name: str, tool_args: dict[str, Any] | None = None):
    tool = await _get_server_tool("aviationstack", tool_name)
    return await tool.ainvoke(tool_args or {})


async def weather_mcp_search(city: str):
    tool = await _get_server_tool("weather", "get_current_weather")
    return await tool.ainvoke({"city": city})


async def forecast_mcp_search(city: str):
    tool = await _get_server_tool("weather", "get_forecast")
    return await tool.ainvoke({"city": city})
