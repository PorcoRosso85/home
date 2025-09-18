"""Environment variables for casting board POC."""

import os
from typing import TypedDict


class EnvironmentVariables(TypedDict):
    """Environment variable configuration."""
    KUZU_DATABASE_PATH: str
    LOG_LEVEL: str


def get_environment_variables() -> EnvironmentVariables:
    """Get environment variables with defaults."""
    return EnvironmentVariables(
        KUZU_DATABASE_PATH=os.getenv("KUZU_DATABASE_PATH", ":memory:"),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO")
    )