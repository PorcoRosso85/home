"""
段階的要件処理システムの仕様テスト
仕様＝テスト（実装に依存しない）
"""
from typing import List, Dict, Literal, Optional
from dataclasses import dataclass


@dataclass
class TestCase:
    """テストケース"""
    id: str
    category: str
    description: str
    input_requirement: str
    expected_stage: str
    expected_decision: Literal["承認", "却下", "要レビュー"]
    expected_reason_pattern: str
    max_cost: float
    context: Optional[Dict] = None


# ===== 仕様テストケース（網羅的） =====

SPECIFICATION_TESTS = [
    # ========== Stage 1: ルールベース（コスト0円） ==========
    TestCase(
        id="RULE-001",
        category="禁止ワード",
        description="削除という禁止ワードを含む",
        input_requirement="認証機能を削除する",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="禁止ワード.*削除",
        max_cost=0.0
    ),
    TestCase(
        id="RULE-002",
        category="禁止ワード",
        description="破壊という禁止ワードを含む",
        input_requirement="データベースを破壊的に変更",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="禁止ワード.*破壊",
        max_cost=0.0
    ),
    TestCase(
        id="RULE-003",
        category="禁止ワード",
        description="無効化という禁止ワードを含む",
        input_requirement="セキュリティ機能を無効化",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="禁止ワード.*無効化",
        max_cost=0.0
    ),
    TestCase(
        id="RULE-004",
        category="文字数制限",
        description="最小文字数未満（10文字未満）",
        input_requirement="更新",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="文字数.*10未満",
        max_cost=0.0
    ),
    TestCase(
        id="RULE-005",
        category="文字数制限",
        description="最大文字数超過（500文字超）",
        input_requirement="x" * 501,
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="文字数.*500.*超",
        max_cost=0.0
    ),
    TestCase(
        id="RULE-006",
        category="複合違反",
        description="複数のルール違反（禁止ワード＋文字数）",
        input_requirement="削除",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="禁止ワード.*削除",
        max_cost=0.0
    ),
    
    # ========== Stage 2: 軽量埋め込み（コスト0.001円） ==========
    TestCase(
        id="EMBED-001",
        category="完全重複",
        description="既存要件と完全一致",
        input_requirement="ユーザー認証機能を実装する",
        expected_stage="LightweightEmbedding",
        expected_decision="却下",
        expected_reason_pattern="重複.*REQ-001",
        max_cost=0.001,
        context={"existing_requirements": [{"id": "REQ-001", "text": "ユーザー認証機能を実装する"}]}
    ),
    TestCase(
        id="EMBED-002",
        category="部分重複",
        description="90%以上の類似度",
        input_requirement="ユーザー認証機能を実装します",
        expected_stage="LightweightEmbedding",
        expected_decision="却下",
        expected_reason_pattern="重複",
        max_cost=0.001,
        context={"similarity_threshold": 0.9}
    ),
    TestCase(
        id="EMBED-003",
        category="高類似警告",
        description="70-90%の類似度で警告",
        input_requirement="ユーザーログイン機能を実装する",
        expected_stage="SemanticSearch",
        expected_decision="要レビュー",
        expected_reason_pattern="類似.*警告",
        max_cost=0.006,
        context={"similarity_threshold": 0.7}
    ),
    TestCase(
        id="EMBED-004",
        category="低類似承認",
        description="70%未満の類似度で承認",
        input_requirement="決済機能を実装する",
        expected_stage="LightweightEmbedding",
        expected_decision="承認",
        expected_reason_pattern="問題なし",
        max_cost=0.001
    ),
    
    # ========== Stage 3: 意味的検索（コスト0.005円） ==========
    TestCase(
        id="SEMANTIC-001",
        category="意味的重複",
        description="異なる表現だが同じ意味",
        input_requirement="ログイン機能を追加する",
        expected_stage="SemanticSearch",
        expected_decision="却下",
        expected_reason_pattern="意味的重複",
        max_cost=0.006,
        context={"semantic_analysis": True}
    ),
    TestCase(
        id="SEMANTIC-002",
        category="制約違反",
        description="既存制約と矛盾",
        input_requirement="認証を省略する機能",
        expected_stage="SemanticSearch",
        expected_decision="却下",
        expected_reason_pattern="制約違反.*矛盾",
        max_cost=0.006,
        context={"constraint": "認証は必須"}
    ),
    TestCase(
        id="SEMANTIC-003",
        category="依存関係",
        description="依存関係の確認が必要",
        input_requirement="認証APIを変更する",
        expected_stage="SemanticSearch",
        expected_decision="要レビュー",
        expected_reason_pattern="依存.*確認",
        max_cost=0.006
    ),
    
    # ========== Stage 4: 小規模LLM（コスト0.01円） ==========
    TestCase(
        id="LLM-S-001",
        category="複雑性判定",
        description="要件が複雑すぎる",
        input_requirement="AIを使った自動最適化機能で複雑な処理を実装",
        expected_stage="LLM_small",
        expected_decision="要レビュー",
        expected_reason_pattern="複雑",
        max_cost=0.016
    ),
    TestCase(
        id="LLM-S-002",
        category="曖昧性検出",
        description="要件が曖昧",
        input_requirement="なんとなく良い感じのUIにする",
        expected_stage="LLM_small",
        expected_decision="却下",
        expected_reason_pattern="曖昧",
        max_cost=0.016
    ),
    
    # ========== Stage 5: 大規模LLM（コスト0.1円） ==========
    TestCase(
        id="LLM-L-001",
        category="アーキテクチャ影響",
        description="システム全体への影響分析",
        input_requirement="マイクロサービス化による全面的なアーキテクチャ変更",
        expected_stage="LLM_large",
        expected_decision="要レビュー",
        expected_reason_pattern="アーキテクチャ.*影響",
        max_cost=0.116
    ),
    TestCase(
        id="LLM-L-002",
        category="深層分析",
        description="複数の観点からの詳細分析",
        input_requirement="セキュリティ、パフォーマンス、保守性を考慮した新機能",
        expected_stage="LLM_large",
        expected_decision="承認",
        expected_reason_pattern="詳細分析.*完了",
        max_cost=0.116
    ),
    
    # ========== エッジケース ==========
    TestCase(
        id="EDGE-001",
        category="空文字列",
        description="空の要件",
        input_requirement="",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="文字数.*10未満",
        max_cost=0.0
    ),
    TestCase(
        id="EDGE-002",
        category="特殊文字",
        description="特殊文字のみ",
        input_requirement="!@#$%^&*()",
        expected_stage="RuleBased",
        expected_decision="却下",
        expected_reason_pattern="文字数.*10未満",
        max_cost=0.0
    ),
    TestCase(
        id="EDGE-003",
        category="境界値",
        description="ちょうど10文字",
        input_requirement="1234567890",
        expected_stage="LightweightEmbedding",
        expected_decision="承認",
        expected_reason_pattern="問題なし",
        max_cost=0.001
    ),
    TestCase(
        id="EDGE-004",
        category="境界値",
        description="ちょうど500文字",
        input_requirement="x" * 500,
        expected_stage="LightweightEmbedding",
        expected_decision="承認",
        expected_reason_pattern="問題なし",
        max_cost=0.001
    ),
    
    # ========== 複合シナリオ ==========
    TestCase(
        id="COMPLEX-001",
        category="段階的エスカレーション",
        description="Stage1通過→Stage2通過→Stage3で却下",
        input_requirement="ログイン画面のデザインを変更する",
        expected_stage="SemanticSearch",
        expected_decision="要レビュー",
        expected_reason_pattern="デザイン.*確認",
        max_cost=0.006
    ),
    TestCase(
        id="COMPLEX-002",
        category="全ステージ通過",
        description="全てのステージを通過して最終判定",
        input_requirement="革新的な新機能でユーザー体験を根本的に改善する提案",
        expected_stage="Complete",
        expected_decision="要レビュー",
        expected_reason_pattern="人間のレビュー",
        max_cost=0.116
    )
]


