# KuzuDB 同期プロトコル仕様（最小構成）

## パッチフォーマット

### 基本構造
```typescript
interface BasePatch {
  id: string;              // パッチのUUID
  clientId: string;        // クライアント識別子
  serverVersion?: number;  // サーバーが付与するバージョン
}
```

### 操作タイプ（最小構成）

#### 1. ノード作成
```typescript
interface CreateNodePatch extends BasePatch {
  op: 'create_node';
  nodeId: string;     // n_[uuid]
  label: string;
  properties?: Record<string, any>;
}
```

#### 2. プロパティ設定
```typescript
interface SetPropertyPatch extends BasePatch {
  op: 'set_property';
  targetType: 'node' | 'edge';
  targetId: string;
  key: string;
  value: any;
}
```

#### 3. ノード削除
```typescript
interface DeleteNodePatch extends BasePatch {
  op: 'delete_node';
  nodeId: string;
}
```

## 通信プロトコル

### クライアント → サーバー
```typescript
interface ClientMessage {
  type: 'patch' | 'sync_request';
  payload: Patch | { fromVersion: number };
}
```

### サーバー → クライアント
```typescript
interface ServerMessage {
  type: 'patch_broadcast' | 'sync_state';
  payload: {
    patch?: Patch;
    version: number;
    patches?: Patch[];  // 初期同期用
  };
}
```

## パッチ → Cypherクエリ変換

### パラメータ化クエリ（必須）
```typescript
async function patchToCypher(patch: Patch, db: KuzuDB) {
  switch (patch.op) {
    case 'create_node':
      const stmt = await db.prepare(
        'CREATE (n:$label {_id: $id, _version: $version})'
      );
      return stmt.bind({
        label: patch.label,
        id: patch.nodeId,
        version: patch.serverVersion
      });
      
    case 'set_property':
      const setProp = await db.prepare(
        'MATCH (n {_id: $id}) SET n[$key] = $value'
      );
      return setProp.bind({
        id: patch.targetId,
        key: patch.key,
        value: patch.value
      });
      
    case 'delete_node':
      const del = await db.prepare(
        'MATCH (n {_id: $id}) SET n._deleted = true'
      );
      return del.bind({ id: patch.nodeId });
  }
}
```

## サーバー処理フロー

```typescript
class SyncServer {
  private version = 0;
  
  handlePatch(patch: Patch): void {
    // 1. バージョン付与（サーバーが順序を決定）
    patch.serverVersion = ++this.version;
    
    // 2. 検証
    if (!this.validatePatch(patch)) {
      return; // 拒否
    }
    
    // 3. ブロードキャスト
    this.broadcast({
      type: 'patch_broadcast',
      payload: { patch, version: this.version }
    });
  }
}
```

## 最小構成での実装優先順位

1. **必須**: サーバーバージョン管理
2. **必須**: パラメータ化クエリ
3. **必須**: 基本的な存在チェック
4. **オプション**: スナップショット機能