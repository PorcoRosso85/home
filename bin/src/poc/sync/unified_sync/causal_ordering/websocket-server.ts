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
  isPartitioned: boolean;
  partitionAllowedClients: Set<string>;
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
    const connection: ConnectionState = { 
      id: clientId, 
      ws: socket,
      isPartitioned: false,
      partitionAllowedClients: new Set()
    };
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
          
          // Get sender client
          const senderClientId = message.clientId || op.clientId;
          const senderClient = Array.from(clients.values()).find(c => c.id === senderClientId);
          
          // Broadcast operation to all clients (respecting partitions)
          const broadcastMsg = JSON.stringify({
            type: "operation",
            operation: op
          });
          
          for (const [id, client] of clients) {
            if (client.ws.readyState === WebSocket.OPEN) {
              // Check partition rules
              let canSend = true;
              
              // If sender is partitioned, only send to allowed clients
              if (senderClient && senderClient.isPartitioned) {
                canSend = senderClient.partitionAllowedClients.has(client.id);
              }
              
              // If receiver is partitioned, only receive from allowed clients
              if (client.isPartitioned && senderClientId) {
                canSend = canSend && client.partitionAllowedClients.has(senderClientId);
              }
              
              if (canSend) {
                client.ws.send(broadcastMsg);
              }
            }
          }
          break;

        case "partition":
          // Set partition for the client
          const partitionClient = Array.from(clients.values()).find(c => c.id === message.clientId);
          if (partitionClient) {
            partitionClient.isPartitioned = true;
            partitionClient.partitionAllowedClients = new Set(message.allowedClients);
            console.log(`Client ${message.clientId} partitioned with allowed clients:`, message.allowedClients);
          }
          break;
          
        case "heal_partition":
          // Heal partition for the client
          const healClient = Array.from(clients.values()).find(c => c.id === message.clientId);
          if (healClient) {
            healClient.isPartitioned = false;
            healClient.partitionAllowedClients.clear();
            console.log(`Client ${message.clientId} partition healed`);
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
    // Find the actual client ID (might have been updated via identify)
    for (const [id, client] of clients) {
      if (client.ws === socket) {
        clients.delete(id);
        break;
      }
    }
  };

  return response;
});