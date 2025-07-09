"""
要件の陳腐化と棚卸しテスト（TDD Red）

長期間更新されていない要件の陳腐化検出と、
アーカイブによる無効化の動作をテストする。
"""
import pytest
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime, timedelta


@pytest.mark.skip(reason="TDD Red: 要件陳腐化機能未実装")
class TestRequirementObsolescence:
    """要件の陳腐化と棚卸しテスト"""

    def test_陳腐化の特定(self):
        """長期間更新・参照されていない要件を陳腐化候補として特定"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.obsolescence_detector import identify_obsolete_requirements
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

            # 古い要件を作成（6ヶ月前）
            old_timestamp = (datetime.now() - timedelta(days=180)).isoformat()

            # 直接古いタイムスタンプで要件を作成
            create_old_req_query = f"""
            CREATE (req:RequirementEntity {{
                id: 'REQ-OLD-001',
                title: '古い要件',
                description: '長期間更新されていない要件',
                status: 'approved'
            }})
            CREATE (loc:LocationURI {{id: 'req://REQ-OLD-001'}})
            CREATE (loc)-[:LOCATES]->(req)
            CREATE (v:VersionState {{
                id: 'ver_REQ-OLD-001_v1',
                timestamp: '{old_timestamp}',
                operation: 'CREATE'
            }})
            CREATE (req)-[:HAS_VERSION]->(v)
            """
            repo["execute"](create_old_req_query, {})

            # 最近の要件を作成
            version_service["create_versioned_requirement"]({
                "id": "REQ-NEW-001",
                "title": "新しい要件",
                "description": "最近作成された要件"
            })

            # 陳腐化候補を特定
            obsolete_candidates = identify_obsolete_requirements(
                repo,
                days_threshold=90  # 90日以上更新なし
            )

            # 古い要件のみが候補として特定される
            assert len(obsolete_candidates) == 1
            assert obsolete_candidates[0]["id"] == "REQ-OLD-001"
            assert obsolete_candidates[0]["days_since_update"] > 90
            assert obsolete_candidates[0]["obsolescence_score"] > 0.7
            assert obsolete_candidates[0]["referenced_count"] == 0  # 参照されていない

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_陳腐化による摩擦(self):
        """新要件が陳腐化候補と関連する場合にtemporal_frictionが検出される"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        # from application.scoring_service import calculate_friction_score  # Removed: scoring system deleted

        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")

        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)

            # 陳腐化した要件（180日前）
            old_timestamp = (datetime.now() - timedelta(days=180)).isoformat()
            create_obsolete_query = f"""
            CREATE (req:RequirementEntity {{
                id: 'REQ-OBSOLETE-001',
                title: '陳腐化した認証方式',
                description: '古いセッション管理方式',
                status: 'approved'
            }})
            CREATE (loc:LocationURI {{id: 'req://REQ-OBSOLETE-001'}})
            CREATE (loc)-[:LOCATES]->(req)
            CREATE (v:VersionState {{
                id: 'ver_REQ-OBSOLETE-001_v1',
                timestamp: '{old_timestamp}',
                operation: 'CREATE'
            }})
            CREATE (req)-[:HAS_VERSION]->(v)
            """
            repo["execute"](create_obsolete_query, {})

            # 陳腐化要件に依存する新要件
            result = version_service["create_versioned_requirement"]({
                "id": "REQ-NEW-AUTH-001",
                "title": "新認証機能",
                "description": "既存の認証方式を拡張",
                "depends_on": ["REQ-OBSOLETE-001"]
            })

            # 依存関係を作成
            dep_query = """
            MATCH (new:RequirementEntity {id: 'REQ-NEW-AUTH-001'})
            MATCH (old:RequirementEntity {id: 'REQ-OBSOLETE-001'})
            CREATE (new)-[:DEPENDS_ON]->(old)
            """
            repo["execute"](dep_query, {})

            # スコアリング
            score = calculate_friction_score(repo, "REQ-NEW-AUTH-001")

            # temporal_frictionが検出される
            assert score["frictions"]["temporal"]["score"] > 0.5
            assert score["frictions"]["temporal"]["obsolete_dependencies"] == 1
            assert "陳腐化した要件に依存" in score["frictions"]["temporal"]["message"]
            assert score["total"]["health"] == "unhealthy"

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def test_アーカイブによる除外(self):
        """要件をarchivedステータスにした際の除外動作を確認"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        # from application.requirement_service import get_active_requirements  # Removed: service deleted
        # from application.scoring_service import calculate_project_health_score  # Removed: scoring system deleted

        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")

        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)

            # アクティブな要件を3つ作成
            for i in range(3):
                version_service["create_versioned_requirement"]({
                    "id": f"REQ-ACTIVE-{i:03d}",
                    "title": f"アクティブ要件{i}",
                    "status": "approved"
                })

            # アーカイブ前の状態確認
            active_reqs = get_active_requirements(repo)
            assert len(active_reqs) == 3

            before_score = calculate_project_health_score(repo)
            assert before_score["total_requirements"] == 3

            # 1つをアーカイブ
            archive_query = """
            MATCH (req:RequirementEntity {id: 'REQ-ACTIVE-001'})
            SET req.status = 'archived'
            """
            repo["execute"](archive_query, {})

            # アーカイブ後の状態確認
            active_reqs_after = get_active_requirements(repo)
            assert len(active_reqs_after) == 2  # 1つ減少

            # アーカイブされた要件は含まれない
            active_ids = [r["id"] for r in active_reqs_after]
            assert "REQ-ACTIVE-001" not in active_ids

            # スコアリングからも除外
            after_score = calculate_project_health_score(repo)
            assert after_score["total_requirements"] == 2  # アーカイブ分を除外
            assert after_score["archived_requirements"] == 1

            # 依存関係分析からも除外
            dependency_query = """
            MATCH (req:RequirementEntity)-[:DEPENDS_ON]->(dep:RequirementEntity)
            WHERE req.status <> 'archived' AND dep.status <> 'archived'
            RETURN count(*) as active_dependencies
            """
            result = repo["execute"](dependency_query, {})
            # アーカイブされた要件への依存関係は無視される

        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
