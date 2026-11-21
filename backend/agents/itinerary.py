"""Itinerary agent: integrated draft for human review."""

from langchain_core.messages import AIMessage

from backend.graph.state import TravelState
from backend.prompts.agent_prompts import ITINERARY_SYSTEM, ITINERARY_USER
from backend.utils.helpers import clip, constraints_text
from backend.utils.llm import llm_text

APPROVAL_REQUEST = (
    "Please review the generated draft itinerary. Approve it to create the "
    "final polished plan, or provide feedback for revision."
)


def itinerary_agent(state: TravelState):
    prompt = ITINERARY_USER.format(
        query=state["user_query"],
        constraints=constraints_text(state.get("trip_constraints")),
        flights=clip(state.get("flight_results") or "Not requested."),
        hotels=clip(state.get("hotel_results") or "Not requested."),
        weather=clip(state.get("weather_results") or "Not requested."),
        budget=clip(state.get("budget_results") or "Not requested."),
    )

    return {
        "itinerary": llm_text(ITINERARY_SYSTEM, prompt),
        "approval_request": APPROVAL_REQUEST,
        "messages": [AIMessage(content="Draft itinerary created for human review.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
