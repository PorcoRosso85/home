# LLM時代の意図駆動型アーキテクチャ記述言語としてのKuzuDB

## 概要

このシステムは単なるタスク管理ツールではない。**LLMと人間が協働する時代の、最小限の意図記述によるアーキテクチャ管理システム**である。

### 核心的な発見

1. **厳密さを捨てる勇気**
   - `payment/webhook.py` → `payment/webhook` で十分
   - 人間が理解できる最小限の情報があれば、LLMが文脈を補完

2. **結果整合性という現実的な選択**
   - リアルタイムの一貫性は不要
   - トランザクション境界の厳密な管理も不要
   - 最終的に整合性が取れればよい

3. **LLMが解決する運用課題**
   - エラーハンドリング：LLMが文脈から判断
   - 自動化：LLMが意図を理解して実行
   - 学習コスト：自然言語での操作が可能

## 設計思想

### 最小限の情報で最大限の表現力

```cypher
-- これだけで十分
CREATE (uri:LocationURI {id: "payment/webhook"})
CREATE (req:RequirementEntity {id: "stripe_integration"})
CREATE (uri)-[:NEEDS]->(req)
```

人間：「webhookにはstripe統合が必要」という意図を表現
LLM：文脈から具体的な実装詳細を補完

### クエリ可能な意図の保存

```cypher
-- 自然な問いかけ
"v2.0で何を作る予定？"
MATCH (v:VersionState {id: "v2.0"})-[:INCLUDES]->(uri)
RETURN uri.id

-- 依存関係の発見
"webhookを作るには何が必要？"
MATCH (webhook {id: "payment/webhook"})-[:NEEDS]->(req)
RETURN req.id
```

## なぜKuzuDBか

### YAMLとの決定的な違い

YAML（階層的で硬直的）:
```yaml
versions:
  v2.0:
    components:
      payment:
        webhook:
          dependencies:
            - stripe:
                type: api
                version: ">=3.0"
```

KuzuDB（グラフ的で柔軟）:
```cypher
(v2.0)-[:INCLUDES]->(webhook)-[:NEEDS]->(stripe)
```

### グラフ構造の利点

1. **多方向からのクエリが可能**
   - 「stripeを使っているのは？」
   - 「v2.0に必要なものは？」
   - 「webhookの依存関係は？」

2. **関係性が第一級市民**
   - 依存、包含、前提条件などを自然に表現
   - 新しい関係性を後から追加可能

3. **部分的な更新が容易**
   - 全体を書き換える必要がない
   - 必要な部分だけを更新

## 実践的な使い方

### 1. 計画フェーズ

```cypher
-- 意図を記述
CREATE (feature:LocationURI {id: "auth"})
CREATE (req:RequirementEntity {id: "oauth_support"})
CREATE (feature)-[:REQUIRES]->(req)
```

### 2. LLMとの対話

```
Human: "authを実装するには何が必要？"
LLM: [KuzuDBをクエリして回答]
      - oauth_support
      - user_database
      - session_management
```

### 3. 進捗確認

```cypher
-- シンプルなステータス管理
MATCH (uri:LocationURI)
WHERE NOT EXISTS((uri)<-[:IMPLEMENTED]-())
RETURN uri.id as "未実装"
```

## 重要な原則

### 1. 完璧を求めない
- 80%の精度で100%継続する > 100%の精度で20%で挫折

### 2. LLMを前提とする
- 人間は意図を記述
- LLMは詳細を補完
- KuzuDBは関係性を保持

### 3. 削除を恐れない
- 完了したものは削除
- 履歴はGitにある
- 未来だけを管理

## セットアップ

### 最小構成のスキーマ

```cypher
CREATE NODE TABLE LocationURI (id STRING PRIMARY KEY);
CREATE NODE TABLE RequirementEntity (id STRING PRIMARY KEY, description STRING);
CREATE NODE TABLE VersionState (id STRING PRIMARY KEY, target_date STRING);

CREATE REL TABLE TRACKS_STATE_OF_LOCATED_ENTITY (FROM VersionState TO LocationURI);
CREATE REL TABLE LOCATED_WITH_REQUIREMENT (FROM LocationURI TO RequirementEntity);
CREATE REL TABLE DEPENDS_ON (FROM RequirementEntity TO RequirementEntity);
```

### 基本的なクエリテンプレート

```cypher
-- 依存関係の確認
MATCH (a)-[:DEPENDS_ON]->(b)
WHERE NOT EXISTS((b)<-[:IMPLEMENTED]-())
RETURN a.id as "blocked_by", b.id as "missing"

-- 進捗の可視化
MATCH (v:VersionState)-[:TRACKS_STATE_OF_LOCATED_ENTITY]->(uri)
OPTIONAL MATCH (uri)<-[:IMPLEMENTED]-(impl)
RETURN uri.id, impl IS NOT NULL as "done"
```

## まとめ

このアプローチの革新性は、**完璧さを捨てて継続性を取った**ことにある。

- Gitが過去を完璧に記録
- KuzuDBが未来を柔軟に管理
- LLMが両者をつなぐ

これは新しい時代の開発手法の萌芽かもしれない。