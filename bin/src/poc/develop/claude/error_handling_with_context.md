# エラー対応時の問い合わせ背景出力設計

## 基本原則
memberがGraphDBへ問い合わせる際は、必ず以下を出力してstream.jsonlに記録する：
1. なぜこの問い合わせが必要か（背景）
2. 実行したCypherクエリ
3. 取得した結果
4. 適用した解決策

## 実装例

### エラー発生時のフロー

```
[Claude member]
    │
    ├─ エラー検出: "error: trait `Clone` is not implemented"
    │
    ├─ 背景出力（必須）
    │   "エラー背景: Rust compilerがCloneトレイト未実装を検出
    │    ファイル: src/auth/user.rs:42
    │    構造体: UserCredentials
    │    このエラーを解決するためGraphDBに問い合わせます"
    │
    ├─ Cypherクエリ出力（必須）
    │   "実行クエリ:
    │    MATCH (e:Error {type: 'trait_not_implemented', trait: 'Clone'})
    │    -[:SOLVED_BY]->(s:Solution)
    │    WHERE s.language = 'rust' AND s.success_rate > 0.7
    │    RETURN s.action, s.code_snippet, s.success_rate
    │    ORDER BY s.success_rate DESC LIMIT 3"
    │
    ├─ 結果出力（必須）
    │   "クエリ結果:
    │    1. #[derive(Clone)]を追加 (成功率: 0.95)
    │    2. 手動でClone実装 (成功率: 0.82)
    │    3. 構造体の設計見直し (成功率: 0.71)"
    │
    └─ 適用記録（必須）
        "解決策適用: #[derive(Clone)]をUserCredentials構造体に追加"
```

## stream.jsonl への記録形式

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "type": "error_handling",
  "phase": "query_context",
  "content": {
    "error": {
      "type": "trait_not_implemented",
      "trait": "Clone",
      "file": "src/auth/user.rs",
      "line": 42,
      "struct": "UserCredentials"
    },
    "background": "Rust compilerがCloneトレイト未実装を検出。このエラーを解決するためGraphDBに問い合わせます",
    "query": {
      "cypher": "MATCH (e:Error {type: 'trait_not_implemented', trait: 'Clone'})...",
      "executed_at": "2024-01-15T10:30:46Z"
    },
    "results": [
      {
        "action": "#[derive(Clone)]を追加",
        "success_rate": 0.95,
        "selected": true
      }
    ],
    "resolution": {
      "action_taken": "#[derive(Clone)]をUserCredentials構造体に追加",
      "applied_at": "2024-01-15T10:30:47Z"
    }
  }
}
```

## memberの実装パターン

```bash
# member/main.sh.template に追加すべき関数

# エラー対応時の問い合わせ（背景付き）
query_error_solution_with_context() {
    local error_type="$1"
    local error_details="$2"
    local context="$3"
    
    # 1. 背景を出力
    echo "=== エラー対応開始 ==="
    echo "エラー: $error_type"
    echo "詳細: $error_details"
    echo "コンテキスト: $context"
    echo "GraphDBに解決策を問い合わせます..."
    
    # 2. Cypherクエリを構築・出力
    local cypher_query="
    MATCH (e:Error {type: '$error_type'})
    -[:SOLVED_BY]->(s:Solution)
    WHERE s.context =~ '.*$context.*' AND s.success_rate > 0.7
    RETURN s.action, s.code_snippet, s.success_rate
    ORDER BY s.success_rate DESC LIMIT 3"
    
    echo "実行クエリ:"
    echo "$cypher_query"
    
    # 3. stream.jsonlに記録
    log_to_stream "error_query_context" \
        "GraphDB問い合わせ: $error_type" \
        "{\"query\": \"$(echo "$cypher_query" | jq -Rs .)\", \"context\": \"$context\"}"
    
    # 4. クエリ実行
    local results=$(query_graph "$cypher_query")
    
    # 5. 結果を出力・記録
    echo "クエリ結果:"
    echo "$results" | jq -r '.[] | "- \(.action) (成功率: \(.success_rate))"'
    
    # 6. 最適解を選択・適用
    local best_solution=$(echo "$results" | jq -r '.[0]')
    echo "適用する解決策: $(echo "$best_solution" | jq -r '.action')"
    
    # 7. 適用結果も記録
    log_to_stream "solution_applied" \
        "解決策適用: $(echo "$best_solution" | jq -r '.action')" \
        "$best_solution"
    
    echo "$best_solution"
}
```

## 効果

1. **完全なトレーサビリティ**: エラーから解決までの全過程が記録される
2. **学習材料の充実**: 背景情報により、より精度の高いパターン学習が可能
3. **デバッグの容易化**: 問題発生時に、なぜその解決策を選んだかが明確
4. **知識の蓄積**: stream.jsonlが価値あるナレッジベースになる

## 次のステップ

1. CLAUDE.mdにこのルールを追加
2. org/main.sh.templateからgraph_context.json作成を削除
3. member/main.sh.templateに上記テンプレートを追加