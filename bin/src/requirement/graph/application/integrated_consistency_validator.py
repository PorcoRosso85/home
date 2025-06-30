"""
IntegratedConsistencyValidator - 統合的不整合性検証
依存: 各種バリデーター
外部依存: なし

すべての不整合性検証を統合し、総合的な健全性評価を提供
"""
from typing import List, Dict, Any, TypedDict
from .semantic_validator import SemanticValidator
from .resource_conflict_detector import ResourceConflictDetector
from .priority_consistency_checker import PriorityConsistencyChecker
from .requirement_completeness_analyzer import RequirementCompletenessAnalyzer


class IntegratedValidationReport(TypedDict):
    """統合検証レポート"""
    semantic_conflicts: List[Dict[str, Any]]
    resource_conflicts: List[Dict[str, Any]]
    priority_issues: List[Dict[str, Any]]
    completeness_gaps: Dict[str, Any]
    overall_health_score: float
    summary: str


class IntegratedConsistencyValidator:
    """すべての不整合性検証を統合"""
    
    def __init__(self):
        self.semantic_validator = SemanticValidator()
        self.resource_detector = ResourceConflictDetector()
        self.priority_checker = PriorityConsistencyChecker()
        self.completeness_analyzer = RequirementCompletenessAnalyzer()
    
    def validate_all(self, requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        すべての観点から要件を検証
        
        Args:
            requirements: 要件のリスト
            
        Returns:
            統合検証レポート
            
        Example:
            >>> validator = IntegratedConsistencyValidator()
            >>> reqs = [{"ID": "req1", "Priority": 100, "Tags": ["feature"]}]
            >>> report = validator.validate_all(reqs)
            >>> "overall_health_score" in report
            True
        """
        # 各バリデーターを実行
        semantic_conflicts = self.semantic_validator.validate_semantic_conflicts(requirements)
        resource_conflicts = self.resource_detector.detect_resource_conflicts(requirements)
        priority_issues = self.priority_checker.check_priority_consistency(requirements)
        completeness_analysis = self.completeness_analyzer.analyze_completeness(requirements)
        
        # 健全性スコアを計算
        health_score = self._calculate_health_score(
            semantic_conflicts,
            resource_conflicts,
            priority_issues,
            completeness_analysis
        )
        
        # サマリーを生成
        summary = self._generate_summary(
            semantic_conflicts,
            resource_conflicts,
            priority_issues,
            completeness_analysis,
            health_score
        )
        
        return {
            "semantic_conflicts": semantic_conflicts,
            "resource_conflicts": resource_conflicts,
            "priority_issues": priority_issues,
            "completeness_gaps": completeness_analysis,
            "overall_health_score": health_score,
            "summary": summary
        }
    
    def _calculate_health_score(
        self,
        semantic_conflicts: List[Dict[str, Any]],
        resource_conflicts: List[Dict[str, Any]],
        priority_issues: List[Dict[str, Any]],
        completeness_analysis: Dict[str, Any]
    ) -> float:
        """
        総合的な健全性スコアを計算（0.0-1.0）
        1.0が最も健全、0.0が最も問題がある状態
        """
        # 各問題に重みを設定
        weights = {
            "semantic": 0.25,
            "resource": 0.3,
            "priority": 0.25,
            "completeness": 0.2
        }
        
        # 各カテゴリのスコアを計算
        scores = {}
        
        # 意味的矛盾: 矛盾があるごとに0.2減点
        scores["semantic"] = max(0, 1.0 - len(semantic_conflicts) * 0.2)
        
        # リソース競合: 競合があるごとに0.3減点
        scores["resource"] = max(0, 1.0 - len(resource_conflicts) * 0.3)
        
        # 優先度問題: 問題があるごとに0.2減点
        scores["priority"] = max(0, 1.0 - len(priority_issues) * 0.2)
        
        # 完全性: 欠落カテゴリごとに0.2減点
        missing_count = len(completeness_analysis.get("missing_categories", []))
        duplicate_count = len(completeness_analysis.get("duplicates", []))
        scores["completeness"] = max(0, 1.0 - missing_count * 0.2 - duplicate_count * 0.1)
        
        # 重み付けスコアを計算
        overall_score = sum(
            scores[category] * weight
            for category, weight in weights.items()
        )
        
        return round(overall_score, 2)
    
    def _generate_summary(
        self,
        semantic_conflicts: List[Dict[str, Any]],
        resource_conflicts: List[Dict[str, Any]],
        priority_issues: List[Dict[str, Any]],
        completeness_analysis: Dict[str, Any],
        health_score: float
    ) -> str:
        """検証結果のサマリーを生成"""
        issues = []
        
        if semantic_conflicts:
            issues.append(f"意味的矛盾: {len(semantic_conflicts)}件")
        
        if resource_conflicts:
            issues.append(f"リソース競合: {len(resource_conflicts)}件")
        
        if priority_issues:
            issues.append(f"優先度問題: {len(priority_issues)}件")
        
        missing = completeness_analysis.get("missing_categories", [])
        if missing:
            issues.append(f"欠落カテゴリ: {', '.join(missing)}")
        
        duplicates = completeness_analysis.get("duplicates", [])
        if duplicates:
            issues.append(f"重複要件: {len(duplicates)}件")
        
        if not issues:
            return f"すべての検証に合格しました。健全性スコア: {health_score}/1.0"
        
        return f"検出された問題: {', '.join(issues)}。健全性スコア: {health_score}/1.0"


# In-source tests
def test_integrated_validator_comprehensive():
    """統合的な不整合検出"""
    validator = IntegratedConsistencyValidator()
    
    requirements = [
        # 意味的矛盾
        {
            "ID": "perf_001",
            "Priority": 200,
            "Tags": ["performance"],
            "Metadata": {"metric": "response_time", "value": 500, "unit": "ms"},
            "Dependencies": []
        },
        {
            "ID": "perf_002",
            "Priority": 220,
            "Tags": ["performance"],
            "Metadata": {"metric": "response_time", "value": 200, "unit": "ms"},
            "Dependencies": []
        },
        # リソース競合
        {
            "ID": "resource_001",
            "Priority": 180,
            "Tags": ["infrastructure"],
            "Metadata": {"resource_type": "db_connection", "required": 80},
            "Dependencies": []
        },
        {
            "ID": "resource_002",
            "Priority": 170,
            "Tags": ["infrastructure"],
            "Metadata": {"resource_type": "db_connection", "required": 60},
            "Dependencies": []
        },
        {
            "ID": "constraint_001",
            "Priority": 255,
            "Tags": ["constraint"],
            "Metadata": {"constraint_type": "resource_limit", "resource": "db_connection", "max": 100},
            "Dependencies": []
        },
        # 優先度逆転
        {
            "ID": "feature_001",
            "Priority": 250,
            "Tags": ["feature"],
            "Dependencies": ["infra_001"]
        },
        {
            "ID": "infra_001",
            "Priority": 100,
            "Tags": ["infrastructure"],
            "Dependencies": []
        }
    ]
    
    report = validator.validate_all(requirements)
    
    # 各種問題が検出されることを確認
    assert len(report["semantic_conflicts"]) > 0
    assert len(report["resource_conflicts"]) > 0
    assert len(report["priority_issues"]) > 0
    assert "missing_categories" in report["completeness_gaps"]
    
    # 健全性スコアが低いことを確認
    assert report["overall_health_score"] < 1.0
    
    # サマリーが生成されていることを確認
    assert "検出された問題" in report["summary"]


def test_integrated_validator_healthy_project():
    """健全なプロジェクトの場合"""
    validator = IntegratedConsistencyValidator()
    
    requirements = [
        {"ID": "sec_001", "Priority": 200, "Tags": ["security"], "Dependencies": []},
        {"ID": "perf_001", "Priority": 180, "Tags": ["performance"], "Dependencies": []},
        {"ID": "func_001", "Priority": 150, "Tags": ["functional"], "Dependencies": []},
        {"ID": "ui_001", "Priority": 140, "Tags": ["usability"], "Dependencies": []},
        {"ID": "rel_001", "Priority": 160, "Tags": ["reliability"], "Dependencies": []}
    ]
    
    report = validator.validate_all(requirements)
    
    assert len(report["semantic_conflicts"]) == 0
    assert len(report["resource_conflicts"]) == 0
    assert len(report["priority_issues"]) == 0
    assert report["completeness_gaps"]["is_complete"] is True
    assert report["overall_health_score"] == 1.0
    assert "すべての検証に合格" in report["summary"]