"""Hotel agent: Tavily MCP live search + shortlist analysis."""

import asyncio
from datetime import datetime

from langchain_core.messages import AIMessage

from backend.graph.state import TravelState
from backend.prompts.agent_prompts import HOTEL_FALLBACK_NOTE, HOTEL_SYSTEM, HOTEL_USER
from backend.tools.mcp_client import tavily_mcp_search
from backend.utils.helpers import clip, constraints_text
from backend.utils.llm import llm_text


def _build_search_query(state: TravelState) -> str:
    """Targeted search query from supervisor constraints, original text as fallback."""
    constraints = state.get("trip_constraints", {}) or {}
    destination = constraints.get("destination")

    if not destination:
        return f"Best hotels for {state['user_query']}"

    parts = ["best hotels in", destination]
    if constraints.get("travel_style"):
        parts.insert(1, constraints["travel_style"])
    if constraints.get("budget"):
        parts.append(f"budget {constraints['budget']}")
    parts.append(f"price per night guest reviews {datetime.now().year}")
    return " ".join(parts)


def hotel_agent(state: TravelState):
    query = _build_search_query(state)

    try:
        search_data = clip(asyncio.run(tavily_mcp_search(query)), 6000)
    except Exception as exc:
        print(f"HOTEL AGENT MCP ERROR: {type(exc).__name__}: {exc}", flush=True)
        search_data = HOTEL_FALLBACK_NOTE

    if state.get("mode") == "chat":
        return {
            "hotel_results": search_data,
            "messages": [AIMessage(content="Hotel data fetched.")],
        }

    try:
        hotel_results = llm_text(
            HOTEL_SYSTEM,
            HOTEL_USER.format(
                query=state["user_query"],
                constraints=constraints_text(state.get("trip_constraints")),
                search_data=search_data,
            ),
            precise=True,
        )
    except Exception as exc:
        print(f"HOTEL AGENT LLM ERROR: {type(exc).__name__}: {exc}", flush=True)
        hotel_results = search_data

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel information processed.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
