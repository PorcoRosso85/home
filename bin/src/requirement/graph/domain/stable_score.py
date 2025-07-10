"""
安定スコアシステム（ドメイン層）
"""
from datetime import datetime


class StableScore:
    """安定スコアシステム"""

    def __init__(self, requirement_id: str = None, initial_violations: list = None):
        self.requirement_id = requirement_id
        self.initial_violations = initial_violations or []
        self.baseline_score = self._calculate_baseline_score()
        self.baseline_timestamp = datetime.now()
        self.current_score = self.baseline_score
        self.score_history = []
        self.frictions = {}
        self.technical_debt = 0

    def initialize(self, initial_score: int):
        """
        ベースラインスコアを初期化

        Args:
            initial_score: 初期スコア
        """
        self.baseline_score = initial_score
        self.baseline_timestamp = datetime.now()
        self.current_score = initial_score
        self.score_history.append({
            "timestamp": self.baseline_timestamp,
            "score": initial_score,
            "is_baseline": True
        })

    def update(self, new_score: int):
        """
        現在スコアを更新

        Args:
            new_score: 新しいスコア
        """
        self.current_score = new_score
        self.score_history.append({
            "timestamp": datetime.now(),
            "score": new_score,
            "is_baseline": False
        })

    def add_history_point(self, day: int, score: int):
        """
        履歴ポイントを追加

        Args:
            day: 経過日数
            score: その時点のスコア
        """
        self.score_history.append({
            "day": day,
            "score": score,
            "is_baseline": False
        })

    def predict_score(self, target_day: int) -> int:
        """
        指定日のスコアを予測

        Args:
            target_day: 予測対象の日数

        Returns:
            予測スコア
        """
        if len(self.score_history) < 2:
            return self.current_score

        # 履歴から線形予測
        history_with_days = [h for h in self.score_history if "day" in h]
        if len(history_with_days) >= 2:
            # 最小二乗法で線形回帰
            days = [h["day"] for h in history_with_days]
            scores = [h["score"] for h in history_with_days]

            # 簡単な線形予測
            if len(days) == 2:
                slope = (scores[1] - scores[0]) / (days[1] - days[0])
            else:
                # 3点以上の場合は最後の2点を使う
                slope = (scores[-1] - scores[-2]) / (days[-1] - days[-2])

            # 最後の点から延長
            last_day = days[-1]
            last_score = scores[-1]
            predicted = last_score + slope * (target_day - last_day)
            return int(predicted)

        return self.current_score

    def predict(self, days_ahead: int = 30) -> int:
        """
        将来のスコアを予測

        Args:
            days_ahead: 予測する日数

        Returns:
            予測スコア
        """
        if len(self.score_history) < 2:
            return self.current_score

        # 簡単な線形劣化モデル
        # 直近の変化率から予測
        recent_scores = [h["score"] for h in self.score_history[-3:]]
        if len(recent_scores) >= 2:
            avg_change = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
            # 1日あたりの劣化を計算
            daily_degradation = avg_change / 30  # 30日で平均変化
            predicted = self.current_score + (daily_degradation * days_ahead)
            return int(predicted)

        return self.current_score

    def _calculate_baseline_score(self) -> int:
        """ベースラインスコアを計算"""
        # 違反がなければ100点
        if not self.initial_violations:
            return 100
        # 違反がある場合は減点
        return 100 - len(self.initial_violations) * 10

    def get_baseline_score(self) -> int:
        """ベースラインスコアを取得"""
        return self.baseline_score

    def get_current_score(self) -> int:
        """現在のスコアを取得"""
        return self.current_score

    def add_friction(self, friction_code: str, count: int):
        """摩擦を追加"""
        self.frictions[friction_code] = self.frictions.get(friction_code, 0) + count
        # スコアを再計算
        friction_penalty = sum(v * 20 for v in self.frictions.values())
        self.current_score = self.baseline_score - friction_penalty - self.technical_debt
        self.update(self.current_score)

    def add_technical_debt(self, debt: int):
        """技術的負債を追加"""
        self.technical_debt += debt
        self.current_score = self.baseline_score - sum(v * 20 for v in self.frictions.values()) - self.technical_debt
        self.update(self.current_score)
