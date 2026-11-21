"""Central configuration: environment variables, paths and constants."""

import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]  # project root
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

load_dotenv(BASE_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env")

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# ---- API keys ----
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
WEATHER_MCP_URL = os.getenv("WEATHER_MCP_URL", "").strip()  # remote weather MCP
AVIATION_STACK_API_KEY = os.getenv("AVIATION_STACK_API_KEY")

# ---- Model ----
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")

# ---- Trip defaults ----
DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "").strip()

# ---- Agent limits ----
CONTEXT_CHAR_LIMIT = 3000  # max characters of raw tool data sent to an LLM prompt

# ---- Agent names ----
AGENT_ORDER = [
    "flight_agent",
    "hotel_agent",
    "weather_agent",
    "budget_agent",
    "itinerary_agent",
]
KNOWN_AGENTS = set(AGENT_ORDER)


def require_env(name: str, value: str | None) -> str:
    """Return an environment value or raise a readable setup error."""
    if not value:
        raise RuntimeError(
            f"{name} is missing. Add {name}=your_key to the project .env file."
        )
    return value


def get_database_url() -> str:
    """Return the PostgreSQL URL, forcing sslmode=require when not set."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Add your PostgreSQL URL to the .env file."
        )

    if "sslmode=" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}sslmode=require"

    return database_url
