#!/usr/bin/env python3
"""仕様テストの実行"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from specification_tests import SPECIFICATION_TESTS, TestCase
from processor import StagedRequirementProcessor
from typing import List, Tuple


def run_specification_test(processor: StagedRequirementProcessor, test: TestCase) -> Tuple[bool, str]:
    """単一の仕様テストを実行"""
    # コンテキストを設定
    if test.context:
        # 既存要件をプロセッサーに反映（実装の簡易版）
        if "existing_requirements" in test.context:
            for stage in processor.stages:
                if hasattr(stage, "existing_requirements"):
                    stage.existing_requirements = test.context["existing_requirements"]
    
    # テスト実行
    result = processor.process(test.input_requirement)
    
    # 検証
    passed = True
    errors = []
    
    # 決定の検証
    if result["decision"] != test.expected_decision:
        passed = False
        errors.append(f"決定が不一致: 期待={test.expected_decision}, 実際={result['decision']}")
    
    # ステージの検証
    if result["stage"] != test.expected_stage:
        passed = False
        errors.append(f"ステージが不一致: 期待={test.expected_stage}, 実際={result['stage']}")
    
    # 理由パターンの検証
    import re
    if not re.search(test.expected_reason_pattern, result["reason"], re.IGNORECASE):
        passed = False
        errors.append(f"理由が不一致: パターン={test.expected_reason_pattern}, 実際={result['reason']}")
    
    # コストの検証
    if result["cost"] > test.max_cost:
        passed = False
        errors.append(f"コスト超過: 最大={test.max_cost}, 実際={result['cost']}")
    
    return passed, "\n".join(errors) if errors else "OK"


def main():
    """仕様テストのメイン実行"""
    print("=== 仕様テスト実行 ===\n")
    
    processor = StagedRequirementProcessor()
    
    passed_count = 0
    failed_count = 0
    failed_tests = []
    
    for test in SPECIFICATION_TESTS:
        print(f"[{test.id}] {test.description} ... ", end="", flush=True)
        
        passed, message = run_specification_test(processor, test)
        
        if passed:
            print("✅ PASS")
            passed_count += 1
        else:
            print(f"❌ FAIL\n  {message}")
            failed_count += 1
            failed_tests.append((test, message))
    
    # サマリー
    print(f"\n{'='*60}")
    print(f"テスト結果サマリー:")
    print(f"  合格: {passed_count}/{len(SPECIFICATION_TESTS)}")
    print(f"  失敗: {failed_count}/{len(SPECIFICATION_TESTS)}")
    
    if failed_tests:
        print(f"\n失敗したテスト:")
        for test, message in failed_tests:
            print(f"  - {test.id}: {test.description}")
            print(f"    {message}")
    
    # 終了コード
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()