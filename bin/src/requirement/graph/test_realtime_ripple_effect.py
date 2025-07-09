"""
リアルタイム波及効果検出のテスト（TDD Red）

既存要件の変更による波及効果をリアルタイムで検出し、
影響を受ける他の要件に対して自動的に警告を発する機能のテスト。
"""
import pytest
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime
import time


@pytest.mark.skip(reason="TDD Red: リアルタイム波及効果検出機能未実装")
class TestRealtimeRippleEffect:
    """リアルタイム波及効果検出のテスト"""
    
    def test_依存要件への自動警告(self):
        """要件変更時に依存する要件へ自動的に警告を発する"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.ripple_effect_detector import RippleEffectMonitor
        from infrastructure.ddl_schema_manager import DDLSchemaManager
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            # DB初期化
            repo = create_kuzu_repository(test_db)
            schema_manager = DDLSchemaManager(repo["connection"])
            schema_path = Path(__file__).parent / "ddl" / "migrations" / "3.2.0_current.cypher"
            success, _ = schema_manager.apply_schema(str(schema_path))
            assert success
            
            version_service = create_version_service(repo)
            
            # 基盤となるAPI要件
            api_req = version_service["create_versioned_requirement"]({
                "id": "REQ-API-001",
                "title": "REST API v1",
                "description": "基本的なREST APIエンドポイント",
                "priority": 200,
                "api_version": "v1",
                "endpoints": ["/users", "/products", "/orders"]
            })
            
            # APIに依存するフロントエンド要件
            frontend_req = version_service["create_versioned_requirement"]({
                "id": "REQ-FRONT-001",
                "title": "ユーザー管理画面",
                "description": "REST API v1を使用したユーザー管理",
                "priority": 150,
                "depends_on": ["REQ-API-001"],
                "api_dependencies": {
                    "endpoints": ["/users"],
                    "version": "v1"
                }
            })
            
            # モバイルアプリ要件
            mobile_req = version_service["create_versioned_requirement"]({
                "id": "REQ-MOBILE-001",
                "title": "モバイルアプリ",
                "description": "REST APIを使用したモバイルアプリ",
                "priority": 140,
                "depends_on": ["REQ-API-001"],
                "api_dependencies": {
                    "endpoints": ["/users", "/products"],
                    "version": "v1"
                }
            })
            
            # 依存関係を作成
            dep_query = """
            MATCH (front:RequirementEntity {id: 'REQ-FRONT-001'})
            MATCH (mobile:RequirementEntity {id: 'REQ-MOBILE-001'})
            MATCH (api:RequirementEntity {id: 'REQ-API-001'})
            CREATE (front)-[:DEPENDS_ON]->(api)
            CREATE (mobile)-[:DEPENDS_ON]->(api)
            """
            repo["execute"](dep_query, {})
            
            # 波及効果モニターを起動
            monitor = RippleEffectMonitor(repo)
            alerts = []
            
            # アラートコールバックを設定
            monitor.on_alert(lambda alert: alerts.append(alert))
            monitor.start()
            
            # APIをv2に変更（破壊的変更）
            update_result = version_service["update_versioned_requirement"]({
                "id": "REQ-API-001",
                "title": "REST API v2",
                "description": "破壊的変更を含むv2 API",
                "api_version": "v2",
                "endpoints": ["/v2/users", "/v2/products", "/v2/orders"],
                "breaking_changes": True,
                "change_reason": "セキュリティ強化のため"
            })
            
            # リアルタイムアラートが発火するまで少し待つ
            time.sleep(0.1)
            monitor.stop()
            
            # 依存する要件に対してアラートが発生
            assert len(alerts) >= 2
            
            # フロントエンドへのアラート
            frontend_alert = next((a for a in alerts if a["affected_requirement"] == "REQ-FRONT-001"), None)
            assert frontend_alert is not None
            assert frontend_alert["alert_type"] == "breaking_change"
            assert frontend_alert["severity"] == "high"
            assert "API v1からv2への破壊的変更" in frontend_alert["message"]
            assert frontend_alert["impact"]["endpoints_affected"] == ["/users"]
            
            # モバイルへのアラート
            mobile_alert = next((a for a in alerts if a["affected_requirement"] == "REQ-MOBILE-001"), None)
            assert mobile_alert is not None
            assert mobile_alert["impact"]["endpoints_affected"] == ["/users", "/products"]
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_優先度変更の波及効果(self):
        """優先度変更が関連要件に波及することを検出"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.priority_ripple_detector import detect_priority_ripples
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # 認証基盤（高優先度）
            auth_req = version_service["create_versioned_requirement"]({
                "id": "REQ-AUTH-001",
                "title": "認証基盤",
                "priority": 200,  # 最高優先度
                "status": "in_progress"
            })
            
            # 認証に依存する機能（中優先度）
            features = []
            for i in range(3):
                feat = version_service["create_versioned_requirement"]({
                    "id": f"REQ-FEAT-{i:03d}",
                    "title": f"機能{i}",
                    "priority": 150,  # 中優先度
                    "depends_on": ["REQ-AUTH-001"],
                    "status": "planned"
                })
                features.append(feat)
            
            # 依存関係を設定
            for i in range(3):
                dep_query = f"""
                MATCH (feat:RequirementEntity {{id: 'REQ-FEAT-{i:03d}'}})
                MATCH (auth:RequirementEntity {{id: 'REQ-AUTH-001'}})
                CREATE (feat)-[:DEPENDS_ON]->(auth)
                """
                repo["execute"](dep_query, {})
            
            # 認証基盤の優先度を下げる
            priority_change_result = version_service["update_versioned_requirement"]({
                "id": "REQ-AUTH-001",
                "priority": 100,  # 低優先度に変更
                "change_reason": "他のプロジェクトを優先"
            })
            
            # 波及効果を検出
            ripples = detect_priority_ripples(repo, "REQ-AUTH-001", old_priority=200, new_priority=100)
            
            assert len(ripples) == 3  # 3つの依存要件に影響
            
            for ripple in ripples:
                assert ripple["affected_requirement"].startswith("REQ-FEAT-")
                assert ripple["ripple_type"] == "priority_inversion"
                assert ripple["issue"] == "依存先の優先度が依存元より低い"
                assert ripple["current_priority"] == 150
                assert ripple["dependency_priority"] == 100
                assert ripple["suggested_action"] == "優先度の見直し"
                assert ripple["risk_level"] == "medium"
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_削除時の依存関係警告(self):
        """要件削除時に依存している要件へ即座に警告"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.deletion_impact_analyzer import analyze_deletion_impact
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # コアライブラリ
            core_lib = version_service["create_versioned_requirement"]({
                "id": "REQ-CORE-001",
                "title": "共通ライブラリ",
                "description": "複数のモジュールが使用",
                "priority": 180
            })
            
            # 依存するモジュール群
            dependent_modules = []
            for module in ["auth", "payment", "notification"]:
                mod = version_service["create_versioned_requirement"]({
                    "id": f"REQ-MOD-{module.upper()}",
                    "title": f"{module}モジュール",
                    "depends_on": ["REQ-CORE-001"],
                    "critical": module == "payment"  # 決済は重要
                })
                dependent_modules.append(mod)
                
                # 依存関係作成
                dep_query = f"""
                MATCH (mod:RequirementEntity {{id: 'REQ-MOD-{module.upper()}'}})
                MATCH (core:RequirementEntity {{id: 'REQ-CORE-001'}})
                CREATE (mod)-[:DEPENDS_ON]->(core)
                """
                repo["execute"](dep_query, {})
            
            # 削除前の影響分析
            impact = analyze_deletion_impact(repo, "REQ-CORE-001")
            
            assert impact["can_delete"] == False
            assert impact["reason"] == "critical_dependencies_exist"
            assert len(impact["affected_requirements"]) == 3
            assert impact["critical_count"] == 1  # paymentモジュール
            
            # 重要な依存関係の詳細
            critical_deps = impact["critical_dependencies"]
            assert len(critical_deps) == 1
            assert critical_deps[0]["id"] == "REQ-MOD-PAYMENT"
            assert critical_deps[0]["impact_level"] == "critical"
            assert "決済機能が動作不能" in critical_deps[0]["impact_description"]
            
            # 削除を試みる（トランザクション内）
            deletion_result = version_service["soft_delete_requirement"]({
                "id": "REQ-CORE-001",
                "force": False  # 強制削除しない
            })
            
            assert deletion_result["success"] == False
            assert deletion_result["blocked_by"] == "critical_dependencies"
            assert len(deletion_result["notifications_sent"]) == 3  # 全依存要件に通知
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)