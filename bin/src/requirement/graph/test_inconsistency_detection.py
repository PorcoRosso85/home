"""
不整合性検出システムのTDD Redテスト

このテストは現在存在しない機能をテストするため、すべて失敗します。
これらのテストが通るようにシステムを実装することで、
多角度からの要件定義における不整合性を自動検出できるようになります。
"""

from datetime import datetime
from typing import TypedDict, List, Dict, Any

# RequirementEntity型定義（テスト用）
class RequirementEntity(TypedDict):
    ID: str
    Title: str
    Description: str
    CreatedBy: str
    CreatedAt: datetime
    UpdatedAt: datetime
    LocationURI: str
    Dependencies: List[str]
    Tags: List[str]
    Priority: int  # 0-255 (UINT8)
    Level: int  # 0-4 (階層レベル)
    Metadata: Dict[str, Any]

# 実装されたクラスをインポート
from application.semantic_validator import SemanticValidator
from application.resource_conflict_detector import ResourceConflictDetector
from application.priority_consistency_checker import PriorityConsistencyChecker
from application.requirement_completeness_analyzer import RequirementCompletenessAnalyzer


class TestSemanticConflictDetection:
    """意味的矛盾の検出テスト"""

    def test_detect_conflicting_performance_requirements(self):
        """同じ性能要件に対して異なる制約を設定した場合の検出"""
        # PM視点の要件：APIレスポンス500ms以内
        pm_requirement = RequirementEntity(
            ID="perf_api_pm_001",
            Title="API Response Time Requirement (PM)",
            Description="API should respond within 500ms for better UX",
            CreatedBy="ProductManager",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://performance/api_response",
            Dependencies=[],
            Tags=["performance", "api", "response-time"],
            Priority=200,
            Level=2,  # モジュールレベル
            Metadata={"constraint_type": "performance", "metric": "response_time", "value": 500, "unit": "ms"}
        )

        # Engineer視点の要件：APIレスポンス200ms以内
        engineer_requirement = RequirementEntity(
            ID="perf_api_eng_001",
            Title="API Response Time Requirement (Engineer)",
            Description="API must respond within 200ms for technical SLA",
            CreatedBy="Engineer",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://performance/api_response",
            Dependencies=[],
            Tags=["performance", "api", "response-time"],
            Priority=220,
            Level=2,  # モジュールレベル
            Metadata={"constraint_type": "performance", "metric": "response_time", "value": 200, "unit": "ms"}
        )

        validator = SemanticValidator()
        conflicts = validator.validate_semantic_conflicts([pm_requirement, engineer_requirement])

        # 期待される動作：同じメトリックに対する異なる値の矛盾を検出
        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "conflicting_constraints"
        assert conflicts[0]["metric"] == "response_time"
        assert conflicts[0]["conflicts"] == [
            {"requirement_id": "perf_api_pm_001", "value": 500, "unit": "ms"},
            {"requirement_id": "perf_api_eng_001", "value": 200, "unit": "ms"}
        ]

    def test_detect_contradictory_security_policies(self):
        """相反するセキュリティポリシーの検出"""
        # Executive視点：利便性重視
        exec_requirement = RequirementEntity(
            ID="sec_policy_exec_001",
            Title="User Convenience Security Policy",
            Description="Minimize authentication steps for better user experience",
            CreatedBy="Executive",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://security/authentication",
            Dependencies=[],
            Tags=["security", "authentication", "ux"],
            Priority=180,
            Level=1,  # アーキテクチャレベル
            Metadata={"policy_type": "authentication", "approach": "minimal", "max_steps": 1}
        )

        # Engineer視点：セキュリティ重視
        engineer_requirement = RequirementEntity(
            ID="sec_policy_eng_001",
            Title="Multi-Factor Authentication Policy",
            Description="Enforce MFA for all user accounts",
            CreatedBy="Engineer",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://security/authentication",
            Dependencies=[],
            Tags=["security", "authentication", "mfa"],
            Priority=250,
            Level=1,  # アーキテクチャレベル
            Metadata={"policy_type": "authentication", "approach": "strict", "min_factors": 2}
        )

        validator = SemanticValidator()
        conflicts = validator.validate_semantic_conflicts([exec_requirement, engineer_requirement])

        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "contradictory_policies"
        assert conflicts[0]["policy_area"] == "authentication"


