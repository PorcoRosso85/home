# RuleExecutor セキュリティアップデート

## 概要
`meta_node.py`のRuleExecutorクラスからeval関数を完全に削除し、Cypherクエリベースの実行に移行しました。

## 変更内容

### 1. eval関数の削除
- `execute_rules`メソッドから`eval(rule.condition, ...)`と`eval(rule.action, ...)`を削除
- `_raise_exception`ヘルパーメソッドを削除
- Python式の評価による任意コード実行リスクを排除

### 2. Cypherクエリベースの実装
- ルールはすべて`cypher_query`フィールドを使用
- クエリ結果の最初のカラムでpass/fail判定
- 2番目のカラムでログメッセージ（オプション）

### 3. エラーハンドリングの改善
- Cypherクエリの構文エラーを適切にキャッチ
- エラー情報を`failed_rules`に記録
- validationタイプのルールが失敗した場合は後続ルールをスキップ

## セキュリティ向上のポイント

1. **任意コード実行の防止**: eval関数を使用しないため、悪意のあるPythonコードを実行するリスクがない
2. **宣言的なルール定義**: CypherクエリはKuzuDBのクエリエンジン内で安全に実行される
3. **パラメータインジェクション対策**: KuzuDBのパラメータバインディングによりSQLインジェクション風の攻撃を防ぐ

## 移行ガイド

### 旧形式（eval使用）
```python
meta_node.create_guardrail_rule(
    rule_type="validation",
    name="email_check",
    description="メールアドレスチェック",
    condition="'@' in data.get('email', '')",
    action="raise_error(ValueError('Invalid email')) if '@' not in data.get('email', '') else 'pass'",
    priority=1,
    active=True
)
```

### 新形式（Cypherクエリ）
```python
meta_node.create_guardrail_rule(
    rule_type="validation",
    name="email_check",
    description="メールアドレスチェック",
    cypher_query="""
        WITH $email AS email
        RETURN 
            CASE WHEN email CONTAINS '@' THEN true ELSE false END AS is_valid,
            CASE WHEN email CONTAINS '@' THEN 'Valid email' ELSE 'Invalid email' END AS message
    """,
    priority=1,
    active=True
)
```

## テスト結果
- 新しいCypherベースのテストはすべてパス
- 旧形式のcondition/actionフィールドを使用するルールは無視される
- セキュリティが大幅に向上し、システムの安全性が確保された