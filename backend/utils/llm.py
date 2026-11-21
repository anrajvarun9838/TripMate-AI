"""Shared LLM instances and small helpers around them."""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.config.settings import GROQ_API_KEY, LLM_MODEL, require_env

_api_key = require_env("GROQ_API_KEY", GROQ_API_KEY)


# Creative agents (itinerary, final answer).
llm = ChatGroq(model=LLM_MODEL, api_key=_api_key, temperature=0.4)

# Routing / extraction / analysis: low temperature keeps JSON and numbers stable.
llm_precise = ChatGroq(model=LLM_MODEL, api_key=_api_key, temperature=0)


def llm_text(system_prompt: str, user_prompt: str, precise: bool = False) -> str:
    """Invoke the model with a system + user prompt and return plain text."""
    model = llm_precise if precise else llm
    response = model.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
    )
    return str(response.content)


def json_from_llm(text: str) -> dict[str, Any]:
    """Extract the first complete JSON object returned by the model."""
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError("The model did not return a JSON object.")

    return json.loads(text[start : end + 1])
