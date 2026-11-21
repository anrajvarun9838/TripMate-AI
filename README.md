# TripMate AI

A multi-agent travel planner built with FastAPI, LangGraph, Groq, MCP (Tavily, AviationStack, OpenWeather) and PostgreSQL.

Flow: **Guardrail → Supervisor → Flight / Hotel / Weather / Budget agents → Itinerary draft → Human approval → Final plan**

## Structure

```
tripmate-ai/
├── backend/
│   ├── main.py                 # FastAPI app (serves the frontend too)
│   ├── config/settings.py      # env vars, paths, constants
│   ├── prompts/agent_prompts.py# every agent prompt
│   ├── agents/                 # supervisor, flight, hotel, weather, budget, itinerary, human_approval, final
│   ├── graph/                  # state, routing, builder (LangGraph + Postgres checkpointer)
│   ├── services/               # run / resume workflow
│   ├── routes/                 # /api/travel endpoints
│   ├── tools/                  # MCP client (Tavily, AviationStack, remote Weather)
│   ├── utils/                  # llm helpers, small helpers
│   └── requirements.txt
├── frontend/                   # index.html, css/, js/
├── Dockerfile
└── .env.example
```

## Run locally

```bash
cp .env.example .env            # fill in your keys
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

AviationStack MCP runs through `uvx`, so `uv` must be installed.
Weather is a remote MCP: deploy the separate `weather-mcp-remote` project and set `WEATHER_MCP_URL`.

## Docker

```bash
docker build -t tripmate-ai .
docker run -p 8000:8000 --env-file .env tripmate-ai
```
