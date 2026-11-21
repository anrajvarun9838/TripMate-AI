"""Small generic helpers shared by agents."""

from typing import Any

from backend.config.settings import CONTEXT_CHAR_LIMIT


def empty_constraints() -> dict[str, Any]:
    return {
        "destination": "",
        "origin": "",
        "duration": "",
        "budget": "",
        "travel_style": "",
        "travelers": "",
        "travel_dates": "",
        "special_preferences": [],
    }


def clip(value: Any, limit: int = CONTEXT_CHAR_LIMIT) -> str:
    """Convert tool output to text and cut it to a safe prompt size."""
    text = str(value) if value is not None else ""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


def constraints_text(constraints: dict[str, Any] | None) -> str:
    """Readable constraint list for prompts (empty values skipped)."""
    lines = []
    for key, value in (constraints or {}).items():
        if value in ("", None, []):
            continue
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value)
        lines.append(f"- {label}: {value}")
    return "\n".join(lines) or "- Not specified"
