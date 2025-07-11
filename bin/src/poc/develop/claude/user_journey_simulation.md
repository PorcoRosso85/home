# ユーザージャーニーシミュレーション

## Iteration 1: 基本的な依頼フロー

```
[me] ────依頼────> [you]
                    │
                    ├─ 「認証機能を実装して」
                    │
                    ▼
                  何をする？
```

### youの行動

1. **要件の明確化**
   ```
   [you]: 「認証機能について詳しく教えてください」
   - JWT使う？
   - どのフレームワーク？
   - テストは必要？
   ```

2. **仕様策定**
   ```
   [you] ───> GraphDB
              │
              └─ CREATE (spec:Specification {
                   feature: "user_auth",
                   tests: ["JWT validation", "token refresh"],
                   acceptance: "全テスト通過"
                 })
   ```

3. **実行計画**
   ```
   [you]: 「/org コマンドで実装を委譲します」
   ```

---

## Iteration 2: /org 実行

```
[you] ─────/org auth-impl src/auth "JWT認証実装"────> [org system]
                                                          │
                                                          ▼
                                                    何が起きる？
```

### org systemの動作

```
[org system]
    │
    ├─1. worktree作成
    │    └─> .worktrees/claude-org/auth-impl-123456/
    │
    ├─2. GraphDB照会
    │    └─> spec_id: user_auth の仕様を取得
    │
    ├─3. member起動準備
    │    ├─> session.json作成
    │    └─> graph_context.json作成
    │
    └─4. Claude member起動
         └─> member/sdk/claude.ts 実行
```

---

## Iteration 3: member の自律動作

```
[Claude member]
    │
    ├─ 初期化
    │   ├─> CLAUDE.md読み込み
    │   ├─> .claude/* 設定確認
    │   └─> graph_context.json確認
    │
    ├─ 実装開始
    │   ├─> 「仕様: JWT validation, token refresh」
    │   └─> 「過去の解決策: 3件見つかりました」
    │
    ▼
  どう実装する？
```

### memberの判断

```
[Claude member 思考]
    │
    ├─ GraphDBの仕様確認 ✓
    ├─ TDD実践が必要 ✓
    └─ 過去の成功パターンあり ✓
    
    ▼
    
実装順序決定:
1. テストファイル作成
2. 実装
3. 統合テスト
```

---

## Iteration 4: エラー発生シナリオ

```
[Claude member]
    │
    ├─ cargo test 実行
    │   └─> ERROR: import 'jsonwebtoken' not found
    │
    ▼
  どう対処する？
```

### エラーハンドリングフロー

```
[Claude member]
    │
    ├─1. 自力解決試行
    │    └─> member/main.sh.template の query_solution_for_error 使用
    │
    ├─2. GraphDBから解決策取得
    │    └─> "add jsonwebtoken to Cargo.toml" (成功率: 0.92)
    │
    ├─3. 解決策適用
    │    └─> Cargo.toml更新
    │
    └─4. stream.jsonlに記録
         └─> {"type": "error_resolved", "solution": "dependency_added"}
```

---

## Iteration 5: 完了と報告

```
[Claude member]
    │
    ├─ 全テスト通過 ✓
    ├─ 実装完了 ✓
    │
    ├─ session.json更新
    │   └─> {"completion": 100, "tests_passed": true}
    │
    └─ 最終報告
        └─> "Task completed: [auth-impl]"
```

### youへの通知

```
[org system] ───状態確認───> [you]
                              │
                              ├─ /org --status
                              │
                              ▼
                         auth-impl: completed (100%) [Tests: true]
```

---

## Iteration 6: 結果の統合

```
[you]
    │
    ├─ 成果物確認
    │   ├─> src/auth/mod.rs ✓
    │   ├─> src/auth/jwt.rs ✓
    │   └─> tests/auth_test.rs ✓
    │
    ├─ ログ分析
    │   └─> stream.jsonl から学習ポイント抽出
    │
    └─ GraphDB更新
        └─> 新しい成功パターンを記録
```

## 問題点の発見

1. **youの負荷がまだ高い**
   - 仕様策定
   - GraphDB更新
   - 結果確認

2. **自動化の余地**
   - テスト仕様からの自動実装
   - 成功パターンの自動学習

次のイテレーションで改善案を検討しますか？