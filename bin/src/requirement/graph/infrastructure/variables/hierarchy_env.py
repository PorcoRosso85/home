"""
階層処理関連の環境変数管理
依存: env.py
外部依存: なし

階層処理に特化した環境変数のアクセスと検証を提供します。
"""
import json
from typing import Optional, Dict, List, Union
from .env import _optional_env
from domain.errors import EnvironmentConfigError

def get_hierarchy_mode() -> Union[Optional[str], EnvironmentConfigError]:
    """階層モード（オプション）

    Returns:
        Union[Optional[str], EnvironmentConfigError]: 'legacy' または 'dynamic'、未設定の場合None、エラーの場合EnvironmentConfigError
    """
    mode = _optional_env('RGL_HIERARCHY_MODE')
    if mode and mode not in ('legacy', 'dynamic'):
        return EnvironmentConfigError(
            type="EnvironmentConfigError",
            message=f"RGL_HIERARCHY_MODE must be 'legacy' or 'dynamic', got: {mode}",
            variable="RGL_HIERARCHY_MODE",
            current_value=mode,
            expected_format="'legacy' or 'dynamic'"
        )
    return mode

def get_max_hierarchy() -> Union[Optional[int], EnvironmentConfigError]:
    """最大階層深度（オプション）

    Returns:
        Union[Optional[int], EnvironmentConfigError]: 最大階層深度、未設定の場合None、エラーの場合EnvironmentConfigError
    """
    value = _optional_env('RGL_MAX_HIERARCHY')
    if value:
        try:
            max_hierarchy = int(value)
            if max_hierarchy < 1:
                return EnvironmentConfigError(
                    type="EnvironmentConfigError",
                    message=f"RGL_MAX_HIERARCHY must be positive integer, got: {max_hierarchy}",
                    variable="RGL_MAX_HIERARCHY",
                    current_value=str(max_hierarchy),
                    expected_format="Positive integer"
                )
            return max_hierarchy
        except ValueError:
            return EnvironmentConfigError(
                type="EnvironmentConfigError",
                message=f"RGL_MAX_HIERARCHY must be an integer, got: {value}",
                variable="RGL_MAX_HIERARCHY",
                current_value=value,
                expected_format="Integer"
            )
    return None

def get_team() -> Optional[str]:
    """チーム名（オプション）

    Returns:
        Optional[str]: チーム名、未設定の場合None
    """
    return _optional_env('RGL_TEAM')

def get_hierarchy_keywords() -> Union[Optional[Dict[int, List[str]]], EnvironmentConfigError]:
    """階層キーワード（オプション）

    Returns:
        Union[Optional[Dict[int, List[str]]], EnvironmentConfigError]: 階層レベルごとのキーワード辞書、
                                        未設定の場合None、エラーの場合EnvironmentConfigError
    """
    value = _optional_env('RGL_HIERARCHY_KEYWORDS')
    if value:
        try:
            keywords = json.loads(value)
            # 型チェック
            if not isinstance(keywords, dict):
                return EnvironmentConfigError(
                    type="EnvironmentConfigError",
                    message="RGL_HIERARCHY_KEYWORDS must be a JSON object",
                    variable="RGL_HIERARCHY_KEYWORDS",
                    current_value=str(type(keywords)),
                    expected_format="JSON object"
                )
            # キーと値の型チェック
            for level, words in keywords.items():
                try:
                    int(level)  # キーが数値に変換可能か
                except ValueError:
                    return EnvironmentConfigError(
                        type="EnvironmentConfigError",
                        message=f"RGL_HIERARCHY_KEYWORDS keys must be numeric, got: {level}",
                        variable="RGL_HIERARCHY_KEYWORDS",
                        current_value=str(level),
                        expected_format="Numeric keys"
                    )
                if not isinstance(words, list):
                    return EnvironmentConfigError(
                        type="EnvironmentConfigError",
                        message=f"RGL_HIERARCHY_KEYWORDS values must be arrays, got: {type(words)}",
                        variable="RGL_HIERARCHY_KEYWORDS",
                        current_value=str(type(words)),
                        expected_format="Array of strings"
                    )
                for word in words:
                    if not isinstance(word, str):
                        return EnvironmentConfigError(
                            type="EnvironmentConfigError",
                            message=f"RGL_HIERARCHY_KEYWORDS array elements must be strings, got: {type(word)}",
                            variable="RGL_HIERARCHY_KEYWORDS",
                            current_value=str(type(word)),
                            expected_format="String array elements"
                        )
            # 整数キーに変換して返す
            return {int(k): v for k, v in keywords.items()}
        except json.JSONDecodeError as e:
            return EnvironmentConfigError(
                type="EnvironmentConfigError",
                message=f"RGL_HIERARCHY_KEYWORDS must be valid JSON: {e}",
                variable="RGL_HIERARCHY_KEYWORDS",
                current_value=value,
                expected_format="Valid JSON"
            )
    return None

def validate_hierarchy_env() -> Dict[str, str]:
    """階層関連の環境変数を検証

    Returns:
        Dict[str, str]: エラーがある場合はエラーメッセージの辞書
    """
    errors = {}

    mode = get_hierarchy_mode()
    if isinstance(mode, EnvironmentConfigError):
        errors['RGL_HIERARCHY_MODE'] = mode["message"]

    max_h = get_max_hierarchy()
    if isinstance(max_h, EnvironmentConfigError):
        errors['RGL_MAX_HIERARCHY'] = max_h["message"]

    keywords = get_hierarchy_keywords()
    if isinstance(keywords, EnvironmentConfigError):
        errors['RGL_HIERARCHY_KEYWORDS'] = keywords["message"]

    return errors
