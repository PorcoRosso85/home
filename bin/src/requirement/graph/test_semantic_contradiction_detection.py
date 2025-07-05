"""
意味的矛盾検出のテスト（TDD Red）

単純な数値比較を超えた、意味レベルでの矛盾を検出する機能のテスト。
例：「セキュリティ重視」と「開発速度優先」の矛盾など。
"""
import pytest
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime


@pytest.mark.skip(reason="TDD Red: 意味的矛盾検出機能未実装")
class TestSemanticContradictionDetection:
    """意味的矛盾検出のテスト"""
    
    def test_セキュリティと開発速度の矛盾検出(self):
        """セキュリティ重視と開発速度優先の矛盾を検出"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.semantic_analyzer import detect_semantic_contradictions
        from infrastructure.ddl_schema_manager import DDLSchemaManager
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            # DB初期化
            repo = create_kuzu_repository(test_db)
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = Path(__file__).parent / "ddl" / "schema.cypher"
            success, _ = schema_manager.apply_schema(str(schema_path))
            assert success
            
            version_service = create_version_service(repo)
            
            # CISO: セキュリティ最優先の要件
            ciso_req = version_service["create_versioned_requirement"]({
                "id": "REQ-SEC-001",
                "title": "ゼロトラストセキュリティアーキテクチャ",
                "description": "すべての通信を検証、暗号化、監査ログ必須",
                "priority": 200,
                "requirement_type": "security",
                "semantic_tags": ["zero-trust", "security-first", "audit-everything"],
                "impact_areas": ["performance", "development-speed"],
                "constraints": {
                    "min_encryption": "AES-256",
                    "audit_retention": "7years",
                    "access_verification": "every-request"
                }
            })
            
            # PM: 開発速度優先の要件
            pm_req = version_service["create_versioned_requirement"]({
                "id": "REQ-SPEED-001",
                "title": "2週間スプリントでのMVPリリース",
                "description": "最小限の機能で高速リリース、後から改善",
                "priority": 180,
                "requirement_type": "process",
                "semantic_tags": ["rapid-development", "mvp-first", "iterate-later"],
                "impact_areas": ["quality", "security"],
                "constraints": {
                    "max_dev_time": "2weeks",
                    "feature_scope": "minimal",
                    "testing": "basic-only"
                }
            })
            
            # 意味的矛盾を検出
            contradictions = detect_semantic_contradictions(repo)
            
            # セキュリティvs速度の矛盾が検出される
            assert len(contradictions) > 0
            
            security_speed_conflict = next(
                (c for c in contradictions 
                 if set(c["requirement_ids"]) == {"REQ-SEC-001", "REQ-SPEED-001"}),
                None
            )
            
            assert security_speed_conflict is not None
            assert security_speed_conflict["contradiction_type"] == "goal_conflict"
            assert security_speed_conflict["severity"] == "high"
            assert "セキュリティ重視と開発速度優先は相反する" in security_speed_conflict["explanation"]
            assert security_speed_conflict["suggested_resolution"] == "段階的セキュリティ実装"
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_品質とコストの矛盾検出(self):
        """高品質要求と低コスト制約の矛盾を検出"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.semantic_analyzer import analyze_quality_cost_tradeoff
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # QA: 高品質要求
            qa_req = version_service["create_versioned_requirement"]({
                "id": "REQ-QUALITY-001",
                "title": "99.99%の可用性保証",
                "description": "エンタープライズグレードの品質基準",
                "priority": 190,
                "requirement_type": "quality",
                "quality_metrics": {
                    "availability": "99.99%",
                    "response_time": "<100ms",
                    "error_rate": "<0.01%"
                },
                "required_resources": ["冗長システム", "24/7監視", "専門QAチーム"]
            })
            
            # CFO: コスト削減要求
            cfo_req = version_service["create_versioned_requirement"]({
                "id": "REQ-COST-001",
                "title": "インフラコスト50%削減",
                "description": "クラウドコストを半減させる",
                "priority": 200,
                "requirement_type": "constraint",
                "cost_constraints": {
                    "max_monthly_cost": "10000USD",
                    "reduction_target": "50%"
                },
                "forbidden_resources": ["冗長システム", "専用サーバー"]
            })
            
            # トレードオフ分析
            tradeoff = analyze_quality_cost_tradeoff(repo, "REQ-QUALITY-001", "REQ-COST-001")
            
            assert tradeoff["conflict_detected"] == True
            assert tradeoff["conflict_reason"] == "required_resources_forbidden"
            assert tradeoff["quality_impact"] == "可用性目標達成不可"
            assert tradeoff["cost_impact"] == "品質要求を満たすには予算3倍必要"
            assert len(tradeoff["compromise_options"]) > 0
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_アーキテクチャ思想の矛盾検出(self):
        """マイクロサービスvsモノリシックの矛盾を検出"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.architecture_conflict_detector import detect_architecture_conflicts
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # アーキテクト1: マイクロサービス推進
            arch1_req = version_service["create_versioned_requirement"]({
                "id": "REQ-ARCH-MS-001",
                "title": "マイクロサービスアーキテクチャ採用",
                "description": "各機能を独立したサービスとして実装",
                "priority": 170,
                "requirement_type": "architecture",
                "architecture_style": "microservices",
                "principles": ["独立デプロイ", "技術スタック自由", "サービス間通信"],
                "team_structure": "機能別チーム"
            })
            
            # アーキテクト2: シンプルさ重視
            arch2_req = version_service["create_versioned_requirement"]({
                "id": "REQ-ARCH-MONO-001",
                "title": "モノリシックで開始",
                "description": "初期はシンプルな一枚岩アーキテクチャ",
                "priority": 160,
                "requirement_type": "architecture", 
                "architecture_style": "monolithic",
                "principles": ["シンプル", "統一技術スタック", "直接関数呼び出し"],
                "team_structure": "単一チーム"
            })
            
            # アーキテクチャ矛盾を検出
            conflicts = detect_architecture_conflicts(repo)
            
            assert len(conflicts) > 0
            arch_conflict = conflicts[0]
            
            assert arch_conflict["conflict_type"] == "architecture_philosophy"
            assert arch_conflict["incompatible_principles"] == ["独立デプロイ vs 統一デプロイ"]
            assert arch_conflict["team_impact"] == "チーム構造の再編成が必要"
            assert arch_conflict["migration_cost"] == "high"
            assert "将来的な移行戦略を明確化" in arch_conflict["recommendation"]
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)