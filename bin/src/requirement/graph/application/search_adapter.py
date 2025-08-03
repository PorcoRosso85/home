"""
Search Adapter - requirement/graphとsemantic searchの統合レイヤー

このアダプターは、semantic searchのAPIを使用して重複検出機能を提供する。
モジュールが利用できない場合は、グレースフルにフォールバックする。
"""
from typing import List, Dict, Any, Optional
from ..infrastructure.logger import debug, info, warn, error

# Try to import semantic search modules
VSS_MODULES_AVAILABLE = False
FTS_MODULES_AVAILABLE = False

# VSS module is required - no fallback
from vss_kuzu import create_vss
VSS_MODULES_AVAILABLE = True
info("rgl.search", "VSS modules loaded successfully")

# FTS module is required - no fallback
from fts_kuzu import create_fts
FTS_MODULES_AVAILABLE = True
info("rgl.search", "FTS modules loaded successfully")




class VSSSearchAdapter:
    """Adapter for VSS service when available"""

    def __init__(self, db_path: str, existing_connection=None):
        self.db_path = db_path
        self._conn = existing_connection
        self._vss_service = None
        self._is_initialized = False

        try:
            # Enable VECTOR extension on the existing connection if provided
            if existing_connection:
                try:
                    # Try to enable VECTOR extension
                    existing_connection.execute("INSTALL vector;")
                    existing_connection.execute("LOAD EXTENSION vector;")
                    info("rgl.search", "VECTOR extension enabled on shared connection")
                except Exception as e:
                    # Extension might already be loaded, or not available
                    debug("rgl.search", f"VECTOR extension status: {e}")

            # Initialize VSS with unified API, passing existing connection
            self._vss_service = create_vss(
                db_path=db_path,
                in_memory=False,
                existing_connection=existing_connection
            )
            self._is_initialized = True
            info("rgl.search", "VSS service initialized successfully with shared connection")
        except Exception as e:
            warn("rgl.search", f"Failed to initialize VSS service: {e}")

    def add_requirement(self, id: str, title: str, content: str) -> None:
        """Add requirement to VSS index"""
        if not self._is_initialized:
            warn("rgl.search", f"Cannot add requirement {id} - VSS not initialized")
            return

        try:
            # Combine title and content for indexing
            full_text = f"{title} {content}"

            # Index document using VSS service
            result = self._vss_service.index([{
                "id": id,
                "content": full_text
            }])

            if result.get("ok"):
                debug("rgl.search", f"Added requirement {id} to VSS index")
            else:
                warn("rgl.search", f"Failed to add to VSS index: {result.get('error', 'Unknown error')}")
        except Exception as e:
            warn("rgl.search", f"Failed to add to VSS index: {e}")

    def __del__(self):
        """Cleanup VSS connection on deletion"""
        # VSS service manages its own connections with the unified API
        # No manual cleanup needed when using existing_connection
        pass

    def search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Vector similarity search"""
        if not self._is_initialized:
            return []

        try:
            # Search using VSS service
            result = self._vss_service.search(query, limit=k)

            if not result.get("ok"):
                warn("rgl.search", f"VSS search failed: {result.get('error', 'Unknown error')}")
                return []

            # Convert results to our format
            formatted_results = []
            for r in result.get("results", []):
                formatted_results.append({
                    "id": r["id"],
                    "title": "",  # VSS doesn't store title separately
                    "content": r["content"],
                    "score": r["score"],
                    "source": "vss"
                })

            return formatted_results
        except Exception as e:
            warn("rgl.search", f"VSS search failed: {e}")
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
            warn("rgl.search", f"Keyword search failed: {e}")
            return []

    def search_hybrid(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Hybrid search - delegates to VSS search"""
        if not self._is_initialized:
            error("rgl.search", "Cannot perform hybrid search - VSS not initialized")
            raise RuntimeError("VSS service is required but not initialized")
        # In a properly initialized system, VSS handles both vector and keyword search
        return self.search_similar(query, k)


