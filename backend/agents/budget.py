"""Budget agent: cost breakdown and feasibility verdict."""

from langchain_core.messages import AIMessage

from backend.graph.state import TravelState
from backend.prompts.agent_prompts import BUDGET_SYSTEM, BUDGET_USER
from backend.utils.helpers import clip, constraints_text
from backend.utils.llm import llm_text


def budget_agent(state: TravelState):
    prompt = BUDGET_USER.format(
        query=state["user_query"],
        constraints=constraints_text(state.get("trip_constraints")),
        flights=clip(state.get("flight_results") or "Flight agent not run."),
        hotels=clip(state.get("hotel_results") or "Hotel agent not run."),
        weather=clip(state.get("weather_results") or "Weather agent not run."),
    )

    return {
        "budget_results": llm_text(BUDGET_SYSTEM, prompt, precise=True),
        "messages": [AIMessage(content="Budget assessment generated.")],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
