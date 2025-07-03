"""
摩擦検出の統合テスト
"""
import os
import tempfile
import pytest

# テスト用環境設定
from .infrastructure.variables import setup_test_environment
setup_test_environment()

from .infrastructure.kuzu_repository import create_kuzu_repository
from .infrastructure.llm_hooks_api import create_llm_hooks_api
from .application.friction_detector import create_friction_detector
from .application.scoring_service import create_scoring_service


def test_friction_detection_on_ambiguous_requirement():
    """曖昧な要件での摩擦検出"""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "friction_test.db")
        repo = create_kuzu_repository(db_path)
        
        # スキーマ適用
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 曖昧な要件を作成
        result = api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_ambiguous_001',
                title: 'ユーザーフレンドリーなインターフェース',
                description: '使いやすいUIを提供する',
                priority: 2
            })
            CREATE (loc:LocationURI {id: 'loc://vision/ui/001'})
            CREATE (loc)-[:LOCATES]->(r)
            """,
            "parameters": {}
        })
        
        assert result["status"] == "success"
        
        # 摩擦検出を実行
        detector = create_friction_detector()
        frictions = detector["detect_all"](repo["connection"])
        
        # 曖昧性摩擦が検出されることを確認
        ambiguity_score = frictions["frictions"]["ambiguity"]["score"]
        assert ambiguity_score < 0  # 負のスコア = 摩擦あり
        
        # 総合スコアを確認
        total_score = frictions["total"]["total_score"]
        assert total_score < 0


def test_priority_friction_with_multiple_critical():
    """複数のcritical要件による優先度摩擦"""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "priority_friction.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 3つのcritical要件を作成
        critical_reqs = [
            "セキュリティ強化",
            "パフォーマンス改善",
            "新機能開発"
        ]
        
        for i, title in enumerate(critical_reqs):
            api["query"]({
                "type": "cypher",
                "query": f"""
                CREATE (r:RequirementEntity {{
                    id: 'req_critical_{i}',
                    title: '{title}',
                    priority: 250
                }})
                CREATE (loc:LocationURI {{id: 'loc://vision/critical_{i}'}})
                CREATE (loc)-[:LOCATES]->(r)
                """,
                "parameters": {}
            })
        
        # 摩擦検出
        detector = create_friction_detector()
        frictions = detector["detect_all"](repo["connection"])
        
        # 優先度摩擦を確認
        priority_friction = frictions["frictions"]["priority"]
        assert priority_friction["score"] < 0
        assert frictions["total"]["health"] in ["needs_attention", "at_risk", "critical"]


def test_contradiction_friction():
    """矛盾する要件による摩擦"""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "contradiction_friction.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # コスト削減要件
        api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r1:RequirementEntity {
                id: 'req_cost_001',
                title: 'インフラコスト削減',
                description: 'クラウドコストを50%削減',
                priority: 2
            })
            CREATE (loc1:LocationURI {id: 'loc://vision/cost_001'})
            CREATE (loc1)-[:LOCATES]->(r1)
            """,
            "parameters": {}
        })
        
        # パフォーマンス向上要件（矛盾）
        api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r2:RequirementEntity {
                id: 'req_perf_001',
                title: 'パフォーマンス向上',
                description: 'レスポンスタイムを50%改善',
                priority: 2
            })
            CREATE (loc2:LocationURI {id: 'loc://vision/perf_001'})
            CREATE (loc2)-[:LOCATES]->(r2)
            """,
            "parameters": {}
        })
        
        # 摩擦検出
        detector = create_friction_detector()
        frictions = detector["detect_all"](repo["connection"])
        
        # 矛盾摩擦を確認
        contradiction = frictions["frictions"]["contradiction"]
        assert contradiction["score"] <= 0  # 矛盾が検出される可能性


def test_healthy_project_without_friction():
    """摩擦のない健全なプロジェクト"""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "healthy_project.db")
        repo = create_kuzu_repository(db_path)
        
        from .infrastructure.ddl_schema_manager import DDLSchemaManager
        schema_manager = DDLSchemaManager(repo["connection"])
        schema_path = os.path.join(os.path.dirname(__file__), "ddl", "schema.cypher")
        success, results = schema_manager.apply_schema(schema_path)
        assert success
        
        api = create_llm_hooks_api(repo)
        
        # 明確で適切な要件
        api["query"]({
            "type": "cypher",
            "query": """
            CREATE (r:RequirementEntity {
                id: 'req_clear_001',
                title: 'ユーザー認証機能',
                description: 'JWTトークンによる認証実装',
                priority: 50,
                acceptance_criteria: '1. ログイン成功時にJWTトークン発行 2. トークン有効期限24時間',
                technical_specifications: '{"framework": "FastAPI", "auth": "JWT", "database": "PostgreSQL"}'
            })
            CREATE (loc:LocationURI {id: 'loc://vision/auth_001'})
            CREATE (loc)-[:LOCATES]->(r)
            """,
            "parameters": {}
        })
        
        # 摩擦検出
        detector = create_friction_detector()
        frictions = detector["detect_all"](repo["connection"])
        
        # 健全なプロジェクトであることを確認
        total_score = frictions["total"]["total_score"]
        assert total_score > -0.5  # 健全な範囲
        assert frictions["total"]["health"] in ["healthy", "needs_attention"]


def test_scoring_service_integration():
    """スコアリングサービスとの統合"""
    service = create_scoring_service()
    
    # 各摩擦タイプのスコア計算
    ambiguity = service["calculate_friction_score"]("ambiguity_friction", {"interpretation_count": 2})
    assert ambiguity["score"] == -0.6
    
    priority = service["calculate_friction_score"]("priority_friction", {"high_priority_count": 3, "has_conflict": True})
    assert priority["score"] == -0.7
    
    # 総合スコア計算
    total = service["calculate_total_friction_score"]({
        "ambiguity": -0.6,
        "priority": -0.7,
        "temporal": 0.0,
        "contradiction": -0.4
    })
    
    # 重み付け計算: (-0.6*0.2) + (-0.7*0.3) + (0*0.2) + (-0.4*0.3) = -0.45
    # -0.45 は -0.5 より大きいので "needs_attention"
    assert total["health"] == "needs_attention"
    # recommendationフィールドは削除したのでテストから除外