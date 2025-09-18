# ユーザージャーニーシミュレーション v2

## 前提条件
- you=0 がGraphDBで仕様照合済み
- memberはGraphDBへ直接アクセス（graph_context.json不要）

## Iteration 1: シンプルな依頼フロー

```
[me] ────「認証機能作って」────> [you]
                                   │
                                   ├─ GraphDB照合
                                   │   └─> 既存仕様 "auth_jwt_v2" 発見
                                   │
                                   └─ 即座に委譲
                                       └─> /org --spec-id auth_jwt_v2
```

---

## Iteration 2: org による環境準備（最小限）

```
[you] ─────/org --spec-id auth_jwt_v2 auth-impl src/auth────> [org system]
                                                                    │
                                                                    ▼
                                                              最小限の準備のみ
```

### org systemの動作（簡素化）

```
[org system]
    │
    ├─1. worktree作成
    │    └─> .worktrees/claude-org/auth-impl-123456/
    │
    ├─2. session.json作成（spec_idのみ記録）
    │    └─> {"spec_id": "auth_jwt_v2", "task_id": "auth-impl-123456"}
    │
    └─3. member起動
         └─> 環境変数: SPEC_ID=auth_jwt_v2, GRAPH_ENDPOINT=...
```

---

## Iteration 3: member の自律動作（GraphDB直接アクセス）

```
[Claude member]
    │
    ├─ 起動時
    │   ├─> CLAUDE.md確認
    │   └─> 環境変数からSPEC_ID取得
    │
    ├─ GraphDB直接照会
    │   ├─> 仕様取得: query_graph("MATCH (s:Spec {id: $SPEC_ID})")
    │   └─> 解決策取得: query_graph("MATCH (sol:Solution)...")
    │
    ▼
```

### GraphDBアクセスフロー

```
[Claude member] ←──DQL──→ [GraphDB]
      │                        │
      ├─ 仕様照会 ────────────→ │
      │                        │
      │ ←──── tests: [...]─────┤
      │       files: [...]     │
      │                        │
      ├─ エラー時の解決策照会 ──→ │
      │                        │
      │ ←──── solutions: [...] ┤
      │                        │
      └─ 実装開始              │
```

---

## Iteration 4: 実装フロー（自律的）

```
[Claude member 内部処理]
    │
    ├─ GraphDBから仕様取得
    │   MATCH (spec:Specification {id: "auth_jwt_v2"})
    │   RETURN spec.tests, spec.acceptance_criteria
    │
    ├─ 実装計画
    │   1. test/auth_jwt_test.rs 作成
    │   2. src/auth/jwt.rs 実装
    │   3. 統合テスト
    │
    └─ 自動実行開始
```

### 直接GraphDBアクセスの利点

```
旧: org → graph_context.json → member読み込み（静的）
新: member → GraphDB（動的・最新）

利点:
- 常に最新の情報を取得
- 実行中の学習も即座に反映
- ファイル管理不要
```

---

## Iteration 5: エラー対応（リアルタイム）

```
[Claude member]
    │
    ├─ エラー発生: "trait Clone not implemented"
    │
    ├─ GraphDB即座に照会
    │   MATCH (e:Error {type: "trait_not_implemented"})
    │   -[:SOLVED_BY]->(s:Solution)
    │   WHERE s.context = "rust" AND s.success_rate > 0.8
    │   RETURN s.action ORDER BY s.success_rate DESC
    │
    └─ 解決策適用: "#[derive(Clone)]追加"
```

### 並行実行時の利点

```
[Claude A] ──DQL──→ [GraphDB] ←──DQL── [Claude B]
    │                    │                    │
    │                    │                    │
    └─ エラー解決 ────DML→ │ ←─即座に参照可能──┘
                   (Root更新後)
```

---

## Iteration 6: 完了フロー

```
[Claude member]
    │
    ├─ 実装完了
    ├─ 全テスト通過
    │
    ├─ session.json更新
    │   └─> {"completion": 100, "status": "completed"}
    │
    └─ stream.jsonl最終エントリ
        └─> {"type": "task_completed", "spec_id": "auth_jwt_v2"}
```

### you の確認作業（最小化）

```
[you]
    │
    └─ /org --status
         │
         └─> auth-impl: completed (100%)
              │
              └─ 成果物は自動的に仕様通り
```

---

## 改善効果

### Before（graph_context.json使用）
```
準備: 重い
- 仕様抽出
- ファイル作成
- 静的な情報

実行: 制限的
- 起動時の情報のみ
- 更新は反映されない
```

### After（GraphDB直接アクセス）
```
準備: 軽い
- spec_idのみ渡す
- ファイル不要

実行: 動的
- 常に最新情報
- リアルタイム学習
```

## 結論

1. **you=0の負荷**: 仕様照合のみ（実装詳細は不要）
2. **org**: 環境準備とspec_id受け渡しのみ
3. **member**: GraphDB直接アクセスで自律的に動作
4. **学習**: 他memberの成功も即座に活用可能

この設計でyouの負荷が大幅に削減され、memberの自律性が向上します。