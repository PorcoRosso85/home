"""
型安全なクエリローダー

requirement/graph互換のインターフェースを提供
"""
import os
from pathlib import Path
from typing import Union, Dict, Any, Optional
from functools import lru_cache

from errors import FileOperationError, ValidationError, NotFoundError
from variables import DEFAULT_QUERY_DIR


def load_typed_query(
    query_name: str,
    query_type: str = "auto",
    base_dir: Optional[str] = None
) -> Union[str, FileOperationError, ValidationError, NotFoundError]:
    """
    requirement/graph互換のクエリ読み込み関数
    
    Args:
        query_name: クエリ名（拡張子なし）
        query_type: "dml", "dql", "auto"のいずれか
        base_dir: クエリディレクトリのベースパス
        
    Returns:
        成功時: クエリ文字列
        失敗時: エラー型（FileOperationError, ValidationError, NotFoundError）
    """
    # query_typeのバリデーション
    valid_types = ["dml", "dql", "auto"]
    if query_type not in valid_types:
        return ValidationError(
            type="ValidationError",
            message=f"Invalid query_type: {query_type}",
            field="query_type",
            value=query_type,
            constraint=f"Must be one of {valid_types}",
            suggestion=f"Use 'auto' to automatically detect query type"
        )
    
    # ベースディレクトリの決定
    if base_dir is None:
        base_dir = DEFAULT_QUERY_DIR
    
    base_path = Path(base_dir)
    if not base_path.exists():
        return FileOperationError(
            type="FileOperationError",
            message=f"Query directory not found: {base_dir}",
            operation="read",
            file_path=str(base_path),
            permission_issue=False,
            exists=False
        )
    
    # クエリファイルの探索
    file_paths = []
    
    if query_type == "auto":
        # dml, dqlの順で探索
        file_paths = [
            base_path / "dml" / f"{query_name}.cypher",
            base_path / "dql" / f"{query_name}.cypher",
            base_path / f"{query_name}.cypher"
        ]
    else:
        # 指定されたタイプのディレクトリのみ探索
        file_paths = [
            base_path / query_type / f"{query_name}.cypher",
            base_path / f"{query_name}.cypher"
        ]
    
    # ファイルを順に探索
    for file_path in file_paths:
        if file_path.exists():
            try:
                return _read_and_clean_query(str(file_path))
            except Exception as e:
                return FileOperationError(
                    type="FileOperationError",
                    message=f"Failed to read query file: {str(e)}",
                    operation="read",
                    file_path=str(file_path),
                    permission_issue=True,
                    exists=True
                )
    
    # ファイルが見つからない場合
    search_locations = [str(p) for p in file_paths]
    return NotFoundError(
        type="NotFoundError",
        message=f"Query '{query_name}' not found",
        resource_type="query",
        resource_id=query_name,
        search_locations=search_locations
    )


@lru_cache(maxsize=128)
def _read_and_clean_query(file_path: str) -> str:
    """クエリファイルを読み込み、コメントを除去"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # コメント行を除去（//と--の両方をサポート）
    cleaned_lines = []
    for line in lines:
        # 行頭のコメントを除去
        stripped = line.strip()
        if not stripped.startswith('//') and not stripped.startswith('--'):
            cleaned_lines.append(line.rstrip())
    
    return '\n'.join(cleaned_lines).strip()


def execute_query(
    repository: Dict[str, Any],
    query_name: str,
    params: Dict[str, Any],
    query_type: str = "auto"
) -> Union[Dict[str, Any], FileOperationError, ValidationError, NotFoundError]:
    """
    requirement/graph互換のクエリ実行関数
    
    Args:
        repository: executeメソッドを持つリポジトリオブジェクト
        query_name: クエリ名
        params: クエリパラメータ
        query_type: クエリタイプ
        
    Returns:
        成功時: クエリ結果
        失敗時: エラー型
    """
    # クエリの読み込み
    query_result = load_typed_query(query_name, query_type)
    
    # エラーチェック
    if isinstance(query_result, dict):
        # エラー型が返された場合
        return query_result
    
    # クエリの実行
    try:
        result = repository["execute"](query_result, params)
        return {"ok": True, "result": result}
    except Exception as e:
        return ValidationError(
            type="ValidationError",
            message=f"Query execution failed: {str(e)}",
            field="query",
            value=query_name,
            constraint="Valid Cypher query",
            suggestion="Check query syntax and parameters"
        )