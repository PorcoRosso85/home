#!/usr/bin/env -S deno run --allow-net --allow-read --allow-env

/**
 * Minimal KuzuDB Sync Server
 * E2Eテストが期待する最小限の実装
 * 
 * Features:
 * - WebSocket sync server with minimal dependencies
 * - Health endpoint with metrics
 * - Telemetry logging support (optional)
 */

import * as telemetry from "./telemetry_log.ts";

const port = parseInt(Deno.env.get("PORT") || "8080");
const clients = new Map<string, WebSocket>();
const serverStartTime = Date.now();

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

// Simple metrics
const metrics = {
  totalConnections: 0,
  totalEvents: 0,
  errors: 0,
  startTime: Date.now()
};

// Log server start
telemetry.info(`Server starting on ws://localhost:${port}`, {
  port,
  telemetry: "enabled"
});

// Start server
Deno.serve({ port }, (req) => {
  const url = new URL(req.url);
  
  // WebSocket upgrade
  if (req.headers.get("upgrade") === "websocket") {
    const { socket, response } = Deno.upgradeWebSocket(req);
    const clientId = url.searchParams.get("clientId") || 
      `client_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    
    socket.addEventListener("open", () => {
      metrics.totalConnections++;
      clients.set(clientId, socket);
      
      telemetry.info(`Client connected: ${clientId}`, {
        clientId,
        activeConnections: clients.size
      });
      
      socket.send(JSON.stringify({
        type: "connected",
        clientId: clientId,
        state: { activeConnections: clients.size }
      }));
    });
    
    socket.addEventListener("message", (event) => {
      try {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case "event":
            metrics.totalEvents++;
            const storedEvent: StoredEvent = {
              ...message.payload,
              sequence: ++eventSequence
            };
            eventHistory.push(storedEvent);
            
            // Log received event
            telemetry.info(`Event received: ${storedEvent.template}`, {
              eventId: storedEvent.id,
              template: storedEvent.template,
              clientId: storedEvent.clientId,
              sequence: storedEvent.sequence,
              params: storedEvent.params
            });
            
            // Apply to in-memory state
            if (storedEvent.template === "INCREMENT_COUNTER") {
              const counterId = storedEvent.params.counterId;
              const amount = storedEvent.params.amount || 1;
              const current = state.counters.get(counterId) || 0;
              state.counters.set(counterId, current + amount);
              telemetry.info(`Counter incremented: ${counterId}`, {
                counterId,
                previousValue: current,
                increment: amount,
                newValue: current + amount
              });
            } else if (storedEvent.template === "QUERY_COUNTER") {
              const counterId = storedEvent.params.counterId;
              const value = state.counters.get(counterId) || 0;
              telemetry.info(`Counter queried: ${counterId}`, {
                counterId,
                value,
                requestingClient: clientId
              });
              
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
              let broadcastCount = 0;
              for (const [cid, ws] of clients) {
                if (cid !== clientId && ws.readyState === WebSocket.OPEN) {
                  ws.send(JSON.stringify({
                    type: "event",
                    payload: storedEvent
                  }));
                  broadcastCount++;
                }
              }
              if (broadcastCount > 0) {
                telemetry.info(`Event broadcasted to ${broadcastCount} clients`, {
                  eventId: storedEvent.id,
                  template: storedEvent.template,
                  sourceClient: storedEvent.clientId,
                  recipientCount: broadcastCount
                });
              }
            }
            break;
            
          case "requestHistory":
            const fromPosition = message.fromPosition || 0;
            const limit = message.limit;
            let historyEvents;
            
            if (limit !== undefined) {
              historyEvents = eventHistory.slice(fromPosition, fromPosition + limit);
            } else {
              historyEvents = eventHistory.slice(fromPosition);
            }
            
            telemetry.info(`History requested`, {
              clientId,
              fromPosition,
              limit,
              eventCount: historyEvents.length,
              totalEvents: eventHistory.length
            });
            
            socket.send(JSON.stringify({
              type: "history",
              events: historyEvents
            }));
            break;
        }
      } catch (error) {
        metrics.errors++;
        telemetry.error("Message processing error", {
          clientId,
          error: error instanceof Error ? error.message : String(error)
        });
      }
    });
    
    socket.addEventListener("close", () => {
      clients.delete(clientId);
      
      telemetry.info(`Client disconnected: ${clientId}`, {
        clientId,
        activeConnections: clients.size
      });
    });
    
    return response;
  }
  
  // Health check with enhanced metrics
  if (url.pathname === "/health") {
    const uptime = Math.floor((Date.now() - serverStartTime) / 1000);
    const eventsPerMinute = uptime > 0 ? Math.round((metrics.totalEvents / uptime) * 60) : 0;
    
    const health = {
      status: "healthy",
      timestamp: new Date().toISOString(),
      uptime,
      connections: clients.size,
      totalConnections: metrics.totalConnections,
      totalEvents: eventHistory.length,
      checks: {
        websocket: "operational",
        storage: "in-memory"
      },
      metrics: {
        eventsPerMinute,
        errors: metrics.errors,
        telemetry: "enabled"
      }
    };
    
    return new Response(JSON.stringify(health), {
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*"
      }
    });
  }
  
  return new Response("Not Found", { status: 404 });
});