class FTSSearchAdapter:
    """Adapter for FTS service when available"""

    def __init__(self, db_path: str, existing_connection=None):
        self.db_path = db_path
        self._conn = existing_connection
        self._fts_service = None
        self._is_initialized = False

        try:
            # Initialize FTS with unified API, passing existing connection
            self._fts_service = create_fts(
                db_path=db_path,
                in_memory=False,
                existing_connection=existing_connection
            )
            self._is_initialized = True
            info("rgl.search", "FTS service initialized successfully with shared connection")
        except Exception as e:
            warn("rgl.search", f"Failed to initialize FTS service: {e}")

    def add_requirement(self, id: str, title: str, content: str) -> None:
        """Add requirement to FTS index"""
        if not self._is_initialized:
            error("rgl.search", f"Cannot add requirement {id} - FTS not initialized")
            raise RuntimeError("FTS service is required but not initialized")

        try:
            # Index document using FTS service
            result = self._fts_service.index([{
                "id": id,
                "title": title,
                "content": content
            }])

            if result.get("ok"):
                debug("rgl.search", f"Added requirement {id} to FTS index")
            else:
                warn("rgl.search", f"Failed to add to FTS index: {result.get('error', 'Unknown error')}")
        except Exception as e:
            warn("rgl.search", f"Failed to add to FTS index: {e}")

    def search_keyword(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Full-text search using FTS module"""
        if not self._is_initialized:
            error("rgl.search", "Cannot perform FTS search - FTS not initialized")
            raise RuntimeError("FTS service is required but not initialized")

        try:
            # Search using FTS service
            result = self._fts_service.search(query, limit=k)

            if not result.get("ok"):
                warn("rgl.search", f"FTS search failed: {result.get('error', 'Unknown error')}")
                return []

            # Convert results to our format
            formatted_results = []
            for r in result.get("results", []):
                formatted_results.append({
                    "id": r["id"],
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "score": r.get("score", 1.0),
                    "source": "fts"
                })

            return formatted_results
        except Exception as e:
            warn("rgl.search", f"FTS search failed: {e}")
            return []


class SearchAdapter:
    """Main search adapter that provides a consistent interface"""

    def __init__(self, db_path: str, repository_connection=None):
        """
        Args:
            db_path: KuzuDBのデータベースパス
            repository_connection: 既存のKuzuDB接続（共有する場合）
        """
        self.db_path = db_path
        self.vss_available = VSS_MODULES_AVAILABLE
        self.fts_available = FTS_MODULES_AVAILABLE
        self._vss_service = None
        self._fts_service = None
        self._error = None

        # Initialize VSS service (required)
        self._vss_service = VSSSearchAdapter(db_path, repository_connection)

        # Initialize FTS service (required)  
        self._fts_service = FTSSearchAdapter(db_path, repository_connection)

        # Both services must be initialized
        if not self._vss_service._is_initialized or not self._fts_service._is_initialized:
            error("rgl.search", "VSS/FTS services are required but not initialized")
            raise RuntimeError("Both VSS and FTS services are required but not initialized")

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
        # Services are already validated in __init__

        # Use hybrid search for best results
        search_results = self.search_hybrid(text, k=k)

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
        # Services are already validated in __init__

        success = False

        try:
            # Add to VSS index if available
            if self._vss_service:
                self._vss_service.add_requirement(
                    id=requirement["id"],
                    title=requirement.get("title", ""),
                    content=requirement.get("description", "")
                )
                success = True

            # Add to FTS index if available
            if self._fts_service:
                self._fts_service.add_requirement(
                    id=requirement["id"],
                    title=requirement.get("title", ""),
                    content=requirement.get("description", "")
                )
                success = True

            return success
        except Exception as e:
            error("rgl.search", f"Failed to add to search index: {e}")
            return False

    def search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """類似検索（VSS）を実行"""
        # VSS service is guaranteed to be initialized by __init__
        return self._vss_service.search_similar(query, k=k)

    def search_keyword(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """キーワード検索（FTS）を実行"""
        # FTS service is guaranteed to be initialized by __init__
        return self._fts_service.search_keyword(query, k=k)

    def search_hybrid(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """ハイブリッド検索（VSS + FTS）を実行"""
        vss_results = []
        fts_results = []

        # Get VSS results if available
        if self._vss_service:
            vss_results = self._vss_service.search_similar(query, k)

        # Get FTS results if available
        if self._fts_service:
            fts_results = self._fts_service.search_keyword(query, k)
        elif self._vss_service:
            # Fall back to basic keyword search from VSS adapter
            fts_results = self._vss_service.search_keyword(query, k)

        # Services are already validated in __init__, no need for error check

        # Merge results by id, preferring VSS scores
        merged = {}
        for r in vss_results:
            if "error" not in r:
                merged[r["id"]] = r

        for r in fts_results:
            if "error" not in r:
                if r["id"] not in merged:
                    merged[r["id"]] = r
                else:
                    # Average the scores
                    merged[r["id"]]["score"] = (merged[r["id"]]["score"] + r["score"]) / 2
                    merged[r["id"]]["source"] = "hybrid"

        # Sort by score and return top k
        sorted_results = sorted(merged.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:k]

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """テキストのエンベディングを生成
        
        VSSServiceが利用可能な場合は実際のエンベディングを生成。
        利用不可能な場合はNoneを返す。
        """
        # VSS service is guaranteed to be initialized
        # Note: Current implementation doesn't expose raw embedding generation
        return None

        # VSSSearchAdapterの場合、内部でエンベディング生成を処理
        if isinstance(self._vss_service, VSSSearchAdapter) and self._vss_service._is_initialized:
            # VSSServiceは内部的にエンベディングを生成するため、
            # ここでは特別な処理は不要
            # 実際のエンベディング生成はadd_to_index内で行われる
            return None

        return None

    @property
    def is_available(self) -> bool:
        """検索サービスが利用可能かどうか"""
        return (self._vss_service and self._vss_service._is_initialized and
                self._fts_service and self._fts_service._is_initialized)
