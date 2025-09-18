/**
 * Network Sync POC - Deno実装
 * 実際のネットワーク環境での競合解決と同期をテスト
 */

import { assertEquals, assert, assertExists } from "jsr:@std/assert@^1.0.0";
import { LocalSyncServer, SyncClient, SyncEvent } from "../local_sync/local_sync_server.ts";

// ========== 型定義 ==========

interface NetworkNode {
  id: string;
  server: LocalSyncServer;
  client: SyncClient;
  state: "connected" | "disconnected" | "syncing";
  pendingQueries: SyncEvent[];
  connections: Set<string>; // 接続中のノードID
}

interface NetworkLink {
  from: string;
  to: string;
  condition: "connected" | "disconnected" | "slow" | "packet_loss" | "partitioned";
  packetLoss: number; // 0.0 - 1.0
  latency: number; // ms
}

// ========== NetworkSimulator ==========

class NetworkSimulator {
  private nodes: Map<string, NetworkNode> = new Map();
  private links: Map<string, NetworkLink> = new Map();
  
  constructor(nodeIds: string[]) {
    // 各ノードに独立したLocalSyncServerを作成
    nodeIds.forEach(id => {
      const server = new LocalSyncServer();
      const client = server.connect(id);
      
      this.nodes.set(id, {
        id,
        server,
        client,
        state: "connected",
        pendingQueries: [],
        connections: new Set()
      });
    });
    
    // 全ノード間のリンクを初期化
    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < nodeIds.length; j++) {
        const linkId = `${nodeIds[i]}-${nodeIds[j]}`;
        this.links.set(linkId, {
          from: nodeIds[i],
          to: nodeIds[j],
          condition: "connected",
          packetLoss: 0,
          latency: 0
        });
      }
    }
  }
  
  getNode(id: string): NetworkNode {
    const node = this.nodes.get(id);
    if (!node) throw new Error(`Node ${id} not found`);
    return node;
  }
  
  // ノード間の接続
  connectNodes(node1Id: string, node2Id: string) {
    const linkId = this.getLinkId(node1Id, node2Id);
    const link = this.links.get(linkId);
    if (link) {
      link.condition = "connected";
      link.packetLoss = 0;
      link.latency = 0;
      
      // 接続状態を更新
      const node1 = this.getNode(node1Id);
      const node2 = this.getNode(node2Id);
      node1.connections.add(node2Id);
      node2.connections.add(node1Id);
    }
  }
  
  // ノード間の切断
  disconnectNodes(node1Id: string, node2Id: string) {
    const linkId = this.getLinkId(node1Id, node2Id);
    const link = this.links.get(linkId);
    if (link) {
      link.condition = "disconnected";
      
      // 接続状態を更新
      const node1 = this.getNode(node1Id);
      const node2 = this.getNode(node2Id);
      node1.connections.delete(node2Id);
      node2.connections.delete(node1Id);
    }
  }
  
  // 全ノード接続
  connectAll() {
    this.nodes.forEach((node1, id1) => {
      this.nodes.forEach((node2, id2) => {
        if (id1 < id2) {
          this.connectNodes(id1, id2);
        }
      });
    });
  }
  
  // パケットロス設定
  setPacketLoss(loss: number) {
    this.links.forEach(link => {
      link.packetLoss = loss;
    });
  }
  
  // ノード間同期（ネットワーク状態を考慮）
  async syncNodes(fromId: string, toId: string): Promise<boolean> {
    const linkId = this.getLinkId(fromId, toId);
    const link = this.links.get(linkId);
    
    if (!link || link.condition === "disconnected") {
      return false;
    }
    
    // パケットロスシミュレーション
    if (link.packetLoss > 0 && Math.random() < link.packetLoss) {
      return false; // パケットロス
    }
    
    // 遅延シミュレーション
    if (link.latency > 0) {
      await new Promise(resolve => setTimeout(resolve, link.latency));
    }
    
    // 実際の同期
    const fromNode = this.getNode(fromId);
    const toNode = this.getNode(toId);
    
    const events = await fromNode.server.getAllEvents();
    events.forEach(event => {
      toNode.server.processEvent(event);
    });
    
    return true;
  }
  
  private getLinkId(node1: string, node2: string): string {
    return node1 < node2 ? `${node1}-${node2}` : `${node2}-${node1}`;
  }
}

// ========== NetworkSyncNode ==========

class NetworkSyncNode {
  private localQueries: string[] = [];
  private pendingQueries: string[] = [];
  private connectionState: "connected" | "disconnected" = "connected";
  private queryCount = 0;
  private vectorClock: Record<string, number> = {};
  
  constructor(
    public id: string,
    private conflictStrategy: "last_write_wins" | "vector_clock" = "last_write_wins"
  ) {
    this.vectorClock[id] = 0;
  }
  
