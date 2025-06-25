# RGL - LLM統合方法

## 統合シーケンス

```
┌─────────┐     ┌──────────────┐     ┌─────────────┐
│  User   │     │ LLM (Claude) │     │     RGL     │
└────┬────┘     └──────┬───────┘     └──────┬──────┘
     │                 │                      │
     │ 要件を追加したい │                      │
     │ "認証機能"      │                      │
     ├────────────────>│                      │
     │                 │                      │
     │                 │ add_requirement({    │
     │                 │   text: "認証機能",  │
     │                 │   metadata: {...}    │
     │                 │ })                   │
     │                 ├─────────────────────>│
     │                 │                      │
     │                 │                      ├─> 埋め込み生成
     │                 │                      ├─> 類似検索
     │                 │                      ├─> スコア計算
     │                 │                      │
     │                 │ {                    │
     │                 │   requirement_id: "",│
     │                 │   scores: {          │
     │                 │     uniqueness: 0.2, │
     │                 │     clarity: 0.3,    │
     │                 │     completeness: 0.1│
     │                 │   },                 │
     │                 │   suggestions: [...] │
     │                 │ }                    │
     │                 │<─────────────────────┤
     │                 │                      │
     │                 ├─> スコア解釈        │
     │                 ├─> 判断ロジック実行   │
     │                 │                      │
     │ "認証機能は曖昧 │                      │
     │  です。具体的に │                      │
     │  記述して下さい"│                      │
     │<────────────────┤                      │
     │                 │                      │
```

## LLMでの実装例

```python
class RequirementManager:
    """LLM内でRGLを使用するマネージャー"""
    
    def __init__(self):
        # RGLシステムの初期化
        self.repo = create_in_memory_repository()
        self.embedder = create_simple_embedder(dimension=10)
        self.add_handler = create_add_requirement_handler(
            self.repo, self.embedder
        )
        
        # 判断閾値（LLM側で設定）
        self.thresholds = {
            "uniqueness_warning": 0.5,
            "uniqueness_reject": 0.1,
            "clarity_minimum": 0.6,
            "completeness_minimum": 0.7
        }
    
    def process_requirement(self, user_text: str) -> str:
        """ユーザーの要件を処理"""
        
        # 1. RGLに問い合わせ
        result = self.add_handler({
            "text": user_text,
            "metadata": {"source": "user_input"}
        })
        
        # 2. エラーチェック
        if "error" in result:
            return f"エラーが発生しました: {result['error']}"
        
        # 3. スコアに基づく判断
        scores = result["scores"]
        messages = []
        
        # 重複チェック
        if scores["uniqueness"] < self.thresholds["uniqueness_reject"]:
            similar = result["similar_requirements"][0]
            return f"この要件は既存要件「{similar['text']}」と重複しています。"
        
        # 品質チェック
        issues = []
        
        if scores["uniqueness"] < self.thresholds["uniqueness_warning"]:
            similar = result["similar_requirements"][0]
            issues.append(
                f"類似要件「{similar['text']}」が存在します（類似度: {similar['similarity']:.0%}）"
            )
        
        if scores["clarity"] < self.thresholds["clarity_minimum"]:
            issues.append("要件の記述が曖昧です")
        
        if scores["completeness"] < self.thresholds["completeness_minimum"]:
            issues.append("必要な要素が不足しています")
        
        # 4. 結果のフォーマット
        if issues:
            messages.append("要件に以下の問題があります：")
            messages.extend(f"- {issue}" for issue in issues)
            messages.append("\n改善案：")
            messages.extend(f"- {sug}" for sug in result["suggestions"])
            return "\n".join(messages)
        else:
            return f"要件を追加しました（ID: {result['requirement_id']}）"
```

## 実際の使用例

```python
# LLM内での使用
manager = RequirementManager()

# ケース1: 良好な要件
response = manager.process_requirement(
    "ユーザーがログイン画面で認証情報を入力した場合、システムは認証処理を実行する"
)
print(response)  # "要件を追加しました（ID: REQ-xxx）"

# ケース2: 曖昧な要件
response = manager.process_requirement("認証機能")
print(response)  
# "要件に以下の問題があります：
#  - 要件の記述が曖昧です
#  - 必要な要素が不足しています
#  
#  改善案：
#  - 要件をより具体的に記述してください（5-20単語が推奨）
#  - 「誰が」「何を」「どのような条件で」を明記してください"
```

## RGLの責務とLLMの責務

### RGLが提供するもの（ファクト）
- 埋め込みベクトルの生成
- 類似度計算
- スコア算出（独自性、明確性、完全性）
- 類似要件の検出
- 改善提案の生成

### LLMが行うこと（判断）
- スコアの閾値設定
- 承認/却下の判断
- ユーザーへのメッセージ生成
- 複数要件間の関係性推論
- コンテキストに応じた判断調整

## まとめ

LLMはRGLを「要件品質の計測器」として使用します。RGLは客観的な数値とファクトのみを返し、LLMがそれらを解釈してユーザーに適切なフィードバックを提供します。