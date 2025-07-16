"""
Search Adapter - requirement/graphとsemantic searchの統合レイヤー

このアダプターは、semantic searchのAPIを直接使用して重複検出機能を提供する。
独自実装は一切含まず、semantic searchの機能をそのまま利用する。
"""
import sys
import os
import math
from typing import List, Dict, Any, Optional

# Semantic searchモジュールへのパスを追加
# ローカルのsearchディレクトリを優先的に使用
local_search_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../search"))
if os.path.exists(local_search_path):
    if local_search_path not in sys.path:
        sys.path.insert(0, local_search_path)
    semantic_search_path = local_search_path
else:
    # フォールバック
    semantic_search_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../poc/search"))
    if semantic_search_path not in sys.path:
        sys.path.insert(0, semantic_search_path)

try:
    from infrastructure.kuzu_search_service import KuzuSearchService
    from domain.interfaces import SearchService, SearchResult
except ImportError as e:
    raise ImportError(f"Semantic search modules not found. Make sure semantic search is available at {semantic_search_path}: {e}")


class RequirementGraphSearchService(KuzuSearchService):
    """Requirement Graph専用の検索サービス（semantic searchベース）"""

    def __init__(self, db_path: Optional[str] = None, existing_connection=None):
        """
        Args:
            db_path: データベースパス
            existing_connection: 既存のKuzuDB接続（共有する場合）
        """
        self._existing_connection = existing_connection
        super().__init__(db_path)

    def _setup_database(self):
        """既存のrequirement graphデータベースを使用"""
        if self._existing_connection:
            # 既存の接続を使用
            self._conn = self._existing_connection
            self._db = None  # 既存接続の場合はDB参照は不要
            print("[DEBUG] Using existing database connection")
        else:
            # 新規接続を作成
            import kuzu
            self._db = kuzu.Database(self._db_path)
            self._conn = kuzu.Connection(self._db)
            print(f"[DEBUG] Created new database connection to {self._db_path}")

        # 既存のRequirementEntityテーブルを使用（新規作成しない）
        # スキーマが存在することを前提とする

        # Store db_path for subprocess access
        self._conn.db_path = self._db_path
        if self._db:
            self._conn.db_obj = self._db

    def add_requirement(self, id: str, title: str, content: str) -> None:
        """要件を追加（descriptionフィールドを使用）"""
        full_text = f"{title} {content}"
        embedding = self._generate_embedding(full_text)

        print(f"[DEBUG] Generated embedding for {id}: {len(embedding)} dimensions")

        # Format embedding for query
        embedding_str = "[" + ", ".join(str(v) for v in embedding) + "]"

        # descriptionフィールドを使用してRequirementEntityを更新
        result = self._conn.execute(f"""
            MATCH (r:RequirementEntity {{id: '{id}'}})
            SET r.embedding = {embedding_str}
            RETURN r.id, r.embedding IS NOT NULL as has_embedding
        """)

        # Debug output
        if result.has_next():
            row = result.get_next()
            print(f"[DEBUG] Updated requirement {row[0]}, has_embedding: {row[1]}")
        else:
            print(f"[DEBUG] No requirement found with id: {id}")

    def _search_similar_direct(self, query_embedding: List[float], k: int) -> List['SearchResult']:
        """requirement graphのスキーマに対応した類似検索"""
        # Get all requirements with embeddings
        result = self._conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.embedding IS NOT NULL
            RETURN r.id, r.title, r.description, r.embedding
        """)

        requirements = []
        while result.has_next():
            row = result.get_next()
            requirements.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],  # contentではなくdescription
                "embedding": row[3]
            })

        # Calculate similarities
        similarities = []
        for req in requirements:
            if req["embedding"]:
                # Simple cosine similarity
                similarity = self._cosine_similarity(query_embedding, req["embedding"])
                similarities.append({
                    "id": req["id"],
                    "title": req["title"],
                    "content": req["description"],  # semantic searchの期待に合わせてcontentとして返す
                    "score": similarity
                })

        # Sort by similarity score
        similarities.sort(key=lambda x: x["score"], reverse=True)

        # Return top k results as SearchResult objects
        results = []
        for sim in similarities[:k]:
            results.append(SearchResult(
                id=sim["id"],
                title=sim["title"],
                content=sim["content"],
                score=sim["score"],
                source="vss"
            ))

        return results

    def search_keyword(self, query: str, k: int = 10) -> List['SearchResult']:
        """requirement graphのスキーマに対応したキーワード検索"""
        # Simple FTS implementation using CONTAINS
        result = self._conn.execute("""
            MATCH (r:RequirementEntity)
            WHERE r.title CONTAINS $query OR r.description CONTAINS $query
            RETURN r.id, r.title, r.description
            LIMIT $k
        """, {"query": query, "k": k})

        results = []
        while result.has_next():
            row = result.get_next()
            results.append(SearchResult(
                id=row[0],
                title=row[1],
                content=row[2],  # semantic searchの期待に合わせてcontentとして返す
                score=1.0,  # キーワード検索は固定スコア
                source="fts"
            ))

        return results

    def search_hybrid(self, query: str, k: int = 10) -> List['SearchResult']:
        """ハイブリッド検索（VSS + FTS）の実装"""
        # VSS結果を取得
        vss_results = self.search_similar(query, k)

        # FTS結果を取得
        fts_results = self.search_keyword(query, k)

        # 結果を統合（重複排除）
        all_results = {}

        # VSS結果を追加
        for result in vss_results:
            all_results[result.id] = result

        # FTS結果を追加（既存のVSS結果があればスコアを統合）
        for result in fts_results:
            if result.id in all_results:
                # スコアを統合（平均）
                existing = all_results[result.id]
                combined_score = (existing.score + result.score) / 2
                all_results[result.id] = SearchResult(
                    id=result.id,
                    title=result.title,
                    content=result.content,
                    score=combined_score,
                    source="hybrid"
                )
            else:
                all_results[result.id] = result

        # スコア順にソートして返す
        sorted_results = sorted(all_results.values(), key=lambda x: x.score, reverse=True)
        return sorted_results[:k]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """コサイン類似度を計算"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)