class TestResourceConflictDetection:
    """リソース競合の検出テスト"""

    def test_detect_database_connection_pool_conflict(self):
        """データベース接続プールの競合検出"""
        # サービスA：接続プールを大量に使用
        service_a_requirement = RequirementEntity(
            ID="resource_db_service_a",
            Title="High Throughput Service DB Requirements",
            Description="Service A needs 80 DB connections for high throughput",
            CreatedBy="ServiceATeam",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://resources/database/connections",
            Dependencies=[],
            Tags=["resource", "database", "connection-pool"],
            Priority=200,
            Level=3,  # コンポーネントレベル
            Metadata={"resource_type": "db_connection", "required": 80, "service": "service_a"}
        )

        # サービスB：同じリソースを要求
        service_b_requirement = RequirementEntity(
            ID="resource_db_service_b",
            Title="Analytics Service DB Requirements",
            Description="Service B needs 60 DB connections for analytics",
            CreatedBy="ServiceBTeam",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://resources/database/connections",
            Dependencies=[],
            Tags=["resource", "database", "connection-pool"],
            Priority=190,
            Level=3,  # コンポーネントレベル
            Metadata={"resource_type": "db_connection", "required": 60, "service": "service_b"}
        )

        # システム制約：最大100接続
        system_constraint = RequirementEntity(
            ID="constraint_db_max",
            Title="Database Connection Pool Limit",
            Description="System constraint: max 100 DB connections",
            CreatedBy="Infrastructure",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://constraints/database",
            Dependencies=[],
            Tags=["constraint", "database", "limit"],
            Priority=255,
            Level=0,  # ビジョンレベル（システム制約）
            Metadata={"constraint_type": "resource_limit", "resource": "db_connection", "max": 100}
        )

        detector = ResourceConflictDetector()
        conflicts = detector.detect_resource_conflicts([
            service_a_requirement,
            service_b_requirement,
            system_constraint
        ])

        assert len(conflicts) == 1
        assert conflicts[0]["type"] == "resource_overallocation"
        assert conflicts[0]["resource"] == "db_connection"
        assert conflicts[0]["total_requested"] == 140
        assert conflicts[0]["available"] == 100
        assert conflicts[0]["shortage"] == 40


class TestPriorityConsistencyChecking:
    """優先度整合性のチェックテスト"""

    def test_detect_priority_dependency_inversion(self):
        """依存関係と優先度の逆転検出"""
        # 高優先度の要件が低優先度の要件に依存している不整合
        high_priority_requirement = RequirementEntity(
            ID="priority_high_001",
            Title="Critical Feature Implementation",
            Description="High priority feature that depends on infrastructure",
            CreatedBy="ProductManager",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://features/critical",
            Dependencies=["priority_low_001"],  # 低優先度の要件に依存
            Tags=["feature", "critical"],
            Priority=250,  # 高優先度
            Level=3,  # コンポーネントレベル
            Metadata={}
        )

        low_priority_requirement = RequirementEntity(
            ID="priority_low_001",
            Title="Infrastructure Optimization",
            Description="Low priority infrastructure work",
            CreatedBy="Engineer",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://infrastructure/optimization",
            Dependencies=[],
            Tags=["infrastructure", "optimization"],
            Priority=100,  # 低優先度
            Level=2,  # モジュールレベル
            Metadata={}
        )

        checker = PriorityConsistencyChecker()
        inconsistencies = checker.check_priority_consistency([
            high_priority_requirement,
            low_priority_requirement
        ])

        assert len(inconsistencies) == 1
        assert inconsistencies[0]["type"] == "priority_inversion"
        assert inconsistencies[0]["high_priority_id"] == "priority_high_001"
        assert inconsistencies[0]["low_priority_id"] == "priority_low_001"
        assert inconsistencies[0]["priority_difference"] == 150


class TestRequirementCompleteness:
    """要件完全性のテスト"""

    def test_detect_duplicate_requirements(self):
        """重複要件の検出"""
        # 異なるIDだが実質的に同じ内容の要件
        req1 = RequirementEntity(
            ID="cache_req_001",
            Title="Implement Caching Layer",
            Description="Add Redis cache for API responses",
            CreatedBy="Engineer1",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://cache/implementation",
            Dependencies=[],
            Tags=["cache", "redis", "performance"],
            Priority=180,
            Level=2,
            Metadata={"technology": "redis", "purpose": "api_cache"}
        )

        req2 = RequirementEntity(
            ID="cache_req_002",
            Title="API Response Caching",
            Description="Use Redis to cache API responses for performance",
            CreatedBy="Engineer2",
            CreatedAt=datetime.now(),
            UpdatedAt=datetime.now(),
            LocationURI="loc://performance/caching",
            Dependencies=[],
            Tags=["performance", "cache", "redis"],
            Priority=170,
            Level=2,
            Metadata={"technology": "redis", "purpose": "api_cache"}
        )

        analyzer = RequirementCompletenessAnalyzer()
        analysis = analyzer.analyze_completeness([req1, req2])

        assert len(analysis["duplicates"]) == 1
        assert set(analysis["duplicates"][0]["requirement_ids"]) == {"cache_req_001", "cache_req_002"}
        assert analysis["duplicates"][0]["similarity_score"] > 0.8


# 統合テスト：複数の不整合性を同時に検出
class TestIntegratedInconsistencyDetection:
    """統合的な不整合性検出テスト"""

    def test_comprehensive_inconsistency_detection(self):
        """複数ペルソナからの要件における包括的な不整合検出"""
        # 統合バリデーターをインポート
        from application.integrated_consistency_validator import IntegratedConsistencyValidator

        # PM, Executive, Engineerからの混在した要件
        mixed_requirements = [
            # ここに各ペルソナからの要件を追加
        ]

        validator = IntegratedConsistencyValidator()

        # 統合的な不整合検出を実行
        report = validator.validate_all(mixed_requirements)

        # 期待される結果の検証
        assert "semantic_conflicts" in report
        assert "resource_conflicts" in report
        assert "priority_issues" in report
        assert "completeness_gaps" in report
        assert "overall_health_score" in report
        assert report["overall_health_score"] < 1.0  # 不整合があるため健全性スコアは低い