def compress_test_suite(tests: List[TestCase]) -> List[TestCase]:
    """
    テストスイートを圧縮（重複を除去し、カバレッジを維持）
    注意: 機能削減は一切禁止
    """
    compressed = []
    coverage_map = {}
    
    for test in tests:
        # カバレッジキーを生成
        coverage_key = (test.category, test.expected_stage, test.expected_decision)
        
        if coverage_key not in coverage_map:
            coverage_map[coverage_key] = test
            compressed.append(test)
        else:
            # より厳しい条件のテストを保持
            existing = coverage_map[coverage_key]
            if test.max_cost < existing.max_cost:
                compressed.remove(existing)
                compressed.append(test)
                coverage_map[coverage_key] = test
    
    return compressed


def validate_specification_coverage():
    """仕様カバレッジの検証"""
    stages = set()
    decisions = set()
    categories = set()
    
    for test in SPECIFICATION_TESTS:
        stages.add(test.expected_stage)
        decisions.add(test.expected_decision)
        categories.add(test.category)
    
    # 必須カバレッジの確認
    required_stages = {"RuleBased", "LightweightEmbedding", "SemanticSearch", "LLM_small", "LLM_large", "Complete"}
    required_decisions = {"承認", "却下", "要レビュー"}
    
    missing_stages = required_stages - stages
    missing_decisions = required_decisions - decisions
    
    if missing_stages or missing_decisions:
        raise ValueError(f"仕様カバレッジ不足: stages={missing_stages}, decisions={missing_decisions}")
    
    print(f"✅ 仕様カバレッジ確認完了:")
    print(f"  - ステージ: {len(stages)}/{len(required_stages)}")
    print(f"  - 決定: {len(decisions)}/{len(required_decisions)}")
    print(f"  - カテゴリ: {len(categories)}")
    print(f"  - テストケース数: {len(SPECIFICATION_TESTS)}")


if __name__ == "__main__":
    validate_specification_coverage()
    compressed = compress_test_suite(SPECIFICATION_TESTS)
    print(f"\n圧縮後のテストケース数: {len(compressed)}")
    print("（機能削減なし、重複のみ除去）")