class SearchAdapter:
    """Semantic searchの機能をrequirement/graphで使用するためのアダプター"""

    def __init__(self, db_path: str, repository_connection=None):
        """
        Args:
            db_path: KuzuDBのデータベースパス
            repository_connection: 既存のKuzuDB接続（共有する場合）
        """
        self.db_path = db_path
        # Requirement Graph専用の検索サービスを初期化
        self.search_service: SearchService = RequirementGraphSearchService(
            db_path,
            existing_connection=repository_connection
        )

    def check_duplicates(self, text: str, k: int = 5, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        テキストに基づいて重複要件をチェック
        
        Args:
            text: 検索テキスト（タイトル + 説明）
            k: 返す結果の最大数
            threshold: 類似度の閾値（0.0-1.0）
            
        Returns:
            重複候補のリスト（スコア順）
        """
        # Semantic searchのハイブリッド検索を直接使用
        search_results: List[SearchResult] = self.search_service.search_hybrid(text, k=k)

        # 閾値以上のスコアの結果のみ返す
        duplicates = []
        for result in search_results:
            if result.score >= threshold:
                duplicates.append({
                    "id": result.id,
                    "title": result.title,
                    "description": result.content,  # semantic searchはcontentフィールドを使用
                    "score": result.score,
                    "type": "hybrid"  # VSS + FTSの結果
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
        try:
            # Semantic searchのadd_requirementメソッドを直接使用
            self.search_service.add_requirement(
                id=requirement["id"],
                title=requirement["title"],
                content=requirement.get("description", "")  # semantic searchはcontentを期待
            )
            return True
        except Exception as e:
            print(f"Failed to add to search index: {e}")
            return False

    def search_similar(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        類似検索（VSS）を実行
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            
        Returns:
            類似要件のリスト
        """
        results = self.search_service.search_similar(query, k=k)
        return [self._convert_result(r) for r in results]

    def search_keyword(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        キーワード検索（FTS）を実行
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            
        Returns:
            マッチした要件のリスト
        """
        results = self.search_service.search_keyword(query, k=k)
        return [self._convert_result(r) for r in results]

    def search_hybrid(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        ハイブリッド検索（VSS + FTS）を実行
        
        Args:
            query: 検索クエリ
            k: 返す結果の最大数
            
        Returns:
            統合された検索結果のリスト
        """
        results = self.search_service.search_hybrid(query, k=k)
        return [self._convert_result(r) for r in results]

    def _convert_result(self, result: SearchResult) -> Dict[str, Any]:
        """SearchResultを辞書形式に変換"""
        return {
            "id": result.id,
            "title": result.title,
            "description": result.content,
            "score": result.score,
            "source": result.source
        }
