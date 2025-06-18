# KuzuDB実践ガイド：検証済みの動作例

## 実証済みテストケース

### 1. 環境セットアップと基本動作確認

```bash
# KuzuDBの起動（インメモリモード）
kuzu :memory:
```

### 2. スキーマ作成（コメントなしバージョン）

```cypher
CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY);
CREATE NODE TABLE CodeEntity (persistent_id STRING PRIMARY KEY, name STRING, type STRING, signature STRING);
CREATE NODE TABLE RequirementEntity (id STRING PRIMARY KEY, title STRING, description STRING);
CREATE NODE TABLE VersionState (id STRING PRIMARY KEY, timestamp STRING, description STRING);

CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (FROM VersionState TO LocationURI);
CREATE REL TABLE LOCATED_WITH (FROM LocationURI TO CodeEntity);
CREATE REL TABLE LOCATED_WITH_REQUIREMENT (FROM LocationURI TO RequirementEntity);
CREATE REL TABLE DEPENDS_ON (FROM RequirementEntity TO RequirementEntity);
CREATE REL TABLE REFERENCES_CODE (FROM CodeEntity TO CodeEntity);
```

### 3. テストデータ投入

```cypher
CREATE (v2:VersionState {id: "v2.0", timestamp: "2024-04-01", description: "決済機能リリース"});
CREATE (uri_webhook:LocationURI {id: "payment/webhook.py"});
CREATE (uri_stripe:LocationURI {id: "external/stripe.py"});
CREATE (uri_api:LocationURI {id: "payment/api.py"});

CREATE (req_webhook:RequirementEntity {id: "req_webhook", title: "Webhook受信", description: "Stripeからの通知を受信"});
CREATE (req_stripe:RequirementEntity {id: "req_stripe", title: "Stripe連携", description: "Stripe APIクライアント"});

CREATE (code_webhook:CodeEntity {persistent_id: "webhook_handler", name: "handle_stripe_event", type: "function", signature: "def handle_stripe_event(event: StripeEvent) -> PaymentResult"});
CREATE (code_stripe:CodeEntity {persistent_id: "stripe_client", name: "StripeClient", type: "class", signature: "class StripeClient"});

MATCH (v:VersionState {id: "v2.0"}), (uri:LocationURI {id: "payment/webhook.py"})
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);
MATCH (v:VersionState {id: "v2.0"}), (uri:LocationURI {id: "payment/api.py"})
CREATE (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri);

MATCH (uri:LocationURI {id: "payment/webhook.py"}), (req:RequirementEntity {id: "req_webhook"})
CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);
MATCH (uri:LocationURI {id: "external/stripe.py"}), (req:RequirementEntity {id: "req_stripe"})
CREATE (uri)-[:LOCATED_WITH_REQUIREMENT]->(req);

MATCH (uri:LocationURI {id: "payment/webhook.py"}), (code:CodeEntity {persistent_id: "webhook_handler"})
CREATE (uri)-[:LOCATED_WITH]->(code);

MATCH (req1:RequirementEntity {id: "req_webhook"}), (req2:RequirementEntity {id: "req_stripe"})
CREATE (req1)-[:DEPENDS_ON]->(req2);

MATCH (c1:CodeEntity {persistent_id: "webhook_handler"}), (c2:CodeEntity {persistent_id: "stripe_client"})
CREATE (c1)-[:REFERENCES_CODE]->(c2);
```

### 4. 検証クエリと期待される結果

#### 4.1 基本的なカウント確認
```cypher
MATCH (v:VersionState) RETURN count(v) as version_count;
-- 結果: 1

MATCH (uri:LocationURI) RETURN count(uri) as uri_count;
-- 結果: 3

MATCH (req:RequirementEntity) RETURN count(req) as req_count;
-- 結果: 2
```

#### 4.2 v2.0の計画内容
```cypher
MATCH (v:VersionState {id: "v2.0"})-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri:LocationURI)
RETURN uri.id as planned_files ORDER BY uri.id;
-- 結果:
-- payment/api.py
-- payment/webhook.py
-- 注意: external/stripe.pyは含まれない
```

#### 4.3 論理的な依存関係の欠落検出
```cypher
MATCH (v:VersionState {id: "v2.0"})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH_REQUIREMENT]->(req)
MATCH (req)-[:DEPENDS_ON]->(dep_req)
WHERE NOT EXISTS {
  MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri2)-[:LOCATED_WITH_REQUIREMENT]->(dep_req)
}
RETURN dep_req.title as missing_requirement, dep_req.id as requirement_id;
-- 結果:
-- missing_requirement: "Stripe連携"
-- requirement_id: "req_stripe"
```

#### 4.4 コードレベルの依存関係チェック
```cypher
MATCH (v:VersionState {id: "v2.0"})
MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)-[:LOCATED_WITH]->(code)
MATCH (code)-[:REFERENCES_CODE]->(dep_code)
WHERE NOT EXISTS {
  MATCH (v)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri2)-[:LOCATED_WITH]->(dep_code)
}
RETURN code.name as depends_on, dep_code.name as missing_code;
-- 結果:
-- depends_on: "handle_stripe_event"
-- missing_code: "StripeClient"
```

## トラブルシューティング

### KuzuDBの制限事項

1. **コメント行はサポートされない**
   - `--`で始まる行はエラーになる
   - すべてのコメントを削除する必要がある

2. **日本語プロパティ名は避ける**
   - クオートしても問題が発生する可能性
   - 英語のプロパティ名を使用

3. **HERE DOCUMENTの扱い**
   - bashでヒアドキュメントを使う際は終端文字に注意

### 実行スクリプトの例

```bash
#!/bin/bash
# run_kuzu_test.sh

# クリーンなCypherファイルを準備
cat > /tmp/test.cypher << 'CYPHER'
CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY);
[... スキーマとデータ ...]
CYPHER

# 実行
kuzu :memory: < /tmp/test.cypher
```

## まとめ

この実証により、以下が確認された：

1. **KuzuDBは期待通りに動作する**
   - Version-URI-Requirement-Codeの階層構造が機能
   - 論理的な依存関係の欠落を正確に検出

2. **シンプルなクエリで強力な検証が可能**
   - 「0件なら成功」という単純なルール
   - 複雑な依存関係も簡潔に表現

3. **LLMとの親和性**
   - 自然言語的なクエリ構造
   - 意図が明確で理解しやすい

この検証済みの例を基に、実際のプロジェクトに適用できる。