// WebSocket server for causal ordering POC
const port = 8083;

interface CausalOperation {
  id: string;
  dependsOn: string[];
  type: 'CREATE' | 'UPDATE' | 'DELETE' | 'INCREMENT';
  payload: any;
  clientId: string;
  timestamp: number;
}

interface ConnectionState {
  id: string;
  ws: WebSocket;
}

const clients = new Map<string, ConnectionState>();
const operations = new Map<string, CausalOperation>();
const appliedOperations = new Set<string>();
let clientIdCounter = 0;

console.log(`WebSocket server starting on ws://localhost:${port}`);

Deno.serve({ port }, (req) => {
  if (req.headers.get("upgrade") !== "websocket") {
    return new Response("Not a websocket request", { status: 400 });
  }

  const { socket, response } = Deno.upgradeWebSocket(req);
  const clientId = `client_${Date.now()}_${crypto.randomUUID().substring(0, 5)}`;
  
  socket.onopen = () => {
    console.log(`Client connected: ${clientId}`);
    const connection: ConnectionState = { id: clientId, ws: socket };
    clients.set(clientId, connection);
  };

  socket.onmessage = async (event) => {
    try {
      const message = JSON.parse(event.data);
      console.log(`Message from ${clientId}:`, JSON.stringify(message));

      switch (message.type) {
        case "identify":
          if (message.clientId) {
            // Update client ID
            const oldConnection = clients.get(clientId);
            if (oldConnection) {
              clients.delete(clientId);
              const newClientId = message.clientId;
              oldConnection.id = newClientId;
              clients.set(newClientId, oldConnection);
              console.log(`Client ${newClientId} identified`);
            }
          }
          break;

        case "operation":
          const op = message.operation as CausalOperation;
          operations.set(op.id, op);
          
          // Broadcast operation to all clients
          const broadcastMsg = JSON.stringify({
            type: "operation",
            operation: op
          });
          
          for (const [id, client] of clients) {
            if (client.ws.readyState === WebSocket.OPEN) {
              client.ws.send(broadcastMsg);
            }
          }
          break;

        case "query":
          // Simple query response for testing
          socket.send(JSON.stringify({
            type: "query_response",
            queryId: message.queryId,
            result: message.query
          }));
          break;
      }
    } catch (error) {
      console.error(`Error handling message from ${clientId}:`, error);
    }
  };

  socket.onerror = (error) => {
    console.error(`WebSocket error for ${clientId}:`, error);
  };

  socket.onclose = () => {
    console.log(`Client disconnected: ${clientId}`);
    clients.delete(clientId);
  };

  return response;
});