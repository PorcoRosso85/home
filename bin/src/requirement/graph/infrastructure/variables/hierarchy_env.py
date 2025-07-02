"""
階層処理関連の環境変数管理
依存: env.py
外部依存: なし

階層処理に特化した環境変数のアクセスと検証を提供します。
"""
import json
from typing import Optional, Dict, List
from .env import _optional_env, EnvironmentError

def get_hierarchy_mode() -> Optional[str]:
    """階層モード（オプション）
    
    Returns:
        Optional[str]: 'legacy' または 'dynamic'、未設定の場合None
    """
    mode = _optional_env('RGL_HIERARCHY_MODE')
    if mode and mode not in ('legacy', 'dynamic'):
        raise EnvironmentError(
            f"RGL_HIERARCHY_MODE must be 'legacy' or 'dynamic', got: {mode}"
        )
    return mode

def get_max_hierarchy() -> Optional[int]:
    """最大階層深度（オプション）
    
    Returns:
        Optional[int]: 最大階層深度、未設定の場合None
        
    Raises:
        EnvironmentError: 値が整数でない場合
    """
    value = _optional_env('RGL_MAX_HIERARCHY')
    if value:
        try:
            max_hierarchy = int(value)
            if max_hierarchy < 1:
                raise EnvironmentError(
                    f"RGL_MAX_HIERARCHY must be positive integer, got: {max_hierarchy}"
                )
            return max_hierarchy
        except ValueError:
            raise EnvironmentError(
                f"RGL_MAX_HIERARCHY must be an integer, got: {value}"
            )
    return None

def get_team() -> Optional[str]:
    """チーム名（オプション）
    
    Returns:
        Optional[str]: チーム名、未設定の場合None
    """
    return _optional_env('RGL_TEAM')

def get_hierarchy_keywords() -> Optional[Dict[int, List[str]]]:
    """階層キーワード（オプション）
    
    Returns:
        Optional[Dict[int, List[str]]]: 階層レベルごとのキーワード辞書、
                                        未設定の場合None
        
    Raises:
        EnvironmentError: JSONパースエラーまたは形式エラーの場合
    """
    value = _optional_env('RGL_HIERARCHY_KEYWORDS')
    if value:
        try:
            keywords = json.loads(value)
            # 型チェック
            if not isinstance(keywords, dict):
                raise EnvironmentError(
                    "RGL_HIERARCHY_KEYWORDS must be a JSON object"
                )
            # キーと値の型チェック
            for level, words in keywords.items():
                try:
                    int(level)  # キーが数値に変換可能か
                except ValueError:
                    raise EnvironmentError(
                        f"RGL_HIERARCHY_KEYWORDS keys must be numeric, got: {level}"
                    )
                if not isinstance(words, list):
                    raise EnvironmentError(
                        f"RGL_HIERARCHY_KEYWORDS values must be arrays, got: {type(words)}"
                    )
                for word in words:
                    if not isinstance(word, str):
                        raise EnvironmentError(
                            f"RGL_HIERARCHY_KEYWORDS array elements must be strings, got: {type(word)}"
                        )
            # 整数キーに変換して返す
            return {int(k): v for k, v in keywords.items()}
        except json.JSONDecodeError as e:
            raise EnvironmentError(
                f"RGL_HIERARCHY_KEYWORDS must be valid JSON: {e}"
            )
    return None

def validate_hierarchy_env() -> Dict[str, str]:
    """階層関連の環境変数を検証
    
    Returns:
        Dict[str, str]: エラーがある場合はエラーメッセージの辞書
    """
    errors = {}
    
    try:
        get_hierarchy_mode()
    except EnvironmentError as e:
        errors['RGL_HIERARCHY_MODE'] = str(e)
        
    try:
        get_max_hierarchy()
    except EnvironmentError as e:
        errors['RGL_MAX_HIERARCHY'] = str(e)
        
    try:
        get_hierarchy_keywords()
    except EnvironmentError as e:
        errors['RGL_HIERARCHY_KEYWORDS'] = str(e)
    
    return errors