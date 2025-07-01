"""
環境変数管理 - 外部設定の一元管理
依存: なし
外部依存: なし

規約遵守:
- デフォルト値禁止
- 必須環境変数は明示的にエラー
- 関数として提供（グローバル状態禁止）
"""
import os
from typing import Dict, Optional, TypedDict


class EnvironmentError(TypedDict):
    """環境変数エラー"""
    type: str
    message: str
    variable: str
    suggestion: str


class EnvironmentConfig(TypedDict):
    """環境設定"""
    # 必須環境変数
    ld_library_path: str
    rgl_db_path: str
    
    # オプション環境変数
    rgl_log_level: Optional[str]
    rgl_log_format: Optional[str]
    rgl_hierarchy_mode: Optional[str]
    rgl_team: Optional[str]
    rgl_skip_schema_check: Optional[str]
    rgl_max_hierarchy: Optional[str]
    rgl_hierarchy_keywords: Optional[str]
    
    # /org用共有DB設定
    rgl_shared_db_path: Optional[str]
    rgl_org_mode: Optional[str]


def get_required_env(name: str) -> str:
    """必須環境変数を取得（デフォルト値なし）"""
    value = os.environ.get(name)
    if value is None:
        raise ValueError({
            "type": "EnvironmentError",
            "message": f"Required environment variable not set: {name}",
            "variable": name,
            "suggestion": f"Set {name}=<value> before running the application"
        })
    return value


def get_optional_env(name: str) -> Optional[str]:
    """オプション環境変数を取得"""
    return os.environ.get(name)


def load_environment() -> EnvironmentConfig:
    """
    環境変数をロード
    
    Returns:
        EnvironmentConfig: 環境設定
        
    Raises:
        ValueError: 必須環境変数が未設定の場合
        
    Example:
        >>> os.environ['LD_LIBRARY_PATH'] = '/path/to/lib'
        >>> os.environ['RGL_DB_PATH'] = '/path/to/db'
        >>> config = load_environment()
        >>> config['rgl_db_path']
        '/path/to/db'
    """
    return {
        # 必須
        "ld_library_path": get_required_env("LD_LIBRARY_PATH"),
        "rgl_db_path": get_required_env("RGL_DB_PATH"),
        
        # オプション
        "rgl_log_level": get_optional_env("RGL_LOG_LEVEL"),
        "rgl_log_format": get_optional_env("RGL_LOG_FORMAT"),
        "rgl_hierarchy_mode": get_optional_env("RGL_HIERARCHY_MODE"),
        "rgl_team": get_optional_env("RGL_TEAM"),
        "rgl_skip_schema_check": get_optional_env("RGL_SKIP_SCHEMA_CHECK"),
        "rgl_max_hierarchy": get_optional_env("RGL_MAX_HIERARCHY"),
        "rgl_hierarchy_keywords": get_optional_env("RGL_HIERARCHY_KEYWORDS"),
        
        # /org用
        "rgl_shared_db_path": get_optional_env("RGL_SHARED_DB_PATH"),
        "rgl_org_mode": get_optional_env("RGL_ORG_MODE")
    }


def get_db_path(config: EnvironmentConfig) -> str:
    """
    DBパスを解決（/org対応）
    
    Args:
        config: 環境設定
        
    Returns:
        str: DBパス
        
    Example:
        >>> config = {"rgl_org_mode": "true", "rgl_shared_db_path": "/shared/db", "rgl_db_path": "/local/db"}
        >>> get_db_path(config)
        '/shared/db'
    """
    # /orgモードの場合は共有DBを優先
    if config.get("rgl_org_mode") == "true" and config.get("rgl_shared_db_path"):
        return config["rgl_shared_db_path"]
    
    return config["rgl_db_path"]


def parse_bool(value: Optional[str]) -> bool:
    """
    文字列をboolに変換
    
    Args:
        value: 文字列値
        
    Returns:
        bool: 変換結果
        
    Example:
        >>> parse_bool("true")
        True
        >>> parse_bool("false")
        False
        >>> parse_bool(None)
        False
    """
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes", "on")


def parse_int(value: Optional[str], name: str) -> Optional[int]:
    """
    文字列をintに変換
    
    Args:
        value: 文字列値
        name: 変数名（エラー用）
        
    Returns:
        Optional[int]: 変換結果
        
    Raises:
        ValueError: 変換失敗時
    """
    if value is None:
        return None
    
    try:
        return int(value)
    except ValueError:
        raise ValueError({
            "type": "EnvironmentError",
            "message": f"Invalid integer value for {name}: {value}",
            "variable": name,
            "suggestion": f"Set {name} to a valid integer"
        })


# In-source tests
def test_load_environment_success():
    """環境変数が正しく設定されている場合"""
    import os
    os.environ["LD_LIBRARY_PATH"] = "/test/lib"
    os.environ["RGL_DB_PATH"] = "/test/db"
    
    config = load_environment()
    
    assert config["ld_library_path"] == "/test/lib"
    assert config["rgl_db_path"] == "/test/db"


def test_load_environment_missing_required():
    """必須環境変数が未設定の場合"""
    import os
    if "RGL_DB_PATH" in os.environ:
        del os.environ["RGL_DB_PATH"]
    
    try:
        load_environment()
        assert False, "Should raise ValueError"
    except ValueError as e:
        error = e.args[0]
        assert error["type"] == "EnvironmentError"
        assert "RGL_DB_PATH" in error["message"]


def test_get_db_path_org_mode():
    """/orgモードでの共有DB優先"""
    config = {
        "rgl_org_mode": "true",
        "rgl_shared_db_path": "/shared/db",
        "rgl_db_path": "/local/db"
    }
    
    assert get_db_path(config) == "/shared/db"


def test_get_db_path_normal_mode():
    """通常モードでのDB選択"""
    config = {
        "rgl_org_mode": "false",
        "rgl_shared_db_path": "/shared/db",
        "rgl_db_path": "/local/db"
    }
    
    assert get_db_path(config) == "/local/db"