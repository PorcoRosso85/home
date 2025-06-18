# KuzuDBによる論理的整合性の検証と実装例

## 4. 論理的整合性の検証

KuzuDBを使用した論理的整合性の検証は、ソフトウェア開発における計画の完全性と実装の正確性を保証するための重要なプロセスです。

### 4.1 事前検証：計画段階での論理的完全性チェック

計画段階での検証は、実装前に潜在的な問題を発見することを目的としています。

#### 依存関係の欠落検出
```cypher
-- 特定バージョンに含まれる要件の依存関係が計画に含まれているかチェック
MATCH (v:VersionState {id: $version_id})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH_REQUIREMENT]->(req)
MATCH (req)-[:DEPENDS_ON]->(dep_req)
WHERE NOT EXISTS {
  MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri2)-[:LOCATED_WITH_REQUIREMENT]->(dep_req)
}
RETURN dep_req.id AS missing_dependency, dep_req.title AS dependency_title, req.id AS required_by
```

#### 型の不整合検出
```cypher
-- インターフェースと実装の型整合性チェック
MATCH (interface:Requirement {type: "interface"})
MATCH (impl:Requirement)-[:IMPLEMENTS]->(interface)
WHERE interface.expected_type <> impl.provided_type
RETURN interface.id, impl.id, interface.expected_type, impl.provided_type
```

#### 循環依存の検出
```cypher
-- 要件間の循環依存を検出
MATCH path = (req1:Requirement)-[:DEPENDS_ON*]->(req1)
RETURN req1.id AS circular_dependency, [node IN nodes(path) | node.id] AS dependency_cycle
```

### 4.2 事後検証：実装の計画準拠チェック

実装後の検証は、実際のコードが計画通りに作成されたかを確認します。

#### 実装状態の確認
```cypher
-- 計画されたすべての要件が実装されているかチェック
MATCH (v:VersionState {id: $version_id})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH_REQUIREMENT]->(req)
WHERE req.status <> "completed"
RETURN req.id AS unimplemented_requirement, req.title, req.status
```

#### ファイル構造の検証
```cypher
-- 計画されたファイルがすべて存在するかチェック
MATCH (v:VersionState {id: $version_id})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)
WHERE NOT EXISTS {
  MATCH (uri)-[:HAS_ACTUAL_FILE]->(file:File {exists: true})
}
RETURN uri.id AS missing_file
```

### 4.3 Cypherのみでの自動テスト

自動テストは「0件なら成功、1件以上ならエラー」という単純なルールに基づいています。

#### テストクエリの基本構造
```cypher
-- 基本的なテストクエリテンプレート
-- このクエリが0件を返せばテスト成功
MATCH (問題のあるパターン)
WHERE (問題を示す条件)
RETURN (問題の詳細)
```

#### 実行例：依存関係の完全性テスト
```cypher
-- テスト：すべての依存関係が満たされているか
MATCH (req:Requirement {status: "active"})
MATCH (req)-[:DEPENDS_ON]->(dep:Requirement)
WHERE dep.status <> "completed"
RETURN COUNT(*) AS unmet_dependencies
-- 期待値：0（0なら成功）
```

## 5. 実装例：決済機能開発

実際のプロジェクトで検証されたシナリオを通じて、論理的整合性検証の実践を説明します。

### 5.1 シナリオ概要

- **要件**：決済機能の実装（webhook処理を含む）
- **問題**：webhookはStripe APIに依存するが、v2.0の計画にStripe API統合が含まれていない
- **検出**：論理的検証により、依存関係の欠落を事前に発見

### 5.2 データ投入

```cypher
-- バージョン状態の作成
CREATE (v:VersionState {id: "v2.0", name: "Payment Feature Release", status: "planning"});

-- URI（ファイル）の作成
CREATE (api:URI {id: "payment/api.py", type: "file"});
CREATE (webhook:URI {id: "payment/webhook.py", type: "file"});

-- 要件の作成
CREATE (payment_req:Requirement {id: "req_payment", title: "決済処理", type: "feature"});
CREATE (webhook_req:Requirement {id: "req_webhook", title: "Webhook処理", type: "feature"});
CREATE (stripe_req:Requirement {id: "req_stripe", title: "Stripe連携", type: "integration"});

-- 依存関係の設定
CREATE (webhook_req)-[:DEPENDS_ON]->(stripe_req);

-- v2.0への計画追加（Stripe連携を意図的に除外）
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(api);
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(webhook);
CREATE (api)-[:LOCATED_WITH_REQUIREMENT]->(payment_req);
CREATE (webhook)-[:LOCATED_WITH_REQUIREMENT]->(webhook_req);
```

