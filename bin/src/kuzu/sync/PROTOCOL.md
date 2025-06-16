# KuzuDB リアルタイム同期プロトコル設計

## 概要

Matthew Weidner氏の「IDベースの操作」アプローチを採用し、グラフDBに特化したリアルタイム同期プロトコルを定義します。

## 設計原則

1. **セキュリティファースト**: クエリではなくパッチ（操作の意図）を送信
2. **シンプルさ**: 複雑なCRDT/OTアルゴリズムを避ける
3. **柔軟性**: アプリケーション固有のルールを容易に追加可能

## 1. パッチフォーマット（JSONスキーマ）

```typescript
// 基本パッチ構造
interface BasePatch {
  id: string;           // パッチのUUID
  timestamp: number;    // クライアントタイムスタンプ
  clientId: string;     // クライアント識別子
  baseVersion?: number; // 基準バージョン（オプティミスティック更新用）
}

// ノード操作
interface NodePatch extends BasePatch {
  op: 'create_node' | 'update_node' | 'delete_node';
  nodeId: string;       // ノードのUUID
  data?: {
    label?: string;
    properties?: Record<string, any>;
  };
}

// エッジ操作
interface EdgePatch extends BasePatch {
  op: 'create_edge' | 'update_edge' | 'delete_edge';
  edgeId: string;       // エッジのUUID
  data?: {
    label?: string;
    fromNodeId?: string;
    toNodeId?: string;
    properties?: Record<string, any>;
  };
}

// プロパティ操作
interface PropertyPatch extends BasePatch {
  op: 'set_property' | 'remove_property';
  targetType: 'node' | 'edge';
  targetId: string;
  propertyKey: string;
  propertyValue?: any;  // remove_propertyの場合は不要
}

// 統合型
type GraphPatch = NodePatch | EdgePatch | PropertyPatch;
```

## 2. 操作タイプ一覧

### ノード操作
- `create_node`: 新規ノード作成
- `update_node`: ノードのラベル/プロパティ更新
- `delete_node`: ノード削除（関連エッジも削除）

### エッジ操作
- `create_edge`: 新規エッジ作成
- `update_edge`: エッジのラベル/プロパティ更新
- `delete_edge`: エッジ削除

### プロパティ操作
- `set_property`: プロパティ設定/更新
- `remove_property`: プロパティ削除

### 拡張操作（将来対応）
- `move_node`: ノードの階層移動
- `batch_operation`: 複数操作のアトミック実行
- `create_index`: インデックス作成
- `create_constraint`: 制約追加

## 3. ID生成方法

### UUID v4 + プレフィックス方式

```typescript
function generateId(type: 'node' | 'edge' | 'patch'): string {
  const uuid = crypto.randomUUID();
  const prefix = {
    'node': 'n',
    'edge': 'e',
    'patch': 'p'
  }[type];
  return `${prefix}_${uuid}`;
}

// 例:
// ノード: n_550e8400-e29b-41d4-a716-446655440000
// エッジ: e_6ba7b810-9dad-11d1-80b4-00c04fd430c8
// パッチ: p_6ba7b814-9dad-11d1-80b4-00c04fd430c8
```

### 利点
- グローバルな一意性保証
- タイプの即座の識別
- デバッグの容易さ

## 4. 競合解決ルール

### 基本ルール: Last-Write-Wins (LWW) + 追加の知的処理

1. **ノード作成の競合**
   ```typescript
   // 同一IDでの複数create_node → 最初の操作のみ有効
   if (nodeExists(patch.nodeId)) {
     return { status: 'ignored', reason: 'node_already_exists' };
   }
   ```

2. **ノード更新の競合**
   ```typescript
   // タイムスタンプベースのLWW
   if (patch.timestamp > existingNode.lastModified) {
     applyUpdate(patch);
   }
   ```

3. **削除済みノードへの操作**
   ```typescript
   // 削除マーカーを保持（tombstone）
   if (node.isDeleted) {
     return { status: 'rejected', reason: 'node_deleted' };
   }
   ```

4. **エッジの参照整合性**
   ```typescript
   // エッジ作成時、両端のノードが存在することを確認
   if (!nodeExists(edge.fromNodeId) || !nodeExists(edge.toNodeId)) {
     return { status: 'rejected', reason: 'invalid_node_reference' };
   }
   ```

5. **プロパティの型競合**
   ```typescript
   // スキーマ定義に基づく型チェック
   if (!validatePropertyType(patch.propertyKey, patch.propertyValue)) {
     return { status: 'rejected', reason: 'invalid_property_type' };
   }
   ```

