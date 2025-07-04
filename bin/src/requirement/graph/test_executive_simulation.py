"""
エグゼクティブ視点での要件管理シミュレーションテスト

経営層として以下の観点から要件を追加：
- コスト削減（リソース最小化、効率化）
- 市場投入速度（MVP、早期リリース）
- コンプライアンス・リスク管理
- 株主価値最大化

技術部門やPMと対立する可能性のある要件を意図的に含める
"""
import pytest
from typing import List, Dict, Any
from application.integrated_consistency_validator import IntegratedConsistencyValidator
from application.semantic_validator import SemanticValidator
from application.resource_conflict_detector import ResourceConflictDetector
from application.priority_consistency_checker import PriorityConsistencyChecker
from application.requirement_completeness_analyzer import RequirementCompletenessAnalyzer


def test_executive_cost_reduction_conflicts():
    """コスト削減要件による矛盾の検出"""
    validator = IntegratedConsistencyValidator()
    
    requirements = [
        # エグゼクティブ要件：インフラコスト50%削減（制約として定義）
        {
            "ID": "EXEC-001",
            "Priority": 250,
            "Tags": ["executive", "cost-reduction", "constraint"],
            "Metadata": {
                "constraint_type": "resource_limit",
                "resource": "infrastructure_budget",
                "max": 50000
            },
            "Dependencies": []
        },
        # エンジニアリング要件：高可用性インフラ構築（コスト増）
        {
            "ID": "ENG-001",
            "Priority": 200,
            "Tags": ["engineering", "infrastructure", "high-availability"],
            "Metadata": {
                "resource_type": "infrastructure_budget",
                "required": 120000,
                "availability_target": "99.99%"
            },
            "Dependencies": []
        }
    ]
    
    report = validator.validate_all(requirements)
    
    # 期待される動作:
    assert report["overall_health_score"] < 0.9
    assert len(report["resource_conflicts"]) > 0


def test_executive_time_to_market_conflicts():
    """市場投入速度要件による矛盾の検出"""
    validator = IntegratedConsistencyValidator()
    
    requirements = [
        # エグゼクティブ要件：MVP早期リリース（40%機能）
        {
            "ID": "EXEC-002",
            "Priority": 255,
            "Tags": ["executive", "mvp", "time-to-market"],
            "Metadata": {
                "metric": "feature_completeness",
                "value": 40,
                "unit": "percent",
                "target_date": "2024-03-01"
            },
            "Dependencies": []
        },
        # PM要件：機能完全性（100%）
        {
            "ID": "PM-001",
            "Priority": 200,
            "Tags": ["product", "feature-complete"],
            "Metadata": {
                "metric": "feature_completeness",
                "value": 100,
                "unit": "percent",
                "quality_standard": "production-ready"
            },
            "Dependencies": []
        },
        # エンジニアリング要件：品質基準（コード品質）
        {
            "ID": "ENG-002",
            "Priority": 180,
            "Tags": ["engineering", "quality"],
            "Metadata": {
                "metric": "code_coverage",
                "value": 90,
                "unit": "percent"
            },
            "Dependencies": []
        },
        # エグゼクティブ要件：技術的負債許容
        {
            "ID": "EXEC-003",
            "Priority": 240,
            "Tags": ["executive", "tech-debt"],
            "Metadata": {
                "metric": "tech_debt_acceptance",
                "value": "high",
                "unit": "level"
            },
            "Dependencies": []
        },
        # エンジニアリング要件：技術的負債回避
        {
            "ID": "ENG-003",
            "Priority": 190,
            "Tags": ["engineering", "quality"],
            "Metadata": {
                "metric": "tech_debt_acceptance",
                "value": "low",
                "unit": "level"
            },
            "Dependencies": []
        }
    ]
    
    report = validator.validate_all(requirements)
    
    # 期待される動作:
    assert len(report["semantic_conflicts"]) >= 2  # feature_completeness と tech_debt_acceptance の矛盾
    
    # 具体的な矛盾を確認
    metrics_with_conflicts = {c["metric"] for c in report["semantic_conflicts"]}
    assert "feature_completeness" in metrics_with_conflicts
    assert "tech_debt_acceptance" in metrics_with_conflicts


