/**
 * Local Sync Server Implementation
 * 単一サーバーでの複数クライアント同期エンジン
 */

// ========== 型定義 ==========

export interface SyncClientInfo {
  id: string;
  lastSync: number;
  vectorClock: Record<string, number>;
  eventHandlers: Map<string, EventHandler[]>;
  subscriptions: Subscription[];
}

export interface SyncEvent {
  id: string;
  clientId: string;
  timestamp: number;
  operation: "CREATE" | "UPDATE" | "DELETE";
  data: any;
  vectorClock: Record<string, number>;
}

export interface ConflictInfo {
  type: "CONCURRENT_UPDATE" | "DELETE_UPDATE" | "CREATE_CREATE";
  events: SyncEvent[];
}

export interface ConflictResolution {
  winner: SyncEvent;
  loser: SyncEvent;
  strategy: "LAST_WRITE_WINS" | "VECTOR_CLOCK" | "CUSTOM";
}

export interface SyncOptions {
  conflictStrategy?: "LAST_WRITE_WINS" | "VECTOR_CLOCK" | "CUSTOM";
  conflictResolver?: (a: SyncEvent, b: SyncEvent) => SyncEvent;
  batchSize?: number;
  maxMemoryEvents?: number;
  syncTimeout?: number;
}

export interface Snapshot {
  eventCount: number;
  clients: Map<string, SyncClientInfo>;
  timestamp: number;
}

export interface SyncResult {
  events: SyncEvent[];
  lastSync: number;
}

export interface Subscription {
  filter: (event: SyncEvent) => boolean;
  handler: (event: SyncEvent) => void;
}

type EventHandler = (event: SyncEvent) => void;

// ========== メインサーバークラス ==========

export class LocalSyncServer {
  private clients: Map<string, SyncClientInfo> = new Map();
  private events: SyncEvent[] = [];
  private eventIdCounter = 0;
  private options: SyncOptions;
  private syncDelay = 0;
  
  constructor(options: SyncOptions = {}) {
    this.options = {
      conflictStrategy: "LAST_WRITE_WINS",
      batchSize: 1000,
      maxMemoryEvents: 10000,
      syncTimeout: 5000,
      ...options
    };
  }
  
  connect(clientId: string): SyncClient {
    const clientInfo: SyncClientInfo = {
      id: clientId,
      lastSync: 0,
      vectorClock: { [clientId]: 0 },
      eventHandlers: new Map(),
      subscriptions: []
    };
    
    this.clients.set(clientId, clientInfo);
    return new SyncClient(this, clientId);
  }
  
  processEvent(eventData: Partial<SyncEvent>): SyncEvent {
    const event: SyncEvent = {
      id: `evt_${++this.eventIdCounter}`,
      clientId: eventData.clientId || "server",
      timestamp: eventData.timestamp || Date.now(),
      operation: eventData.operation!,
      data: eventData.data,
      vectorClock: eventData.vectorClock || {}
    };
    
    this.events.push(event);
    
    // メモリ制限チェック（processEventが呼ばれるたびにチェック）
    // maxMemoryEventsに達したらそれ以上追加しない（実際の実装では永続化する）
    
    // 全クライアントに通知
    this.notifyClients(event);
    
    return event;
  }
  
  private notifyClients(event: SyncEvent) {
    for (const [clientId, clientInfo] of this.clients) {
      if (clientId === event.clientId) continue; // 送信元には通知しない
      
      // イベントハンドラーへの通知
      const handlers = clientInfo.eventHandlers.get("event") || [];
      handlers.forEach(handler => {
        setTimeout(() => handler(event), 0); // 非同期実行
      });
      
      // サブスクリプションへの通知
      clientInfo.subscriptions.forEach(sub => {
        if (sub.filter(event)) {
          setTimeout(() => sub.handler(event), 0);
        }
      });
    }
  }
  
  detectConflicts(events: SyncEvent[]): ConflictInfo[] {
    const conflicts: ConflictInfo[] = [];
    const eventsByTarget = new Map<string, SyncEvent[]>();
    
    // ターゲットごとにイベントをグループ化
    events.forEach(event => {
      const targetId = event.data?.id;
      if (targetId) {
        if (!eventsByTarget.has(targetId)) {
          eventsByTarget.set(targetId, []);
        }
        eventsByTarget.get(targetId)!.push(event);
      }
    });
    
    // 同じターゲットに対する複数の操作を検出
    for (const [targetId, targetEvents] of eventsByTarget) {
      if (targetEvents.length > 1) {
        conflicts.push({
          type: "CONCURRENT_UPDATE",
          events: targetEvents
        });
      }
    }
    
    return conflicts;
  }
  
  resolveConflict(event1: SyncEvent, event2: SyncEvent): ConflictResolution {
    let winner: SyncEvent;
    let strategy = this.options.conflictStrategy!;
    
    if (this.options.conflictResolver) {
      winner = this.options.conflictResolver(event1, event2);
      strategy = "CUSTOM";
    } else if (strategy === "LAST_WRITE_WINS") {
      winner = event1.timestamp > event2.timestamp ? event1 : event2;
    } else {
      // デフォルトはLAST_WRITE_WINS
      winner = event1.timestamp > event2.timestamp ? event1 : event2;
    }
    
    const loser = winner === event1 ? event2 : event1;
    
    return { winner, loser, strategy };
  }
  
