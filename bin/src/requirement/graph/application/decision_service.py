"""
Decision Service - 決定管理ユースケース
依存: domain層のみ
外部依存: なし
"""
from typing import List, Dict, Callable, Optional
from ..domain.types import Decision, DecisionResult, DecisionError, DecisionNotFoundError
from ..domain.decision import create_decision, calculate_similarity
from ..domain.embedder import create_embedding


# Repository型定義（依存性注入用）
DecisionRepository = Dict[str, Callable]


def create_decision_service(repository: DecisionRepository):
    """
    DecisionServiceを作成（依存性注入）
    
    Args:
        repository: save, find, find_all, searchメソッドを持つ辞書
    
    Returns:
        DecisionService関数の辞書
    """
    
    def add_decision(
        title: str,
        description: str,
        tags: Optional[List[str]] = None
    ) -> DecisionResult:
        """新しい決定事項を追加"""
        # ID生成（簡易版）
        import time
        decision_id = f"req_{int(time.time() * 1000) % 1000000}"
        
        # 埋め込み生成
        embedding_result = create_embedding(f"{title} {description}")
        if "type" in embedding_result:
            return embedding_result
        
        # Decision作成
        decision_result = create_decision(
            id=decision_id,
            title=title,
            description=description,
            tags=tags,
            embedding=embedding_result
        )
        
        if "type" in decision_result:
            return decision_result
        
        # 保存
        save_result = repository["save"](decision_result)
        return save_result
    
    def find_decision(decision_id: str) -> DecisionResult:
        """IDで決定事項を検索"""
        return repository["find"](decision_id)
    
    def search_similar(
        query: str,
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Decision]:
        """類似する決定事項を検索"""
        # クエリの埋め込み生成
        query_embedding = create_embedding(query)
        if "type" in query_embedding:
            return []
        
        # 全決定事項を取得
        all_decisions = repository["find_all"]()
        
        # 類似度計算とフィルタリング
        results = []
        for decision in all_decisions:
            similarity = calculate_similarity(
                query_embedding,
                decision["embedding"]
            )
            if similarity >= threshold:
                results.append((similarity, decision))
        
        # ソートして上位を返す
        results.sort(key=lambda x: x[0], reverse=True)
        # 類似度を含めて返す
        return [{**decision, "similarity": sim} for sim, decision in results[:limit]]
    
    def list_by_tag(tag: str) -> List[Decision]:
        """タグで決定事項を検索"""
        all_decisions = repository["find_all"]()
        return [d for d in all_decisions if tag in d.get("tags", [])]
    
    def list_all() -> List[Decision]:
        """全ての決定事項を取得"""
        return repository["find_all"]()
    
    return {
        "add_decision": add_decision,
        "find_decision": find_decision,
        "search_similar": search_similar,
        "list_by_tag": list_by_tag,
        "list_all": list_all
    }


# Test cases
def test_decision_service_add_valid_data_returns_saved_decision():
    """decision_service_add_正常データ_保存された決定事項を返す"""
    # モックリポジトリ
    storage = {}
    
    def mock_save(decision):
        storage[decision["id"]] = decision
        return decision
    
    def mock_find(decision_id):
        if decision_id in storage:
            return storage[decision_id]
        return {
            "type": "DecisionNotFoundError",
            "message": f"Decision {decision_id} not found",
            "decision_id": decision_id
        }
    
    def mock_find_all():
        return list(storage.values())
    
    repository = {
        "save": mock_save,
        "find": mock_find,
        "find_all": mock_find_all,
    }
    
    service = create_decision_service(repository)
    
    # 決定事項を追加
    result = service["add_decision"](
        title="KuzuDB移行",
        description="関係性クエリを可能にする",
        tags=["architecture", "L1"]
    )
    
    assert "type" not in result
    assert result["title"] == "KuzuDB移行"
    assert len(result["embedding"]) == 50


def test_decision_service_search_similar_query_returns_matching_decisions():
    """decision_service_search_類似クエリ_マッチする決定事項を返す"""
    storage = {}
    
    # 3つの決定事項を準備
    decisions = [
        {
            "id": "req_001",
            "title": "データベース移行",
            "description": "PostgreSQLからKuzuDBへ",
            "status": "approved",
            "tags": ["db"],
            "created_at": None,
            "embedding": create_embedding("データベース移行 PostgreSQLからKuzuDBへ")
        },
        {
            "id": "req_002", 
            "title": "API設計",
            "description": "RESTful APIの実装",
            "status": "approved",
            "tags": ["api"],
            "created_at": None,
            "embedding": create_embedding("API設計 RESTful APIの実装")
        },
        {
            "id": "req_003",
            "title": "データベース最適化",
            "description": "クエリパフォーマンス改善",
            "status": "approved", 
            "tags": ["db"],
            "created_at": None,
            "embedding": create_embedding("データベース最適化 クエリパフォーマンス改善")
        }
    ]
    
    for d in decisions:
        storage[d["id"]] = d
    
    repository = {
        "save": lambda d: d,
        "find": lambda id: storage.get(id),
        "find_all": lambda: list(storage.values()),
    }
    
    service = create_decision_service(repository)
    
    # "データベース"で検索
    results = service["search_similar"]("データベース", threshold=0.3)
    
    # データベース関連がヒット
    assert len(results) >= 1
    # 少なくとも1つはデータベース関連
    assert any("データベース" in r["title"] or "データベース" in r["description"] 
               for r in results)
