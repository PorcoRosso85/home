"""
過去の意思決定（不採用ノード）を文脈とした摩擦検出テスト（TDD Red）

過去に不採用となった要件と類似した新要件を提案した際の
警告やスコア低下の動作をテストする。
"""
import pytest
from pathlib import Path
import tempfile
import os
import shutil
from datetime import datetime, timedelta


@pytest.mark.skip(reason="TDD Red: 過去の意思決定コンテキスト機能未実装")
class TestPastDecisionContext:
    """過去の意思決定を文脈とした摩擦検出テスト"""
    
    def test_類似要件の再提案_コスト理由(self):
        """コストで不採用となった要件と類似した新要件でスコア低下を確認"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.scoring_service import calculate_friction_score
        from application.similarity_detector import find_similar_rejected_requirements
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
            
            # 過去に不採用となった要件を作成
            rejected_timestamp = (datetime.now() - timedelta(days=90)).isoformat()
            create_rejected_query = f"""
            CREATE (req:RequirementEntity {{
                id: 'REQ-REJECTED-001',
                title: '高性能サーバー導入',
                description: '専用サーバー3台による冗長構成',
                priority: 200,
                status: 'rejected',
                rejection_reason: 'cost_too_high',
                rejection_details: '初期投資500万円、運用コスト月50万円',
                rejected_at: '{rejected_timestamp}',
                estimated_cost: 5000000
            }})
            CREATE (loc:LocationURI {{id: 'req://REQ-REJECTED-001'}})
            CREATE (loc)-[:LOCATES]->(req)
            CREATE (v:VersionState {{
                id: 'ver_REQ-REJECTED-001_v1',
                timestamp: '{rejected_timestamp}',
                operation: 'CREATE'
            }})
            CREATE (req)-[:HAS_VERSION]->(v)
            
            // 決定ノードも作成
            CREATE (decision:Decision {{
                id: 'DEC-001',
                decision_type: 'rejection',
                reason: 'cost',
                timestamp: '{rejected_timestamp}',
                stakeholder: 'CTO',
                impact_analysis: 'コストが予算の3倍を超過'
            }})
            CREATE (req)-[:HAS_DECISION]->(decision)
            """
            repo["execute"](create_rejected_query, {})
            
            # 類似した新要件を提案
            result = version_service["create_versioned_requirement"]({
                "id": "REQ-NEW-SERVER-001",
                "title": "高可用性サーバー環境",
                "description": "専用サーバーによる高可用性構成",
                "priority": 180,
                "estimated_cost": 4000000  # 少し安いが依然高額
            })
            
            # 類似性を検出
            similar_rejected = find_similar_rejected_requirements(
                repo, 
                "REQ-NEW-SERVER-001"
            )
            
            assert len(similar_rejected) > 0
            assert similar_rejected[0]["id"] == "REQ-REJECTED-001"
            assert similar_rejected[0]["similarity_score"] > 0.7
            assert similar_rejected[0]["rejection_reason"] == "cost_too_high"
            
            # スコアリング
            score = calculate_friction_score(repo, "REQ-NEW-SERVER-001")
            
            # 過去の不採用事例による警告とスコア低下
            assert score["frictions"]["past_decisions"]["score"] > 0.6
            assert score["frictions"]["past_decisions"]["similar_rejected_count"] == 1
            assert "過去に類似要件がコストで不採用" in score["frictions"]["past_decisions"]["message"]
            assert score["total"]["health"] == "risky"
            
            # 警告の詳細
            warnings = score["frictions"]["past_decisions"]["warnings"]
            assert len(warnings) > 0
            assert warnings[0]["past_requirement_id"] == "REQ-REJECTED-001"
            assert warnings[0]["rejection_reason"] == "cost_too_high"
            assert warnings[0]["estimated_cost_ratio"] == 0.8  # 4M/5M
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_類似要件の再提案_技術的理由(self):
        """技術的理由で不採用となった要件と類似した新要件の検出"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.scoring_service import calculate_friction_score
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # 技術的理由で不採用の要件
            rejected_timestamp = (datetime.now() - timedelta(days=60)).isoformat()
            create_rejected_tech_query = f"""
            CREATE (req:RequirementEntity {{
                id: 'REQ-REJECTED-TECH-001',
                title: 'ブロックチェーンによるデータ管理',
                description: 'すべてのデータをブロックチェーンで管理',
                priority: 150,
                status: 'rejected',
                rejection_reason: 'technical_infeasibility',
                rejection_details: 'パフォーマンス要件を満たせない',
                rejected_at: '{rejected_timestamp}',
                technical_constraints: 'レスポンス時間10秒以上'
            }})
            CREATE (loc:LocationURI {{id: 'req://REQ-REJECTED-TECH-001'}})
            CREATE (loc)-[:LOCATES]->(req)
            
            CREATE (decision:Decision {{
                id: 'DEC-TECH-001',
                decision_type: 'rejection',
                reason: 'technical',
                timestamp: '{rejected_timestamp}',
                stakeholder: 'Tech Lead',
                technical_analysis: 'ブロックチェーンのコンセンサスに時間がかかりすぎる'
            }})
            CREATE (req)-[:HAS_DECISION]->(decision)
            """
            repo["execute"](create_rejected_tech_query, {})
            
            # 類似技術を使う新要件
            result = version_service["create_versioned_requirement"]({
                "id": "REQ-NEW-BLOCKCHAIN-001",
                "title": "分散台帳によるトランザクション管理",
                "description": "ブロックチェーン技術を活用した取引管理",
                "priority": 160,
                "performance_requirement": "レスポンス3秒以内"
            })
            
            # スコアリング
            score = calculate_friction_score(repo, "REQ-NEW-BLOCKCHAIN-001")
            
            # 技術的な不採用履歴による高い摩擦
            assert score["frictions"]["past_decisions"]["score"] > 0.7
            assert "技術的制約で不採用" in score["frictions"]["past_decisions"]["message"]
            assert score["frictions"]["past_decisions"]["technical_risks"] == ["performance"]
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_不採用理由の学習と改善提案(self):
        """過去の不採用理由から学習し、改善提案を生成"""
        from infrastructure.kuzu_repository import create_kuzu_repository
        from application.version_service import create_version_service
        from application.decision_learner import generate_improvement_suggestions
        
        temp_dir = tempfile.mkdtemp()
        test_db = os.path.join(temp_dir, "test.db")
        
        try:
            repo = create_kuzu_repository(test_db)
            version_service = create_version_service(repo)
            
            # 複数の不採用事例を作成
            rejection_cases = [
                {
                    "id": "REQ-REJ-COST-001",
                    "title": "AIチャットボット導入",
                    "rejection_reason": "cost_too_high",
                    "cost": 3000000
                },
                {
                    "id": "REQ-REJ-COST-002", 
                    "title": "機械学習プラットフォーム",
                    "rejection_reason": "cost_too_high",
                    "cost": 5000000
                },
                {
                    "id": "REQ-REJ-TECH-001",
                    "title": "リアルタイム画像処理",
                    "rejection_reason": "technical_infeasibility",
                    "constraint": "GPU不足"
                }
            ]
            
            for case in rejection_cases:
                create_case_query = f"""
                CREATE (req:RequirementEntity {{
                    id: '{case["id"]}',
                    title: '{case["title"]}',
                    status: 'rejected',
                    rejection_reason: '{case["rejection_reason"]}'
                }})
                CREATE (loc:LocationURI {{id: 'req://{case["id"]}'}})
                CREATE (loc)-[:LOCATES]->(req)
                """
                repo["execute"](create_case_query, {})
            
            # 新しいAI関連要件
            new_req = version_service["create_versioned_requirement"]({
                "id": "REQ-NEW-AI-001",
                "title": "AI画像認識システム",
                "description": "リアルタイムでの画像認識と分類",
                "priority": 200,
                "estimated_cost": 2500000
            })
            
            # 改善提案を生成
            suggestions = generate_improvement_suggestions(
                repo,
                "REQ-NEW-AI-001"
            )
            
            # 過去の不採用パターンに基づく提案
            assert len(suggestions) > 0
            
            # コスト関連の提案
            cost_suggestions = [s for s in suggestions if s["type"] == "cost_reduction"]
            assert len(cost_suggestions) > 0
            assert "段階的導入" in cost_suggestions[0]["suggestion"]
            assert cost_suggestions[0]["based_on_cases"] == ["REQ-REJ-COST-001", "REQ-REJ-COST-002"]
            
            # 技術的な提案
            tech_suggestions = [s for s in suggestions if s["type"] == "technical_mitigation"]
            assert len(tech_suggestions) > 0
            assert "GPU" in tech_suggestions[0]["suggestion"]
            
            # リスクスコアの改善見込み
            assert suggestions[0]["potential_score_improvement"] > 0.2
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)