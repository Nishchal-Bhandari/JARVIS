"""Settings and scoring weights (specsheet §6-8, agent.md §5)."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Anchor the default SQLite file to the repo root, so the DB location does not
# depend on the directory the server was started from.
_DEFAULT_DB = f"sqlite:///{Path(__file__).resolve().parents[2] / 'jarvis.db'}"


class Settings(BaseSettings):
    database_url: str = _DEFAULT_DB
    correlation_threshold: float = 0.45
    window_minutes: int = 10
    tick_seconds: int = 2
    seed: int = 42
    cors_origins: str = "http://localhost:3000"
    anthropic_api_key: str = ""
    llm_model: str = ""

    # correlation weights
    W_TIME: float = 0.40
    W_TOPO: float = 0.35
    W_CTX: float = 0.15
    W_TEXT: float = 0.10
    # root-cause weights
    W_EARLY: float = 0.35
    W_UPSTREAM: float = 0.35
    W_SIG: float = 0.20
    W_SEV: float = 0.10

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
