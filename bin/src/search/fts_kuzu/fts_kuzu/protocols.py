#!/usr/bin/env python3
"""
Search System Protocol Definition

共通のインターフェースとなるProtocolを定義
FTSとVSSで統一されたAPIを提供
"""

from typing import Protocol, Any, Dict, List, runtime_checkable


class SearchSystem(Protocol):
    """
    検索システムの統一プロトコル
    
    FTSとVSSの両方で実装される共通インターフェース
    """
    
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        ドキュメントをインデックスに追加
        
        Args:
            documents: インデックスするドキュメントのリスト
                      各ドキュメントは最低限 {"id": str, "content": str} を含む
        
        Returns:
            インデックス結果を含む辞書:
            - ok: bool - 成功/失敗
            - indexed_count: int - インデックスされたドキュメント数
            - index_time_ms: float - 処理時間（ミリ秒）
            - error: str - エラーメッセージ（失敗時のみ）
            - details: dict - 追加の詳細情報
        """
        ...
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        ドキュメントを検索
        
        Args:
            query: 検索クエリ文字列
            limit: 返す結果の最大数
            **kwargs: 実装固有の追加パラメータ
                     FTS: なし
                     VSS: query_vector, efs など
        
        Returns:
            検索結果を含む辞書:
            - ok: bool - 成功/失敗
            - results: List[Dict] - 検索結果のリスト
            - metadata: Dict - メタデータ（total_results, query, search_time_ms など）
            - error: str - エラーメッセージ（失敗時のみ）
            - details: dict - 追加の詳細情報
        """
        ...
    
    def close(self) -> None:
        """
        リソースをクリーンアップ
        
        データベース接続やその他のリソースを解放
        """
        ...


@runtime_checkable
class FTSAlgebra(Protocol):
    """
    FTS操作の代数的インターフェース
    
    Protocol-based algebraic design following Tagless Final pattern.
    This enables type-safe structural subtyping and multiple implementations.
    """
    
    def index(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        ドキュメントをインデックスに追加
        
        Args:
            documents: インデックスするドキュメントのリスト
                      各ドキュメントは最低限 {"id": str, "content": str} を含む
                      オプションで "title" フィールドも可能
        
        Returns:
            インデックス結果を含む辞書:
            - ok: bool - 成功/失敗
            - indexed_count: int - インデックスされたドキュメント数
            - index_time_ms: float - 処理時間（ミリ秒）
            - error: str - エラーメッセージ（失敗時のみ）
            - details: dict - 追加の詳細情報
        """
        ...
    
    def search(self, query: str, limit: int = 10, **kwargs) -> Dict[str, Any]:
        """
        ドキュメントを検索
        
        Args:
            query: 検索クエリ文字列
            limit: 返す結果の最大数
            **kwargs: 実装固有の追加パラメータ
        
        Returns:
            検索結果を含む辞書:
            - ok: bool - 成功/失敗
            - results: List[Dict] - 検索結果のリスト
            - metadata: Dict - メタデータ（total_results, query, search_time_ms など）
            - error: str - エラーメッセージ（失敗時のみ）
            - details: dict - 追加の詳細情報
        """
        ...