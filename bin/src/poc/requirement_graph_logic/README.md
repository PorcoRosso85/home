# Requirement Graph Logic (RGL) - LLM統合ガイド

## システム概要

RGLは要件管理のスコアリングエンジンです。LLM（Claude Code）に判断材料を提供します。

## LLMからの問い合わせ方法

### 1. Python APIとして直接利用

```python
from poc.requirement_graph_logic.application.commands import (
    create_add_requirement_handler,
    create_add_relation_handler
)
from poc.requirement_graph_logic.infrastructure.adapters import (
    create_in_memory_repository,
    create_simple_embedder
)

# 初期化
repo = create_in_memory_repository()
embedder = create_simple_embedder(dimension=10)
add_requirement = create_add_requirement_handler(repo, embedder)

# 要件追加の問い合わせ
result = add_requirement({
    "text": "ユーザー認証機能を実装する",
    "metadata": {"priority": "high"}
})

# 結果の解釈
if result.get("requirement_id"):
    print(f"要件が追加されました: {result['requirement_id']}")
    print(f"スコア: {result['scores']}")
    if result['scores']['uniqueness'] < 0.5:
        print("警告: 類似要件が存在します")
else:
    print("要件は重複のため追加されませんでした")
```

### 2. シーケンス図

```
User/LLM          RGL System           Repository         Embedder
   |                  |                     |                |
   |--AddRequirement->|                     |                |
   |                  |                     |                |
   |                  |--embed(text)------->|                |
   |                  |<--embedding---------|                |
   |                  |                     |                |
   |                  |--find_similar------>|                |
   |                  |<--similar_list------|                |
   |                  |                     |                |
   |                  |== スコア計算 ==     |                |
   |                  | - uniqueness        |                |
   |                  | - clarity           |                |
   |                  | - completeness      |                |
   |                  |                     |                |
   |                  |--save(if unique)--->|                |
   |                  |<--requirement_id----|                |
   |                  |                     |                |
   |<--Result---------|                     |                |
   |  {                                     |                |
   |   requirement_id,                      |                |
   |   scores: {...},                       |                |
   |   similar_requirements: [...],         |                |
   |   suggestions: [...]                   |                |
   |  }                                     |                |
```

## 返却値の解釈

### AddRequirementResult

```python
{
    "requirement_id": str,      # 空文字列 = 重複のため追加されず
    "scores": {
        "uniqueness": float,    # 1.0 = 完全に独自, 0.0 = 重複
        "clarity": float,       # 1.0 = 明確, 0.0 = 曖昧
        "completeness": float,  # 1.0 = 完全, 0.0 = 不完全
        "graph_fit": float      # 1.0 = 整合, 0.0 = 不整合
    },
    "similar_requirements": [   # 類似要件リスト
        {
            "id": str,
            "text": str,
            "similarity": float # 1.0 = 同一, 0.0 = 無関係
        }
    ],
    "suggestions": [str]        # 改善提案
}
```

### LLMによる判断例

```python
def llm_decision(result):
    """LLMがRGL結果を基に判断"""
    
    # 1. 重複チェック
    if not result["requirement_id"]:
        return "この要件は既存要件と重複しています"
    
    # 2. 品質チェック
    scores = result["scores"]
    if scores["clarity"] < 0.6:
        return f"要件を明確化してください: {result['suggestions']}"
    
    # 3. 類似要件の確認
    if scores["uniqueness"] < 0.5:
        similar = result["similar_requirements"][0]
        return f"類似要件「{similar['text']}」との関係を定義してください"
    
    # 4. 承認
    return f"要件を追加しました（ID: {result['requirement_id']}）"
```

## エラーハンドリング

```python
result = add_requirement(command)

if "error" in result:
    # エラー時の構造
    # {
    #     "error": str,        # エラーメッセージ
    #     "code": str,         # エラーコード
    #     "details": dict|None # 詳細情報
    # }
    print(f"エラー: {result['error']} (コード: {result['code']})")
```

## 注意事項

1. **RGLは判断しない**: スコアと事実のみを返す
2. **LLMが最終判断**: 閾値や条件はLLM側で設定
3. **エラーは値として返る**: 例外は投げない

## 実装の健全性チェック

```bash
# テスト実行
python test_rgl.py

# CLI デモ
python -m poc.requirement_graph_logic.cli
```