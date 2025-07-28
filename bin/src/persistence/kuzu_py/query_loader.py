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


def load_structured_query(
    query_name: str,
    query_type: str = "auto",
    base_dir: str = "."
) -> Union[str, ErrorDict]:
    """
    構造化されたディレクトリからクエリを読み込む
    
    Args:
        query_name: クエリ名（拡張子なし）
        query_type: "dml", "dql", "auto"（自動検出）
        base_dir: クエリディレクトリのベースパス
        
    Returns:
        成功時: クエリ文字列
        失敗時: ErrorDict
    """
    base_path = Path(base_dir)
    
    # query_typeの検証
    import variables
    if query_type not in variables.VALID_QUERY_TYPES:
        return ErrorDict(
            ok=False,
            error=f"Invalid query_type: {query_type}",
            details={"valid_types": variables.VALID_QUERY_TYPES}
        )
    
    # ファイル名
    filename = f"{query_name}{variables.QUERY_FILE_EXTENSION}"
    
    # autoの場合、両方のディレクトリを検索
    if query_type == "auto":
        for type_dir in ["dml", "dql"]:
            query_path = base_path / type_dir / filename
            if query_path.exists():
                return load_query_from_file(query_path)
        
        # 見つからない場合
        return ErrorDict(
            ok=False,
            error="Query file not found",
            details={
                "query_name": query_name,
                "searched_paths": [
                    str(base_path / "dml" / filename),
                    str(base_path / "dql" / filename)
                ]
            }
        )
    
    # 特定のタイプが指定された場合
    query_path = base_path / query_type / filename
    
    # ディレクトリが存在しない場合もエラーとして扱う
    if not query_path.parent.exists():
        return ErrorDict(
            ok=False,
            error=f"{query_type} directory not found",
            details={"expected_dir": str(query_path.parent)}
        )
    
    # ファイルの読み込み
    result = load_query_from_file(query_path)
    
    # エラーの場合、詳細情報を追加
    if isinstance(result, dict) and not result.get("ok", True):
        result["details"]["query_name"] = query_name
        result["details"]["query_type"] = query_type
    
    return result