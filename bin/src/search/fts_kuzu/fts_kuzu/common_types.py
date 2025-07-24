#!/usr/bin/env python3
"""
Common Result Types

FTSとVSSで共通の結果型定義
TypedDictで型安全な辞書として実装
"""

from typing import List, Dict, Any, Optional, TypedDict


class SearchResultItem(TypedDict, total=False):
    """
    個別の検索結果アイテム
    
    Attributes:
        id: ドキュメントID
        content: ドキュメント内容
        score: 関連度スコア（0.0-1.0）
        highlights: ハイライト情報（FTS用、オプション）
        distance: 距離（VSS用、オプション）
    """
    id: str  # required
    content: str  # required
    score: float  # required
    highlights: List[str]  # optional
    distance: float  # optional


class SearchResults(TypedDict, total=False):
    """
    検索結果のコンテナ
    
    Attributes:
        ok: 成功/失敗フラグ
        results: 検索結果のリスト
        metadata: メタデータ（検索時間、クエリなど）
        error: エラーメッセージ（失敗時のみ）
        details: 追加の詳細情報
    """
    ok: bool  # required
    results: List[SearchResultItem]  # required
    metadata: Dict[str, Any]  # required
    error: str  # optional
    details: Dict[str, Any]  # optional


class IndexResult(TypedDict, total=False):
    """
    インデックス操作の結果
    
    Attributes:
        ok: 成功/失敗フラグ
        indexed_count: インデックスされたドキュメント数
        index_time_ms: 処理時間（ミリ秒）
        status: ステータス文字列
        error: エラーメッセージ（失敗時のみ）
        details: 追加の詳細情報
    """
    ok: bool  # required
    indexed_count: int  # required
    index_time_ms: float  # required
    status: str  # required (with default "success")
    error: str  # optional
    details: Dict[str, Any]  # optional


class SearchConfig(TypedDict, total=False):
    """
    検索システムの設定
    
    Attributes:
        db_path: データベースパス
        in_memory: インメモリデータベースを使用するか
        default_limit: デフォルトの検索結果数
    """
    db_path: str  # optional (with default "./kuzu_db")
    in_memory: bool  # optional (with default False)
    default_limit: int  # optional (with default 10)