def test_executive_compliance_vs_cost():
    """コンプライアンスとコスト削減の矛盾"""
    validator = IntegratedConsistencyValidator()
    
    requirements = [
        # エグゼクティブ要件：最小限セキュリティ投資（制約として定義）
        {
            "ID": "EXEC-003",
            "Priority": 200,
            "Tags": ["executive", "cost-reduction", "security", "constraint"],
            "Metadata": {
                "constraint_type": "resource_limit",
                "resource": "security_budget",
                "max": 10000
            },
            "Dependencies": []
        },
        # コンプライアンス要件：GDPR完全準拠（リソース要求）
        {
            "ID": "COMP-001",
            "Priority": 255,  # 高優先度
            "Tags": ["compliance", "gdpr", "security"],
            "Metadata": {
                "resource_type": "security_budget",
                "required": 150000,
                "compliance_level": "full",
                "required_features": ["encryption", "audit-logging", "data-retention", "consent-management"]
            },
            "Dependencies": []
        }
    ]
    
    report = validator.validate_all(requirements)
    
    # 期待される動作:
    # コンプライアンス要件が高優先度
    comp_req = next((r for r in requirements if r["ID"] == "COMP-001"), None)
    assert comp_req["Priority"] == 255
    
    # セキュリティ投資最小化との矛盾（リソース競合）
    assert len(report["resource_conflicts"]) > 0
    assert any(c["resource"] == "security_budget" for c in report["resource_conflicts"])


def test_executive_comprehensive_simulation():
    """エグゼクティブ要件の総合的シミュレーション"""
    validator = IntegratedConsistencyValidator()
    
    requirements = [
        # エグゼクティブ要件群
        {
            "ID": "EXEC-004",
            "Priority": 240,
            "Tags": ["executive", "cost-reduction", "constraint"],
            "Metadata": {
                "constraint_type": "resource_limit",
                "resource": "infrastructure_budget",
                "max": 50000
            },
            "Dependencies": []
        },
        {
            "ID": "EXEC-005",
            "Priority": 255,
            "Tags": ["executive", "mvp", "time-to-market"],
            "Metadata": {
                "metric": "feature_completeness",
                "value": 40,
                "unit": "percent"
            },
            "Dependencies": ["ENG-003"]  # 高優先度が低優先度に依存
        },
        {
            "ID": "EXEC-006",
            "Priority": 220,
            "Tags": ["executive", "security", "cost-reduction", "constraint"],
            "Metadata": {
                "constraint_type": "resource_limit",
                "resource": "security_budget",
                "max": 10000
            },
            "Dependencies": []
        },
        {
            "ID": "EXEC-007",
            "Priority": 250,
            "Tags": ["executive", "profit"],
            "Metadata": {
                "metric": "quality_focus",
                "value": "short_term",
                "unit": "strategy"
            },
            "Dependencies": []
        },
        # 他部門要件群
        {
            "ID": "ENG-003",
            "Priority": 200,
            "Tags": ["engineering", "infrastructure"],
            "Metadata": {
                "resource_type": "infrastructure_budget",
                "required": 120000,
                "availability_target": "99.99%"
            },
            "Dependencies": []
        },
        {
            "ID": "PM-002",
            "Priority": 190,
            "Tags": ["product", "feature-complete"],
            "Metadata": {
                "metric": "feature_completeness",
                "value": 100,
                "unit": "percent"
            },
            "Dependencies": []
        },
        {
            "ID": "COMP-002",
            "Priority": 255,
            "Tags": ["compliance", "gdpr"],
            "Metadata": {
                "resource_type": "security_budget",
                "required": 150000,
                "compliance_requirement": "gdpr_full"
            },
            "Dependencies": []
        },
        {
            "ID": "QA-001",
            "Priority": 180,
            "Tags": ["quality", "long-term"],
            "Metadata": {
                "metric": "quality_focus",
                "value": "long_term",
                "unit": "strategy"
            },
            "Dependencies": []
        }
    ]
    
    report = validator.validate_all(requirements)
    
    # 期待される結果:
    # overall_health_score <= 0.6（多数の矛盾）
    assert report["overall_health_score"] <= 0.6
    
    # 各カテゴリで複数の問題を検出
    assert len(report["semantic_conflicts"]) > 0
    assert len(report["resource_conflicts"]) > 0
    assert len(report["priority_issues"]) > 0
    
    # エグゼクティブ要件が他部門要件と衝突していることを確認
    # 多数の矛盾が検出されることを確認（semantic + resource + priority）
    total_conflicts = len(report["semantic_conflicts"]) + len(report["resource_conflicts"]) + len(report["priority_issues"])
    assert total_conflicts >= 5  # 複数カテゴリで矛盾が検出される


# generate_executive_report関数とmain実行部分は削除
# TDD Redフェーズではレポート生成機能は不要