#!/usr/bin/env python3
"""段階的要件処理のデモ"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from processor import StagedRequirementProcessor


def main():
    """デモのメイン関数"""
    print("=== 段階的要件処理POC ===")
    print("低コストから高コストへ段階的にエスカレーション\n")
    
    # テストケース
    test_cases = [
        # ルールベースで即却下
        "削除",
        
        # 埋め込みで重複検出
        "ユーザー認証機能を実装する",
        
        # 意味的分析が必要
        "ログイン画面を青色にする",
        
        # LLM判定が必要
        "新機能として複雑な推薦システムを追加する",
        
        # 正常なケース
        "ユーザープロフィール編集機能を追加する"
    ]
    
    # 引数があればそれを使用
    if len(sys.argv) > 1:
        test_cases = [" ".join(sys.argv[1:])]
    
    processor = StagedRequirementProcessor()
    
    # 各テストケースを処理
    for i, requirement in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"テストケース {i}")
        
        result = processor.process(requirement)
        
        print(f"\n📊 最終結果:")
        print(f"  決定: {result['decision']}")
        print(f"  理由: {result['reason']}")
        print(f"  総コスト: {result['cost']:.3f}円")
        print(f"  最終ステージ: {result['stage']}")
        
        # 類似要件があれば表示
        if "similar_requirements" in result["details"]:
            print(f"\n  類似要件:")
            for req in result["details"]["similar_requirements"]:
                print(f"    - {req['id']}: {req['text']} (類似度: {req['similarity']:.2f})")
                if req.get("relationship"):
                    print(f"      関係: {req['relationship']}")
    
    # コストサマリー表示
    print(f"\n{'='*60}")
    print("💰 コストサマリー:")
    summary = processor.get_cost_summary()
    for stage_name, stats in summary.items():
        print(f"  {stage_name}:")
        print(f"    実行回数: {stats['count']}")
        print(f"    合計コスト: {stats['total']:.3f}円")
        print(f"    平均コスト: {stats['average']:.3f}円")


if __name__ == "__main__":
    main()