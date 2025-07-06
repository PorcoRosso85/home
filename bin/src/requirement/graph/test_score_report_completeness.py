"""
スコアレポート完全性のTDD Redテスト
すべてのドメイン観点がレポートに含まれることを保証
"""
import pytest
from typing import Dict, List, Any


class TestScoreReportDomainCompleteness:
    """スコアレポートがすべてのドメイン観点を含むことを検証"""
    
    def test_レポートは構造ドメインの評価を含む(self):
        """constraints.pyの観点がレポートに反映される"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "タスク実装",
            "level": 4,
            "depends_on": ["req_000"]  # ビジョンへの直接依存
        }
        
        report = generate_score_report(requirement)
        
        # constraintsドメインの評価が含まれる（読み替えなし）
        assert "constraints" in report["domains"]
        
        constraints = report["domains"]["constraints"]
        assert "circular_dependency" in constraints
        assert "max_depth" in constraints
        assert "implementation_completeness" in constraints
        
        # 具体的な違反情報
        assert constraints["violations"] == [
            {
                "type": "hierarchy_skip",
                "from_level": 4,
                "to_level": 0,
                "severity": "critical"
            }
        ]
    
    def test_レポートは決定ドメインの評価を含む(self):
        """decision.pyの観点がレポートに反映される"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "API設計",
            "description": "効率的なAPIを実装する",
            "status": "proposed"
        }
        
        report = generate_score_report(requirement)
        
        # 決定ドメインの評価が含まれる
        assert "decision" in report["domains"]
        
        decision = report["domains"]["decision"]
        assert "completeness" in decision
        assert "clarity" in decision
        assert "rationale_strength" in decision
        
        # 品質メトリクス
        assert decision["metrics"] == {
            "description_length": 15,  # 文字数
            "ambiguous_terms": ["効率的"],
            "missing_fields": ["acceptance_criteria"]
        }
    
    def test_レポートは埋め込みドメインの評価を含む(self):
        """embedder.pyの観点がレポートに反映される"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "ログイン機能",
            "embedding": [0.1, 0.2] + [0.0] * 48  # 50次元
        }
        
        report = generate_score_report(requirement)
        
        # 埋め込みドメインの評価が含まれる
        assert "embedder" in report["domains"]
        
        semantic = report["domains"]["embedder"]
        assert "similarity_conflicts" in semantic
        assert "semantic_drift" in semantic
        assert "clustering_info" in semantic
        
        # 類似要件との関係
        assert "similar_requirements" in semantic
        assert len(semantic["similar_requirements"]) > 0
    
    def test_レポートはバージョンドメインの評価を含む(self):
        """version_tracking.pyの観点がレポートに反映される"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "version": 5,
            "change_frequency": "high"
        }
        
        report = generate_score_report(requirement)
        
        # バージョンドメインの評価が含まれる
        assert "version_tracking" in report["domains"]
        
        version = report["domains"]["version_tracking"]
        assert "change_rate" in version
        assert "major_pivots" in version
        assert "stability_score" in version
        
        # 時間経過による劣化
        assert version["temporal_friction"] == {
            "evolution_steps": 5,
            "has_major_pivot": True,
            "friction_score": -80
        }
    
    def test_レポートは型ドメインの評価を含む(self):
        """types.pyの型整合性がレポートに反映される"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "priority": "high",  # 型違反：文字列
            "status": "invalid_status"  # 不正な値
        }
        
        report = generate_score_report(requirement)
        
        # 型ドメインの評価が含まれる
        assert "types" in report["domains"]
        
        types = report["domains"]["types"]
        assert "type_violations" in types
        assert "invalid_values" in types
        
        # 型違反の詳細
        assert types["violations"] == [
            {
                "field": "priority",
                "expected": "int",
                "actual": "str",
                "value": "high"
            },
            {
                "field": "status",
                "expected": "Literal[proposed,approved,implemented,deprecated]",
                "actual": "str",
                "value": "invalid_status"
            }
        ]


class TestScoreReportCrossDomainIntegration:
    """ドメイン横断的な統合評価"""
    
    def test_すべてのドメインスコアが統合される(self):
        """各ドメインのスコアが適切に重み付けされて統合"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "機能実装",
            "level": 3,
            "status": "proposed"
        }
        report = generate_score_report(requirement)
        
        # ドメインごとのスコア
        assert "domain_scores" in report
        scores = report["domain_scores"]
        
        assert "constraints" in scores
        assert "decision" in scores
        assert "embedder" in scores
        assert "version_tracking" in scores
        assert "types" in scores
        
        # 重み付け情報
        assert "domain_weights" in report
        weights = report["domain_weights"]
        
        # 重みの合計は1.0
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001
        
        # 統合スコアの計算過程
        assert "integration" in report
        integration = report["integration"]
        assert "weighted_scores" in integration
        assert "final_score" in integration
    
    def test_ドメイン間の相互作用が分析される(self):
        """異なるドメイン間の相関や影響"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "機能実装",
            "level": 3,
            "status": "proposed"
        }
        report = generate_score_report(requirement)
        
        assert "cross_domain_analysis" in report
        cross = report["cross_domain_analysis"]
        
        # 構造違反が決定品質に与える影響
        assert "structural_decision_impact" in cross
        
        # バージョン不安定性が型整合性に与える影響
        assert "version_type_correlation" in cross
        
        # 相互影響マトリクス
        assert "interaction_matrix" in cross
    
    def test_欠落ドメインが警告として報告される(self):
        """評価できなかったドメインの報告"""
        from application.score_report_generator import generate_score_report
        
        # 不完全な要件
        requirement = {"id": "req_123"}  # 最小限の情報
        
        report = generate_score_report(requirement)
        
        assert "missing_domains" in report
        missing = report["missing_domains"]
        
        assert "embedding" in missing  # 埋め込みなし
        assert missing["embedding"]["reason"] == "No embedding vector found"
        assert missing["embedding"]["impact"] == "Semantic analysis unavailable"
    
    def test_ドメイン評価の信頼度が含まれる(self):
        """各ドメイン評価の信頼度スコア"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "機能実装",
            "level": 3,
            "status": "proposed"
        }
        report = generate_score_report(requirement)
        
        assert "domain_confidence" in report
        confidence = report["domain_confidence"]
        
        # 各ドメインの信頼度（0.0-1.0）
        for domain in ["constraints", "decision", "embedder", "version_tracking", "types"]:
            assert domain in confidence
            assert 0.0 <= confidence[domain] <= 1.0
        
        # 全体の信頼度
        assert "overall_confidence" in report["summary"]


class TestScoreReportFormat:
    """レポートフォーマットの完全性"""
    
    def test_レポートは必須セクションをすべて含む(self):
        """標準レポート構造の検証"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "機能実装",
            "level": 3,
            "status": "proposed"
        }
        report = generate_score_report(requirement)
        
        # 必須トップレベルキー
        required_keys = [
            "type",           # "score_report"
            "timestamp",      # ISO形式
            "requirement_id", # 対象要件
            "summary",        # サマリ情報
            "domains",        # ドメイン別評価
            "breakdown",      # 詳細内訳
            "reasoning",      # 推論過程
            "recommendations" # 改善提案
        ]
        
        for key in required_keys:
            assert key in report, f"Missing required key: {key}"
    
    def test_レポートはメタデータを含む(self):
        """計算バージョンや設定情報"""
        from application.score_report_generator import generate_score_report
        
        requirement = {
            "id": "req_123",
            "title": "機能実装",
            "level": 3,
            "status": "proposed"
        }
        report = generate_score_report(requirement)
        
        assert "metadata" in report
        meta = report["metadata"]
        
        assert "calculation_version" in meta
        assert "business_phase" in meta
        assert "organization_mode" in meta
        assert "applied_rules" in meta
        assert "processing_time_ms" in meta