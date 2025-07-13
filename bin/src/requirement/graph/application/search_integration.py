"""
POC Search統合モジュール
重複検出にPOC searchのハイブリッド検索（VSS + FTS）を活用
"""

from typing import List, Dict, Any, Optional
from ..search.infrastructure.search_service_factory import SearchServiceFactory
from ..search.infrastructure.kuzu_search_service import KuzuSearchService


class SearchIntegration:
    """POC Searchを利用した重複検出 - 直接POC Search APIを使用"""
    
    def __init__(self, db_path: Optional[str] = None, connection: Optional[Any] = None):
        """
        Args:
            db_path: SearchServiceのデータベースパス（Noneの場合は一時DB）
            connection: 既存のKuzuDB接続（指定された場合はdb_pathは無視）
        """
        if connection:
            # 既存の接続を使用
            self.search_service = KuzuSearchService(connection=connection)
        else:
            # POC searchのKuzuSearchServiceを直接使用
            self.search_service = KuzuSearchService(db_path=db_path)
    
    def check_duplicates(self, text: str, k: int = 5, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        テキストの重複をチェック
        
        Args:
            text: 検索対象テキスト
            k: 取得する類似結果の最大数
            threshold: 類似度の閾値（0.0-1.0）
            
        Returns:
            類似要件のリスト（スコア順）
        """
        try:
            # POC searchのハイブリッド検索を利用
            results = self.search_service.search_hybrid(
                query=text,
                k=k
            )
            
            # 閾値以上のスコアの結果のみ返す
            duplicates = []
            for result in results:
                # SearchResultオブジェクトから属性として取得
                if result.score >= threshold:
                    duplicates.append({
                        "id": result.id,
                        "title": result.title,
                        "description": result.content,  # SearchResultのcontentにはdescriptionが入っている
                        "score": result.score,
                        "type": "hybrid"  # VSS + FTSのハイブリッド
                    })
            
            return duplicates
            
        except Exception as e:
            # エラー時は空リストを返す（検索失敗を理由に処理を止めない）
            print(f"Search error: {str(e)}")
            return []
    
    def add_to_search_index(self, requirement: Dict[str, Any]) -> bool:
        """
        要件を検索インデックスに追加
        
        Args:
            requirement: 追加する要件データ
            
        Returns:
            成功時True
        """
        try:
            # POC searchのadd_requirementメソッドを直接使用
            self.search_service.add_requirement(
                id=requirement.get("id"),
                title=requirement.get("title", ""),
                description=requirement.get("description", "")
            )
            return True
            
        except Exception as e:
            print(f"Index error: {str(e)}")
            return False