"""Final agent: polished customer-ready response (applies human feedback)."""

from langchain_core.messages import AIMessage

from backend.graph.state import TravelState
from backend.prompts.agent_prompts import FINAL_SYSTEM, FINAL_USER
from backend.utils.helpers import clip, constraints_text
from backend.utils.llm import llm_text


def final_agent(state: TravelState):
    if state.get("approved", False):
        review_instruction = (
            "The user APPROVED the draft. Preserve its decisions while polishing it."
        )
    else:
        feedback = state.get("human_feedback", "") or "Improve the draft before finalizing it."
        review_instruction = (
            "The user REQUESTED A REVISION. Apply this feedback carefully and keep "
            f"all sections consistent with it:\n{feedback}"
        )

    prompt = FINAL_USER.format(
        review_instruction=review_instruction,
        query=state["user_query"],
        constraints=constraints_text(state.get("trip_constraints")),
        flights=clip(state.get("flight_results") or "Not requested."),
        hotels=clip(state.get("hotel_results") or "Not requested."),
        weather=clip(state.get("weather_results") or "Not requested."),
        budget=clip(state.get("budget_results") or "Not requested."),
        itinerary=clip(state.get("itinerary") or "", 8000),
    )

    final_text = llm_text(FINAL_SYSTEM, prompt)

    return {
        "final_response": final_text,
        "messages": [AIMessage(content=final_text)],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
