# RequirementEntity命名規則

## 重要な注意事項

KuzuDBのテーブル名は `RequirementEntity` です。`Requirement` ではありません。

### 正しい使用例:
```cypher
CREATE (r:RequirementEntity {id: "req_001", title: "タイトル"})
MATCH (r:RequirementEntity) WHERE r.id = "req_001" RETURN r
```

### 間違った使用例:
```cypher
CREATE (r:Requirement {id: "req_001", title: "タイトル"})  -- ❌ エラー
MATCH (r:Requirement) WHERE r.id = "req_001" RETURN r      -- ❌ エラー
```

## 要件IDの命名

要件IDに特別な命名規則はありません。以下のような命名も全て有効です：
- `req_001`, `req_002`, `req_003` （連番）
- `auth_login`, `auth_logout` （機能別）
- `2024_01_feature_x` （日付入り）

**重要**: `req_vision_xxx`、`req_task_xxx` のような階層を示唆する命名は、システムによる特別な扱いを受けません。

## 背景

スキーマ定義（`ddl/schema.cypher`）では、要件を表すノードテーブルは `RequirementEntity` として定義されています。これは、KuzuDBの予約語との衝突を避けるため、または将来の拡張性を考慮した設計です。

## 移行時の注意

既存のドキュメントやテストコードで `Requirement` を使用している場合は、`RequirementEntity` に修正する必要があります。