/**
 * WebSocket Server for Multi-Browser Sync
 * 複数ブラウザ間でKuzuDB WASMの同期を実現
 * 
 * 規約準拠:
 * - ESモジュールのみ使用
 * - モックフリー実装
 * - TDD Green Phase
 */

// ========== サーバー設定 ==========

const port = 8080;
const clients = new Map<string, ClientConnection>();
const eventHistory: StoredEvent[] = [];
let eventSequence = 0;

// ========== 型定義 ==========

interface ClientConnection {
  id: string;
  socket: WebSocket;
  subscriptions: Set<string>;
  connectedAt: number;
}

interface StoredEvent {
  id: string;
  template: string;
  params: any;
  clientId: string;
  timestamp: number;
  sequence: number;
}

interface ServerState {
  activeConnections: number;
  clientIds: string[];
  totalEventsProcessed: number;
}

// ========== サーバー状態管理 ==========

export function getServerState(): ServerState {
  return {
    activeConnections: clients.size,
    clientIds: Array.from(clients.keys()),
    totalEventsProcessed: eventHistory.length
  };
}

// テスト用エンドポイント
let stateEndpointEnabled = false;

// ========== イベント検証 ==========

function validateEvent(event: any): void {
  if (!event.id) {
    throw new Error("Invalid event: missing id");
  }
  if (!event.template) {
    throw new Error("Invalid event: missing template");
  }
  if (!event.params) {
    throw new Error("Invalid event: missing params");
  }
  if (!event.clientId) {
    throw new Error("Invalid event: missing clientId");
  }
  if (typeof event.timestamp !== 'number') {
    throw new Error("Invalid event: missing or invalid timestamp");
  }
}

// ========== イベント処理 ==========

function storeEvent(event: any): StoredEvent {
  const stored: StoredEvent = {
    ...event,
    sequence: ++eventSequence
  };
  eventHistory.push(stored);
  return stored;
}

function getEventHistory(fromPosition: number = 0, limit?: number): StoredEvent[] {
  if (limit !== undefined && limit > 0) {
    return eventHistory.slice(fromPosition, fromPosition + limit);
  }
  return eventHistory.slice(fromPosition);
}

// ========== ブロードキャスト ==========

function broadcastEvent(event: StoredEvent, sourceClientId: string): void {
  const message = JSON.stringify({
    type: "event",
    payload: event
  });
  
  for (const [clientId, connection] of clients) {
    // 送信元クライアントには送らない
    if (clientId === sourceClientId) continue;
    
    // サブスクリプションチェック
    if (connection.subscriptions.size > 0 && 
        !connection.subscriptions.has(event.template)) {
      continue;
    }
    
    if (connection.socket.readyState === WebSocket.OPEN) {
      connection.socket.send(message);
    }
  }
}

// ========== WebSocketサーバー ==========

console.log(`WebSocket server starting on ws://localhost:${port}`);

Deno.serve({ port }, (req) => {
  const url = new URL(req.url);
  
  // Handle HTTP GET request to /state endpoint
  if (req.method === "GET" && url.pathname === "/state") {
    return new Response(JSON.stringify(getServerState()), {
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
  
  // Handle WebSocket upgrade
  if (req.headers.get("upgrade") !== "websocket") {
    return new Response("Not Found", { status: 404 });
  }

  const { socket, response } = Deno.upgradeWebSocket(req);
  
  // URLパラメータからクライアントIDを取得（テスト用）
  const clientId = url.searchParams.get("clientId") || 
    `client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;

  socket.addEventListener("open", () => {
    console.log(`Client connected: ${clientId}`);
    
    const connection: ClientConnection = {
      id: clientId,
      socket: socket,
      subscriptions: new Set(),
      connectedAt: Date.now()
    };
    
    clients.set(clientId, connection);
    
    socket.send(JSON.stringify({
      type: "connected",
      clientId: clientId,
      state: getServerState()
    }));
  });

  socket.addEventListener("message", (event) => {
    console.log(`Message from ${clientId}:`, event.data);
    
    try {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case "event":
          // イベント検証
          validateEvent(message.payload);
          
          // イベント保存
          const storedEvent = storeEvent(message.payload);
          
          // 他のクライアントにブロードキャスト
          broadcastEvent(storedEvent, clientId);
          break;
          
        case "requestHistory":
          const fromPosition = message.fromPosition || 0;
          const limit = message.limit;
          const history = getEventHistory(fromPosition, limit);
          
          socket.send(JSON.stringify({
            type: "history",
            events: history
          }));
          break;
          
        case "subscribe":
          const connection = clients.get(clientId);
          if (connection && message.template) {
            connection.subscriptions.add(message.template);
          }
          break;
          
        case "unsubscribe":
          const conn = clients.get(clientId);
          if (conn && message.template) {
            conn.subscriptions.delete(message.template);
          }
          break;
          
        case "getState":
          socket.send(JSON.stringify({
            type: "state",
            state: getServerState()
          }));
          break;
      }
    } catch (error) {
      console.error("Error processing message:", error);
      
      // エラーをクライアントに通知
      if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({
          type: "error",
          error: error.message
        }));
      }
    }
  });

  socket.addEventListener("close", () => {
    console.log(`Client disconnected: ${clientId}`);
    clients.delete(clientId);
  });

  socket.addEventListener("error", (error) => {
    console.error(`WebSocket error for ${clientId}:`, error);
  });

  return response;
});