"""
RGLシステムの問題を検証するTDD Redテスト
実際の使用で発見された問題を再現し、修正を促す
"""
import pytest
import json
from typing import Dict, List, Any


class TestFrictionDetectionIssues:
    """摩擦検出が画一的な問題のテスト"""
    
    def test_摩擦検出は要件固有の問題を検出すべき(self):
        """無関係な要件の曖昧性ではなく、作成した要件の具体的な問題を検出"""
        # Arrange
        from .application.scoring_service import create_scoring_service
        scoring_service = create_scoring_service()
        
        # 新しい要件を作成
        new_requirement = {
            "id": "req_test_guard_vision",
            "title": "テスト規約自動遵守システム",
            "description": "開発者が自然に規約準拠のテストが書けるよう支援"
        }
        
        # Act
        friction_result = scoring_service["calculate_friction_score"](
            "ambiguity_friction",
            {"requirement": new_requirement}
        )
        
        # Assert
        # 現在は「使いやすいUI」の曖昧性が常に報告される（画一的）
        # 本来は「自然に」という曖昧な表現を検出すべき
        assert friction_result["message"] == "「自然に」という表現が曖昧です"
        assert "req_test_guard_vision" in friction_result.get("affected_requirement", "")


class TestDependencyCreationIssues:
    """依存関係作成エラーの問題のテスト"""
    
    def test_複数ノードの依存関係を一度に作成できるべき(self):
        """MATCH-CREATEパターンで複数の依存関係を作成"""
        # Arrange
        from .infrastructure.versioned_cypher_executor import create_versioned_cypher_executor
        executor = create_versioned_cypher_executor()
        
        cypher = """
        MATCH (v:RequirementEntity {id: "req_vision"}),
              (a1:RequirementEntity {id: "req_arch_1"}),
              (a2:RequirementEntity {id: "req_arch_2"})
        CREATE (v)-[:DEPENDS_ON]->(a1),
               (v)-[:DEPENDS_ON]->(a2)
        RETURN v.id, a1.id, a2.id
        """
        
        # Act
        result = executor["execute"]({"type": "cypher", "query": cypher})
        
        # Assert
        assert result["status"] == "success"
        assert len(result["data"]) == 1
        assert result["data"][0] == ["req_vision", "req_arch_1", "req_arch_2"]


class TestContradictionDetectionIssues:
    """矛盾検出が機能しない問題のテスト"""
    
    def test_パフォーマンスとコストの矛盾を検出すべき(self):
        """高速処理要件と低コスト要件の矛盾を検出"""
        # Arrange
        from .application.requirement_service import create_requirement_service
        from .infrastructure.kuzu_repository import create_kuzu_repository
        repo = create_kuzu_repository()
        service = create_requirement_service(repo)
        
        requirements = [
            {
                "id": "req_perf",
                "title": "高速AST解析",
                "description": "1000行を50ms以内で解析",
                "requirement_type": "performance"
            },
            {
                "id": "req_cost",
                "title": "低コスト運用",
                "description": "開発者1人あたり月額100円以下",
                "requirement_type": "cost"
            }
        ]
        
        # Act
        contradiction_result = service["detect_contradictions"](requirements)
        
        # Assert
        assert len(contradiction_result["contradictions"]) > 0
        assert any(
            c["type"] == "resource_conflict" and
            "パフォーマンス" in c["description"] and
            "コスト" in c["description"]
            for c in contradiction_result["contradictions"]
        )


class TestRequirementTypeIssues:
    """要件タイプが無視される問題のテスト"""
    
    def test_要件タイプが正しく保存され使用されるべき(self):
        """performance、cost等の要件タイプが正しく処理される"""
        # Arrange
        from .infrastructure.kuzu_repository import create_kuzu_repository
        repo = create_kuzu_repository()
        
        requirement = {
            "id": "req_perf_001",
            "title": "応答時間要件",
            "requirement_type": "performance",
            "priority": 3
        }
        
        # Act
        saved = repo["save"](requirement)
        # find_by_idではなくexecuteを使用
        result = repo["execute"]("MATCH (r:RequirementEntity {id: 'req_perf_001'}) RETURN r", {})
        retrieved = result["data"][0][0] if result["data"] else {}
        
        # Assert
        assert retrieved["requirement_type"] == "performance"
        assert retrieved["requirement_type"] != "functional"


class TestFeedbackUsabilityIssues:
    """フィードバックが実用的でない問題のテスト"""
    
    def test_具体的な改善提案を含むべき(self):
        """健康スコアだけでなく、具体的な改善アクションを提示"""
        # Arrange
        from .application.score_report_generator import generate_score_report
        
        project_state = {
            "requirements": [
                {"id": "req_1", "priority": 5},
                {"id": "req_2", "priority": 5},
                {"id": "req_3", "priority": 5},
                {"id": "req_4", "priority": 5},
                {"id": "req_5", "priority": 5}
            ]
        }
        
        # Act
        report = generate_score_report(project_state)
        
        # Assert
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0
        assert any(
            "優先度" in r["action"] and
            "差別化" in r["action"]
            for r in report["recommendations"]
        )
        assert report["health"] != "healthy"  # 全て最高優先度は健全ではない