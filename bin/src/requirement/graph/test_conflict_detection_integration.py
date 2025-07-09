"""
要件矛盾検出の統合テスト（規約準拠版）
クラスを使わず、setup/teardown関数で実装
"""
from typing import Dict, Any, Optional
import json
from .infrastructure.kuzu_repository import create_kuzu_repository
from .domain.requirement_conflict_rules import (
    detect_all_conflicts,
    detect_numeric_threshold_conflicts,
    ConflictDetectionResult
)
from .infrastructure.ddl_schema_manager import DDLSchemaManager
from pathlib import Path


# テスト環境のセットアップ
def setup_test_environment() -> Dict[str, Any]:
    """テスト環境を準備し、リポジトリを返す"""
    repo = create_kuzu_repository()
    
    # スキーマを適用
    schema_manager = DDLSchemaManager(repo["connection"])
    schema_path = Path(__file__).parent / "ddl" / "migrations" / "3.2.0_current.cypher"
    
    if not schema_path.exists():
        return {"repo": repo, "error": "Schema file not found"}
    
    success, results = schema_manager.apply_schema(str(schema_path))
    if not success:
        return {"repo": repo, "error": f"Failed to apply schema: {results}"}
    
    return {"repo": repo, "error": None}


# テストデータ作成ヘルパー
def create_test_requirements(repo: Dict[str, Any], requirements_data: list) -> Optional[str]:
    """テスト用要件をデータベースに作成"""
    for query in requirements_data:
        try:
            repo["execute"](query, {})
        except Exception as e:
            return f"Failed to create requirement: {e}"
    return None


# データベースから要件を取得
def fetch_requirements_with_constraints(repo: Dict[str, Any], id_prefix: str) -> list:
    """制約を持つ要件を取得"""
    query = """
    MATCH (r:RequirementEntity)
    WHERE r.id STARTS WITH $prefix
    RETURN r.id, r.title, r.priority, r.requirement_type,
           r.numeric_constraints, r.temporal_constraint,
           r.exclusive_constraint, r.quality_attributes
    ORDER BY r.priority DESC
    """
    
    result = repo["execute"](query, {"prefix": id_prefix})
    requirements = []
    
    while result.has_next():
        row = result.get_next()
        req = {
            "id": row[0],
            "title": row[1],
            "priority": row[2],
            "requirement_type": row[3]
        }
        
        # JSON制約をパース
        if row[4]:  # numeric_constraints
            try:
                req["numeric_constraints"] = json.loads(row[4])
            except json.JSONDecodeError:
                pass
        
        if row[5]:  # temporal_constraint
            try:
                req["temporal_constraint"] = json.loads(row[5])
            except json.JSONDecodeError:
                pass
                
        if row[6]:  # exclusive_constraint
            try:
                req["exclusive_constraint"] = json.loads(row[6])
            except json.JSONDecodeError:
                pass
                
        if row[7]:  # quality_attributes
            try:
                req["quality_attributes"] = json.loads(row[7])
            except json.JSONDecodeError:
                pass
        
        requirements.append(req)
    
    return requirements


# テスト1: 金融決済システムの矛盾検出
def test_fintech_payment_conflicts_detection():
    """金融決済システムの矛盾を検出"""
    env = setup_test_environment()
    if env["error"]:
        return f"Setup failed: {env['error']}"
    
    repo = env["repo"]
    
    # 矛盾する要件を作成
    test_data = [
        """CREATE (r1:RequirementEntity {
            id: 'FINTECH_FIXED_001',
            title: '即時決済（1秒）',
            priority: 255,
            requirement_type: 'business',
            numeric_constraints: '{"metric": "response_time", "operator": "<", "value": 1, "unit": "seconds"}'
        })""",
        """CREATE (r2:RequirementEntity {
            id: 'FINTECH_FIXED_002',
            title: '現実的な処理時間',
            priority: 230,
            requirement_type: 'technical',
            numeric_constraints: '{"metric": "response_time", "operator": "<", "value": 4, "unit": "seconds"}'
        })""",
        """CREATE (r3:RequirementEntity {
            id: 'FINTECH_FIXED_003',
            title: 'グローバル即時展開',
            priority: 245,
            requirement_type: 'business',
            temporal_constraint: '{"timeline": "immediate", "duration": 0}'
        })""",
        """CREATE (r4:RequirementEntity {
            id: 'FINTECH_FIXED_004',
            title: '段階的リリース計画',
            priority: 240,
            requirement_type: 'technical',
            temporal_constraint: '{"timeline": "months", "duration": 6}'
        })"""
    ]
    
    error = create_test_requirements(repo, test_data)
    if error:
        return error
    
    # 要件を取得
    requirements = fetch_requirements_with_constraints(repo, "FINTECH_FIXED")
    
    # 矛盾を検出
    all_conflicts = detect_all_conflicts(requirements)
    
    # 検証
    numeric_result = all_conflicts.get("numeric_threshold", {})
    temporal_result = all_conflicts.get("temporal_incompatibility", {})
    
    assert numeric_result.get("has_conflict", False) is True, "数値的矛盾が検出されるべき"
    assert temporal_result.get("has_conflict", False) is True, "時間的矛盾が検出されるべき"
    
    # 具体的な矛盾内容を確認
    if numeric_result.get("conflicts"):
        conflict = numeric_result["conflicts"][0]
        assert conflict["ratio"] >= 2.0, "レスポンスタイムの差が2倍以上であるべき"
    
    return "✅ Fintech conflicts detected successfully"


