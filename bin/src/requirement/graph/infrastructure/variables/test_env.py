"""
Test env.py error handling with error-as-value pattern
Testing error cases for environment variable management
"""
import os
from unittest.mock import patch

from .env import (
    get_db_path,
    get_log_level,
    validate_environment,
)


class TestGetDbPath:
    """Test get_db_path function"""

    def test_get_db_path_returns_value_when_rgl_database_path_set(self):
        """Should return database path when RGL_DATABASE_PATH is set"""
        with patch.dict(os.environ, {"RGL_DATABASE_PATH": ":memory:"}, clear=True):
            result = get_db_path()
            assert result == ":memory:"

    def test_get_db_path_returns_value_when_legacy_path_set(self):
        """Should return database path when RGL_DB_PATH is set (legacy)"""
        with patch.dict(os.environ, {"RGL_DB_PATH": "/path/to/db"}, clear=True):
            result = get_db_path()
            assert result == "/path/to/db"

    def test_get_db_path_returns_error_when_not_set(self):
        """Should return EnvironmentConfigError when no database path is set"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_db_path()
            assert isinstance(result, dict)
            assert result["type"] == "EnvironmentConfigError"
            assert "RGL_DATABASE_PATH" in result["message"]
            assert ":memory:" in result["message"]  # Should suggest format

    def test_get_db_path_fallback_to_legacy(self):
        """Should fallback to RGL_DB_PATH for backward compatibility"""
        with patch.dict(os.environ, {"RGL_DB_PATH": "/legacy/db"}, clear=True):
            result = get_db_path()
            assert result == "/legacy/db"

    def test_get_db_path_prefers_new_over_legacy(self):
        """Should prefer RGL_DATABASE_PATH over RGL_DB_PATH"""
        with patch.dict(
            os.environ,
            {"RGL_DATABASE_PATH": "/new/db", "RGL_DB_PATH": "/legacy/db"},
            clear=True,
        ):
            result = get_db_path()
            assert result == "/new/db"


class TestGetLogLevel:
    """Test get_log_level function (optional env var)"""

    def test_get_log_level_returns_value_when_set(self):
        """Should return log level when set"""
        with patch.dict(os.environ, {"RGL_LOG_LEVEL": "DEBUG"}, clear=True):
            result = get_log_level()
            assert result == "DEBUG"

    def test_get_log_level_returns_none_when_not_set(self):
        """Should return None when not set (optional variable)"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_log_level()
            assert result is None


class TestValidateEnvironment:
    """Test validate_environment function"""

    def test_validate_environment_returns_empty_dict_when_valid(self):
        """Should return empty dict when all required env vars are set"""
        with patch.dict(os.environ, {"RGL_DATABASE_PATH": ":memory:"}, clear=True):
            result = validate_environment()
            assert result == {}

    def test_validate_environment_returns_errors_when_missing(self):
        """Should return dict with errors when required vars are missing"""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_environment()
            assert isinstance(result, dict)
            assert len(result) > 0
            assert "RGL_DATABASE_PATH" in result

    def test_validate_environment_checks_org_mode_consistency(self):
        """Should check org mode configuration consistency"""
        with patch.dict(
            os.environ,
            {"RGL_DATABASE_PATH": ":memory:", "RGL_ORG_MODE": "true"},
            clear=True,
        ):
            result = validate_environment()
            assert "RGL_SHARED_DB_PATH" in result
