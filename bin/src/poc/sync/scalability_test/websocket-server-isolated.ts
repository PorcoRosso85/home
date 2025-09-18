// Isolated WebSocket server that can run with custom port
const port = parseInt(Deno.env.get("PORT") || "8083");

interface CausalOperation {
  id: string;
  dependsOn: string[];
  type: 'CREATE' | 'UPDATE' | 'DELETE' | 'INCREMENT' | 'DDL' | 'DML';
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

// Schema tracking
interface SchemaVersion {
  version: number;
  operations: string[];
  tables: Record<string, any>;
}

const schemaVersion: SchemaVersion = {
  version: 0,
  operations: [],
  tables: {}
};

// Enhanced DDL operations handler based on KuzuDB documentation
function handleServerDDL(op: CausalOperation) {
  const { ddlType, query } = op.payload;
  
  switch (ddlType) {
    case 'CREATE_TABLE':
      const createTableMatch = query.match(/CREATE\s+NODE\s+TABLE\s+(\w+)\s*\(([^)]+)\)/i);
      if (createTableMatch) {
        const [, tableName, columnsStr] = createTableMatch;
        const columns = parseTableColumns(columnsStr);
        schemaVersion.tables[tableName] = { columns };
      }
      break;
      
    case 'ADD_COLUMN':
      const addColumnMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+ADD\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+(\w+)(?:\s+DEFAULT\s+(.+))?/i);
      if (addColumnMatch) {
        const [, tableName, columnName, columnType, defaultValue] = addColumnMatch;
        const table = schemaVersion.tables[tableName];
        if (table && table.columns) {
          if (!table.columns[columnName]) {
            table.columns[columnName] = { 
              type: columnType,
              ...(defaultValue && { default: defaultValue })
            };
          }
        }
      }
      break;
      
    case 'DROP_COLUMN':
      const dropColumnMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+DROP\s+(?:IF\s+EXISTS\s+)?(\w+)/i);
      if (dropColumnMatch) {
        const [, tableName, columnName] = dropColumnMatch;
        const table = schemaVersion.tables[tableName];
        if (table && table.columns) {
          delete table.columns[columnName];
        }
      }
      break;
      
    case 'RENAME_TABLE':
      const renameTableMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+RENAME\s+TO\s+(\w+)/i);
      if (renameTableMatch) {
        const [, oldTableName, newTableName] = renameTableMatch;
        if (schemaVersion.tables[oldTableName]) {
          schemaVersion.tables[newTableName] = schemaVersion.tables[oldTableName];
          delete schemaVersion.tables[oldTableName];
        }
      }
      break;
      
    case 'RENAME_COLUMN':
      const renameColumnMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+RENAME\s+(\w+)\s+TO\s+(\w+)/i);
      if (renameColumnMatch) {
        const [, tableName, oldColumnName, newColumnName] = renameColumnMatch;
        const table = schemaVersion.tables[tableName];
        if (table && table.columns && table.columns[oldColumnName]) {
          table.columns[newColumnName] = table.columns[oldColumnName];
          delete table.columns[oldColumnName];
        }
      }
      break;
      
    case 'COMMENT_ON_TABLE':
      const commentMatch = query.match(/COMMENT\s+ON\s+TABLE\s+(\w+)\s+IS\s+'([^']+)'/i);
      if (commentMatch) {
        const [, tableName, comment] = commentMatch;
        const table = schemaVersion.tables[tableName];
        if (table) {
          table.comment = comment;
        }
      }
      break;
  }
  
  schemaVersion.version++;
  schemaVersion.operations.push(op.id);
}

function parseTableColumns(columnsStr: string): Record<string, any> {
  const columns: Record<string, any> = {};
  const parts = columnsStr.split(',');
  
  for (const part of parts) {
    const trimmed = part.trim();
    const columnMatch = trimmed.match(/^(\w+)\s+(\w+)/);
    if (columnMatch && !trimmed.includes('PRIMARY KEY')) {
      const [, columnName, columnType] = columnMatch;
      columns[columnName] = { type: columnType };
    }
  }
  
  return columns;
}

console.log(`WebSocket server starting on ws://localhost:${port}`);

const server = Deno.serve({ port }, (req) => {
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
          
          if (op.type === 'DDL') {
            handleServerDDL(op);
          }
          
          const senderClientId = message.clientId || op.clientId;
          const senderClient = Array.from(clients.values()).find(c => c.id === senderClientId);
          
          const broadcastMsg = JSON.stringify({
            type: "operation",
            operation: op
          });
          
          for (const [id, client] of clients) {
            if (client.ws.readyState === WebSocket.OPEN) {
              let canSend = true;
              
              if (senderClient && senderClient.isPartitioned) {
                canSend = senderClient.partitionAllowedClients.has(client.id);
              }
              
              if (client.isPartitioned && senderClientId) {
                canSend = canSend && client.partitionAllowedClients.has(senderClientId);
              }
              
              if (canSend) {
                client.ws.send(broadcastMsg);
                
                if (op.type === 'DDL') {
                  client.ws.send(JSON.stringify({
                    type: "schema_update",
                    schema: schemaVersion
                  }));
                }
              }
            }
          }
          break;

        case "partition":
          const partitionClient = Array.from(clients.values()).find(c => c.id === message.clientId);
          if (partitionClient) {
            partitionClient.isPartitioned = true;
            partitionClient.partitionAllowedClients = new Set(message.allowedClients || []);
            console.log(`Client ${message.clientId} partitioned. Allowed clients: ${[...partitionClient.partitionAllowedClients].join(', ')}`);
          }
          break;

        case "heal_partition":
          const healClient = Array.from(clients.values()).find(c => c.id === message.clientId);
          if (healClient) {
            healClient.isPartitioned = false;
            healClient.partitionAllowedClients.clear();
            console.log(`Client ${message.clientId} partition healed`);
          }
          break;

        case "query":
          const queryResult = handleQuery(message.query);
          socket.send(JSON.stringify({
            type: "query_response",
            queryId: message.queryId,
            result: queryResult
          }));
          break;
      }
    } catch (error) {
      console.error(`Error handling message from ${clientId}:`, error);
    }
  };

  socket.onclose = () => {
    console.log(`Client disconnected: ${clientId}`);
    clients.delete(clientId);
  };

  socket.onerror = (error) => {
    console.error(`WebSocket error for ${clientId}:`, error);
  };

  return response;
});

function handleQuery(query: string): any {
  return { success: true, data: [] };
}

// Handle graceful shutdown
globalThis.addEventListener("unload", () => {
  console.log("Server shutting down...");
  for (const [id, client] of clients) {
    if (client.ws.readyState === WebSocket.OPEN) {
      client.ws.close();
    }
  }
});