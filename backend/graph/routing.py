"""Dynamic supervisor routing between specialist agents."""
from backend.config.settings import AGENT_ORDER
from backend.graph.state import TravelState

ROUTE_MAP = {
    "guardrail_blocked": "guardrail_blocked",
    "flight_agent": "flight_agent",
    "hotel_agent": "hotel_agent",
    "weather_agent": "weather_agent",
    "budget_agent": "budget_agent",
    "itinerary_agent": "itinerary_agent",
    "chat_agent": "chat_agent",
}


def _selected_agents(state: TravelState) -> list[str]:
    selected = state.get("selected_agents", [])
    return [agent for agent in AGENT_ORDER if agent in selected]


def route_from_supervisor(state: TravelState) -> str:
    if not state.get("guardrail_allowed", True):
        return "guardrail_blocked"

    selected = _selected_agents(state)
    last_stop = "itinerary_agent" if state.get("mode") == "trip" else "chat_agent"
    return selected[0] if selected else last_stop


def route_after_agent(current_agent: str):
    def route(state: TravelState) -> str:
        selected = _selected_agents(state)
        current_index = AGENT_ORDER.index(current_agent)

        for next_agent in AGENT_ORDER[current_index + 1 :]:
            if next_agent in selected:
                return next_agent

        # Trip mode ends in the itinerary; simple questions go straight to a chat answer.
        return "itinerary_agent" if state.get("mode") == "trip" else "chat_agent"

    return route