### 5.3 検証クエリの実行

#### v2.0に含まれる予定のファイル確認
```cypher
MATCH (v:VersionState {id: "v2.0"})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)
RETURN uri.id
ORDER BY uri.id;
```

**結果**：
- payment/api.py
- payment/webhook.py

#### 論理的に必要だが計画にない要件の検出
```cypher
MATCH (v:VersionState {id: "v2.0"})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH_REQUIREMENT]->(req)
MATCH (req)-[:DEPENDS_ON]->(dep_req)
WHERE NOT EXISTS {
  MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri2)-[:LOCATED_WITH_REQUIREMENT]->(dep_req)
}
RETURN DISTINCT dep_req.title AS missing_requirement, req.title AS required_by;
```

**結果**：
- missing_requirement: "Stripe連携"
- required_by: "Webhook処理"

### 5.4 論理的フィードバックループ

論理的フィードバックループは、検証結果を次の計画サイクルに反映させるプロセスです。

#### 1. 検出フェーズ
```cypher
-- 欠落している依存関係を検出し、アラートを生成
MATCH (v:VersionState {status: "planning"})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH_REQUIREMENT]->(req)
MATCH (req)-[:DEPENDS_ON]->(dep_req)
WHERE NOT EXISTS {
  MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri2)-[:LOCATED_WITH_REQUIREMENT]->(dep_req)
}
CREATE (alert:Alert {
  id: "alert_" + v.id + "_" + dep_req.id,
  type: "missing_dependency",
  severity: "high",
  message: dep_req.title + " is required but not included in " + v.id,
  created_at: datetime()
})
CREATE (alert)-[:ALERTS_ABOUT]->(v)
CREATE (alert)-[:REFERENCES]->(dep_req)
RETURN alert;
```

#### 2. 修正フェーズ
```cypher
-- アラートに基づいて計画を修正
MATCH (alert:Alert {type: "missing_dependency", resolved: false})
MATCH (alert)-[:ALERTS_ABOUT]->(v:VersionState)
MATCH (alert)-[:REFERENCES]->(dep_req:Requirement)
// 新しいURIを作成し、依存要件を追加
CREATE (new_uri:URI {id: dep_req.suggested_path, type: "file"})
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(new_uri)
CREATE (new_uri)-[:LOCATED_WITH_REQUIREMENT]->(dep_req)
SET alert.resolved = true, alert.resolved_at = datetime()
RETURN new_uri;
```

#### 3. 検証フェーズ
```cypher
-- 修正後の完全性を再検証
MATCH (v:VersionState {id: "v2.0"})
OPTIONAL MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH_REQUIREMENT]->(req)
OPTIONAL MATCH (req)-[:DEPENDS_ON]->(dep_req)
WHERE NOT EXISTS {
  MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri2)-[:LOCATED_WITH_REQUIREMENT]->(dep_req)
}
RETURN COUNT(dep_req) AS remaining_issues;
-- 期待値：0（すべての依存関係が解決）
```

### 5.5 継続的改善のメトリクス

```cypher
-- バージョンごとの問題検出率
MATCH (v:VersionState)
OPTIONAL MATCH (v)<-[:ALERTS_ABOUT]-(alert:Alert)
RETURN v.id AS version,
       COUNT(DISTINCT alert) AS total_alerts,
       COUNT(DISTINCT CASE WHEN alert.resolved = true THEN alert END) AS resolved_alerts,
       AVG(duration.between(alert.created_at, alert.resolved_at).days) AS avg_resolution_days
ORDER BY v.id;
```

## まとめ

KuzuDBを使用した論理的整合性の検証は、以下の利点を提供します：

1. **早期問題発見**：計画段階で依存関係の欠落や不整合を検出
2. **自動化**：Cypherクエリによる継続的な検証
3. **トレーサビリティ**：すべての変更と決定の追跡
4. **フィードバックループ**：検出された問題の自動的な計画への反映

この手法により、複雑なソフトウェアプロジェクトでも高い品質と整合性を維持できます。