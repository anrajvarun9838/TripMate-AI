"""Travel API routes."""

import traceback

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.services.travel_service import resume_travel_agent, run_travel_agent

router = APIRouter(prefix="/api/travel", tags=["travel"])


class TravelRequest(BaseModel):
    message: str


class ApprovalRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    approved: bool
    feedback: str = ""


def _error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "error": message},
    )


# Plain `def` endpoints run in FastAPI's threadpool, so the long agent run
# never blocks the event loop.
@router.post("")
def travel_planner(request_data: TravelRequest):
    user_message = request_data.message.strip()

    if not user_message:
        return _error(400, "Message cannot be empty.")

    try:
        result = run_travel_agent(user_input=user_message)
        return JSONResponse(content={"success": True, **result})
    except Exception as exc:
        print("ERROR:", exc)
        traceback.print_exc()
        return _error(500, str(exc))


@router.post("/approve")
def approve_travel_plan(request_data: ApprovalRequest):
    if not request_data.approved and not request_data.feedback.strip():
        return _error(400, "Please provide revision feedback when rejecting the draft.")

    try:
        result = resume_travel_agent(
            thread_id=request_data.thread_id,
            approved=request_data.approved,
            feedback=request_data.feedback,
        )
        return JSONResponse(content={"success": True, **result})
    except Exception as exc:
        print("APPROVAL ERROR:", exc)
        traceback.print_exc()
        return _error(500, str(exc))
