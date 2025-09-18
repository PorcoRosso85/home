"""
Environment variables and configuration for the guardrail module.

Following module design conventions:
- No global state (functions return values)
- No default values (required variables must error explicitly)
- Type safety with TypedDict
"""
import os
from typing import TypedDict, Optional


class GuardrailConfig(TypedDict):
    """Configuration for guardrail module."""
    database_path: str
    enable_strict_mode: bool
    log_level: str
    exception_approval_timeout_days: int


class GuardrailOptionalConfig(TypedDict, total=False):
    """Optional configuration with defaults."""
    max_reference_count: int
    enable_auto_categorization: bool


def get_required_env(key: str) -> str:
    """
    Get a required environment variable.
    
    Args:
        key: Environment variable name
        
    Returns:
        The environment variable value
        
    Raises:
        ValueError: If the environment variable is not set
    """
    value = os.environ.get(key)
    if value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    return value


def get_guardrail_config() -> GuardrailConfig:
    """
    Get the guardrail configuration from environment variables.
    
    Returns:
        GuardrailConfig with all required settings
        
    Raises:
        ValueError: If any required environment variable is missing
    """
    return GuardrailConfig(
        database_path=get_required_env("GUARDRAIL_DATABASE_PATH"),
        enable_strict_mode=get_required_env("GUARDRAIL_STRICT_MODE").lower() == "true",
        log_level=get_required_env("GUARDRAIL_LOG_LEVEL"),
        exception_approval_timeout_days=int(get_required_env("GUARDRAIL_EXCEPTION_TIMEOUT_DAYS"))
    )


def get_optional_config() -> GuardrailOptionalConfig:
    """
    Get optional configuration with sensible defaults.
    
    Returns:
        GuardrailOptionalConfig with optional settings
    """
    config: GuardrailOptionalConfig = {}
    
    # Max reference count (default: no limit)
    max_ref_str = os.environ.get("GUARDRAIL_MAX_REFERENCE_COUNT")
    if max_ref_str:
        config["max_reference_count"] = int(max_ref_str)
    
    # Auto categorization (default: enabled)
    auto_cat_str = os.environ.get("GUARDRAIL_AUTO_CATEGORIZATION")
    if auto_cat_str:
        config["enable_auto_categorization"] = auto_cat_str.lower() == "true"
    
    return config


def validate_log_level(level: str) -> bool:
    """
    Validate that the log level is valid.
    
    Args:
        level: Log level string
        
    Returns:
        True if valid, False otherwise
    """
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    return level.upper() in valid_levels


def get_database_connection_params() -> dict[str, str]:
    """
    Get database connection parameters.
    
    Returns:
        Dictionary with connection parameters
        
    Raises:
        ValueError: If required parameters are missing
    """
    config = get_guardrail_config()
    return {
        "database_path": config["database_path"],
        "read_only": False  # Guardrails need write access for exception requests
    }


def is_development_mode() -> bool:
    """
    Check if running in development mode.
    
    Returns:
        True if in development mode (allows relaxed validation)
    """
    return os.environ.get("GUARDRAIL_ENV", "production").lower() == "development"


def get_security_config() -> dict[str, bool]:
    """
    Get security-related configuration.
    
    Returns:
        Dictionary with security settings
    """
    config = get_guardrail_config()
    return {
        "strict_mode": config["enable_strict_mode"],
        "require_references": not is_development_mode(),
        "allow_exceptions": os.environ.get("GUARDRAIL_ALLOW_EXCEPTIONS", "true").lower() == "true"
    }