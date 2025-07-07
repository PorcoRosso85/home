"""
正規化されたスコアリング仕様のTDD Redテスト
整数ベース、コード化、二層スコアシステムを反映
"""
import pytest
from typing import Dict, List, Tuple


class TestViolationCodeSystem:
    """違反コード体系の仕様"""
    
    def test_違反コードは4桁の整数で定義される(self):
        """1xxx=構造、2xxx=整合性、3xxx=規約、9xxx=正常"""
        from domain.violation_codes import ViolationCode
        
        assert ViolationCode.GRAPH_DEPTH_EXCEEDED == 1001
        assert ViolationCode.SELF_REFERENCE == 1002
        assert ViolationCode.CIRCULAR_REFERENCE == 1003
        assert ViolationCode.MISSING_DEPENDENCY == 2001
        assert ViolationCode.NO_VIOLATION == 9000
    
    def test_違反コードから基本スコアを取得できる(self):
        """各コードは整数の基本スコアを持つ"""
        from domain.violation_codes import get_base_score
        
        assert get_base_score(1001) == -100  # 構造違反
        assert get_base_score(2001) == -30   # 整合性違反
        assert get_base_score(3001) == -10   # 規約違反
        assert get_base_score(9000) == 0     # 違反なし
    
    def test_違反レベルは1から5の整数で表現される(self):
        """1=正常、5=重大違反"""
        from domain.violation_codes import get_violation_level
        
        assert get_violation_level(9000) == 1
        assert get_violation_level(3001) == 2
        assert get_violation_level(2001) == 3
        assert get_violation_level(1001) == 5


class TestBusinessPhaseCoefficients:
    """ビジネスフェーズ係数の仕様"""
    
    def test_フェーズは02から10の小数で定義される(self):
        """0.2刻みで5段階"""
        from domain.business_phase import BusinessPhase
        
        phases = BusinessPhase.get_all_phases()
        assert phases == [0.2, 0.4, 0.6, 0.8, 1.0]
    
    def test_フェーズごとに4つの係数を持つ(self):
        """構造、摩擦、完全性、速度の係数"""
        from domain.business_phase import get_phase_coefficients
        
        coeffs = get_phase_coefficients(0.2)  # 初期探索期
        assert coeffs["structure"] == 0.5
        assert coeffs["friction"] == 0.3
        assert coeffs["completeness"] == 0.2
        assert coeffs["speed"] == 2.0
        
        coeffs = get_phase_coefficients(1.0)  # 成熟期
        assert coeffs["structure"] == 1.5
        assert coeffs["friction"] == 1.2
        assert coeffs["completeness"] == 1.0
        assert coeffs["speed"] == 0.5


class TestFrictionCodeSystem:
    """摩擦要因コードの仕様"""
    
    def test_摩擦要因はFで始まる3桁コードで定義される(self):
        """F001-F999の範囲"""
        from domain.friction_codes import FrictionCode
        
        assert FrictionCode.INTERPRETATION_COMPLEXITY == "F001"
        assert FrictionCode.PRIORITY_CONFLICT == "F002"
        assert FrictionCode.CHANGE_FREQUENCY == "F003"
        assert FrictionCode.CONTRADICTION_COUNT == "F004"
    
    def test_摩擦は基本値と乗数で計算される(self):
        """整数値のみ使用"""
        from domain.friction_codes import calculate_friction_score
        
        # 解釈複雑度2 = 2 × -20 = -40
        assert calculate_friction_score("F001", 2) == -40
        
        # 優先度競合3 = 3 × -30 = -90（上限）
        assert calculate_friction_score("F002", 3) == -90
        assert calculate_friction_score("F002", 5) == -90  # 上限でキャップ


