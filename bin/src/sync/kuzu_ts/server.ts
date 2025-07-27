#!/usr/bin/env -S deno run --allow-net --allow-read --allow-env

/**
 * Minimal KuzuDB Sync Server
 * E2Eテストが期待する最小限の実装
 */

const port = parseInt(Deno.env.get("PORT") || "8080");
const clients = new Map<string, WebSocket>();

interface StoredEvent {
  id: string;
  template: string;
  params: any;
  clientId: string;
  timestamp: number;
  sequence: number;
}

const eventHistory: StoredEvent[] = [];
let eventSequence = 0;

// Simple in-memory state
const state = {
  counters: new Map<string, number>()
};

console.log(`🚀 Server starting on ws://localhost:${port}`);

// Start server
Deno.serve({ port }, (req) => {
  const url = new URL(req.url);
  
  // WebSocket upgrade
  if (req.headers.get("upgrade") === "websocket") {
    const { socket, response } = Deno.upgradeWebSocket(req);
    const clientId = url.searchParams.get("clientId") || 
      `client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    
    socket.addEventListener("open", () => {
      console.log(`✅ Client connected: ${clientId}`);
      clients.set(clientId, socket);
      
      socket.send(JSON.stringify({
        type: "connected",
        clientId: clientId,
        state: { activeConnections: clients.size }
      }));
    });
    
    socket.addEventListener("message", async (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case "event":
            const storedEvent: StoredEvent = {
              ...message.payload,
              sequence: ++eventSequence
            };
            eventHistory.push(storedEvent);
            
            // Apply to in-memory state
            if (storedEvent.template === "INCREMENT_COUNTER") {
              const counterId = storedEvent.params.counterId;
              const amount = storedEvent.params.amount || 1;
              const current = state.counters.get(counterId) || 0;
              state.counters.set(counterId, current + amount);
            } else if (storedEvent.template === "QUERY_COUNTER") {
              const counterId = storedEvent.params.counterId;
              const value = state.counters.get(counterId) || 0;
              
              // Send counter value back
              socket.send(JSON.stringify({
                type: "event",
                payload: {
                  id: `evt_${Date.now()}`,
                  template: "COUNTER_VALUE",
                  params: {
                    counterId: counterId,
                    value: value
                  },
                  clientId: clientId,
                  timestamp: Date.now()
                }
              }));
            } else {
              // Broadcast to other clients (not for query events)
              for (const [cid, ws] of clients) {
                if (cid !== clientId && ws.readyState === WebSocket.OPEN) {
                  ws.send(JSON.stringify({
                    type: "event",
                    payload: storedEvent
                  }));
                }
              }
            }
            break;
            
          case "requestHistory":
            socket.send(JSON.stringify({
              type: "history",
              events: eventHistory.slice(message.fromPosition || 0)
            }));
            break;
        }
      } catch (error) {
        console.error("Message error:", error);
      }
    });
    
    socket.addEventListener("close", () => {
      console.log(`❌ Client disconnected: ${clientId}`);
      clients.delete(clientId);
    });
    
    return response;
  }
  
  // Health check
  if (url.pathname === "/health") {
    return new Response(JSON.stringify({ status: "healthy" }), {
      headers: { "Content-Type": "application/json" }
    });
  }
  
  return new Response("Not Found", { status: 404 });
});