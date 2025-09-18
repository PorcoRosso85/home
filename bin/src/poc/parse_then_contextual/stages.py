"""段階的処理の実装"""
from typing import List, Dict, Optional
import time
from datetime import datetime
from ptc_types import ProcessingResult, CheckResult, SimilarRequirement, CostRecord


class BaseStage:
    """処理ステージの基底クラス"""
    
    def __init__(self, name: str, base_cost: float = 0.0):
        self.name = name
        self.base_cost = base_cost
        self.cost_records: List[CostRecord] = []
    
    def record_cost(self, operation: str, cost: float):
        """コストを記録"""
        self.cost_records.append({
            "stage": self.name,
            "cost": cost,
            "timestamp": datetime.now(),
            "operation": operation
        })
    
    def check(self, requirement_text: str, context: Dict) -> CheckResult:
        """チェック実行（サブクラスで実装）"""
        raise NotImplementedError


class RuleBasedChecker(BaseStage):
    """Stage 1: ルールベースチェッカー"""
    
    def __init__(self):
        super().__init__("RuleBased", 0.0)
        self.rules = {
            "禁止ワード": ["削除", "破壊", "無効化"],
            "必須ワード": ["テスト", "ドキュメント"],
            "文字数制限": {"min": 10, "max": 500}
        }
    
    def check(self, requirement_text: str, context: Dict) -> CheckResult:
        """ルールベースでチェック"""
        violations = []
        warnings = []
        
        # 空文字列チェック
        if not requirement_text:
            violations.append(f"文字数が{self.rules['文字数制限']['min']}未満です")
            self.record_cost("rule_check", 0.0)
            return {
                "passed": False,
                "violations": violations,
                "warnings": warnings,
                "next_stage_needed": False
            }
        
        # 禁止ワードチェック
        for word in self.rules["禁止ワード"]:
            if word in requirement_text:
                violations.append(f"禁止ワード'{word}'が含まれています")
        
        # 文字数チェック
        length = len(requirement_text)
        if length < self.rules["文字数制限"]["min"]:
            violations.append(f"文字数が{self.rules['文字数制限']['min']}未満です")
        elif length > self.rules["文字数制限"]["max"]:
            violations.append(f"文字数が{self.rules['文字数制限']['max']}を超えています")
        
        # コスト記録（ルールベースは0円）
        self.record_cost("rule_check", 0.0)
        
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "next_stage_needed": len(violations) == 0
        }


class LightweightEmbeddingChecker(BaseStage):
    """Stage 2: 軽量埋め込みチェッカー"""
    
    def __init__(self):
        super().__init__("LightweightEmbedding", 0.001)
        self.existing_requirements = [
            {"id": "REQ-001", "text": "ユーザー認証機能を実装する", "embedding": [0.1, 0.2, 0.3]},
            {"id": "REQ-002", "text": "ログイン機能を追加する", "embedding": [0.1, 0.2, 0.4]},
            {"id": "REQ-003", "text": "データベース接続を最適化する", "embedding": [0.5, 0.6, 0.7]},
            {"id": "REQ-004", "text": "認証は必須", "embedding": [0.1, 0.2, 0.5]}
        ]
    
    def _compute_similarity(self, text: str, existing: Dict) -> float:
        """簡易的な類似度計算（実際は埋め込みベクトルで計算）"""
        # デモ用の簡易実装
        common_words = set(text.split()) & set(existing["text"].split())
        return len(common_words) / max(len(text.split()), len(existing["text"].split()))
    
    def check(self, requirement_text: str, context: Dict) -> CheckResult:
        """軽量埋め込みでチェック"""
        violations = []
        warnings = []
        similar_reqs: List[SimilarRequirement] = []
        
        # 類似要件を検索
        for existing in self.existing_requirements:
            similarity = self._compute_similarity(requirement_text, existing)
            if similarity > 0.9:
                violations.append(f"重複: {existing['id']} ({existing['text']})")
                similar_reqs.append({
                    "id": existing["id"],
                    "text": existing["text"],
                    "similarity": similarity,
                    "relationship": "重複"
                })
            elif similarity > 0.7:
                warnings.append(f"類似: {existing['id']} (類似度: {similarity:.2f})")
                similar_reqs.append({
                    "id": existing["id"],
                    "text": existing["text"],
                    "similarity": similarity,
                    "relationship": None
                })
        
        # コンテキストに類似要件を追加
        context["similar_requirements"] = similar_reqs
        
        # コスト記録
        self.record_cost("embedding_search", self.base_cost)
        
        # 特定の条件で次のステージへ
        needs_semantic = False
        if len(warnings) > 0 or any(0.7 <= req["similarity"] < 0.9 for req in similar_reqs):
            needs_semantic = True
        
        # 特殚パターンの検出
        if "ログイン画面" in requirement_text or "API" in requirement_text:
            needs_semantic = True
        if "複雑" in requirement_text or "なんとなく" in requirement_text:
            needs_semantic = True
        if "マイクロサービス" in requirement_text or "セキュリティ" in requirement_text:
            needs_semantic = True
        if "革新的" in requirement_text:
            needs_semantic = True
            
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "next_stage_needed": len(violations) == 0 and needs_semantic
        }


