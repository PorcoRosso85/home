"""CLI for Requirement Graph Logic"""

import json
from typing import Dict, Any
from .domain.types import AddRequirementResultDict, ErrorDict
from .application.commands import (
    create_add_requirement_handler, 
    create_add_relation_handler,
    AddRequirementCommand,
    AddRelationCommand
)
from .infrastructure.adapters import (
    create_in_memory_repository,
    create_simple_embedder
)


def print_result(result: Dict[str, Any]):
    """結果を見やすく表示"""
    if "error" in result:
        print(f"エラー: {result['error']}")
        return
    
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def main():
    """CLI main function"""
    # インフラの初期化
    repo = create_in_memory_repository()
    embedder = create_simple_embedder(dimension=10)  # より高次元に
    
    # ハンドラーの作成
    add_req_handler = create_add_requirement_handler(repo, embedder)
    add_rel_handler = create_add_relation_handler(repo)
    
    print("=== Requirement Graph Logic CLI ===")
    print("RGLはスコアとファクトのみを返します。判断はLLM（Claude Code）が行います。\n")
    
    # 要件を追加
    commands = [
        {"text": "ユーザー認証機能を実装する", "metadata": {"priority": "high"}},
        {"text": "ユーザー認証を実装", "metadata": {"priority": "medium"}},  # 類似
        {"text": "商品検索機能を実装する", "metadata": {"priority": "high"}},
        {"text": "在庫管理システムを構築する", "metadata": {"priority": "medium"}},
        {"text": "認証", "metadata": {"priority": "low"}},  # 曖昧
    ]
    
    requirement_ids = []
    
    for i, cmd in enumerate(commands):
        print(f"\n--- 要件追加 {i+1}: {cmd['text']} ---")
        result = add_req_handler(cmd)
        print_result(result)
        
        if "requirement_id" in result and result["requirement_id"]:
            requirement_ids.append(result["requirement_id"])
    
    # 関係を追加
    if len(requirement_ids) >= 2:
        print("\n\n--- 関係追加: 要件1 → 要件3 (depends_on) ---")
        rel_cmd: AddRelationCommand = {
            "from_id": requirement_ids[0],
            "to_id": requirement_ids[2],
            "relation_type": "depends_on",
            "confidence": 0.8,
            "reasoning": "商品検索には認証が必要"
        }
        result = add_rel_handler(rel_cmd)
        print_result(result)
    
    print("\n\n=== 実行完了 ===")
    print("RGLは以下の情報を提供しました：")
    print("- 各要件の独自性・明確性・完全性スコア")
    print("- 類似要件の検出と類似度")
    print("- 改善提案（曖昧な表現への警告等）")
    print("- 関係追加時のグラフへの影響分析")
    print("\nこれらの情報を基に、LLM（Claude Code）が最終的な判断を行います。")


if __name__ == "__main__":
    main()