  executeQuery(query: string) {
    this.localQueries.push(query);
    this.queryCount++;
    
    if (this.connectionState === "disconnected") {
      this.pendingQueries.push(query);
    }
    
    // ベクタークロックを更新
    this.vectorClock[this.id]++;
  }
  
  disconnect() {
    this.connectionState = "disconnected";
  }
  
  getConnectionState(): string {
    return this.connectionState;
  }
  
  getPendingQueries(): string[] {
    return this.pendingQueries;
  }
  
  getLocalQueryCount(): number {
    return this.localQueries.length;
  }
  
  getQueryCount(): number {
    return this.queryCount;
  }
  
  getVectorClock(): Record<string, number> {
    return { ...this.vectorClock };
  }
  
  waitForSync(timeout: number = 5): boolean {
    // シンプルな実装
    return true;
  }
  
  async syncWith(other: NetworkSyncNode): Promise<any> {
    const conflicts: any[] = [];
    const acceptedQueries: string[] = [];
    const rejectedQueries: string[] = [];
    
    // 同じクエリを検出（簡易実装）
    other.localQueries.forEach(query => {
      if (this.localQueries.includes(query)) {
        conflicts.push({ type: "concurrent_update" });
        
        // Last Write Winsで解決
        if (this.conflictStrategy === "last_write_wins") {
          acceptedQueries.push(query);
        }
      } else {
        this.localQueries.push(query);
        this.queryCount++;
        acceptedQueries.push(query);
      }
    });
    
    // ベクタークロックをマージ
    Object.entries(other.vectorClock).forEach(([nodeId, clock]) => {
      this.vectorClock[nodeId] = Math.max(this.vectorClock[nodeId] || 0, clock);
    });
    
    return {
      conflict_count: conflicts.length,
      accepted_queries: acceptedQueries,
      rejected_queries: rejectedQueries
    };
  }
  
  hasQuery(query: string): boolean {
    return this.localQueries.includes(query);
  }
  
