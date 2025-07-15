"""
検索サービスのドメインインターフェース
実装詳細から独立した、ビジネスロジックの契約を定義
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SearchResult:
    """検索結果を表す値オブジェクト"""
    id: str
    title: str
    content: str
    score: float
    source: str  # "vss", "fts", "cypher", "hybrid"
    
    def __post_init__(self):
        """バリデーション"""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0 and 1, got {self.score}")
        if self.source not in ["vss", "fts", "cypher", "hybrid"]:
            raise ValueError(f"Invalid source: {self.source}")


class SearchService(ABC):
    """検索サービスのインターフェース（抽象基底クラス）"""
    
    @abstractmethod
    def search_similar(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        類似検索を実行
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            
        Returns:
            類似度順にソートされた検索結果のリスト
        """
        pass
    
    @abstractmethod
    def search_keyword(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        キーワード検索を実行
        
        Args:
            query: 検索キーワード
            k: 返す結果の最大数
            
        Returns:
            関連度順にソートされた検索結果のリスト
        """
        pass
    
    @abstractmethod
    def search_hybrid(self, query: str, k: int = 10) -> List[SearchResult]:
        """
        ハイブリッド検索を実行（VSS + FTS + Graph）
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            
        Returns:
            統合スコア順にソートされた検索結果のリスト
        """
        pass
    
    @abstractmethod
    def add_requirement(self, id: str, title: str, content: str) -> None:
        """
        要件を追加（テスト用）
        
        Args:
            id: 要件ID
            title: 要件タイトル
            content: 要件内容
        """
        pass