class TestStableScoreSystem:
    """二層スコアシステムの仕様"""
    
    def test_ベースラインスコアは作成時に固定される(self):
        """要件の本質的価値は不変"""
        from domain.stable_score import StableScore
        
        score = StableScore(initial_violations=[])
        baseline = score.get_baseline_score()
        
        # 時間経過や状態変更があってもベースラインは不変
        score.add_friction("F001", 2)
        score.add_technical_debt(10)
        
        assert score.get_baseline_score() == baseline
    
    def test_現在スコアは累積的な変化を反映する(self):
        """摩擦や技術的負債で減少"""
        from domain.stable_score import StableScore
        
        score = StableScore(initial_violations=[])
        initial = score.get_current_score()
        
        score.add_friction("F001", 2)  # -40
        assert score.get_current_score() == initial - 40
    
    def test_予測スコアは将来の劣化を推定する(self):
        """トレンドベースの予測"""
        from domain.stable_score import StableScore
        
        score = StableScore(initial_violations=[])
        score.add_history_point(0, 85)
        score.add_history_point(30, 80)  # 30日で-5
        score.add_history_point(60, 75)  # 60日で-10
        
        # 90日後の予測: 線形なら70
        prediction = score.predict_score(90)
        assert prediction == 70


class TestScorePresentation:
    """外部向けスコア表示の仕様"""
    
    def test_内部スコアは0から100の表示スコアに変換される(self):
        """負の内部値を正の表示値に"""
        from domain.score_presentation import convert_to_display_score
        
        assert convert_to_display_score(0) == 100
        assert convert_to_display_score(-15) == 85
        assert convert_to_display_score(-30) == 70
        assert convert_to_display_score(-100) == 0
    
    def test_判定は複数の要素を統合する(self):
        """ベースライン、現在値、予測値から総合判定"""
        from domain.score_presentation import make_decision
        
        # ベースラインOK、現在OK
        decision = make_decision(baseline=85, current=72, predicted=68)
        assert decision["status"] == "PASS"
        assert decision["warning"] == "予測値が閾値を下回ります"
        
        # ベースラインOK、現在NG
        decision = make_decision(baseline=85, current=65, predicted=60)
        assert decision["status"] == "PASS_WITH_WARNING"
        assert decision["action"] == "メンテナンス推奨"


class TestContextCoefficients:
    """コンテキスト係数の仕様"""
    
    def test_コンテキストIDで係数が決まる(self):
        """C01-C99の範囲"""
        from domain.context_coefficients import get_context_coefficient
        
        assert get_context_coefficient("C01") == 0.5  # hotfix
        assert get_context_coefficient("C02") == 0.3  # security
        assert get_context_coefficient("C03") == 1.5  # tech_debt
        assert get_context_coefficient("C04") == 1.0  # normal
    
    def test_コンテキストは自動識別される(self):
        """プレフィックスやタグから判定"""
        from domain.context_coefficients import identify_context
        
        assert identify_context("hotfix_login_bug") == "C01"
        assert identify_context("normal_feature", tags=["security_critical"]) == "C02"
        assert identify_context("refactor_legacy", tags=["technical_debt"]) == "C03"


class TestHealthIndicators:
    """健全性指標の仕様（整数ベース）"""
    
    def test_カテゴリ別スコアは負の整数で表現される(self):
        """-100から0の範囲"""
        from domain.health_indicators import HealthIndicator
        
        health = HealthIndicator()
        health.set_category_score("structure", -20)
        health.set_category_score("friction", -50)
        health.set_category_score("completeness", -10)
        health.set_category_score("debt", -30)
        
        scores = health.get_all_scores()
        assert all(isinstance(s, int) for s in scores.values())
        assert all(-100 <= s <= 0 for s in scores.values())
    
    def test_重み付き平均は整数で計算される(self):
        """小数点を避けて精度を保つ"""
        from domain.health_indicators import calculate_weighted_average
        
        scores = {"structure": -20, "friction": -50, "completeness": -10, "debt": -30}
        weights = {"structure": 30, "friction": 40, "completeness": 20, "debt": 10}
        
        # (-20×30 + -50×40 + -10×20 + -30×10) / 100 = -31
        average = calculate_weighted_average(scores, weights)
        assert average == -31
    
    def test_健全性レベルはS01からS05で表現される(self):
        """状態IDによる5段階評価"""
        from domain.health_indicators import get_health_level
        
        assert get_health_level(-10) == "S01"  # 続行可能
        assert get_health_level(-30) == "S02"  # 注意喚起
        assert get_health_level(-50) == "S03"  # 修正推奨
        assert get_health_level(-70) == "S04"  # 修正必須
        assert get_health_level(-90) == "S05"  # 変更拒否