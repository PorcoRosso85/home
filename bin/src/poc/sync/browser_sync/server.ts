/**
 * WebSocket Server for Browser Sync
 * LocalSyncServerを使用してブラウザ間同期を実現
 */

import { LocalSyncServer, SyncClient } from "../local_sync/local_sync_server.ts";

// WebSocketクライアント管理
interface WSClient {
  socket: WebSocket;
  syncClient: SyncClient;
  id: string;
}

const wsClients = new Map<string, WSClient>();
const syncServer = new LocalSyncServer({
  conflictStrategy: "LAST_WRITE_WINS",
  batchSize: 100
});

// HTTPサーバーとWebSocketアップグレード
Deno.serve({ port: 8080 }, async (req) => {
  const url = new URL(req.url);
  
  // WebSocketアップグレード
  if (req.headers.get("upgrade") === "websocket") {
    const { socket, response } = Deno.upgradeWebSocket(req);
    
    socket.onopen = () => {
      // クライアントID生成
      const clientId = `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const syncClient = syncServer.connect(clientId);
      
      // クライアント管理
      const wsClient: WSClient = { socket, syncClient, id: clientId };
      wsClients.set(clientId, wsClient);
      
      console.log(`Client connected: ${clientId}`);
      
      // 接続確認メッセージ
      socket.send(JSON.stringify({
        type: "connected",
        clientId,
        message: "Connected to sync server"
      }));
      
      // リアルタイムイベント購読
      syncClient.on("event", (event) => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: "sync_event",
            event
          }));
        }
      });
    };
    
    socket.onmessage = async (e) => {
      const wsClient = findClientBySocket(socket);
      if (!wsClient) return;
      
      try {
        const message = JSON.parse(e.data);
        
        switch (message.type) {
          case "send_event":
            // イベント送信
            const event = wsClient.syncClient.send({
              operation: message.operation,
              data: message.data
            });
            
            // 送信元に確認を返す
            socket.send(JSON.stringify({
              type: "event_sent",
              event
            }));
            break;
            
          case "sync":
            // 同期リクエスト
            const events = await wsClient.syncClient.sync(message.lastSync);
            socket.send(JSON.stringify({
              type: "sync_response",
              events,
              lastSync: wsClient.syncClient.getLastSync()
            }));
            break;
            
          case "get_state":
            // 現在の状態を取得
            const allEvents = await syncServer.getAllEvents();
            socket.send(JSON.stringify({
              type: "state_response",
              events: allEvents,
              vectorClock: wsClient.syncClient.getVectorClock()
            }));
            break;
            
          default:
            console.warn(`Unknown message type: ${message.type}`);
        }
      } catch (error) {
        console.error("Message handling error:", error);
        socket.send(JSON.stringify({
          type: "error",
          message: error.message
        }));
      }
    };
    
    socket.onclose = () => {
      const wsClient = findClientBySocket(socket);
      if (wsClient) {
        wsClients.delete(wsClient.id);
        console.log(`Client disconnected: ${wsClient.id}`);
      }
    };
    
    socket.onerror = (e) => {
      console.error("WebSocket error:", e);
    };
    
    return response;
  }
  
  // 静的ファイル配信
  if (url.pathname === "/" || url.pathname === "/client.html") {
    const html = await Deno.readTextFile("./client.html");
    return new Response(html, {
      headers: { "content-type": "text/html" }
    });
  }
  
  if (url.pathname === "/client.js") {
    const js = await Deno.readTextFile("./client.js");
    return new Response(js, {
      headers: { "content-type": "application/javascript" }
    });
  }
  
  return new Response("Not Found", { status: 404 });
});

// ヘルパー関数
function findClientBySocket(socket: WebSocket): WSClient | undefined {
  for (const client of wsClients.values()) {
    if (client.socket === socket) {
      return client;
    }
  }
  return undefined;
}

console.log("Browser Sync Server running on http://localhost:8080");
console.log("WebSocket endpoint: ws://localhost:8080");