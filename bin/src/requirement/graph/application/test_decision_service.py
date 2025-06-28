"""
Tests for Decision Service
"""
from ..domain.embedder import create_embedding
from .decision_service import create_decision_service


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
            "created_at": None,
            "embedding": create_embedding("データベース移行 PostgreSQLからKuzuDBへ")
        },
        {
            "id": "req_002", 
            "title": "API設計",
            "description": "RESTful APIの実装",
            "status": "approved",
            "created_at": None,
            "embedding": create_embedding("API設計 RESTful APIの実装")
        },
        {
            "id": "req_003",
            "title": "データベース最適化",
            "description": "クエリパフォーマンス改善",
            "status": "approved", 
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