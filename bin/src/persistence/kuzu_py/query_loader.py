"""
Query loader - ファイルからCypherクエリを読み込む
"""
from pathlib import Path
from typing import Union, Dict, Optional
import os

from result_types import ErrorDict

# クエリキャッシュ
_query_cache: Dict[str, tuple[str, float]] = {}  # {path: (query, mtime)}


def clear_query_cache() -> None:
    """クエリキャッシュをクリアする"""
    global _query_cache
    _query_cache.clear()


def load_query_from_file(path: Path, force_reload: bool = False) -> Union[str, ErrorDict]:
    """
    クエリファイルを読み込む
    
    Args:
        path: クエリファイルのパス
        force_reload: キャッシュを無視して強制的に再読み込みする
        
    Returns:
        成功時: クエリ文字列
        失敗時: ErrorDict
    """
    # ファイルの存在チェック
    if not path.exists():
        return ErrorDict(
            ok=False,
            error="Query file not found",
            details={"path": str(path)}
        )
    
    try:
        path_str = str(path.absolute())
        
        # キャッシュチェック
        if not force_reload and path_str in _query_cache:
            cached_query, cached_mtime = _query_cache[path_str]
            current_mtime = os.path.getmtime(path_str)
            
            # ファイルが変更されていなければキャッシュを返す
            if current_mtime == cached_mtime:
                return cached_query
        # ファイルを読み込む
        content = path.read_text(encoding="utf-8").strip()
        
        # 空ファイルチェック
        if not content:
            return ErrorDict(
                ok=False,
                error="Query file is empty",
                details={"path": str(path)}
            )
        
        # コメント行を除去 (// と -- の両方をサポート)
        lines = content.split('\n')
        query_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that start with // or --
            if stripped.startswith('//') or stripped.startswith('--'):
                continue
            # Remove inline -- comments
            if '--' in line:
                line = line[:line.index('--')]
            # Add non-empty lines
            if line.strip():
                query_lines.append(line)
        
        query = '\n'.join(query_lines).strip()
        
        # コメント除去後に空になった場合
        if not query:
            return ErrorDict(
                ok=False,
                error="Query file is empty after removing comments",
                details={"path": str(path)}
            )
        
        # キャッシュに保存
        current_mtime = os.path.getmtime(path_str)
        _query_cache[path_str] = (query, current_mtime)
        
        return query
        
    except Exception as e:
        return ErrorDict(
            ok=False,
            error=f"Failed to read query file: {str(e)}",
            details={"path": str(path), "exception": str(e)}
        )