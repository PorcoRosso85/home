"""
SearchServiceのファクトリー
テスト用と本番用のインスタンス生成を管理
"""

from typing import Optional
from poc.search.domain.interfaces import SearchService
from poc.search.infrastructure.kuzu_search_service import KuzuSearchService


class SearchServiceFactory:
    """SearchServiceインスタンスを生成するファクトリー"""
    
    @staticmethod
    def create_for_test() -> SearchService:
        """
        テスト用のSearchServiceインスタンスを生成
        
        Returns:
            一時的なデータベースを使用するSearchService
        """
        # 一時ディレクトリを使用
        return KuzuSearchService(db_path=None)
    
    @staticmethod
    def create_for_production(db_path: str) -> SearchService:
        """
        本番用のSearchServiceインスタンスを生成
        
        Args:
            db_path: データベースパス
            
        Returns:
            指定されたデータベースを使用するSearchService
        """
        return KuzuSearchService(db_path=db_path)
    
    @staticmethod
    def create_with_mock_embeddings() -> SearchService:
        """
        モック埋め込みを使用するSearchServiceインスタンスを生成
        （sentence_transformersが利用できない環境用）
        
        Returns:
            決定論的なモック埋め込みを使用するSearchService
        """
        # KuzuSearchServiceは内部でフォールバック処理を行う
        return KuzuSearchService(db_path=None)