## 5. 具体的なパッチ例

### 例1: ユーザーノードの作成

```json
{
  "id": "p_123e4567-e89b-12d3-a456-426614174000",
  "timestamp": 1672531200000,
  "clientId": "client_001",
  "op": "create_node",
  "nodeId": "n_550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "label": "User",
    "properties": {
      "name": "Alice",
      "email": "alice@example.com",
      "created_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

### 例2: フォロー関係の作成

```json
{
  "id": "p_223e4567-e89b-12d3-a456-426614174001",
  "timestamp": 1672531201000,
  "clientId": "client_001",
  "op": "create_edge",
  "edgeId": "e_660e8400-e29b-41d4-a716-446655440001",
  "data": {
    "label": "FOLLOWS",
    "fromNodeId": "n_550e8400-e29b-41d4-a716-446655440000",
    "toNodeId": "n_550e8400-e29b-41d4-a716-446655440001",
    "properties": {
      "since": "2023-01-01T00:00:00Z"
    }
  }
}
```

### 例3: プロパティの更新

```json
{
  "id": "p_323e4567-e89b-12d3-a456-426614174002",
  "timestamp": 1672531202000,
  "clientId": "client_002",
  "op": "set_property",
  "targetType": "node",
  "targetId": "n_550e8400-e29b-41d4-a716-446655440000",
  "propertyKey": "status",
  "propertyValue": "active"
}
```

## 6. Cypherクエリへの変換

### パッチからCypherへの変換関数

```typescript
function patchToCypher(patch: GraphPatch): string {
  switch (patch.op) {
    case 'create_node':
      return `
        CREATE (n:${patch.data.label} {
          id: '${patch.nodeId}',
          ${Object.entries(patch.data.properties || {})
            .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
            .join(', ')}
        })
      `;
    
    case 'update_node':
      return `
        MATCH (n {id: '${patch.nodeId}'})
        SET ${Object.entries(patch.data.properties || {})
          .map(([k, v]) => `n.${k} = ${JSON.stringify(v)}`)
          .join(', ')}
      `;
    
    case 'delete_node':
      return `
        MATCH (n {id: '${patch.nodeId}'})
        DETACH DELETE n
      `;
    
    case 'create_edge':
      return `
        MATCH (from {id: '${patch.data.fromNodeId}'})
        MATCH (to {id: '${patch.data.toNodeId}'})
        CREATE (from)-[e:${patch.data.label} {
          id: '${patch.edgeId}',
          ${Object.entries(patch.data.properties || {})
            .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
            .join(', ')}
        }]->(to)
      `;
    
    case 'delete_edge':
      return `
        MATCH ()-[e {id: '${patch.edgeId}'}]->()
        DELETE e
      `;
    
    case 'set_property':
      const target = patch.targetType === 'node' ? 'n' : 'e';
      return `
        MATCH (${target} {id: '${patch.targetId}'})
        SET ${target}.${patch.propertyKey} = ${JSON.stringify(patch.propertyValue)}
      `;
    
    case 'remove_property':
      const t = patch.targetType === 'node' ? 'n' : 'e';
      return `
        MATCH (${t} {id: '${patch.targetId}'})
        REMOVE ${t}.${patch.propertyKey}
      `;
  }
}
```

### セキュリティ考慮事項

1. **パラメータ化クエリの使用**（実際の実装時）
   ```typescript
   // 安全な実装例
   const statement = await connection.prepare(`
     CREATE (n:$label {id: $id})
   `);
   await statement.run({ label: patch.data.label, id: patch.nodeId });
   ```

2. **入力検証**
   - ラベル名の検証（英数字のみ）
   - プロパティキーの検証
   - 値の型とサイズ制限

3. **権限チェック**
   - 操作タイプごとの権限
   - ノード/エッジタイプごとの権限
   - プロパティレベルの権限

## 7. 実装上の考慮事項

### サーバー側
- WebSocketハンドラー
- パッチ検証ロジック
- 状態管理（メモリ or KuzuDB WASM）
- ブロードキャスト機能
- スナップショット生成（R2保存）

### クライアント側
- オプティミスティック更新
- パッチ生成
- ローカルKuzuDB WASM管理
- サーバー同期とリベース

### パフォーマンス最適化
- パッチのバッチング
- 差分圧縮
- 接続プーリング
- 読み取り専用レプリカ

## まとめ

このプロトコルにより、KuzuDBを使用したグラフデータベースのリアルタイム同期が、セキュアかつ効率的に実現できます。Matthew Weidner氏のシンプルなアプローチを基礎としつつ、グラフDBの特性に適した拡張を加えています。