"""
スコアリングルール仕様のTDD Redテスト
ドメイン層にビジネスルールを配置することを前提とした失敗するテスト
"""
import pytest
from typing import Dict, Any, List


class TestViolationScoresSpecification:
    """違反スコアのビジネスルール仕様"""
    
    def test_違反タイプごとの固定スコアが定義されている(self):
        """各違反タイプは固定のスコア値を持つ"""
        from domain.scoring_rules import ViolationScores
        
        scores = ViolationScores()
        
        # 重大違反（即座にエラー）: -1.0
        assert scores.GRAPH_DEPTH_EXCEEDED == -1.0
        assert scores.SELF_REFERENCE == -1.0
        assert scores.CIRCULAR_REFERENCE == -1.0
        
        # 中程度違反: -0.3 ~ -0.5
        assert scores.INVALID_DEPENDENCY == -0.5
        assert scores.MISSING_REQUIRED_FIELD == -0.5
        
        # 軽微違反: -0.1 ~ -0.2
        assert scores.NAMING_CONVENTION == -0.1
        assert scores.DESCRIPTION_TOO_SHORT == -0.2
        
        # 違反なし
        assert scores.NO_VIOLATION == 0.0
    
    def test_違反の重要度レベルが定義されている(self):
        """各違反タイプにseverityレベルが設定されている"""
        from domain.scoring_rules import ViolationScores
        
        scores = ViolationScores()
        
        assert scores.get_severity("graph_depth_exceeded") == "critical"
        assert scores.get_severity("invalid_dependency") == "moderate"
        assert scores.get_severity("missing_required_field") == "moderate"
        assert scores.get_severity("no_violation") == "none"
    
    def test_制約違反は累積スコアを計算する(self):
        """constraint_violationsは違反数に応じて増加"""
        from domain.scoring_rules import ViolationScores
        
        scores = ViolationScores()
        
        assert scores.calculate_constraint_score(1) == -0.2
        assert scores.calculate_constraint_score(2) == -0.4
        assert scores.calculate_constraint_score(3) == -0.6
        assert scores.calculate_constraint_score(5) == -1.0  # 上限
        assert scores.calculate_constraint_score(10) == -1.0  # 上限維持


class TestFrictionRulesSpecification:
    """摩擦スコアのビジネスルール仕様"""
    
    def test_曖昧性摩擦は解釈の多様性に比例する(self):
        """解釈数が多いほどスコアが悪化"""
        from domain.friction_rules import AmbiguityFriction
        
        # 明確（解釈なし）
        friction = AmbiguityFriction(interpretation_count=0)
        assert friction.calculate_score() == 0.0
        assert friction.get_level() == "clear"
        
        # やや曖昧（1つの解釈）
        friction = AmbiguityFriction(interpretation_count=1)
        assert friction.calculate_score() == -0.3
        assert friction.get_level() == "ambiguous"
        
        # 非常に曖昧（複数の解釈）
        friction = AmbiguityFriction(interpretation_count=2)
        assert friction.calculate_score() == -0.6
        assert friction.get_level() == "highly_ambiguous"
    
    def test_曖昧な用語の存在でペナルティが追加される(self):
        """特定の曖昧用語でスコア悪化"""
        from domain.friction_rules import AmbiguityFriction
        
        ambiguous_terms = ["効率的", "適切な", "最適な"]
        friction = AmbiguityFriction(
            interpretation_count=1,
            ambiguous_terms=ambiguous_terms
        )
        
        # 基本スコア-0.3 + 用語ペナルティ-0.3 = -0.6
        assert friction.calculate_score() == -0.6
    
    def test_優先度摩擦はリソース競合を反映する(self):
        """高優先度タスクの競合でスコア悪化"""
        from domain.friction_rules import PriorityFriction
        
        # 競合なし
        friction = PriorityFriction(high_priority_count=1, has_conflict=False)
        assert friction.calculate_score() == 0.0
        
        # 複数だが競合なし
        friction = PriorityFriction(high_priority_count=2, has_conflict=False)
        assert friction.calculate_score() == -0.4
        
        # 複数かつ競合あり
        friction = PriorityFriction(high_priority_count=3, has_conflict=True)
        assert friction.calculate_score() == -0.7
    
    def test_時間経過摩擦は変更頻度を反映する(self):
        """バージョン数と内容の変質度"""
        from domain.friction_rules import TemporalFriction
        
        # 安定（少ないバージョン）
        friction = TemporalFriction(evolution_steps=1)
        assert friction.calculate_score() == 0.0
        
        # 変化中（中程度のバージョン）
        friction = TemporalFriction(evolution_steps=3)
        assert friction.calculate_score() == -0.3
        
        # 原型なし（多数のバージョン＋大幅変更）
        friction = TemporalFriction(
            evolution_steps=5,
            has_major_pivot=True
        )
        assert friction.calculate_score() == -0.8


