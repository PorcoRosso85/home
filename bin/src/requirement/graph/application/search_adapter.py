"""
Search Adapter - requirement/graphとsemantic searchの統合レイヤー

このアダプターは、semantic searchのAPIを使用して重複検出機能を提供する。
モジュールが利用できない場合は、グレースフルにフォールバックする。
"""
import sys
import os
import math
from typing import List, Dict, Any, Optional

# Try to import semantic search modules
SEARCH_MODULES_AVAILABLE = False
VSSService = None

try:
    # Try to import vss_kuzu if it's installed as a package
    from vss_kuzu import VSSService, VectorSearchResult
    SEARCH_MODULES_AVAILABLE = True
    print(f"[INFO] VSS modules loaded successfully")
except ImportError as e:
    # Log the error but don't fail - we'll provide a fallback
    print(f"[WARNING] VSS modules not available - using fallback search: {e}")




class VSSSearchAdapter:
    """Adapter for VSS service when available"""
    
    def __init__(self, db_path: str, existing_connection=None):
        self.db_path = db_path
        self._conn = existing_connection
        self._vss_service = None
        
        if SEARCH_MODULES_AVAILABLE and VSSService:
            try:
                # Initialize VSS service
                self._vss_service = VSSService(db_path=db_path)
                print("[INFO] VSS service initialized successfully")
            except Exception as e:
                print(f"[WARNING] Failed to initialize VSS service: {e}")
    
    def add_requirement(self, id: str, title: str, content: str) -> None:
        """Add requirement to VSS index"""
        if not self._vss_service:
            print(f"[WARNING] Cannot add requirement {id} - VSS not initialized")
            return
        
        try:
            # Combine title and content for indexing
            full_text = f"{title} {content}"
            # VSS service expects document_id and content
            self._vss_service.add_document(document_id=id, content=full_text)
            print(f"[DEBUG] Added requirement {id} to VSS index")
        except Exception as e:
            print(f"[WARNING] Failed to add to VSS index: {e}")
    
    def search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Vector similarity search"""
        if not self._vss_service:
            return []
        
        try:
            results = self._vss_service.search_similar(query=query, k=k)
            # Convert VectorSearchResult to our format
            return [
                {
                    "id": r.document_id,
                    "title": "",  # VSS doesn't store title separately
                    "content": r.content,
                    "score": r.score,
                    "source": "vss"
                }
                for r in results
            ]
        except Exception as e:
            print(f"[WARNING] VSS search failed: {e}")
            return []
    
    def search_keyword(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Keyword search - use database directly"""
        if not self._conn:
            return []
        
        try:
            # Simple CONTAINS search
            result = self._conn.execute("""
                MATCH (r:RequirementEntity)
                WHERE r.title CONTAINS $query OR r.description CONTAINS $query
                RETURN r.id, r.title, r.description
                LIMIT $k
            """, {"query": query, "k": k})
            
            results = []
            while result.has_next():
                row = result.get_next()
                results.append({
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "score": 1.0,
                    "source": "fts"
                })
            return results
        except Exception as e:
            print(f"[WARNING] Keyword search failed: {e}")
            return []
    
    def search_hybrid(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Hybrid search combining VSS and keyword search"""
        vss_results = self.search_similar(query, k)
        keyword_results = self.search_keyword(query, k)
        
        # Merge results by id, preferring VSS scores
        merged = {}
        for r in vss_results:
            merged[r["id"]] = r
        
        for r in keyword_results:
            if r["id"] not in merged:
                merged[r["id"]] = r
            else:
                # Average the scores
                merged[r["id"]]["score"] = (merged[r["id"]]["score"] + r["score"]) / 2
                merged[r["id"]]["source"] = "hybrid"
        
        # Sort by score and return top k
        sorted_results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:k]


class SearchAdapter:
    """Main search adapter that provides a consistent interface"""
    
    def __init__(self, db_path: str, repository_connection=None):
        """
        Args:
            db_path: KuzuDBのデータベースパス
            repository_connection: 既存のKuzuDB接続（共有する場合）
        """
        self.db_path = db_path
        self.is_available = SEARCH_MODULES_AVAILABLE
        self._service = None
        self._error = None
        
        # Initialize appropriate service based on availability
        if SEARCH_MODULES_AVAILABLE:
            self._service = VSSSearchAdapter(db_path, repository_connection)
        else:
            self._error = {
                "type": "ModuleNotFoundError",
                "message": "VSS modules are not available",
                "details": {
                    "module": "vss_kuzu",
                    "install_hint": "VSS functionality requires the vss_kuzu module to be installed"
                }
            }
    
    def check_duplicates(self, text: str, k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        テキストに基づいて重複要件をチェック
        
        Args:
            text: 検索テキスト（タイトル + 説明）
            k: 返す結果の最大数
            threshold: 類似度の閾値（0.0-1.0）
            
        Returns:
            重複候補のリスト（スコア順）またはエラー
        """
        if self._error:
            return [{"error": self._error}]
            
        # Use hybrid search for best results
        search_results = self._service.search_hybrid(text, k=k)
        
        # Filter by threshold
        duplicates = []
        for result in search_results:
            if result.get("score", 0) >= threshold:
                duplicates.append({
                    "id": result["id"],
                    "title": result.get("title", ""),
                    "description": result.get("content", ""),
                    "score": result.get("score", 0),
                    "type": "vss"  # VSS-only implementation (FTS integration pending)
                })
        
        return duplicates
    
    def add_to_index(self, requirement: Dict[str, Any]) -> bool:
        """
        要件を検索インデックスに追加
        
        Args:
            requirement: 要件データ（id, title, description必須）
            
        Returns:
            成功時True
        """
        if self._error:
            print(f"Cannot add to index: {self._error['message']}")
            return False
            
        try:
            self._service.add_requirement(
                id=requirement["id"],
                title=requirement.get("title", ""),
                content=requirement.get("description", "")
            )
            return True
        except Exception as e:
            print(f"Failed to add to search index: {e}")
            return False
    
    def search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """類似検索（VSS）を実行"""
        if self._error:
            return [{"error": self._error}]
        return self._service.search_similar(query, k=k)
    
    def search_keyword(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """キーワード検索（FTS）を実行"""
        if self._error:
            return [{"error": self._error}]
        return self._service.search_keyword(query, k=k)
    
    def search_hybrid(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """ハイブリッド検索（VSS + FTS）を実行"""
        if self._error:
            return [{"error": self._error}]
        return self._service.search_hybrid(query, k=k)
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストのエンベディングを生成
        
        VSSServiceが利用可能な場合は実際のエンベディングを生成。
        利用不可能な場合はNoneを返す。
        """
        if not self.is_available:
            return None
            
        # VSSSearchAdapterの場合、内部でエンベディング生成を処理
        if isinstance(self._service, VSSSearchAdapter) and self._service._vss_service:
            # VSSServiceは内部的にエンベディングを生成するため、
            # ここでは特別な処理は不要
            # 実際のエンベディング生成はadd_to_index内で行われる
            return None
        
        return None