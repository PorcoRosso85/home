# サーバー側KuzuDB統合設計

## 背景

現在のアーキテクチャでは、KuzuDBインスタンスは各クライアント（ブラウザ）側にのみ存在し、サーバーはイベント中継のみを行うステートレスな設計となっている。これにより、サーバー側でデータベースの状態を直接クエリすることができない。

## 設計目標

1. **サーバー側でのin-memoryクエリ実現**
   - CLIや他のツールからサーバーに対してクエリを実行可能に
   - リアルタイムで最新の状態を取得

2. **既存アーキテクチャとの互換性維持**
   - クライアント側の実装に影響を与えない
   - イベントソーシングモデルを維持

3. **パフォーマンスと一貫性**
   - サーバー側KuzuDBインスタンスの同期遅延を最小化
   - すべてのクライアントと同じ状態を保証

## 設計オプション評価

### Option A: サーバーもクライアントの1つとして振る舞う
- **利点**: 既存のクライアント実装を再利用可能
- **欠点**: サーバーの特権的な立場を活かせない
- **評価**: △

### Option B: サーバー専用のKuzuDBインスタンスを持つ（推奨）
- **利点**: 
  - サーバー独自の最適化が可能
  - 全イベントの集約ポイントとして機能
  - クエリエンドポイントの実装が容易
- **欠点**: サーバー側専用の実装が必要
- **評価**: ◎

### Option C: クライアントのKuzuDBをプロキシ
- **利点**: サーバー側にデータベースを持たない
- **欠点**: 
  - クライアントへの依存性が高い
  - レスポンス時間が不安定
- **評価**: ✗

## 実装設計（Option B）

### 1. ServerKuzuClient クラス

```typescript
// core/server/server_kuzu_client.ts
export class ServerKuzuClient {
  private db: any;
  private conn: any;
  private events: TemplateEvent[] = [];
  private stateCache = new StateCache();
  
  async initialize(): Promise<void> {
    // Deno環境でKuzuDB WASMを初期化
    const kuzu = await import("kuzu-wasm/sync");
    await kuzu.init();
    
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    
    await this.createSchema();
  }
  
  // イベント適用（クライアントと同じロジック）
  async applyEvent(event: TemplateEvent): Promise<void> {
    // 実装...
  }
  
  // クエリ実行
  async executeQuery(cypher: string, params?: Record<string, any>): Promise<any> {
    if (!this.conn) {
      throw new Error("Server KuzuDB not initialized");
    }
    return await this.conn.query(cypher, params);
  }
}
```

### 2. WebSocketサーバー統合

```typescript
// core/websocket/server.ts の拡張
import { ServerKuzuClient } from "../server/server_kuzu_client.ts";

const serverKuzu = new ServerKuzuClient();
await serverKuzu.initialize();

// イベント受信時の処理を拡張
case "event":
  validateEvent(message.payload);
  const storedEvent = storeEvent(message.payload);
  
  // サーバー側KuzuDBにも適用
  await serverKuzu.applyEvent(storedEvent);
  
  broadcastEvent(storedEvent, clientId);
  break;
```

### 3. クエリエンドポイント

```typescript
// HTTPエンドポイントの追加
if (req.method === "POST" && url.pathname === "/query") {
  const body = await req.json();
  const { cypher, params } = body;
  
  try {
    const result = await serverKuzu.executeQuery(cypher, params);
    return new Response(JSON.stringify({
      success: true,
      data: result
    }), {
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
}
```

### 4. CLIツール

```typescript
// cli/query.ts
export async function queryServer(
  serverUrl: string, 
  cypher: string, 
  params?: Record<string, any>
): Promise<any> {
  const response = await fetch(`${serverUrl}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cypher, params })
  });
  
  const result = await response.json();
  if (!result.success) {
    throw new Error(result.error);
  }
  
  return result.data;
}
```

## 実装手順

1. **ServerKuzuClientクラスの実装**
   - BrowserKuzuClientをベースに、サーバー環境用に最適化
   - 不要なブラウザ固有の機能を削除

2. **WebSocketサーバーの拡張**
   - サーバー起動時にKuzuDBインスタンスを初期化
   - イベント受信時に自身のKuzuDBも更新
   - 既存イベントのリプレイ機能

3. **HTTPクエリエンドポイント**
   - REST APIとして実装
   - 認証・認可の考慮（将来的に）

4. **CLIツールの実装**
   - コマンドライン引数でCypherクエリを受け取る
   - 結果をJSON/テーブル形式で出力

## セキュリティ考慮事項

1. **クエリインジェクション対策**
   - パラメータ化クエリの使用を強制
   - 危険なCypher文の検出とブロック

2. **アクセス制御**
   - 読み取り専用クエリの制限（初期実装）
   - 将来的には認証トークンベースのアクセス制御

3. **リソース制限**
   - クエリタイムアウトの設定
   - 結果セットサイズの制限

## パフォーマンス最適化

1. **キャッシュ戦略**
   - 頻繁なクエリ結果のキャッシュ
   - イベント適用時の適切なキャッシュ無効化

2. **インデックス管理**
   - 主要なクエリパターンに基づくインデックス作成
   - 定期的なインデックス最適化

## 監視とデバッグ

1. **メトリクス収集**
   - クエリ実行時間
   - イベント適用遅延
   - メモリ使用量

2. **ログ出力**
   - クエリログ
   - エラーログ
   - パフォーマンスログ

## 今後の拡張

1. **永続化オプション**
   - 定期的なスナップショット保存
   - S3へのバックアップ

2. **分散クエリ**
   - 複数サーバー間でのクエリ分散
   - 読み取りレプリカの実装

3. **ストリーミングクエリ**
   - WebSocketを使用したリアルタイムクエリ結果
   - 変更通知の購読