"""Builds and compiles the LangGraph workflow with a PostgreSQL checkpointer."""

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row

from backend.agents.budget import budget_agent
from backend.agents.chat import chat_agent
from backend.agents.final import final_agent
from backend.agents.flight import flight_agent
from backend.agents.hotel import hotel_agent
from backend.agents.human_approval import human_approval_agent
from backend.agents.itinerary import itinerary_agent
from backend.agents.supervisor import guardrail_blocked_agent, supervisor_agent
from backend.agents.weather import weather_agent
from backend.config.settings import get_database_url
from backend.graph.routing import ROUTE_MAP, route_after_agent, route_from_supervisor
from backend.graph.state import TravelState


def build_graph() -> StateGraph:
    graph = StateGraph(TravelState)

    graph.add_node("supervisor", supervisor_agent)
    graph.add_node("guardrail_blocked", guardrail_blocked_agent)
    graph.add_node("flight_agent", flight_agent)
    graph.add_node("hotel_agent", hotel_agent)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("budget_agent", budget_agent)
    graph.add_node("itinerary_agent", itinerary_agent)
    graph.add_node("human_approval", human_approval_agent)
    graph.add_node("final_agent", final_agent)
    graph.add_node("chat_agent", chat_agent)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges("supervisor", route_from_supervisor, ROUTE_MAP)

    for agent in ("flight_agent", "hotel_agent", "weather_agent", "budget_agent"):
        graph.add_conditional_edges(agent, route_after_agent(agent), ROUTE_MAP)

    graph.add_edge("itinerary_agent", "human_approval")
    graph.add_edge("human_approval", "final_agent")
    graph.add_edge("final_agent", END)
    graph.add_edge("guardrail_blocked", END)
    graph.add_edge("chat_agent", END)

    return graph


def compile_graph():
    connection = psycopg.connect(
        get_database_url(),
        autocommit=True,
        row_factory=dict_row,
    )
    checkpointer = PostgresSaver(connection)
    checkpointer.setup()
    return build_graph().compile(checkpointer=checkpointer)


travel_graph = compile_graph()
