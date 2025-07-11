# エラー対応時の問い合わせ背景出力フロー

## 現在の問題点

```
[Claude member]
    │
    ├─ エラー発生
    │   └─> 解決策をGraphDBから取得
    │       └─> 適用
    │
    └─ stream.jsonlには結果のみ記録
        └─> 「なぜその解決策を選んだか」が不明
```

## 改善後のフロー

```
[Claude member]
    │
    ├─ エラー発生: "trait Clone not implemented"
    │
    ├─ 背景出力 ──────────────────┐
    │   │                         │
    │   └─> "なぜ問い合わせるか"   │
    │                             ▼
    ├─ Cypherクエリ構築 ────────> stream.jsonl
    │   │                         ▲
    │   └─> "何を問い合わせるか"   │
    │                             │
    ├─ GraphDB実行 ───────────────┤
    │   │                         │
    │   └─> "結果は何だったか"    │
    │                             │
    └─ 解決策適用 ───────────────┘
        │
        └─> "何を適用したか"
```

## stream.jsonlの記録例

```
時刻: 10:30:45
├─ "エラー検出: trait Clone not implemented on UserCredentials"
├─ "背景: 構造体をcloneする必要があるが未実装"
├─ "GraphDBクエリ: MATCH (e:Error {type: 'trait_not_implemented'})..."
├─ "結果: 3件の解決策（#[derive(Clone)] 95%成功率）"
└─ "適用: #[derive(Clone)]を追加"

時刻: 10:31:02
├─ "テスト実行: cargo test auth_module"
└─ "結果: 全テスト通過"
```

## GraphDBアクセスパターン

### Pattern 1: エラー解決

```
[Claude member]
    │
    ├─ 思考プロセス出力
    │   "コンパイルエラーが発生しました。
    │    エラー内容から、Cloneトレイトの実装が
    │    必要と判断します。過去の類似事例を
    │    GraphDBから検索します。"
    │
    ├─ クエリ実行
    │   MATCH (e:Error)-[:SOLVED_BY]->(s:Solution)
    │   WHERE e.type = 'trait_not_implemented'
    │   AND e.trait = 'Clone'
    │   RETURN s ORDER BY s.success_rate DESC
    │
    └─ 結果適用と記録
        "最も成功率の高い解決策を適用します"
```

### Pattern 2: 仕様確認

```
[Claude member]
    │
    ├─ 思考プロセス出力
    │   "JWT認証の実装を開始します。
    │    spec_id: auth_jwt_v2 の詳細仕様を
    │    GraphDBから取得します。"
    │
    ├─ クエリ実行
    │   MATCH (spec:Specification {id: 'auth_jwt_v2'})
    │   RETURN spec.tests, spec.acceptance_criteria
    │
    └─ 実装計画出力
        "仕様に基づき、以下の順序で実装します：
         1. JWT validation test
         2. Token refresh test
         3. 実装本体"
```

## 効果的な背景出力の例

### 良い例 ✅

```
"背景: Cargo.tomlにjsonwebtokenクレートが未登録のため、
       import文でエラーが発生。このプロジェクトでの
       JWT実装に必要な依存関係をGraphDBから確認します。"
       
理由: 具体的な状況と問い合わせ目的が明確
```

### 悪い例 ❌

```
"エラーが出たのでGraphDBに聞きます"

理由: 背景情報が不足、後で見返しても理解困難
```

## 実装における注意点

```
[必須出力項目]
    │
    ├─ 1. 状況説明（何が起きているか）
    ├─ 2. 判断根拠（なぜGraphDBが必要か）
    ├─ 3. 期待結果（何を得たいか）
    ├─ 4. クエリ内容（どう問い合わせるか）
    └─ 5. 適用結果（どうなったか）
```

この設計により、stream.jsonlが「実行ログ」から「学習可能な知識ベース」に進化します。