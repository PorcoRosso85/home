/**
 * Network Sync POC v2 - 改善版
 * NetworkSimulatorとの統合を強化
 */

import { assertEquals, assert, assertExists } from "jsr:@std/assert@^1.0.0";
import { LocalSyncServer, SyncClient, SyncEvent } from "../local_sync/local_sync_server.ts";

// ========== 改善された型定義 ==========

interface NetworkMessage {
  id: string;
  from: string;
  to: string;
  type: "sync" | "event" | "ack";
  data: any;
  sequenceNumber: number;
  timestamp: number;
  retryCount?: number;
}

interface NetworkNode {
  id: string;
  server: LocalSyncServer;
  client: SyncClient;
  state: "connected" | "disconnected" | "syncing";
  messageQueue: NetworkMessage[];
  sequenceNumber: number;
  lastReceivedSequence: Map<string, number>;
  pendingAcks: Map<string, NetworkMessage>;
}

// ========== 改善されたNetworkSimulator ==========

class NetworkSimulator {
  private nodes: Map<string, NetworkNode> = new Map();
  private links: Map<string, NetworkLink> = new Map();
  private messageInTransit: NetworkMessage[] = [];
  private time = 0;
  
  constructor(nodeIds: string[]) {
    nodeIds.forEach(id => {
      const server = new LocalSyncServer();
      const client = server.connect(id);
      
      this.nodes.set(id, {
        id,
        server,
        client,
        state: "connected",
        messageQueue: [],
        sequenceNumber: 0,
        lastReceivedSequence: new Map(),
        pendingAcks: new Map()
      });
      
      // リアルタイムイベントリスナー設定
      client.on("event", (event) => {
        this.propagateEvent(id, event);
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
          latency: 10 // デフォルト10ms
        });
      }
    }
  }
  
  // イベント伝播（改善版）
  private propagateEvent(fromNodeId: string, event: SyncEvent) {
    const fromNode = this.nodes.get(fromNodeId);
    if (!fromNode) return;
    
    // 他のすべてのノードに送信
    this.nodes.forEach((toNode) => {
      if (toNode.id !== fromNodeId) {
        const message: NetworkMessage = {
          id: `msg_${Date.now()}_${Math.random()}`,
          from: fromNodeId,
          to: toNode.id,
          type: "event",
          data: event,
          sequenceNumber: ++fromNode.sequenceNumber,
          timestamp: this.time
        };
        
        this.sendMessage(message);
      }
    });
  }
  
  // メッセージ送信（パケットロスと遅延を考慮）
  private async sendMessage(message: NetworkMessage) {
    const link = this.getLink(message.from, message.to);
    if (!link || link.condition === "disconnected") {
      return; // 接続なし
    }
    
    // パケットロスシミュレーション
    if (link.packetLoss > 0 && Math.random() < link.packetLoss) {
      // パケットロスした場合、再送を試みる
      if (!message.retryCount) message.retryCount = 0;
      if (message.retryCount < 3) {
        message.retryCount++;
        setTimeout(() => this.sendMessage(message), 100 * message.retryCount);
      }
      return;
    }
    
    // 遅延をシミュレート
    setTimeout(() => {
      this.deliverMessage(message);
    }, link.latency);
  }
  
  // メッセージ配信
  private deliverMessage(message: NetworkMessage) {
    const toNode = this.nodes.get(message.to);
    if (!toNode || toNode.state === "disconnected") return;
    
    // 重複チェック
    const lastSeq = toNode.lastReceivedSequence.get(message.from) || 0;
    if (message.sequenceNumber <= lastSeq) {
      return; // 重複メッセージ
    }
    
    toNode.lastReceivedSequence.set(message.from, message.sequenceNumber);
    
    // メッセージ処理
    if (message.type === "event") {
      // イベントを直接サーバーに適用
      toNode.server.processEvent(message.data);
    }
    
    // ACK送信
    const ack: NetworkMessage = {
      id: `ack_${message.id}`,
      from: message.to,
      to: message.from,
      type: "ack",
      data: { originalId: message.id },
      sequenceNumber: ++toNode.sequenceNumber,
      timestamp: this.time
    };
    
    this.sendMessage(ack);
  }
  
  // ノード操作の改善
  executeOnNode(nodeId: string, operation: string, data: any) {
    const node = this.nodes.get(nodeId);
    if (!node) return;
    
    const event = node.client.send({
      operation: operation as any,
      data
    });
    
    // ローカルで実行されたイベントも他ノードに伝播
    if (node.state === "connected") {
      this.propagateEvent(nodeId, event);
    } else {
      // 切断中はキューに追加
      node.messageQueue.push({
        id: `queued_${Date.now()}`,
        from: nodeId,
        to: "*",
        type: "event",
        data: event,
        sequenceNumber: ++node.sequenceNumber,
        timestamp: this.time
      });
    }
  }
  