class SemanticSearchChecker(BaseStage):
    """Stage 3: CCG統合による意味検索チェッカー"""
    
    def __init__(self):
        super().__init__("SemanticSearch", 0.005)
    
    def check(self, requirement_text: str, context: Dict) -> CheckResult:
        """CCGを使った意味的検索（デモ用簡易実装）"""
        violations = []
        warnings = []
        
        # デモ: 類似要件がある場合の意味的分析
        if "similar_requirements" in context:
            for req in context["similar_requirements"]:
                if req["similarity"] > 0.7:
                    # 意味的な関係を分析（実際はCCGを使用）
                    if "認証" in req["text"] and "ログイン" in requirement_text:
                        req["relationship"] = "重複"
                        violations.append(f"意味的重複: {req['id']}")
                    elif "削除" in requirement_text and "必須" in req["text"]:
                        req["relationship"] = "矛盾"
                        violations.append(f"制約違反: {req['id']}と矛盾")
                    elif "認証" in requirement_text and "省略" in requirement_text:
                        violations.append(f"制約違反: 認証は必須のため省略できません")
                    elif "API" in requirement_text and "変更" in requirement_text:
                        warnings.append(f"依存関係の確認が必要です")
        
        # コスト記録
        self.record_cost("semantic_search", self.base_cost)
        
        # LLMチェックが必要なパターン
        needs_llm = False
        if len(warnings) > 0:
            needs_llm = True
        if "複雑" in requirement_text or "なんとなく" in requirement_text:
            needs_llm = True
        if "マイクロサービス" in requirement_text:
            needs_llm = True
        if "革新的" in requirement_text:
            needs_llm = True
            
        return {
            "passed": len(violations) == 0,
            "violations": violations,  
            "warnings": warnings,
            "next_stage_needed": len(violations) == 0 and needs_llm
        }


class LLMChecker(BaseStage):
    """Stage 4/5: LLM判定チェッカー"""
    
    def __init__(self, model: str = "small"):
        cost = 0.01 if model == "small" else 0.1
        super().__init__(f"LLM_{model}", cost)
        self.model = model
    
    def check(self, requirement_text: str, context: Dict) -> CheckResult:
        """LLMによる判定（デモ用簡易実装）"""
        violations = []
        warnings = []
        
        # デモ: LLM判定のシミュレーション
        time.sleep(0.1)  # API呼び出しのシミュレーション
        
        if self.model == "small":
            # 小規模モデルの判定
            if "複雑" in requirement_text:
                warnings.append("要件が複雑すぎる可能性があります")
            elif "なんとなく" in requirement_text or "良い感じ" in requirement_text:
                violations.append("要件が曖昧です")
        else:
            # 大規模モデルの詳細分析
            if "新機能" in requirement_text:
                warnings.append("既存アーキテクチャへの影響を検討してください")
            elif "マイクロサービス" in requirement_text and "アーキテクチャ" in requirement_text:
                warnings.append("アーキテクチャへの影響を詳細に分析しました")
            elif "セキュリティ" in requirement_text and "パフォーマンス" in requirement_text:
                context["deep_analysis"] = True
        
        # コスト記録
        self.record_cost(f"llm_{self.model}_analysis", self.base_cost)
        
        # 大規模LLMが必要な場合
        needs_large_llm = False
        if self.model == "small" and ("マイクロサービス" in requirement_text or 
                                      "セキュリティ" in requirement_text or
                                      "革新的" in requirement_text):
            needs_large_llm = True
            
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "next_stage_needed": len(violations) == 0 and needs_large_llm
        }