# KuzuDB リアルタイム同期実装ガイド

## アーキテクチャ概要

```
┌─────────────┐     WebSocket      ┌─────────────┐     R2 Storage
│  Browser A  │ ◄─────────────────► │             │ ◄──────────────►
│ KuzuDB WASM │                     │   Deno      │     Snapshots
└─────────────┘                     │   Server    │
                                    │             │
┌─────────────┐                     │  - Patch    │
│  Browser B  │ ◄─────────────────► │    Router   │
│ KuzuDB WASM │     Patches         │  - Conflict │
└─────────────┘                     │    Resolver │
                                    │  - Broadcast │
┌─────────────┐                     │    Manager  │
│  Browser C  │ ◄─────────────────► │             │
│ KuzuDB WASM │                     └─────────────┘
└─────────────┘
```

## 実装ステップ

### 1. サーバー側（Deno）

```typescript
// server.ts
import { serve } from "https://deno.land/std/http/server.ts";
import { GraphPatch, ServerMessage, ClientMessage } from "./types/protocol.ts";
import { ConflictResolver, GraphState, applyPatch } from "./conflict-resolver.ts";
import { patchToCypher } from "./patch-to-cypher.ts";

class SyncServer {
  private state: GraphState = {
    nodes: new Map(),
    edges: new Map(),
    version: 0
  };
  
  private clients = new Set<WebSocket>();
  private resolver = new ConflictResolver(this.state);
  
  async handleWebSocket(ws: WebSocket) {
    this.clients.add(ws);
    
    // Send initial state
    await this.sendSyncState(ws);
    
    ws.onmessage = async (event) => {
      const message: ClientMessage = JSON.parse(event.data);
      await this.handleMessage(ws, message);
    };
    
    ws.onclose = () => {
      this.clients.delete(ws);
    };
  }
  
  private async handleMessage(ws: WebSocket, message: ClientMessage) {
    switch (message.type) {
      case 'patch':
        await this.handlePatch(ws, message.payload as GraphPatch);
        break;
      case 'sync_request':
        await this.sendSyncState(ws);
        break;
    }
  }
  
  private async handlePatch(sender: WebSocket, patch: GraphPatch) {
    // Resolve conflicts
    const resolution = this.resolver.resolve(patch);
    
    if (resolution.action === 'reject') {
      // Send rejection to sender only
      const response: ServerMessage = {
        type: 'patch_response',
        payload: {
          patchId: patch.id,
          status: 'rejected',
          reason: resolution.reason,
          serverVersion: this.state.version
        }
      };
      sender.send(JSON.stringify(response));
      return;
    }
    
    // Apply patch (possibly modified)
    const patchToApply = resolution.modifiedPatch || patch;
    this.state = applyPatch(this.state, patchToApply);
    
    // Broadcast to all clients
    const broadcast: ServerMessage = {
      type: 'patch_broadcast',
      payload: patchToApply
    };
    
    for (const client of this.clients) {
      client.send(JSON.stringify(broadcast));
    }
    
    // Periodically save snapshots to R2
    if (this.state.version % 100 === 0) {
      await this.saveSnapshot();
    }
  }
  
  private async sendSyncState(ws: WebSocket) {
    // Convert state to patches for reconstruction
    const patches: GraphPatch[] = [];
    
    // ... Build patches from current state ...
    
    const syncState: ServerMessage = {
      type: 'sync_state',
      payload: {
        version: this.state.version,
        patches,
        snapshot: await this.getLatestSnapshot()
      }
    };
    
    ws.send(JSON.stringify(syncState));
  }
  
  private async saveSnapshot() {
    // Save to R2
    // Implementation depends on your R2 setup
  }
  
  private async getLatestSnapshot() {
    // Get from R2
    // Implementation depends on your R2 setup
    return undefined;
  }
}
```

### 2. クライアント側（Browser）

```typescript
// client.ts
import { GraphPatch, ClientMessage, ServerMessage } from "./types/protocol";

class KuzuSyncClient {
  private ws: WebSocket;
  private kuzu: any; // KuzuDB WASM instance
  private pendingPatches: GraphPatch[] = [];
  private serverVersion = 0;
  
  constructor(private wsUrl: string) {
    this.connect();
  }
  
  private connect() {
    this.ws = new WebSocket(this.wsUrl);
    
    this.ws.onmessage = async (event) => {
      const message: ServerMessage = JSON.parse(event.data);
      await this.handleServerMessage(message);
    };
    
    this.ws.onopen = () => {
      // Request initial sync
      this.send({ type: 'sync_request', payload: { fromVersion: 0 } });
    };
  }
  
  private async handleServerMessage(message: ServerMessage) {
    switch (message.type) {
      case 'patch_broadcast':
        await this.applyRemotePatch(message.payload as GraphPatch);
        break;
      
      case 'sync_state':
        await this.applySyncState(message.payload);
        break;
      
      case 'patch_response':
        this.handlePatchResponse(message.payload);
        break;
    }
  }
  
  private async applyRemotePatch(patch: GraphPatch) {
    // Server reconciliation:
    // 1. Undo pending local patches
    await this.undoPendingPatches();
    
    // 2. Apply remote patch
    const query = patchToCypher(patch);
    await this.kuzu.execute(query.statement, query.parameters);
    
    // 3. Redo pending patches
    await this.redoPendingPatches();
    
    this.serverVersion++;
  }
  
  // User operations
  async createNode(label: string, properties: Record<string, any>) {
    const patch: GraphPatch = {
      id: generateId('patch'),
      timestamp: Date.now(),
      clientId: this.getClientId(),
      op: 'create_node',
      nodeId: generateId('node'),
      data: { label, properties }
    };
    
    // Optimistic update
    const query = patchToCypher(patch);
    await this.kuzu.execute(query.statement, query.parameters);
    
    // Track as pending
    this.pendingPatches.push(patch);
    
    // Send to server
    this.send({ type: 'patch', payload: patch });
  }
  
  // ... Similar methods for other operations ...
  
  private send(message: ClientMessage) {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

### 3. 初期同期の最適化

```typescript
// snapshot-manager.ts
class SnapshotManager {
  async createSnapshot(kuzu: any): Promise<Blob> {
    // Use EXPORT DATABASE
    await kuzu.execute("EXPORT DATABASE '/tmp/snapshot'");
    
    // Create tar.gz of exported files
    // Return as Blob
  }
  
  async loadSnapshot(kuzu: any, snapshot: Blob) {
    // Extract snapshot
    // Use IMPORT DATABASE
    await kuzu.execute("IMPORT DATABASE '/tmp/snapshot'");
  }
}
```

## セキュリティ考慮事項

1. **入力検証**: すべてのパッチデータを検証
2. **レート制限**: クライアントごとの操作数を制限
3. **認証**: WebSocket接続時の認証
4. **暗号化**: WSS（WebSocket Secure）の使用

## パフォーマンス最適化

1. **パッチバッチング**: 複数の小さな操作をまとめて送信
2. **デバウンス**: 高頻度の更新を適切に間引く
3. **差分圧縮**: パッチデータの圧縮
4. **接続プール**: WebSocket接続の効率的な管理

## まとめ

この実装により、Matthew Weidner氏のアプローチに基づいた、セキュアで効率的なKuzuDBのリアルタイム同期が実現できます。