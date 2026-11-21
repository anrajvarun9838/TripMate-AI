"""Flight agent: AviationStack MCP data + expert route guidance."""

import asyncio

from langchain_core.messages import AIMessage

from backend.config.settings import DEFAULT_ORIGIN_IATA
from backend.graph.state import TravelState
from backend.prompts.agent_prompts import FLIGHT_SYSTEM, FLIGHT_USER
from backend.tools.mcp_client import aviation_mcp_call
from backend.utils.helpers import clip, constraints_text
from backend.utils.llm import llm_text


def _safe_aviation_call(tool_name: str) -> str:
    """One failing directory call must not stop the whole flight agent."""
    try:
        return clip(asyncio.run(aviation_mcp_call(tool_name)))
    except Exception as exc:
        print(f"FLIGHT AGENT MCP ERROR ({tool_name}): {type(exc).__name__}: {exc}", flush=True)
        return "unavailable"


def flight_agent(state: TravelState):
    print("\nINSIDE FLIGHT AGENT\n")

    if state.get("mode") == "chat":
        return {
            "flight_results": (
                f"Airports: {_safe_aviation_call('list_airports')}\n"
                f"Airlines: {_safe_aviation_call('list_airlines')}\n"
                "Note: this is a partial directory, not live fares or schedules."
            ),
            "messages": [AIMessage(content="Flight data fetched.")],
        }

    try:
        prompt = FLIGHT_USER.format(
            query=state["user_query"],
            constraints=constraints_text(state.get("trip_constraints")),
            default_origin=DEFAULT_ORIGIN_IATA or "none",
            airport_data=_safe_aviation_call("list_airports"),
            airline_data=_safe_aviation_call("list_airlines"),
        )
        flight_data = llm_text(FLIGHT_SYSTEM, prompt, precise=True)
    except Exception as exc:
        flight_data = f"Flight information unavailable: {exc}"

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight recommendations generated")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