  // 接続/切断の改善
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
      // キューに入っているメッセージを送信
      while (node.messageQueue.length > 0) {
        const msg = node.messageQueue.shift()!;
        if (msg.to === "*") {
          // ブロードキャスト
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
  
  setPacketLoss(node1Id: string, node2Id: string, loss: number) {
    const link = this.getLink(node1Id, node2Id);
    if (link) {
      link.packetLoss = loss;
    }
  }
  
  setLatency(node1Id: string, node2Id: string, latency: number) {
    const link = this.getLink(node1Id, node2Id);
    if (link) {
      link.latency = latency;
    }
  }
  
  // ユーティリティ
  private getLink(node1: string, node2: string): NetworkLink | undefined {
    const linkId = node1 < node2 ? `${node1}-${node2}` : `${node2}-${node1}`;
    return this.links.get(linkId);
  }
  
  getNodeEventCount(nodeId: string): number {
    const node = this.nodes.get(nodeId);
    return node ? node.server.getEventCount() : 0;
  }
  
  async waitForSync(timeout: number = 5000): Promise<boolean> {
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
      const counts = Array.from(this.nodes.values()).map(n => n.server.getEventCount());
      if (counts.every(c => c === counts[0] && c > 0)) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    return false;
  }
  
  // 時間を進める（遅延メッセージの処理）
  tick(ms: number = 100) {
    this.time += ms;
  }
}

// NetworkLink型の定義
interface NetworkLink {
  from: string;
  to: string;
  condition: "connected" | "disconnected" | "slow" | "packet_loss" | "partitioned";
  packetLoss: number;
  latency: number;
}

// ========== 改善されたテスト ==========

Deno.test("分断時のローカル書き込み v2", () => {
  const sim = new NetworkSimulator(["node1"]);
  
  // 接続中に書き込み
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 1 });
  assertEquals(sim.getNodeEventCount("node1"), 1);
  
  // ネットワーク分断
  sim.disconnectNode("node1");
  
  // 分断中もローカル書き込み可能
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 2 });
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 3 });
  
  assertEquals(sim.getNodeEventCount("node1"), 3);
});

Deno.test("自動再接続と同期 v2", async () => {
  const sim = new NetworkSimulator(["node1", "node2"]);
  
  // node1で書き込み
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 1 });
  
  // 少し待機（伝播のため）
  await new Promise(resolve => setTimeout(resolve, 50));
  
  // 両ノードが同じイベント数を持つことを確認
  assertEquals(sim.getNodeEventCount("node1"), 1);
  assertEquals(sim.getNodeEventCount("node2"), 1);
  
  // node1とnode2の間を切断
  sim.disconnectLink("node1", "node2");
  
  // 切断中の書き込み
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 2 });
  sim.executeOnNode("node2", "CREATE", { type: "product", id: 1 });
  
  // この時点では同期されていない
  assertEquals(sim.getNodeEventCount("node1"), 2);
  assertEquals(sim.getNodeEventCount("node2"), 2);
  
  // 再接続
  sim.connectLink("node1", "node2");
  
  // 同期を待つ
  const synced = await sim.waitForSync(1000);
  assert(synced);
  
  // 両ノードが全イベントを持つ
  assertEquals(sim.getNodeEventCount("node1"), 3);
  assertEquals(sim.getNodeEventCount("node2"), 3);
});

Deno.test("部分的なネットワーク分断 v2", async () => {
  const sim = new NetworkSimulator(["node1", "node2", "node3"]);
  
  // node1とnode2の間だけ切断
  sim.disconnectLink("node1", "node2");
  
  // 各ノードで書き込み
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 1 });
  sim.executeOnNode("node2", "CREATE", { type: "user", id: 2 });
  sim.executeOnNode("node3", "CREATE", { type: "user", id: 3 });
  
  // 少し待機
  await new Promise(resolve => setTimeout(resolve, 100));
  
  // node3は両方と通信可能なので、3つのイベントを持つ
  assertEquals(sim.getNodeEventCount("node3"), 3);
  
  // node1とnode2は互いのイベントを受信していない
  assertEquals(sim.getNodeEventCount("node1"), 2); // 自分 + node3から
  assertEquals(sim.getNodeEventCount("node2"), 2); // 自分 + node3から
});

Deno.test("パケットロス対策 v2", async () => {
  const sim = new NetworkSimulator(["node1", "node2"]);
  
  // 30%のパケットロスを設定
  sim.setPacketLoss("node1", "node2", 0.3);
  
  // 複数のイベントを送信
  for (let i = 0; i < 10; i++) {
    sim.executeOnNode("node1", "CREATE", { type: "user", id: i });
    await new Promise(resolve => setTimeout(resolve, 10));
  }
  
  // 再送により最終的に全て到達
  const synced = await sim.waitForSync(5000);
  assert(synced);
  assertEquals(sim.getNodeEventCount("node2"), 10);
});

Deno.test("高遅延環境での同期 v2", async () => {
  const sim = new NetworkSimulator(["node1", "node2"]);
  
  // 500msの遅延を設定
  sim.setLatency("node1", "node2", 500);
  
  // イベント送信
  sim.executeOnNode("node1", "CREATE", { type: "user", id: 1 });
  
  // すぐには同期されない
  assertEquals(sim.getNodeEventCount("node2"), 0);
  
  // 遅延後に同期される
  await new Promise(resolve => setTimeout(resolve, 600));
  assertEquals(sim.getNodeEventCount("node2"), 1);
});

// 実行
if (import.meta.main) {
  console.log("=== Network Sync POC v2 - 改善版 ===");
}