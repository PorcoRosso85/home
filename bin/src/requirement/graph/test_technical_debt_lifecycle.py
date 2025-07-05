"""
技術的負債のライフサイクルテスト（TDD Red）

技術的負債の受け入れから返済までのライフサイクルを通じて、
システムがどのように摩擦を検出し、健全性を管理するかをテストする。
"""
import pytest
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime, timedelta


@pytest.mark.skip(reason="TDD Red: 技術的負債ライフサイクル機能未実装")
class TestTechnicalDebtLifecycle:
    """技術的負債のライフサイクルテスト"""
    
    def test_負債の受け入れ(self):
        """技術的負債を許容する要件を追加し、スコアが意図通りであることを確認"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from infrastructure.ddl_schema_manager import DDLSchemaManager
        
        # テスト用DB
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
            
            # 技術的負債を含む要件を作成
            result = version_service["create_versioned_requirement"]({
                "id": "REQ-DEBT-001",
                "title": "簡易実装でMVP対応",
                "description": "適切なアーキテクチャを犠牲にして短期リリースを優先",
                "priority": 150,
                "requirement_type": "functional",
                "status": "approved",
                "technical_debt_accepted": True,  # 技術的負債を許容
                "debt_justification": "MVPのため一時的に許容",
                "debt_impact_level": "medium"
            })
            
            assert result is not None
            
            # スコアリングを実行
            from application.scoring_service import calculate_friction_score
            score = calculate_friction_score(repo, "REQ-DEBT-001")
            
            # 技術的負債は許容されているため、スコアは健全な範囲内
            assert score["total"]["health"] == "acceptable"
            assert score["frictions"]["technical_debt"]["accepted"] == True
            assert score["frictions"]["technical_debt"]["score"] < 0.5  # 許容範囲内
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_負債影響の顕在化(self):
        """負債要件に依存する新機能追加時にスコアが悪化することを確認"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
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
            
            # 技術的負債を含む基盤要件
            version_service["create_versioned_requirement"]({
                "id": "REQ-DEBT-BASE-001",
                "title": "簡易データアクセス層",
                "description": "SQLインジェクション対策なしの簡易実装",
                "priority": 200,
                "technical_debt_accepted": True,
                "debt_impact_level": "high"
            })
            
            # 負債要件に依存する新機能
            result = version_service["create_versioned_requirement"]({
                "id": "REQ-NEW-FEATURE-001",
                "title": "ユーザー管理機能",
                "description": "簡易データアクセス層を使用したユーザー管理",
                "priority": 180,
                "depends_on": ["REQ-DEBT-BASE-001"]
            })
            
            # 依存関係を作成
            create_dependency_query = """
            MATCH (feature:RequirementEntity {id: 'REQ-NEW-FEATURE-001'})
            MATCH (debt:RequirementEntity {id: 'REQ-DEBT-BASE-001'})
            CREATE (feature)-[:DEPENDS_ON]->(debt)
            """
            repo["execute"](create_dependency_query, {})
            
            # スコアリング
            from application.scoring_service import calculate_friction_score
            score = calculate_friction_score(repo, "REQ-NEW-FEATURE-001")
            
            # 技術的負債に依存しているため、スコアが悪化
            assert score["total"]["health"] == "unhealthy"
            assert score["frictions"]["technical_debt"]["inherited"] == True
            assert score["frictions"]["technical_debt"]["score"] > 0.7  # 高い摩擦
            assert "技術的負債を継承" in score["frictions"]["technical_debt"]["message"]
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_負債の返済(self):
        """技術的負債の返済タスクが正しくリンクされることを確認"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            # DB初期化（省略）
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # 技術的負債要件
            version_service["create_versioned_requirement"]({
                "id": "REQ-DEBT-001",
                "title": "簡易実装",
                "technical_debt_accepted": True
            })
            
            # 返済タスク
            result = version_service["create_versioned_requirement"]({
                "id": "REQ-PAYBACK-001",
                "title": "アーキテクチャ改善タスク",
                "description": "技術的負債の返済",
                "requirement_type": "debt_payback",
                "targets_debt": "REQ-DEBT-001"
            })
            
            # 返済関係を作成
            payback_query = """
            MATCH (payback:RequirementEntity {id: 'REQ-PAYBACK-001'})
            MATCH (debt:RequirementEntity {id: 'REQ-DEBT-001'})
            CREATE (payback)-[:PAYS_BACK]->(debt)
            RETURN payback, debt
            """
            result = repo["execute"](payback_query, {})
            
            # 返済タスクが負債と正しくリンクされている
            assert result.has_next()
            
            # 返済タスクのメタデータ確認
            metadata_query = """
            MATCH (payback:RequirementEntity {id: 'REQ-PAYBACK-001'})-[:PAYS_BACK]->(debt)
            RETURN debt.id as debt_id, payback.requirement_type as type
            """
            result = repo["execute"](metadata_query, {})
            row = result.get_next()
            
            assert row[0] == "REQ-DEBT-001"
            assert row[1] == "debt_payback"
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_健全性の回復(self):
        """返済タスク完了後、プロジェクトのスコアが改善されることを確認"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.scoring_service import calculate_project_health_score
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # 技術的負債を含むプロジェクト
            version_service["create_versioned_requirement"]({
                "id": "REQ-DEBT-001",
                "title": "簡易実装A",
                "technical_debt_accepted": True,
                "status": "active"
            })
            
            version_service["create_versioned_requirement"]({
                "id": "REQ-DEBT-002", 
                "title": "簡易実装B",
                "technical_debt_accepted": True,
                "status": "active"
            })
            
            # 返済前のスコア
            before_score = calculate_project_health_score(repo)
            assert before_score["technical_debt"]["total_debt"] == 2
            assert before_score["health"] == "unhealthy"
            
            # 返済タスクを作成して完了
            version_service["create_versioned_requirement"]({
                "id": "REQ-PAYBACK-001",
                "title": "負債返済A",
                "requirement_type": "debt_payback",
                "targets_debt": "REQ-DEBT-001",
                "status": "completed"
            })
            
            # 負債要件を解決済みに更新
            update_query = """
            MATCH (debt:RequirementEntity {id: 'REQ-DEBT-001'})
            SET debt.status = 'resolved',
                debt.technical_debt_paid = true
            """
            repo["execute"](update_query, {})
            
            # 返済後のスコア
            after_score = calculate_project_health_score(repo)
            assert after_score["technical_debt"]["total_debt"] == 1  # 1つ減少
            assert after_score["technical_debt"]["paid_debt"] == 1
            assert after_score["health"] == "acceptable"  # 改善
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)