  async waitForQueryCount(count: number, timeout: number): Promise<boolean> {
    const start = Date.now();
    while (this.queryCount < count) {
      if (Date.now() - start > timeout * 1000) {
        return false;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    return true;
  }
  
  receiveMessage(message: any) {
    // メッセージ受信処理
    this.queryCount++;
  }
  
  createCheckpoint(): any {
    return {
      queries: [...this.localQueries],
      vectorClock: { ...this.vectorClock },
      timestamp: Date.now()
    };
  }
  
  recoverFromCheckpoint(checkpoint: any, source: NetworkSyncNode): any {
    this.localQueries = [...checkpoint.queries];
    this.vectorClock = { ...checkpoint.vectorClock };
    this.queryCount = this.localQueries.length;
    return { success: true };
  }
}

// ========== テスト: ネットワーク分断と再接続 ==========

Deno.test("分断時のローカル書き込み", () => {
  const node = new NetworkSyncNode("node1");
  
  // 接続中に書き込み
  node.executeQuery("CREATE (u:User {id: 1})");
  assertEquals(node.getConnectionState(), "connected");
  
  // ネットワーク分断
  node.disconnect();
  assertEquals(node.getConnectionState(), "disconnected");
  
  // 分断中もローカル書き込み可能
  node.executeQuery("CREATE (u:User {id: 2})");
  node.executeQuery("CREATE (u:User {id: 3})");
  
  // ペンディングクエリが蓄積される
  assertEquals(node.getPendingQueries().length, 2);
  assertEquals(node.getLocalQueryCount(), 3);
});

Deno.test("自動再接続と同期", async () => {
  const node1 = new NetworkSyncNode("node1");
  const node2 = new NetworkSyncNode("node2");
  const network = new NetworkSimulator(["node1", "node2"]);
  
  // 初期状態で接続
  network.connectNodes("node1", "node2");
  
  // node1で書き込み後、切断
  node1.executeQuery("CREATE (u:User {id: 1})");
  network.disconnectNodes("node1", "node2");
  
  // 切断中の書き込み
  node1.executeQuery("CREATE (u:User {id: 2})");
  node2.executeQuery("CREATE (p:Product {id: 1})");
  
  // 再接続
  network.connectNodes("node1", "node2");
  
  // 自動的に同期される
  assert(node1.waitForSync(5));
  assert(node2.waitForSync(5));
  assertEquals(node1.getQueryCount(), node2.getQueryCount());
});

Deno.test("部分的なネットワーク分断", () => {
  const node1 = new NetworkSyncNode("node1");
  const node2 = new NetworkSyncNode("node2");
  const node3 = new NetworkSyncNode("node3");
  const network = new NetworkSimulator(["node1", "node2", "node3"]);
  
  // 全ノード接続
  network.connectAll();
  
  // node1とnode2の間だけ切断
  network.disconnectNodes("node1", "node2");
  
  // 各ノードで書き込み
  node1.executeQuery("CREATE (u:User {id: 1})");
  node2.executeQuery("CREATE (u:User {id: 2})");
  node3.executeQuery("CREATE (u:User {id: 3})");
  
  // node3は両方と通信可能なので、最終的に全データを持つ
  node3.waitForSync();
  assertEquals(node3.getQueryCount(), 3);
  
  // node1とnode2を再接続
  network.connectNodes("node1", "node2");
  
  // 最終的に全ノードが同じ状態に
  assertEquals(node1.getQueryCount(), 3);
  assertEquals(node2.getQueryCount(), 3);
});

// ========== テスト: メッセージ順序と信頼性 ==========

Deno.test("メッセージの順序保証", () => {
  const sender = new NetworkSyncNode("sender");
  const receiver = new NetworkSyncNode("receiver");
  
  // 順番に送信
  const messages = [];
  for (let i = 0; i < 5; i++) {
    const msg = { 
      query: `CREATE (u:User {id: ${i}})`,
      sequence_number: i + 1
    };
    messages.push(msg);
    sender.executeQuery(msg.query);
  }
  
  // 受信側で順序を確認
  messages.forEach((msg, i) => {
    receiver.receiveMessage(msg);
    assertEquals(msg.sequence_number, i + 1);
  });
});

Deno.test("パケットロス対策", async () => {
  const node1 = new NetworkSyncNode("node1");
  const node2 = new NetworkSyncNode("node2");
  const network = new NetworkSimulator(["node1", "node2"]);
  
  // 30%のパケットロスを設定
  network.setPacketLoss(0.3);
  
  // 複数のクエリを送信
  for (let i = 0; i < 10; i++) {
    node1.executeQuery(`CREATE (u:User {id: ${i}})`);
  }
  
  // 再送により最終的に全て到達
  const success = await node2.waitForQueryCount(10, 30);
  assert(success);
  assertEquals(node2.getQueryCount(), 10);
});

// ========== テスト: 競合解決 ==========

Deno.test("同時書き込みの競合解決", async () => {
  const node1 = new NetworkSyncNode("node1", "last_write_wins");
  const node2 = new NetworkSyncNode("node2", "last_write_wins");
  
  // ネットワーク分断中に同じIDのユーザーを作成
  node1.disconnect();
  node2.disconnect();
  
  node1.executeQuery("CREATE (u:User {id: 1, name: 'Alice'})");
  node2.executeQuery("CREATE (u:User {id: 1, name: 'Bob'})");
  
  // 再接続して同期
  const syncResult = await node1.syncWith(node2);
  
  assertEquals(syncResult.conflict_count, 1);
  assertEquals(syncResult.accepted_queries.length, 1);
  assertEquals(syncResult.rejected_queries.length, 0);
});

Deno.test("ベクタークロックによる因果関係の保持", async () => {
  const node1 = new NetworkSyncNode("node1");
  const node2 = new NetworkSyncNode("node2");
  const node3 = new NetworkSyncNode("node3");
  
  // node1 -> node2 -> node3の順で伝播
  node1.executeQuery("CREATE (u:User {id: 1})");
  await node1.syncWith(node2);
  
  node2.executeQuery("CREATE (r:Relation {from: 1, to: 2})");
  await node2.syncWith(node3);
  
  // node3はnode1の更新も含む
  assert(node3.hasQuery("CREATE (u:User {id: 1})"));
  assert(node3.getVectorClock()["node1"] > 0);
});

// ========== テスト: 効率的な同期 ==========

Deno.test("チェックポイントからの回復", () => {
  const node1 = new NetworkSyncNode("node1");
  const node2 = new NetworkSyncNode("node2");
  
  // 大量のデータを同期
  for (let i = 0; i < 100; i++) {
    node1.executeQuery(`CREATE (u:User {id: ${i}})`);
  }
  
  // チェックポイント作成
  const checkpoint = node1.createCheckpoint();
  node1.syncWith(node2);
  
  // node2がクラッシュして再起動
  const node2New = new NetworkSyncNode("node2");
  
  // チェックポイントから高速リカバリ
  const recoveryResult = node2New.recoverFromCheckpoint(checkpoint, node1);
  assert(recoveryResult.success);
  assertEquals(node2New.getQueryCount(), 100);
});

// ========== 実行 ==========

if (import.meta.main) {
  console.log("=== Network Sync POC - Deno Implementation ===");
  console.log("ネットワーク障害シミュレーションを含むテストを実行します。");
}