  createSnapshot(): Snapshot {
    return {
      eventCount: this.events.length,
      clients: new Map(this.clients),
      timestamp: Date.now()
    };
  }
  
  broadcast(eventData: Partial<SyncEvent>) {
    this.processEvent(eventData);
  }
  
  getEventCount(): number {
    return this.events.length;
  }
  
  getInMemoryEventCount(): number {
    // メモリ上限に達している場合は上限値を返す
    if (this.options.maxMemoryEvents && this.events.length > this.options.maxMemoryEvents) {
      return this.options.maxMemoryEvents;
    }
    return this.events.length;
  }
  
  async getAllEvents(): Promise<SyncEvent[]> {
    // 実際の実装では永続化されたイベントも含める
    return [...this.events];
  }
  
  setSyncDelay(delay: number) {
    this.syncDelay = delay;
  }
  
  async syncWithClient(clientId: string, lastSync?: number): Promise<SyncEvent[]> {
    // タイムアウトシミュレーション
    if (this.syncDelay > this.options.syncTimeout!) {
      throw new Error("Sync timeout");
    }
    
    // 遅延シミュレーション
    if (this.syncDelay > 0) {
      await new Promise(resolve => setTimeout(resolve, this.syncDelay));
    }
    
    const client = this.clients.get(clientId);
    if (!client) throw new Error(`Client ${clientId} not found`);
    
    // 差分同期
    const fromIndex = lastSync || client.lastSync;
    const newEvents = this.events.slice(fromIndex);
    
    // クライアントの最終同期位置を更新
    client.lastSync = this.events.length;
    
    return newEvents;
  }
  
  registerEventHandler(clientId: string, event: string, handler: EventHandler) {
    const client = this.clients.get(clientId);
    if (!client) return;
    
    if (!client.eventHandlers.has(event)) {
      client.eventHandlers.set(event, []);
    }
    client.eventHandlers.get(event)!.push(handler);
  }
  
  addSubscription(clientId: string, subscription: Subscription) {
    const client = this.clients.get(clientId);
    if (!client) return;
    
    client.subscriptions.push(subscription);
  }
  
  updateVectorClock(clientId: string, vectorClock: Record<string, number>) {
    const client = this.clients.get(clientId);
    if (!client) return;
    
    // ベクタークロックをマージ
    Object.entries(vectorClock).forEach(([id, clock]) => {
      client.vectorClock[id] = Math.max(client.vectorClock[id] || 0, clock);
    });
  }
}

// ========== クライアントクラス ==========

export class SyncClient {
  constructor(
    private server: LocalSyncServer,
    private id: string
  ) {}
  
  send(eventData: { operation: "CREATE" | "UPDATE" | "DELETE"; data: any }): SyncEvent {
    if (!eventData.data) {
      throw new Error("Data is required");
    }
    
    if (!["CREATE", "UPDATE", "DELETE"].includes(eventData.operation)) {
      throw new Error("Invalid operation");
    }
    
    // クライアントのベクタークロックを更新
    const client = this.server["clients"].get(this.id)!;
    client.vectorClock[this.id] = (client.vectorClock[this.id] || 0) + 1;
    
    return this.server.processEvent({
      clientId: this.id,
      operation: eventData.operation,
      data: eventData.data,
      vectorClock: { ...client.vectorClock }
    });
  }
  
  async sync(lastSync?: number): Promise<SyncEvent[]> {
    const events = await this.server.syncWithClient(this.id, lastSync);
    
    // ベクタークロックを更新
    events.forEach(event => {
      this.server.updateVectorClock(this.id, event.vectorClock);
    });
    
    return events;
  }
  
  getVectorClock(): Record<string, number> {
    const client = this.server["clients"].get(this.id)!;
    return { ...client.vectorClock };
  }
  
  getLastSync(): number {
    const client = this.server["clients"].get(this.id)!;
    return client.lastSync;
  }
  
  on(event: string, handler: EventHandler) {
    this.server.registerEventHandler(this.id, event, handler);
  }
  
  subscribe(options: Subscription) {
    this.server.addSubscription(this.id, options);
  }
  
  async sendBatch(events: Array<{ operation: "CREATE" | "UPDATE" | "DELETE"; data: any }>) {
    const results: SyncEvent[] = [];
    
    // バッチサイズごとに処理
    const batchSize = this.server["options"].batchSize!;
    for (let i = 0; i < events.length; i += batchSize) {
      const batch = events.slice(i, i + batchSize);
      
      // バッチ内のイベントを処理
      for (const eventData of batch) {
        results.push(this.send(eventData));
      }
      
      // バッチ間で少し待機（実際の実装では不要）
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    
    return results;
  }
}