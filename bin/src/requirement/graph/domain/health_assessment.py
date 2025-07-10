"""
健全性評価（ドメイン層）
"""
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class HealthReport:
    """健全性レポート"""
    level: str
    overall_score: int
    category_scores: Dict[str, int]
    issues: List[str]
    recommendations: List[str]


class HealthAssessment:
    """要件の健全性評価"""

    def __init__(self):
        self.category_scores = {}
        self.category_weights = {}

    def add_category_score(self, category: str, score: float, weight: float):
        """カテゴリ別スコアを追加"""
        self.category_scores[category] = score
        self.category_weights[category] = weight

    def calculate_overall_score(self) -> float:
        """重み付き平均を計算"""
        if not self.category_scores:
            return 0.0

        total_weighted = sum(
            score * self.category_weights.get(cat, 0.0)
            for cat, score in self.category_scores.items()
        )

        return total_weighted

    # カテゴリごとの重み（デフォルト）
    CATEGORY_WEIGHTS = {
        "structure": 0.3,
        "friction": 0.3,
        "completeness": 0.2,
        "consistency": 0.2
    }

    # 健全性レベルの定義
    HEALTH_LEVELS = {
        "healthy": {"threshold": -20, "label": "健全"},
        "warning": {"threshold": -50, "label": "要注意"},
        "critical": {"threshold": -100, "label": "危機的"}
    }

    @classmethod
    def calculate_weighted_score(cls, scores: Dict[str, int]) -> int:
        """重み付きスコアを計算"""
        total = 0
        total_weight = 0

        for category, score in scores.items():
            weight = cls.CATEGORY_WEIGHTS.get(category, 0.1)
            total += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0

        return int(total / total_weight)

    def get_health_level(self, score: float) -> str:
        """スコアから健全性レベルを判定"""
        if score >= 0.7:
            return "healthy"
        elif score >= 0.4:
            return "needs_attention"
        else:
            return "critical"

    @classmethod
    def classify_health_level(cls, score: int) -> str:
        """スコアから健全性レベルを判定"""
        if score >= cls.HEALTH_LEVELS["healthy"]["threshold"]:
            return "healthy"
        elif score >= cls.HEALTH_LEVELS["warning"]["threshold"]:
            return "warning"
        else:
            return "critical"

    def generate_report(self) -> Dict[str, Any]:
        """健全性レポートを生成"""
        overall_score = self.calculate_overall_score()
        level = self.get_health_level(overall_score)

        # 問題点の抽出
        problem_areas = []
        recommendations = []

        for category, score in self.category_scores.items():
            if score < 0.5:
                problem_areas.append(category)

                if category == "graph_consistency":
                    recommendations.append("要件の依存関係グラフを見直してください")
                elif category == "friction_level":
                    recommendations.append("チーム間の認識を統一してください")
                elif category == "completeness":
                    recommendations.append("不足している要件を追加してください")
                elif category == "technical_debt":
                    recommendations.append("技術的負債を解消してください")

        return {
            "level": level,
            "overall_score": overall_score,
            "category_scores": self.category_scores,
            "problem_areas": problem_areas,
            "recommendations": recommendations
        }

    @classmethod
    def generate_report_from_scores(cls, scores: Dict[str, int]) -> HealthReport:
        """健全性レポートを生成"""
        overall_score = cls.calculate_weighted_score(scores)
        level = cls.classify_health_level(overall_score)

        # 問題点の抽出
        issues = []
        recommendations = []

        for category, score in scores.items():
            if score < -50:
                issues.append(f"{category}に深刻な問題があります（スコア: {score}）")

                if category == "structure":
                    recommendations.append("要件の依存関係構造を見直してください")
                elif category == "friction":
                    recommendations.append("チーム間の認識を統一してください")
                elif category == "completeness":
                    recommendations.append("不足している要件を追加してください")
                elif category == "consistency":
                    recommendations.append("矛盾する要件を解消してください")

        return HealthReport(
            level=level,
            overall_score=overall_score,
            category_scores=scores,
            issues=issues,
            recommendations=recommendations
        )


def assess_project_health(total_score: int) -> str:
    """
    総合スコアからプロジェクト健全性を判定
    
    Args:
        total_score: 総合スコア
        
    Returns:
        健全性レベル
    """
    if total_score > -20:
        return "healthy"
    elif total_score > -50:
        return "needs_attention"
    elif total_score > -70:
        return "at_risk"
    else:
        return "critical"
