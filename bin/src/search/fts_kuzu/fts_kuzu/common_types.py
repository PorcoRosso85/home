#!/usr/bin/env python3
"""
Common Result Types

FTSとVSSで共通の結果型定義
不変データ構造として実装
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class SearchResultItem:
    """
    個別の検索結果アイテム
    
    Attributes:
        id: ドキュメントID
        content: ドキュメント内容
        score: 関連度スコア（0.0-1.0）
        highlights: ハイライト情報（FTS用、オプション）
        distance: 距離（VSS用、オプション）
    """
    id: str
    content: str
    score: float
    highlights: List[str] = None
    distance: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "id": self.id,
            "content": self.content,
            "score": self.score
        }
        if self.highlights is not None:
            result["highlights"] = self.highlights
        if self.distance is not None:
            result["distance"] = self.distance
        return result


@dataclass(frozen=True)
class SearchResults:
    """
    検索結果のコンテナ
    
    Attributes:
        ok: 成功/失敗フラグ
        results: 検索結果のリスト
        metadata: メタデータ（検索時間、クエリなど）
        error: エラーメッセージ（失敗時のみ）
        details: 追加の詳細情報
    """
    ok: bool
    results: List[SearchResultItem]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "ok": self.ok,
            "results": [item.to_dict() for item in self.results],
            "metadata": self.metadata
        }
        if self.error:
            result["error"] = self.error
        if self.details:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class IndexResult:
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
    ok: bool
    indexed_count: int
    index_time_ms: float
    status: str = "success"
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        result = {
            "ok": self.ok,
            "indexed_count": self.indexed_count,
            "index_time_ms": self.index_time_ms,
            "status": self.status
        }
        if self.error:
            result["error"] = self.error
        if self.details:
            result["details"] = self.details
        return result


@dataclass(frozen=True)
class SearchConfig:
    """
    検索システムの設定
    
    Attributes:
        db_path: データベースパス
        in_memory: インメモリデータベースを使用するか
        default_limit: デフォルトの検索結果数
    """
    db_path: str = "./kuzu_db"
    in_memory: bool = False
    default_limit: int = 10