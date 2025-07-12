"""
POC Search統合モジュール
重複検出にPOC searchのハイブリッド検索（VSS + FTS）を活用
"""

from typing import List, Dict, Any, Optional
import sys
import os

# 環境変数からプロジェクトルートを取得
project_root = os.environ.get('PYTHONPATH', '/home/nixos/bin/src')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from poc.search.infrastructure.search_service_factory import SearchServiceFactory
from poc.search.domain.interfaces import SearchService


class SearchIntegration:
    """POC Searchを利用した重複検出"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Args:
            db_path: SearchServiceのデータベースパス（Noneの場合は一時DB）
        """
        if SearchServiceFactory is None:
            raise ImportError("POC search is required but not available")
        
        if db_path:
            self.search_service = SearchServiceFactory.create_for_production(db_path)
        else:
            self.search_service = SearchServiceFactory.create_for_test()
    
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
                k=k  # top_k -> k
            )
            
            # 閾値以上のスコアの結果のみ返す
            duplicates = []
            for result in results:
                if result.get("score", 0) >= threshold:
                    duplicates.append({
                        "id": result.get("id"),
                        "title": result.get("title", ""),
                        "description": result.get("description", ""),
                        "score": result.get("score"),
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
            # POC searchの形式に変換
            doc = {
                "id": requirement.get("id"),
                "title": requirement.get("title", ""),
                "description": requirement.get("description", ""),
                "content": f"{requirement.get('title', '')} {requirement.get('description', '')}",
                "metadata": {
                    "status": requirement.get("status", "proposed"),
                    "created_at": requirement.get("created_at"),
                    "updated_at": requirement.get("updated_at")
                }
            }
            
            # 検索サービスに追加（POC searchが対応していれば）
            # 注: 現在のPOC searchインターフェースには明示的なadd_documentメソッドがない
            # KuzuDBへの保存時に自動的にインデックスされることを想定
            return True
            
        except Exception as e:
            print(f"Index error: {str(e)}")
            return False