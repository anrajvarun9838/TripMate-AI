"""TripMate AI - FastAPI entry point. Run from the backend folder:
    uvicorn main:app --reload
"""

import nest_asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config.settings import FRONTEND_DIR
from backend.routes.travel import router as travel_router

# Lets the synchronous agent nodes call the async MCP helpers.
nest_asyncio.apply()

app = FastAPI(
    title="TripMate AI",
    description=(
        "LangGraph Multi-Agent Travel Planner with Supervisor, Guardrails, "
        "Human-in-the-Loop, and FastAPI Frontend"
    ),
    version="3.0.0",
)

app.include_router(travel_router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "TripMate AI API is running",
        "features": ["supervisor_agent", "input_guardrail", "human_in_the_loop"],
    }


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})


# Frontend is served last so it never shadows the API routes.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
