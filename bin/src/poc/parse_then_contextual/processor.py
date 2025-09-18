"""段階的要件処理プロセッサー"""
from typing import List, Dict, Optional
from ptc_types import ProcessingResult, CostRecord
from stages import (
    RuleBasedChecker,
    LightweightEmbeddingChecker,
    SemanticSearchChecker,
    LLMChecker
)


class StagedRequirementProcessor:
    """段階的に要件を処理するメインクラス"""
    
    def __init__(self):
        # 各ステージを初期化
        self.stages = [
            RuleBasedChecker(),
            LightweightEmbeddingChecker(),
            SemanticSearchChecker(),
            LLMChecker("small"),
            LLMChecker("large")
        ]
        self.cost_records: List[CostRecord] = []
    
    def process(self, requirement_text: str) -> ProcessingResult:
        """要件を段階的に処理"""
        total_cost = 0.0
        context = {}  # ステージ間で共有するコンテキスト
        
        print(f"\n処理開始: '{requirement_text}'")
        print("=" * 60)
        
        for stage in self.stages:
            print(f"\n[{stage.name}] 実行中...")
            
            # チェック実行
            result = stage.check(requirement_text, context)
            total_cost += stage.base_cost
            
            # 結果表示
            if result["violations"]:
                print(f"  ❌ 違反: {', '.join(result['violations'])}")
            if result["warnings"]:
                print(f"  ⚠️  警告: {', '.join(result['warnings'])}")
            print(f"  💰 コスト: {stage.base_cost:.3f}円")
            
            # 違反があれば却下
            if not result["passed"]:
                return self._create_result(
                    "却下",
                    f"{stage.name}で違反: {result['violations'][0]}",
                    total_cost,
                    stage.name,
                    context
                )
            
            # 次のステージが不要なら承認
            if not result["next_stage_needed"]:
                return self._create_result(
                    "承認",
                    f"{stage.name}で問題なし",
                    total_cost,
                    stage.name,
                    context
                )
        
        # 全ステージを通過
        return self._create_result(
            "要レビュー",
            "全ステージを通過しましたが、人間のレビューを推奨",
            total_cost,
            "Complete",
            context
        )
    
    def _create_result(
        self,
        decision: str,
        reason: str,
        cost: float,
        stage: str,
        details: Dict
    ) -> ProcessingResult:
        """処理結果を作成"""
        return {
            "decision": decision,
            "reason": reason,
            "cost": cost,
            "stage": stage,
            "details": details
        }
    
    def get_cost_summary(self) -> Dict[str, float]:
        """コストサマリーを取得"""
        summary = {}
        for stage in self.stages:
            stage_costs = [r["cost"] for r in stage.cost_records]
            if stage_costs:
                summary[stage.name] = {
                    "total": sum(stage_costs),
                    "average": sum(stage_costs) / len(stage_costs),
                    "count": len(stage_costs)
                }
        return summary