# テスト2: 矛盾の動的検出（Cypherクエリパターン）
def test_conflict_query_patterns():
    """データベースレベルでの矛盾検出パターン"""
    env = setup_test_environment()
    if env["error"]:
        return f"Setup failed: {env['error']}"
    
    repo = env["repo"]
    
    # 様々なタイプの矛盾を作成
    test_data = [
        # 排他的選択の矛盾
        """CREATE (r1:RequirementEntity {
            id: 'PATTERN_001',
            title: 'クラウドオンリー',
            exclusive_constraint: '{"category": "deployment", "value": "cloud-only"}'
        })""",
        """CREATE (r2:RequirementEntity {
            id: 'PATTERN_002',
            title: 'オンプレミス必須',
            exclusive_constraint: '{"category": "deployment", "value": "on-premise"}'
        })""",
        # 品質属性の矛盾
        """CREATE (r3:RequirementEntity {
            id: 'PATTERN_003',
            title: '超高速処理',
            quality_attributes: '["performance", "speed"]'
        })""",
        """CREATE (r4:RequirementEntity {
            id: 'PATTERN_004',
            title: '最高セキュリティ',
            quality_attributes: '["security", "encryption"]'
        })"""
    ]
    
    error = create_test_requirements(repo, test_data)
    if error:
        return error
    
    # Cypherで直接矛盾パターンを検出
    conflict_query = """
    MATCH (r1:RequirementEntity), (r2:RequirementEntity)
    WHERE r1.id < r2.id
      AND r1.id STARTS WITH 'PATTERN'
      AND r2.id STARTS WITH 'PATTERN'
      AND r1.exclusive_constraint IS NOT NULL
      AND r2.exclusive_constraint IS NOT NULL
    WITH r1, r2
    WHERE r1.exclusive_constraint CONTAINS '"category":"deployment"'
      AND r2.exclusive_constraint CONTAINS '"category":"deployment"'
      AND r1.exclusive_constraint <> r2.exclusive_constraint
    RETURN r1.id as id1, r1.title as title1,
           r2.id as id2, r2.title as title2,
           'Deployment conflict' as conflict_type
    """
    
    result = repo["execute"](conflict_query, {})
    conflicts = []
    while result.has_next():
        row = result.get_next()
        conflicts.append({
            "req1": (row[0], row[1]),
            "req2": (row[2], row[3]),
            "type": row[4]
        })
    
    assert len(conflicts) > 0, "デプロイメント矛盾が検出されるべき"
    return "✅ Query pattern conflicts detected successfully"


# テスト3: 矛盾解決の追跡
def test_conflict_resolution_tracking():
    """矛盾の解決プロセスを追跡"""
    env = setup_test_environment()
    if env["error"]:
        return f"Setup failed: {env['error']}"
    
    repo = env["repo"]
    
    # 初期の矛盾する要件
    test_data = [
        """CREATE (r1:RequirementEntity {
            id: 'RESOLVE_001',
            title: '0.1秒レスポンス',
            priority: 250,
            status: 'proposed',
            numeric_constraints: '{"metric": "response_time", "operator": "<", "value": 0.1, "unit": "seconds"}'
        })""",
        """CREATE (r2:RequirementEntity {
            id: 'RESOLVE_002',
            title: '技術的制約2秒',
            priority: 230,
            status: 'proposed',
            numeric_constraints: '{"metric": "response_time", "operator": "<", "value": 2, "unit": "seconds"}'
        })"""
    ]
    
    error = create_test_requirements(repo, test_data)
    if error:
        return error
    
    # 矛盾を検出
    requirements = fetch_requirements_with_constraints(repo, "RESOLVE")
    conflicts = detect_numeric_threshold_conflicts(requirements)
    
    assert conflicts["has_conflict"] is True, "初期状態で矛盾があるべき"
    
    # 矛盾を解決（要件を更新）
    repo["execute"]("""
    MATCH (r:RequirementEntity {id: 'RESOLVE_001'})
    SET r.status = 'rejected',
        r.rejection_reason = 'Technical infeasibility: 0.1s not achievable'
    """, {})
    
    # 妥協案を追加
    repo["execute"]("""
    CREATE (r:RequirementEntity {
        id: 'RESOLVE_003',
        title: '最適化レスポンス',
        priority: 240,
        status: 'approved',
        numeric_constraints: '{"metric": "response_time", "operator": "<", "value": 1, "unit": "seconds"}',
        resolution_notes: 'Balanced between business needs and technical constraints'
    })
    """, {})
    
    # 解決後の状態を確認
    approved_query = """
    MATCH (r:RequirementEntity)
    WHERE r.id STARTS WITH 'RESOLVE' AND r.status = 'approved'
    RETURN count(r) as approved_count
    """
    
    result = repo["execute"](approved_query, {})
    if result.has_next():
        row = result.get_next()
        assert row[0] == 1, "承認された妥協案が1つあるべき"
    
    return "✅ Conflict resolution tracked successfully"


# メイン実行関数
def run_all_integration_tests():
    """すべての統合テストを実行"""
    tests = [
        ("Fintech conflicts", test_fintech_payment_conflicts_detection),
        ("Query patterns", test_conflict_query_patterns),
        ("Resolution tracking", test_conflict_resolution_tracking)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            result = test_func()
            results.append(result)
            print(result)
        except AssertionError as e:
            error_msg = f"❌ {test_name} failed: {e}"
            results.append(error_msg)
            print(error_msg)
        except Exception as e:
            error_msg = f"❌ {test_name} error: {e}"
            results.append(error_msg)
            print(error_msg)
    
    # 結果サマリー
    success_count = sum(1 for r in results if r.startswith("✅"))
    total_count = len(results)
    
    print(f"\n{'='*50}")
    print(f"Test Summary: {success_count}/{total_count} passed")
    if success_count == total_count:
        print("🎉 All integration tests passed!")
    else:
        print("⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    run_all_integration_tests()