class TestHealthAssessmentSpecification:
    """プロジェクト健全性評価の仕様"""
    
    def test_健全性スコアは重み付き平均で計算される(self):
        """各カテゴリの重要度に応じた重み付け"""
        from domain.health_assessment import HealthAssessment
        
        assessment = HealthAssessment()
        
        # カテゴリごとのスコアを設定
        assessment.add_category_score("graph_consistency", 0.8, weight=0.3)
        assessment.add_category_score("friction_level", 0.5, weight=0.4)
        assessment.add_category_score("completeness", 0.9, weight=0.2)
        assessment.add_category_score("technical_debt", 0.6, weight=0.1)
        
        # 重み付き平均: (0.8*0.3 + 0.5*0.4 + 0.9*0.2 + 0.6*0.1) = 0.68
        assert abs(assessment.calculate_overall_score() - 0.68) < 0.01
    
    def test_健全性レベルは3段階で分類される(self):
        """スコアから健全性レベルを判定"""
        from domain.health_assessment import HealthAssessment
        
        assessment = HealthAssessment()
        
        assert assessment.get_health_level(0.8) == "healthy"
        assert assessment.get_health_level(0.5) == "needs_attention"
        assert assessment.get_health_level(0.3) == "critical"
    
    def test_健全性レポートには詳細な分析が含まれる(self):
        """各カテゴリの問題点と改善提案"""
        from domain.health_assessment import HealthAssessment
        
        assessment = HealthAssessment()
        assessment.add_category_score("graph_consistency", 0.3, weight=0.3)
        
        report = assessment.generate_report()
        
        assert "graph_consistency" in report["problem_areas"]
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0


class TestGraphRulesSpecification:
    """グラフ制約ルールの仕様"""
    
    def test_グラフ深さ制限が検証できる(self):
        """プロジェクトで設定された深さ制限を超えないか"""
        from infrastructure.graph_depth_validator import GraphDepthValidator
        
        validator = GraphDepthValidator(max_depth=3)
        
        # 正常な依存関係（深さ3以内）
        dependencies = [("A", "B"), ("B", "C"), ("C", "D")]
        result = validator.validate_graph_depth(dependencies)
        assert result["is_valid"] == True
        assert result["max_depth_found"] == 3
        
        # 深さ制限違反（深さ4）
        dependencies = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]
        result = validator.validate_graph_depth(dependencies)
        assert result["is_valid"] == False
        assert result["max_depth_found"] == 4
        assert len(result["violations"]) > 0
    
    def test_循環参照が検出できる(self):
        """依存関係のループを検出"""
        from infrastructure.circular_reference_detector import CircularReferenceDetector
        
        detector = CircularReferenceDetector()
        
        # 自己参照
        dependencies = [("A", "A")]
        result = detector.detect_cycles(dependencies)
        assert result["has_cycles"] == True
        assert "A" in result["self_references"]
        
        # 循環参照
        dependencies = [("A", "B"), ("B", "C"), ("C", "A")]
        result = detector.detect_cycles(dependencies)
        assert result["has_cycles"] == True
        assert len(result["cycles"]) > 0


class TestScoreMessagesSpecification:
    """スコアメッセージ変換の仕様"""
    
    def test_スコアは人間が理解できるメッセージに変換される(self):
        """技術的なスコアを業務用語に変換"""
        from domain.score_messages import ScoreMessageGenerator
        
        generator = ScoreMessageGenerator()
        
        assert "承認できません" in generator.generate_message(-1.0)
        assert "問題があります" in generator.generate_message(-0.5)
        assert "改善してください" in generator.generate_message(-0.2)
        assert "問題ありません" in generator.generate_message(0.0)
    
    def test_違反の組み合わせで詳細メッセージが生成される(self):
        """複数違反時の統合メッセージ"""
        from domain.score_messages import ScoreMessageGenerator
        
        generator = ScoreMessageGenerator()
        
        violations = [
            {"type": "graph_depth_exceeded", "score": -1.0},
            {"type": "priority_friction", "score": -0.7}
        ]
        
        message = generator.generate_combined_message(violations)
        
        assert "依存関係グラフに問題" in message
        assert "リソース配分" in message
        assert "早急な対応が必要" in message


class TestBusinessRulesSpecification:
    """ビジネス固有ルールの仕様"""
    
    def test_緊急時の例外ルールが定義されている(self):
        """hotfixなど緊急時のスコアリング調整"""
        from domain.business_rules import EmergencyRules
        
        rules = EmergencyRules()
        
        # 通常のグラフ深さ制限違反
        normal_score = rules.adjust_score(
            violation_type="graph_depth_exceeded",
            original_score=-1.0,
            context={}
        )
        assert normal_score == -1.0
        
        # hotfix時のグラフ深さ制限違反
        hotfix_score = rules.adjust_score(
            violation_type="graph_depth_exceeded", 
            original_score=-1.0,
            context={"is_hotfix": True}
        )
        assert hotfix_score == -0.5  # 軽減される
    
    def test_組織モードによってスコアリングが調整される(self):
        """組織の文化に応じた重み付け"""
        from domain.business_rules import OrganizationMode
        
        # スタートアップモード（速度重視）
        startup = OrganizationMode("startup")
        assert startup.adjust_friction_weight("priority") == 0.5  # 摩擦許容
        assert startup.adjust_friction_weight("completeness") == 0.3  # 完全性は低優先
        
        # エンタープライズモード（品質重視）
        enterprise = OrganizationMode("enterprise")
        assert enterprise.adjust_friction_weight("priority") == 1.5  # 摩擦に厳格
        assert enterprise.adjust_friction_weight("completeness") == 1.2  # 完全性重視