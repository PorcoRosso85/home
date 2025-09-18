# FTSSearchSystem クラス設計

## 概要

`FTSSearchSystem`クラスは、`SearchSystem`プロトコルを実装し、既存のFTS関数をラップして統一APIを提供します。VSS側の`VSS`クラスと同様のパターンで実装します。

## クラス構造

```python
from typing import Dict, List, Any, Optional
from protocols import SearchSystem
from types import SearchConfig, IndexResult, SearchResults, SearchResultItem


class FTSSearchSystem:
    """
    FTS統一APIインターフェース
    
    create_fts()で作成し、SearchSystemプロトコルを実装
    """
    
    def __init__(self, config: SearchConfig, connection: Any, database: Any):
        """内部使用のみ - create_fts()を使用してください"""
        self.config = config
        self._connection = connection
        self._database = database
        self._closed = False
    
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        ドキュメントをFTSインデックスに追加
        
        既存のindex_fts_documents関数をラップし、
        結果をIndexResult型に変換して返す
        """
        if self._closed:
            raise RuntimeError("FTSSearchSystem is already closed")
        
        # 既存のヘルパー関数を使用
        result = _index_documents_with_connection(documents, self._connection)
        
        # IndexResult型に変換
        if result["ok"]:
            return IndexResult(
                ok=True,
                indexed_count=result["indexed_count"],
                index_time_ms=result["index_time_ms"],
                status=result["status"]
            ).to_dict()
        else:
            return IndexResult(
                ok=False,
                indexed_count=0,
                index_time_ms=0.0,
                status="failed",
                error=result["error"],
                details=result.get("details")
            ).to_dict()
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        FTS検索を実行
        
        既存のsearch_fts_documents関数をラップし、
        結果をSearchResults型に変換して返す
        """
        if self._closed:
            raise RuntimeError("FTSSearchSystem is already closed")
        
        search_input = {"query": query, "limit": limit}
        search_input.update(kwargs)
        
        # 既存のヘルパー関数を使用
        result = _search_documents_with_connection(
            search_input, self._connection, self.config
        )
        
        # SearchResults型に変換
        if result["ok"]:
            items = []
            for r in result["results"]:
                items.append(SearchResultItem(
                    id=r["id"],
                    content=r["content"],
                    score=r["score"],
                    highlights=r.get("highlights", [])
                ))
            
            return SearchResults(
                ok=True,
                results=items,
                metadata=result["metadata"]
            ).to_dict()
        else:
            return SearchResults(
                ok=False,
                results=[],
                metadata={},
                error=result["error"],
                details=result.get("details")
            ).to_dict()
    
    def close(self) -> None:
        """データベース接続をクローズ"""
        if not self._closed:
            from infrastructure import close_connection
            close_connection(self._connection)
            self._closed = True


def create_fts(
    db_path: str = "./kuzu_db",
    in_memory: bool = False,
    **kwargs
) -> FTSSearchSystem:
    """
    FTS統一APIインスタンスを作成
    
    Args:
        db_path: データベースパス
        in_memory: インメモリデータベースを使用するか
        **kwargs: その他の設定パラメータ
    
    Returns:
        FTSSearchSystemインスタンス
    
    Example:
        fts = create_fts(in_memory=True)
        fts.index([{"id": "1", "title": "タイトル", "content": "本文"}])
        results = fts.search("検索語")
        fts.close()
    """
    # SearchConfigを作成
    config = SearchConfig(
        db_path=db_path,
        in_memory=in_memory,
        default_limit=kwargs.get('default_limit', 10)
    )
    
    # 既存のcreate_fts_connection関数を使用
    conn_result = create_fts_connection(db_path, in_memory)
    
    if not conn_result["ok"]:
        raise RuntimeError(
            f"Failed to create FTS connection: {conn_result.get('error', 'Unknown error')}"
        )
    
    return FTSSearchSystem(
        config=config,
        connection=conn_result["connection"],
        database=conn_result["database"]
    )
```

## 設計のポイント

1. **プロトコル準拠**: `SearchSystem`プロトコルのすべてのメソッドを実装
2. **既存コードの再利用**: 既存の`_index_documents_with_connection`と`_search_documents_with_connection`を活用
3. **型安全性**: 共通型（`IndexResult`, `SearchResults`, `SearchResultItem`）を使用
4. **リソース管理**: `close()`メソッドで適切にリソースを解放
5. **エラーハンドリング**: 閉じられた接続への操作を防ぐチェック

## VSS側との統一性

- 両方とも`create_xxx()`関数でインスタンスを作成
- 同じメソッド名（`index()`, `search()`, `close()`）
- 同じ結果型を返す
- 設定は`xxxConfig`データクラスで管理

## 実装の次のステップ

1. `application.py`に`FTSSearchSystem`クラスを追加
2. 既存の関数との互換性を維持
3. テストを追加して動作を確認
4. `__init__.py`でエクスポート