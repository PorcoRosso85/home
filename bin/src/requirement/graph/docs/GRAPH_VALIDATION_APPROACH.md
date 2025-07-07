# グラフ検証アプローチ（階層に依存しない）

## 現状の問題

現在のコードベースには以下のような階層を前提とした実装があります：
- `domain/hierarchy_rules.py` - 固定レベル0-4を前提
- `infrastructure/hierarchy_validator.py` - hierarchy_levelプロパティを使用
- 各種テスト - ビジョン/タスクなどの固定概念

## 新しいアプローチ

### 1. グラフ深さ制限（必要な場合のみ）
```cypher
-- 任意の2つの要件間の最短パスをチェック
MATCH path = shortestPath((a:RequirementEntity)-[:DEPENDS_ON*]-(b:RequirementEntity))
WHERE a.id = $fromId AND b.id = $toId
RETURN length(path) as depth
```

### 2. 循環参照検出（これは必須）
```cypher
-- 循環参照の検出
MATCH path = (r:RequirementEntity)-[:DEPENDS_ON*]->(r)
RETURN r.id as circular_requirement
```

### 3. 制約はプロジェクトごとに設定
```python
# プロジェクト設定（例）
PROJECT_CONSTRAINTS = {
    "max_graph_depth": 10,  # None = 無制限
    "allow_circular": False,
    "custom_rules": []
}
```

## 移行計画

1. **Phase 1**: 新しいグラフベースの検証を実装
2. **Phase 2**: 既存の階層ベース検証と並行実行
3. **Phase 3**: 階層ベース検証を非推奨に
4. **Phase 4**: 階層関連コードを削除

## 重要な注意

- スキーマに`hierarchy_level`を追加しない
- 要件IDに階層的な命名を強制しない
- ドキュメントで「ビジョン」「タスク」を使う場合は単なる例として明記