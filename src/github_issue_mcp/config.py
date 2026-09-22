"""Load local configuration without depending on the launching shell's environment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class ConfigurationError(RuntimeError):
    """Raised when required local configuration is missing or invalid."""


def _positive_integer(raw_value: object, *, name: str, default: int) -> int:
    """Parse a positive integer from .env while returning a safe public error."""
    if raw_value in (None, ""):
        return default
    try:
        value = int(str(raw_value))
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be a positive integer in .env.") from exc
    if value <= 0:
        raise ConfigurationError(f"{name} must be a positive integer in .env.")
    return value


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated application settings loaded from the project-local .env file."""

    github_token: str | None
    rate_limit_max_calls: int
    rate_limit_window_seconds: int

    @classmethod
    def load(cls, *, require_token: bool = True) -> Settings:
        values = dotenv_values(ENV_FILE)
        raw_token = values.get("GITHUB_TOKEN")
        token = str(raw_token).strip() if raw_token else None

        if token and "REPLACE_WITH_YOUR_TOKEN" in token:
            token = None

        if require_token and not token:
            raise ConfigurationError(
                "GitHub authentication is not configured. Copy .env.example to .env "
                "and set GITHUB_TOKEN."
            )

        return cls(
            github_token=token,
            rate_limit_max_calls=_positive_integer(
                values.get("RATE_LIMIT_MAX_CALLS"),
                name="RATE_LIMIT_MAX_CALLS",
                default=5,
            ),
            rate_limit_window_seconds=_positive_integer(
                values.get("RATE_LIMIT_WINDOW_SECONDS"),
                name="RATE_LIMIT_WINDOW_SECONDS",
                default=60,
            ),
        )

