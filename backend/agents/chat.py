"""Chat agent: answers simple questions naturally from whichever tool data exists."""

from langchain_core.messages import AIMessage

from backend.graph.state import TravelState
from backend.prompts.agent_prompts import CHAT_SYSTEM, CHAT_USER
from backend.utils.helpers import clip, constraints_text
from backend.utils.llm import llm_text

TOOL_FIELDS = (
    ("Weather", "weather_results"),
    ("Flights", "flight_results"),
    ("Hotels", "hotel_results"),
    ("Budget", "budget_results"),
)


def chat_agent(state: TravelState):
    tool_data = "\n\n".join(
        f"{label}:\n{clip(state[key])}" for label, key in TOOL_FIELDS if state.get(key)
    ) or "No tool data (greeting or general question)."

    answer = llm_text(
        CHAT_SYSTEM,
        CHAT_USER.format(
            query=state["user_query"],
            constraints=constraints_text(state.get("trip_constraints")),
            tool_data=tool_data,
        ),
    )

    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }
