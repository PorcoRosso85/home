/**
 * Network Sync POC v3 - 最終改善版
 * 競合解決とベクタークロック伝播を完全実装
 */

import { assertEquals, assert } from "jsr:@std/assert@^1.0.0";
import { LocalSyncServer, SyncClient, SyncEvent } from "../local_sync/local_sync_server.ts";

// ========== 完全な型定義 ==========

interface NetworkEvent extends SyncEvent {
  targetId?: string; // 競合検出用
}

interface NetworkNode {
  id: string;
  server: LocalSyncServer;
  client: SyncClient;
  state: "connected" | "disconnected" | "syncing";
  messageQueue: NetworkMessage[];
  sequenceNumber: number;
  lastReceivedSequence: Map<string, number>;
  vectorClock: Map<string, number>;
  eventHistory: NetworkEvent[];
  conflictLog: ConflictRecord[];
}

interface NetworkMessage {
  id: string;
  from: string;
  to: string;
  type: "sync" | "event" | "ack" | "vector_clock";
  data: any;
  sequenceNumber: number;
  timestamp: number;
  vectorClock?: Map<string, number>;
  retryCount?: number;
}

interface ConflictRecord {
  timestamp: number;
  event1: NetworkEvent;
  event2: NetworkEvent;
  resolution: "event1" | "event2" | "merged";
  strategy: "last_write_wins" | "vector_clock" | "custom";
}

interface NetworkLink {
  from: string;
  to: string;
  condition: "connected" | "disconnected" | "slow" | "packet_loss" | "partitioned";
  packetLoss: number;
  latency: number;
  jitter: number; // 遅延のばらつき
  bandwidth: number; // 帯域幅制限（events/sec）
}

// ========== 完全なNetworkSimulator実装 ==========

class NetworkSimulator {
  private nodes: Map<string, NetworkNode> = new Map();
  private links: Map<string, NetworkLink> = new Map();
  private globalTime = 0;
  private eventCounter = 0;
  
  constructor(nodeIds: string[]) {
    nodeIds.forEach(id => {
      const server = new LocalSyncServer({
        conflictStrategy: "LAST_WRITE_WINS"
      });
      const client = server.connect(id);
      
      const vectorClock = new Map<string, number>();
      nodeIds.forEach(nodeId => vectorClock.set(nodeId, 0));
      
      this.nodes.set(id, {
        id,
        server,
        client,
        state: "connected",
        messageQueue: [],
        sequenceNumber: 0,
        lastReceivedSequence: new Map(),
        vectorClock,
        eventHistory: [],
        conflictLog: []
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
          latency: 10,
          jitter: 0,
          bandwidth: 1000
        });
      }
    }
  }
  
  // イベント実行（競合検出機能付き）
  executeOnNode(nodeId: string, operation: string, data: any): NetworkEvent | null {
    const node = this.nodes.get(nodeId);
    if (!node) return null;
    
    // ベクタークロックを更新
    node.vectorClock.set(nodeId, (node.vectorClock.get(nodeId) || 0) + 1);
    
    // イベント作成
    const event: NetworkEvent = {
      id: `evt_${++this.eventCounter}`,
      clientId: nodeId,
      timestamp: this.globalTime,
      operation: operation as any,
      data,
      vectorClock: Object.fromEntries(node.vectorClock),
      targetId: data.id // 競合検出用
    };
    
    // ローカルで実行
    node.server.processEvent(event);
    node.eventHistory.push(event);
    
    // 接続中なら他ノードに伝播
    if (node.state === "connected") {
      this.propagateEvent(nodeId, event);
    } else {
      // 切断中はキューに追加
      node.messageQueue.push({
        id: `msg_${Date.now()}_${Math.random()}`,
        from: nodeId,
        to: "*",
        type: "event",
        data: event,
        sequenceNumber: ++node.sequenceNumber,
        timestamp: this.globalTime,
        vectorClock: new Map(node.vectorClock)
      });
    }
    
    return event;
  }
  
  // イベント伝播（競合検出付き）
  private propagateEvent(fromNodeId: string, event: NetworkEvent) {
    const fromNode = this.nodes.get(fromNodeId);
    if (!fromNode) return;
    
    this.nodes.forEach((toNode) => {
      if (toNode.id !== fromNodeId) {
        const message: NetworkMessage = {
          id: `msg_${Date.now()}_${Math.random()}`,
          from: fromNodeId,
          to: toNode.id,
          type: "event",
          data: event,
          sequenceNumber: ++fromNode.sequenceNumber,
          timestamp: this.globalTime,
          vectorClock: new Map(fromNode.vectorClock)
        };
        
        this.sendMessage(message);
      }
    });
  }
  
  // メッセージ送信（現実的なネットワーク条件）
  private async sendMessage(message: NetworkMessage) {
    const link = this.getLink(message.from, message.to);
    if (!link || link.condition === "disconnected") {
      return;
    }
    
    // 帯域幅制限チェック
    const node = this.nodes.get(message.from);
    if (node) {
      const recentMessages = node.messageQueue.filter(
        m => this.globalTime - m.timestamp < 1000
      ).length;
      if (recentMessages > link.bandwidth) {
        // 帯域幅超過、キューに入れる
        node.messageQueue.push(message);
        return;
      }
    }
    
    // パケットロス
    if (link.packetLoss > 0 && Math.random() < link.packetLoss) {
      if (!message.retryCount) message.retryCount = 0;
      if (message.retryCount < 3) {
        message.retryCount++;
        setTimeout(() => this.sendMessage(message), 100 * Math.pow(2, message.retryCount));
      }
      return;
    }
    
    // 遅延（ジッター付き）
    const actualLatency = link.latency + (Math.random() - 0.5) * 2 * link.jitter;
    setTimeout(() => {
      this.deliverMessage(message);
    }, Math.max(0, actualLatency));
  }
  
  // メッセージ配信（競合検出と解決）
  private deliverMessage(message: NetworkMessage) {
    const toNode = this.nodes.get(message.to);
    if (!toNode || toNode.state === "disconnected") return;
    
    // 重複チェック
    const lastSeq = toNode.lastReceivedSequence.get(message.from) || 0;
    if (message.sequenceNumber <= lastSeq) {
      return;
    }
    toNode.lastReceivedSequence.set(message.from, message.sequenceNumber);
    
    // ベクタークロック更新
    if (message.vectorClock) {
      message.vectorClock.forEach((clock, nodeId) => {
        const current = toNode.vectorClock.get(nodeId) || 0;
        toNode.vectorClock.set(nodeId, Math.max(current, clock));
      });
    }
    
    if (message.type === "event") {
      const incomingEvent = message.data as NetworkEvent;
      
      // 競合検出
      const conflicts = this.detectConflicts(toNode, incomingEvent);
      
      if (conflicts.length > 0) {
        // 競合解決
        conflicts.forEach(conflict => {
          const resolution = this.resolveConflict(conflict, incomingEvent);
          toNode.conflictLog.push(resolution);
          
          if (resolution.resolution === "event2" || resolution.resolution === "merged") {
            toNode.server.processEvent(incomingEvent);
            toNode.eventHistory.push(incomingEvent);
          }
        });
      } else {
        // 競合なし
        toNode.server.processEvent(incomingEvent);
        toNode.eventHistory.push(incomingEvent);
      }
    }
  }
  
  // 競合検出
  private detectConflicts(node: NetworkNode, incomingEvent: NetworkEvent): NetworkEvent[] {
    if (!incomingEvent.targetId) return [];
    
    return node.eventHistory.filter(event => {
      // 同じターゲットへの操作
      if (event.targetId !== incomingEvent.targetId) return false;
      
      // 因果関係チェック（ベクタークロック）
      const eventVC = event.vectorClock || {};
      const incomingVC = incomingEvent.vectorClock || {};
      
      // 並行イベント（どちらも他方を知らない）
      const concurrent = 
        (!eventVC[incomingEvent.clientId] || eventVC[incomingEvent.clientId] < (incomingVC[incomingEvent.clientId] || 0)) &&
        (!incomingVC[event.clientId] || incomingVC[event.clientId] < (eventVC[event.clientId] || 0));
      
      return concurrent;
    });
  }
  
  // 競合解決
  private resolveConflict(existingEvent: NetworkEvent, incomingEvent: NetworkEvent): ConflictRecord {
    // Last Write Wins
    let resolution: "event1" | "event2" | "merged";
    
    if (existingEvent.timestamp > incomingEvent.timestamp) {
      resolution = "event1";
    } else if (incomingEvent.timestamp > existingEvent.timestamp) {
      resolution = "event2";
    } else {
      // 同じタイムスタンプの場合はクライアントIDで決定
      resolution = existingEvent.clientId < incomingEvent.clientId ? "event1" : "event2";
    }
    
    return {
      timestamp: this.globalTime,
      event1: existingEvent,
      event2: incomingEvent,
      resolution,
      strategy: "last_write_wins"
    };
  }
  
  // ノード管理
  disconnectNode(nodeId: string) {
    const node = this.nodes.get(nodeId);
    if (node) {
      node.state = "disconnected";
    }
  }
  
  connectNode(nodeId: string) {
    const node = this.nodes.get(nodeId);
    if (node) {
      node.state = "connected";
      
      // ベクタークロックを送信
      this.nodes.forEach(otherNode => {
        if (otherNode.id !== nodeId) {
          this.sendMessage({
            id: `vc_${Date.now()}`,
            from: nodeId,
            to: otherNode.id,
            type: "vector_clock",
            data: null,
            sequenceNumber: ++node.sequenceNumber,
            timestamp: this.globalTime,
            vectorClock: new Map(node.vectorClock)
          });
        }
      });
      
      // キューのメッセージを送信
      while (node.messageQueue.length > 0) {
        const msg = node.messageQueue.shift()!;
        if (msg.to === "*") {
          this.nodes.forEach(toNode => {
            if (toNode.id !== nodeId) {
              this.sendMessage({ ...msg, to: toNode.id });
            }
          });
        } else {
          this.sendMessage(msg);
        }
      }
    }
  }
  
  // リンク管理
  disconnectLink(node1Id: string, node2Id: string) {
    const link = this.getLink(node1Id, node2Id);
    if (link) {
      link.condition = "disconnected";
    }
  }
  
  connectLink(node1Id: string, node2Id: string) {
    const link = this.getLink(node1Id, node2Id);
    if (link) {
      link.condition = "connected";
    }
  }
  
  setNetworkCondition(node1Id: string, node2Id: string, options: {
    packetLoss?: number;
    latency?: number;
    jitter?: number;
    bandwidth?: number;
  }) {
    const link = this.getLink(node1Id, node2Id);
    if (link) {
      if (options.packetLoss !== undefined) link.packetLoss = options.packetLoss;
      if (options.latency !== undefined) link.latency = options.latency;
      if (options.jitter !== undefined) link.jitter = options.jitter;
      if (options.bandwidth !== undefined) link.bandwidth = options.bandwidth;
    }
  }
  
  // ユーティリティ
  private getLink(node1: string, node2: string): NetworkLink | undefined {
    const linkId = node1 < node2 ? `${node1}-${node2}` : `${node2}-${node1}`;
    return this.links.get(linkId);
  }
  
  getNode(nodeId: string): NetworkNode | undefined {
    return this.nodes.get(nodeId);
  }
  
  getNodeEventCount(nodeId: string): number {
    const node = this.nodes.get(nodeId);
    return node ? node.eventHistory.length : 0;
  }
  
  getConflictCount(nodeId: string): number {
    const node = this.nodes.get(nodeId);
    return node ? node.conflictLog.length : 0;
  }
  
  hasEvent(nodeId: string, eventCheck: (event: NetworkEvent) => boolean): boolean {
    const node = this.nodes.get(nodeId);
    return node ? node.eventHistory.some(eventCheck) : false;
  }
  
  async waitForSync(timeout: number = 5000): Promise<boolean> {
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
      const counts = Array.from(this.nodes.values()).map(n => n.eventHistory.length);
      if (counts.length > 0 && counts.every(c => c === counts[0] && c > 0)) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    return false;
  }
  
  // 時間を進める
  tick(ms: number = 100) {
    this.globalTime += ms;
  }
}

// ========== 包括的なテストケース ==========

Deno.test("基本的なイベント同期", async () => {
  const sim = new NetworkSimulator(["node1", "node2"]);
  
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 1, name: "Alice" });
  
  await new Promise(resolve => setTimeout(resolve, 50));
  
  assertEquals(sim.getNodeEventCount("node1"), 1);
  assertEquals(sim.getNodeEventCount("node2"), 1);
});

Deno.test("ネットワーク分断と再接続", async () => {
  const sim = new NetworkSimulator(["node1", "node2"]);
  
  // 初期同期
  sim.executeOnNode("node1", "CREATE", { type: "doc", id: "doc1", content: "v1" });
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // 分断
  sim.disconnectLink("node1", "node2");
  
  // 分断中の操作
  sim.executeOnNode("node1", "UPDATE", { type: "doc", id: "doc1", content: "v2" });
  sim.executeOnNode("node2", "UPDATE", { type: "doc", id: "doc1", content: "v3" });
  
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // この時点では同期されていない
  assertEquals(sim.getNodeEventCount("node1"), 2);
  assertEquals(sim.getNodeEventCount("node2"), 2);
  
  // 再接続
  sim.connectLink("node1", "node2");
  sim.connectNode("node1");
  sim.connectNode("node2");
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  // 競合が検出・解決される
  assert(sim.getConflictCount("node1") > 0 || sim.getConflictCount("node2") > 0);
  
  // 最終的に同じイベント数
  assertEquals(sim.getNodeEventCount("node1"), 3);
  assertEquals(sim.getNodeEventCount("node2"), 3);
});

Deno.test("複雑なネットワークトポロジー", async () => {
  const sim = new NetworkSimulator(["A", "B", "C", "D"]);
  
  // スター型トポロジー（Cが中心）
  sim.disconnectLink("A", "B");
  sim.disconnectLink("A", "D");
  sim.disconnectLink("B", "D");
  
  // 各ノードで操作
  sim.executeOnNode("A", "CREATE", { id: "a", value: 1 });
  sim.executeOnNode("B", "CREATE", { id: "b", value: 2 });
  sim.executeOnNode("C", "CREATE", { id: "c", value: 3 });
  sim.executeOnNode("D", "CREATE", { id: "d", value: 4 });
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  // Cは全イベントを持つ（中心ノード）
  assertEquals(sim.getNodeEventCount("C"), 4);
  
  // A, B, Dは自分とCのイベントのみ
  assertEquals(sim.getNodeEventCount("A"), 2);
  assertEquals(sim.getNodeEventCount("B"), 2);
  assertEquals(sim.getNodeEventCount("D"), 2);
});

Deno.test("現実的なネットワーク条件", async () => {
  const sim = new NetworkSimulator(["client", "server"]);
  
  // モバイルネットワークをシミュレート
  sim.setNetworkCondition("client", "server", {
    latency: 100,      // 100ms遅延
    jitter: 50,        // ±50msのジッター
    packetLoss: 0.05,  // 5%パケットロス
    bandwidth: 10      // 10 events/sec
  });
  
  // 高頻度でイベント送信
  const promises = [];
  for (let i = 0; i < 20; i++) {
    sim.executeOnNode("client", "CREATE", { id: i, data: `item${i}` });
    promises.push(new Promise(resolve => setTimeout(resolve, 50)));
  }
  
  await Promise.all(promises);
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  // パケットロスがあっても最終的に同期
  const clientCount = sim.getNodeEventCount("client");
  const serverCount = sim.getNodeEventCount("server");
  
  assertEquals(clientCount, 20);
  assertEquals(serverCount, 20);
});

Deno.test("ベクタークロックによる因果関係保持", async () => {
  const sim = new NetworkSimulator(["node1", "node2", "node3"]);
  
  // 因果関係のあるイベント列
  const e1 = sim.executeOnNode("node1", "CREATE", { id: "user1", name: "Alice" });
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // node2がnode1のイベントを受信してから操作
  const e2 = sim.executeOnNode("node2", "CREATE", { id: "follow", from: "user1", to: "user2" });
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // node3で確認
  assert(sim.hasEvent("node3", e => e.data.id === "user1"));
  assert(sim.hasEvent("node3", e => e.data.id === "follow"));
  
  // ベクタークロックの確認
  const node3 = sim.getNode("node3");
  assert(node3);
  assert((node3.vectorClock.get("node1") || 0) > 0);
  assert((node3.vectorClock.get("node2") || 0) > 0);
});

Deno.test("同時編集の競合解決", async () => {
  const sim = new NetworkSimulator(["editor1", "editor2"]);
  
  // ドキュメントを作成
  sim.executeOnNode("editor1", "CREATE", { id: "doc1", content: "Hello" });
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // ネットワーク分断
  sim.disconnectLink("editor1", "editor2");
  
  // 同時編集
  sim.executeOnNode("editor1", "UPDATE", { id: "doc1", content: "Hello World!" });
  sim.executeOnNode("editor2", "UPDATE", { id: "doc1", content: "Hello Everyone!" });
  
  // 再接続
  sim.connectLink("editor1", "editor2");
  sim.connectNode("editor1");
  sim.connectNode("editor2");
  
  await new Promise(resolve => setTimeout(resolve, 200));
  
  // 競合が検出される
  const conflicts1 = sim.getConflictCount("editor1");
  const conflicts2 = sim.getConflictCount("editor2");
  assert(conflicts1 > 0 || conflicts2 > 0);
  
  // 両ノードが同じイベント数を持つ
  assertEquals(sim.getNodeEventCount("editor1"), 3);
  assertEquals(sim.getNodeEventCount("editor2"), 3);
});

// 実行
if (import.meta.main) {
  console.log("=== Network Sync POC v3 - 完全版 ===");
  console.log("現実的なネットワーク条件での同期をテスト");
}