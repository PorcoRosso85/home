# KuzuDB WASM リアルタイム同期 - コンセプト

## 概要

Matthew Weidner氏の「Collaborative Text Editing without CRDTs or OT」アプローチを採用し、最小限のサーバー機能で各ブラウザ上のKuzuDB WASMインスタンスを同期するシステムです。

## 設計原則

1. **シンプルさ**: 複雑なCRDT/OTアルゴリズムを避ける
2. **セキュリティ**: クエリではなくパッチ（操作の意図）を送信
3. **柔軟性**: アプリケーション固有のルールを容易に追加可能

## コアコンセプト

### 1. IDベースの操作

各エンティティ（ノード、エッジ）にUUIDを付与し、インデックスではなくIDで参照します。

```typescript
// ❌ 悪い例：インデックスベース
{ op: "update", index: 5, value: "新しい値" }

// ✅ 良い例：IDベース
{ op: "set_property", nodeId: "n_123e4567", key: "name", value: "新しい値" }
```

### 2. サーバーによる順序付け

**重要**: クライアントのタイムスタンプ（LWW）は使用しません。サーバーが操作を受信した順序でシーケンシャルバージョン番号を付与します。

```typescript
// サーバー側の処理
function handlePatch(patch: Patch) {
  const versionedPatch = {
    ...patch,
    serverVersion: ++this.currentVersion,  // サーバーが順序を決定
    receivedAt: Date.now()
  };
  broadcast(versionedPatch);
}
```

### 3. プロパティレベルの操作

`update_node`のような粗粒度の操作は避け、`set_property`/`remove_property`を使用します。

```typescript
// ❌ 避けるべき：ノード全体の更新
{ op: "update_node", nodeId: "n_123", properties: { name: "Alice", age: 30 } }

// ✅ 推奨：プロパティレベルの操作
{ op: "set_property", nodeId: "n_123", key: "name", value: "Alice" }
{ op: "set_property", nodeId: "n_123", key: "age", value: 30 }
```

### 4. セキュアな実行

**必須**: パラメータ化クエリを使用し、Cypherインジェクションを防止します。

```typescript
// ❌ 危険：文字列結合
const query = `CREATE (n:User {name: '${name}'})`;

// ✅ 安全：パラメータ化クエリ
const query = await db.prepare('CREATE (n:User {name: $name})');
await query.run({ name: userInput });
```

## 同期フロー

### 初期同期
1. 新規クライアントが接続
2. サーバーが最新スナップショット（R2から）を提供
3. クライアントがIMPORT DATABASEで初期化
4. 最新のパッチを適用

### リアルタイム同期
1. クライアントがローカルで操作を実行（オプティミスティックUI）
2. パッチをサーバーに送信
3. サーバーがバージョン番号を付与してブロードキャスト
4. 全クライアントがServer Reconciliationで状態を更新

## 競合解決

### 基本ルール
1. **存在チェック**: 操作対象が存在することを確認
2. **参照整合性**: エッジ作成時に両端ノードの存在を確認
3. **Tombstone**: 削除されたエンティティのIDを保持

### Dangling Edge問題の対処
```typescript
// エッジ作成失敗時の処理
if (!nodeExists(fromId) || !nodeExists(toId)) {
  // オプション1: 操作を拒否
  return { status: 'rejected', reason: 'node_not_found' };
  
  // オプション2: 遅延実行キューに追加
  pendingQueue.add({ patch, retryAt: Date.now() + 5000 });
}
```

## 最小構成での実装

1. **フェーズ1**: WebSocket通信とパッチの送受信
2. **フェーズ2**: サーバーバージョン管理とブロードキャスト
3. **フェーズ3**: KuzuDB統合とパラメータ化クエリ
4. **フェーズ4**: 初期同期（スナップショット）機能

この設計により、DO + R2でクライアント側以外の同期課題を解決できます。