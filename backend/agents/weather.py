"""Weather agent: OpenWeather MCP data + packing/planning advice."""
import asyncio

from langchain_core.messages import AIMessage

from backend.graph.state import TravelState
from backend.prompts.agent_prompts import (
    DESTINATION_SYSTEM,
    DESTINATION_USER,
    WEATHER_FALLBACK_NOTE,
    WEATHER_SYSTEM,
    WEATHER_USER,
)
from backend.tools.mcp_client import forecast_mcp_search, weather_mcp_search
from backend.utils.helpers import constraints_text
from backend.utils.llm import llm_text


def extract_destination(text: str) -> str:
    """Return one city name suitable for a weather lookup."""
    destination = llm_text(
        DESTINATION_SYSTEM,
        DESTINATION_USER.format(query=text),
        precise=True,
    ).strip().strip("\"'.")

    if not destination:
        raise ValueError("The destination could not be extracted.")

    return destination


def weather_agent(state: TravelState):
    constraints = state.get("trip_constraints", {}) or {}
    city = extract_destination(constraints.get("destination") or state["user_query"])
    calls = 1

    try:
        weather_data = (
            f"Current Weather:\n{asyncio.run(weather_mcp_search(city))}\n\n"
            f"Forecast:\n{asyncio.run(forecast_mcp_search(city))}"
        )
    except Exception as exc:
        print(f"WEATHER AGENT MCP ERROR: {type(exc).__name__}: {exc}", flush=True)
        weather_data = WEATHER_FALLBACK_NOTE.format(city=city)

    if state.get("mode") == "chat":
        # Simple question: hand the live data to the chat agent, skip the long report.
        return {
            "weather_results": f"City used for the lookup: {city}\n\n{weather_data}",
            "messages": [AIMessage(content="Weather data fetched.")],
            "llm_calls": state.get("llm_calls", 0) + calls,
        }

    try:
        weather_results = llm_text(
            WEATHER_SYSTEM,
            WEATHER_USER.format(
                city=city,
                constraints=constraints_text(constraints),
                weather_data=weather_data,
            ),
            precise=True,
        )
        calls += 1
    except Exception as exc:
        print(f"WEATHER AGENT LLM ERROR: {type(exc).__name__}: {exc}", flush=True)
        weather_results = weather_data

    return {
        "weather_results": weather_results,
        "messages": [AIMessage(content="Weather information processed.")],
        "llm_calls": state.get("llm_calls", 0) + calls,
    }
