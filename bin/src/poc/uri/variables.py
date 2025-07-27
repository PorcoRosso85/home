"""Environment variables management for URI POC.

This module provides type-safe access to environment variables
with no default values - all required variables must be explicitly set.
"""

import os
from typing import TypedDict


class Config(TypedDict):
    """Configuration from environment variables."""
    DB_PATH: str
    MODEL_NAME: str


def get_config() -> Config:
    """Get configuration from environment variables.
    
    Raises:
        KeyError: If required environment variable is missing.
        
    Returns:
        Config: Typed configuration dictionary.
    """
    return Config(
        DB_PATH=_get_required_env("DB_PATH"),
        MODEL_NAME=_get_required_env("MODEL_NAME")
    )


def _get_required_env(key: str) -> str:
    """Get required environment variable.
    
    Args:
        key: Environment variable name.
        
    Returns:
        str: Environment variable value.
        
    Raises:
        KeyError: If environment variable is not set.
    """
    value = os.environ.get(key)
    if value is None:
        raise KeyError(f"Required environment variable '{key}' is not set")
    return value