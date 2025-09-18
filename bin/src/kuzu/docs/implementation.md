# KuzuDB 同期実装ガイド（最小構成）

## 最小構成アーキテクチャ

```
Browser A (KuzuDB WASM) ←→ WebSocket ←→ DO Server ←→ R2 Storage
Browser B (KuzuDB WASM) ←→ WebSocket ←────┘
```

## 実装手順

### 1. サーバー実装（Deno on DO）

```typescript
// server.ts
class MinimalSyncServer {
  private version = 0;
  private clients = new Set<WebSocket>();
  
  async handleRequest(request: Request) {
    if (request.headers.get('upgrade') === 'websocket') {
      const { socket, response } = Deno.upgradeWebSocket(request);
      this.handleWebSocket(socket);
      return response;
    }
    return new Response('WebSocket endpoint', { status: 200 });
  }
  
  handleWebSocket(ws: WebSocket) {
    this.clients.add(ws);
    
    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'patch') {
        this.handlePatch(ws, msg.payload);
      }
    };
    
    ws.onclose = () => this.clients.delete(ws);
  }
  
  handlePatch(sender: WebSocket, patch: any) {
    // サーバーがバージョンを付与（最重要）
    patch.serverVersion = ++this.version;
    
    // 全クライアントにブロードキャスト
    const broadcast = {
      type: 'patch_broadcast',
      payload: { patch, version: this.version }
    };
    
    for (const client of this.clients) {
      client.send(JSON.stringify(broadcast));
    }
  }
}

// Denoサーバー起動
const server = new MinimalSyncServer();
Deno.serve({ port: 8000 }, (req) => server.handleRequest(req));
```

### 2. クライアント実装（Browser）

```typescript
// client.ts
import { Database } from 'kuzu-wasm';

class MinimalSyncClient {
  private ws: WebSocket;
  private db: Database;
  private pendingPatches: any[] = [];
  private serverVersion = 0;
  
  async connect(wsUrl: string) {
    // KuzuDB WASM初期化
    this.db = await Database.create();
    await this.db.execute('CREATE NODE TABLE IF NOT EXISTS Node(_id STRING PRIMARY KEY)');
    
    // WebSocket接続
    this.ws = new WebSocket(wsUrl);
    this.ws.onmessage = (e) => this.handleServerMessage(JSON.parse(e.data));
  }
  
  async createNode(label: string, properties: any) {
    const nodeId = `n_${crypto.randomUUID()}`;
    const patch = {
      id: crypto.randomUUID(),
      clientId: 'client_' + Date.now(),
      op: 'create_node',
      nodeId,
      label,
      properties
    };
    
    // オプティミスティック更新
    await this.applyPatchLocally(patch);
    this.pendingPatches.push(patch);
    
    // サーバーに送信
    this.ws.send(JSON.stringify({ type: 'patch', payload: patch }));
  }
  
  private async handleServerMessage(msg: any) {
    if (msg.type === 'patch_broadcast') {
      // Server Reconciliation
      await this.rollbackPendingPatches();
      await this.applyPatchLocally(msg.payload.patch);
      await this.reapplyPendingPatches();
      
      this.serverVersion = msg.payload.version;
      
      // 自分のパッチなら pending から削除
      this.pendingPatches = this.pendingPatches.filter(
        p => p.id !== msg.payload.patch.id
      );
    }
  }
  
  private async applyPatchLocally(patch: any) {
    // パラメータ化クエリ（セキュリティ必須）
    const stmt = await this.db.prepare(
      'CREATE (n:Node {_id: $id, _version: $version})'
    );
    await stmt.run({ 
      id: patch.nodeId, 
      version: patch.serverVersion || 'pending' 
    });
  }
  
  private async rollbackPendingPatches() {
    // pending パッチを逆順でロールバック
    for (const patch of [...this.pendingPatches].reverse()) {
      await this.db.execute(`MATCH (n {_id: '${patch.nodeId}'}) DELETE n`);
    }
  }
  
  private async reapplyPendingPatches() {
    // pending パッチを再適用
    for (const patch of this.pendingPatches) {
      await this.applyPatchLocally(patch);
    }
  }
}
```

### 3. 最小構成のHTML

```html
<!DOCTYPE html>
<html>
<head>
  <title>KuzuDB Sync PoC</title>
  <script type="module">
    import { MinimalSyncClient } from './client.js';
    
    const client = new MinimalSyncClient();
    await client.connect('ws://localhost:8000');
    
    // ノード作成ボタン
    document.getElementById('create').onclick = () => {
      client.createNode('Task', { 
        title: 'New Task', 
        created: new Date().toISOString() 
      });
    };
  </script>
</head>
<body>
  <h1>KuzuDB Sync PoC</h1>
  <button id="create">Create Node</button>
  <div id="nodes"></div>
</body>
</html>
```

## 実装の優先順位

### フェーズ1（必須）
1. WebSocket接続
2. サーバーバージョン管理
3. パッチのブロードキャスト

### フェーズ2（必須）
1. KuzuDB WASM統合
2. パラメータ化クエリ
3. Server Reconciliation

### フェーズ3（オプション）
1. R2スナップショット
2. 初期同期
3. エラーハンドリング

## セキュリティチェックリスト

- [ ] パラメータ化クエリの使用
- [ ] 入力値の検証
- [ ] WSS（TLS）の使用
- [ ] クライアント認証

## 動作確認

1. Denoサーバー起動: `deno run --allow-net server.ts`
2. ブラウザAでindex.htmlを開く
3. ブラウザBでindex.htmlを開く
4. 両方でノード作成し、同期を確認

この最小構成により、Matthew氏のアプローチの核心部分を実装できます。