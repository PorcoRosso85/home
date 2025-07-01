"""
KuzuDB パスヘルパー - KuzuDBモジュールの確実なインポート
依存: env
外部依存: なし

規約遵守:
- 副作用を明示的に分離
- エラーを値として扱う
"""
import os
import sys
from typing import Optional, Dict

from .env import get_kuzu_module_path


def setup_kuzu_path() -> Dict[str, str]:
    """
    KuzuDBモジュールのパスをsys.pathに追加
    
    Returns:
        成功時: {"status": "success", "path": str}
        失敗時: {"status": "error", "message": str}
    """
    kuzu_path = get_kuzu_module_path()
    
    if not kuzu_path:
        return {
            "status": "error",
            "message": "KuzuDB module path not found. Set RGL_KUZU_MODULE_PATH or install kuzu"
        }
    
    # 親ディレクトリをsys.pathに追加
    parent_path = os.path.dirname(kuzu_path)
    if parent_path not in sys.path:
        sys.path.insert(0, parent_path)
    
    return {
        "status": "success",
        "path": kuzu_path
    }


def import_kuzu() -> Dict[str, any]:
    """
    KuzuDBをインポート（パス設定込み）
    
    Returns:
        成功時: {"status": "success", "module": kuzu}
        失敗時: {"status": "error", "message": str}
    """
    # パス設定
    path_result = setup_kuzu_path()
    if path_result["status"] == "error":
        return path_result
    
    # インポート試行
    try:
        import kuzu
        return {
            "status": "success",
            "module": kuzu
        }
    except ImportError as e:
        return {
            "status": "error",
            "message": f"Failed to import kuzu after path setup: {str(e)}"
        }


# In-source test
def test_setup_kuzu_path():
    """setup_kuzu_path の基本動作テスト"""
    result = setup_kuzu_path()
    assert "status" in result
    assert result["status"] in ["success", "error"]
    if result["status"] == "success":
        assert "path" in result
    else:
        assert "message" in result


def test_import_kuzu():
    """import_kuzu の基本動作テスト"""
    result = import_kuzu()
    assert "status" in result
    assert result["status"] in ["success", "error"]
    if result["status"] == "success":
        assert "module" in result
    else:
        assert "message" in result