# テンプレートクエリ設計方針

## バッチ設計原則

**すべてのクエリはバッチ設計とする。1件の処理であっても必ずバッチ形式で実装する。**

### 設計理由

1. **一貫性**: すべてのクエリが同じインターフェースを持つ
2. **拡張性**: 将来的な複数件処理への対応が容易
3. **性能**: バッチ処理による最適化の余地を残す
4. **トランザクション**: 複数操作の原子性を保証しやすい

### 実装規則

#### ❌ 非推奨: 単一処理
```cypher
// 単一の要件を作成
CREATE (r:RequirementEntity {
    id: $id,
    title: $title
})
RETURN r
```

#### ✅ 推奨: バッチ処理
```cypher
// バッチ形式（1件でも配列で渡す）
WITH $requirements AS batch
UNWIND batch AS req
CREATE (r:RequirementEntity {
    id: req.id,
    title: req.title
})
RETURN collect(r) AS created_requirements
```

### パラメータ形式

すべてのテンプレートは配列形式のパラメータを受け取る：

```json
{
  "template": "create_requirements",
  "parameters": {
    "requirements": [
      {
        "id": "req_001",
        "title": "ログイン機能",
        "uri_path": "projectA/auth"
      }
    ]
  }
}
```

1件の処理でも必ず配列に含める：

```json
{
  "template": "update_requirement_stage",
  "parameters": {
    "transitions": [
      {
        "requirement_id": "req_001",
        "from_stage": "pending",
        "to_stage": "active"
      }
    ]
  }
}
```

### 戻り値形式

バッチ処理の結果も配列形式で返す：

```json
{
  "status": "success",
  "data": {
    "processed": 1,
    "results": [
      {
        "id": "req_001",
        "status": "created",
        "uri": "req://projectA/auth/req_001"
      }
    ]
  }
}
```

### エラーハンドリング

部分的な失敗を許容する場合：

```json
{
  "status": "partial_success",
  "data": {
    "processed": 3,
    "succeeded": 2,
    "failed": 1,
    "results": [
      {"id": "req_001", "status": "created"},
      {"id": "req_002", "status": "created"},
      {"id": "req_003", "status": "error", "reason": "duplicate_id"}
    ]
  }
}
```

### 命名規則

- 複数形を使用: `create_requirements` (create_requirementではない)
- バッチ操作を明示: `batch_update_stages`
- 配列パラメータも複数形: `requirements`, `transitions`, `hierarchies`

### 実装例

#### 要件作成（バッチ）
```cypher
// create_requirements.cypher
WITH $requirements AS batch
UNWIND batch AS req
MERGE (l:LocationURI {id: 'req://' + req.uri_path + '/' + req.id})
CREATE (r:RequirementEntity {
    id: req.id,
    title: req.title,
    description: req.description
})
CREATE (l)-[:LOCATES]->(r)
RETURN collect({
    id: r.id,
    uri: l.id,
    status: 'created'
}) AS results
```

#### ステージ遷移（バッチ）
```cypher
// transition_stages.cypher
WITH $transitions AS batch
UNWIND batch AS trans
MATCH (r:RequirementEntity {id: trans.requirement_id})
WHERE r.stage = trans.from_stage
SET r.stage = trans.to_stage,
    r.stage_updated_at = datetime()
RETURN collect({
    id: r.id,
    old_stage: trans.from_stage,
    new_stage: r.stage,
    status: 'updated'
}) AS results
```

### トランザクション考慮事項

- すべてのバッチ操作は単一トランザクション内で実行
- 全成功または全失敗の原則（部分成功を許可する場合は明示的に設計）
- 大量バッチの場合はチャンク分割を検討

この設計により、システム全体の一貫性と拡張性を確保します。

## ユーザーの思考 → クエリユースケース

### 「ログイン機能が必要だ」
→ `check_duplicates_local` で類似要件を確認
→ `create_requirements` で新規作成

### 「これ、似た要件あったかも」
→ `check_duplicates_local` でスコープ内を高速検索
→ `find_requirements_by_uri` で詳細確認

### 「この機能は認証が前提だ」
→ `add_dependencies` で依存関係を定義

### 「ログイン機能に2FA追加したい」（将来実装）
→ `create_requirement_versions` で新バージョン作成

## 実装状況

- ✅ バッチ設計（全クエリ共通）
- 🚧 LocationURI階層管理
- 📋 スコープベース重複検出
- ❌ 要件バージョニング