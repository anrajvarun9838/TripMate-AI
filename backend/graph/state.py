"""LangGraph shared state."""

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage


class TravelState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str

    # Supervisor + guardrail
    guardrail_allowed: bool
    guardrail_reason: str
    mode: str  # "chat" = answer one question, "trip" = full trip plan
    selected_agents: list[str]
    trip_constraints: dict[str, Any]
    supervisor_reasoning: str

    # Specialist results
    flight_results: str
    hotel_results: str
    weather_results: str
    budget_results: str
    itinerary: str

    # Human-in-the-loop
    approval_request: str
    approved: bool
    human_feedback: str
    final_response: str

    llm_calls: int
