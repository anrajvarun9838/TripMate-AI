"""Supervisor agent: input guardrail + agent selection + constraint extraction."""

from langchain_core.messages import AIMessage

from backend.config.settings import AGENT_ORDER, KNOWN_AGENTS
from backend.graph.state import TravelState
from backend.prompts.agent_prompts import (
    GUARDRAIL_SYSTEM,
    GUARDRAIL_USER,
    SUPERVISOR_SYSTEM,
    SUPERVISOR_USER,
)
from backend.utils.helpers import empty_constraints
from backend.utils.llm import json_from_llm, llm_text

BLOCKED_DEFAULT_REASON = (
    "TripMate AI can only help with travel-planning requests. "
    "Please ask about a destination, flight, hotel, weather, budget, or itinerary."
)


def supervisor_agent(state: TravelState):
    query = state["user_query"]
    llm_calls = state.get("llm_calls", 0)

    # ---- 1. Input guardrail (fails open so a parsing error never blocks travel requests) ----
    try:
        raw = llm_text(
            GUARDRAIL_SYSTEM,
            GUARDRAIL_USER.format(query=query),
            precise=True,
        )
        result = json_from_llm(raw)
        allowed = bool(result.get("allowed", True))
        guardrail_reason = str(result.get("reason", "")).strip()
        llm_calls += 1
    except Exception as exc:
        print(f"Guardrail fallback used: {exc}")
        allowed = True
        guardrail_reason = "Guardrail validation fallback allowed the request."

    if not allowed:
        reason = guardrail_reason or BLOCKED_DEFAULT_REASON
        return {
            "guardrail_allowed": False,
            "guardrail_reason": reason,
            "mode": "chat",
            "selected_agents": [],
            "trip_constraints": empty_constraints(),
            "supervisor_reasoning": reason,
            "final_response": reason,
            "messages": [AIMessage(content=f"Guardrail blocked request: {reason}")],
            "llm_calls": llm_calls,
        }

    # ---- 2. Supervisor planning ----
    try:
        raw = llm_text(
            SUPERVISOR_SYSTEM,
            SUPERVISOR_USER.format(query=query),
            precise=True,
        )
        parsed = json_from_llm(raw)

        mode = "trip" if parsed.get("mode") == "trip" else "chat"
        requested = parsed.get("selected_agents", [])
        selected_agents = [
            name for name in AGENT_ORDER if name in requested and name in KNOWN_AGENTS
        ]

        constraints = empty_constraints()
        parsed_constraints = parsed.get("trip_constraints", {})
        if isinstance(parsed_constraints, dict):
            constraints.update(parsed_constraints)

        if mode == "trip":
            # A stated budget always needs the budget agent.
            if constraints.get("budget") and "budget_agent" not in selected_agents:
                selected_agents.append("budget_agent")

            # The itinerary agent integrates every selected specialist result.
            if "itinerary_agent" not in selected_agents:
                selected_agents.append("itinerary_agent")
        else:
            # Simple questions never build an itinerary.
            selected_agents = [n for n in selected_agents if n != "itinerary_agent"]

        selected_agents = [name for name in AGENT_ORDER if name in selected_agents]
        reasoning = str(parsed.get("reasoning", "")).strip()
        llm_calls += 1
    except Exception as exc:
        print(f"Supervisor fallback used: {exc}")
        # Safe fallback: answer conversationally instead of launching a full trip plan.
        mode = "chat"
        selected_agents = []
        constraints = empty_constraints()
        reasoning = "Supervisor parsing failed, so the request is answered directly."

    return {
        "guardrail_allowed": True,
        "guardrail_reason": guardrail_reason,
        "mode": mode,
        "selected_agents": selected_agents,
        "trip_constraints": constraints,
        "supervisor_reasoning": reasoning,
        "messages": [AIMessage(content="Supervisor created the agent plan.")],
        "llm_calls": llm_calls,
    }


def guardrail_blocked_agent(state: TravelState):
    reason = (
        state.get("final_response")
        or state.get("guardrail_reason")
        or "This request was blocked by the travel input guardrail."
    )
    return {
        "final_response": reason,
        "messages": [AIMessage(content=reason)],
    }
