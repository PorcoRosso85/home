// WebSocket server for causal ordering POC with enhanced DDL support
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
let clientIdCounter = 0;

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
  
  // Validate DDL syntax first
  if (!query || typeof query !== 'string') {
    console.error(`Invalid DDL query in operation ${op.id}`);
    return;
  }
  
  // Check for invalid syntax
  if (query.toUpperCase().includes('INVALID') || 
      !query.match(/^(CREATE|ALTER|DROP|RENAME|COMMENT)/i)) {
    console.error(`Invalid DDL syntax in operation ${op.id}: ${query}`);
    return;
  }
  
  switch (ddlType) {
    case 'CREATE_TABLE':
      // CREATE TABLE文をパース
      const createTableMatch = query.match(/CREATE\s+NODE\s+TABLE\s+(\w+)\s*\(([^)]+)\)/i);
      if (createTableMatch) {
        const [, tableName, columnsStr] = createTableMatch;
        const columns = parseTableColumns(columnsStr);
        schemaVersion.tables[tableName] = { columns };
        // 成功時のみバージョンを増加
        schemaVersion.version++;
        schemaVersion.operations.push(op.id);
      }
      break;
      
    case 'ADD_COLUMN':
      // ALTER TABLE ADD COLUMN文をパース (IF NOT EXISTS, DEFAULT値サポート)
      const addColumnMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+ADD\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+(\w+)(?:\s+DEFAULT\s+(.+))?/i);
      if (addColumnMatch) {
        const [, tableName, columnName, columnType, defaultValue] = addColumnMatch;
        const table = schemaVersion.tables[tableName];
        if (!table) {
          console.warn(`Table ${tableName} does not exist for ADD_COLUMN operation`);
          return; // テーブルが存在しない場合は何もしない
        }
        if (table.columns) {
          // IF NOT EXISTSの場合、既存カラムがあれば何もしない
          if (!table.columns[columnName]) {
            table.columns[columnName] = { 
              type: columnType,
              ...(defaultValue && { default: defaultValue })
            };
            // 成功時のみバージョンを増加
            schemaVersion.version++;
            schemaVersion.operations.push(op.id);
          }
        }
      }
      break;
      
    case 'DROP_COLUMN':
      // ALTER TABLE DROP COLUMN文をパース (IF EXISTSサポート)
      const dropColumnMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+DROP\s+(?:IF\s+EXISTS\s+)?(\w+)/i);
      if (dropColumnMatch) {
        const [, tableName, columnName] = dropColumnMatch;
        const table = schemaVersion.tables[tableName];
        if (table && table.columns && table.columns[columnName]) {
          delete table.columns[columnName];
          // 成功時のみバージョンを増加
          schemaVersion.version++;
          schemaVersion.operations.push(op.id);
        }
      }
      break;
      
    case 'RENAME_TABLE':
      // ALTER TABLE RENAME TO文をパース
      const renameTableMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+RENAME\s+TO\s+(\w+)/i);
      if (renameTableMatch) {
        const [, oldTableName, newTableName] = renameTableMatch;
        if (schemaVersion.tables[oldTableName]) {
          schemaVersion.tables[newTableName] = schemaVersion.tables[oldTableName];
          delete schemaVersion.tables[oldTableName];
          // 成功時のみバージョンを増加
          schemaVersion.version++;
          schemaVersion.operations.push(op.id);
        }
      }
      break;
      
    case 'RENAME_COLUMN':
      // ALTER TABLE RENAME COLUMN文をパース
      const renameColumnMatch = query.match(/ALTER\s+TABLE\s+(\w+)\s+RENAME\s+(\w+)\s+TO\s+(\w+)/i);
      if (renameColumnMatch) {
        const [, tableName, oldColumnName, newColumnName] = renameColumnMatch;
        const table = schemaVersion.tables[tableName];
        if (table && table.columns && table.columns[oldColumnName]) {
          table.columns[newColumnName] = table.columns[oldColumnName];
          delete table.columns[oldColumnName];
          // 成功時のみバージョンを増加
          schemaVersion.version++;
          schemaVersion.operations.push(op.id);
        }
      }
      break;
      
    case 'COMMENT_ON_TABLE':
      // COMMENT ON TABLE文をパース
      const commentMatch = query.match(/COMMENT\s+ON\s+TABLE\s+(\w+)\s+IS\s+'([^']+)'/i);
      if (commentMatch) {
        const [, tableName, comment] = commentMatch;
        const table = schemaVersion.tables[tableName];
        if (table) {
          table.comment = comment;
          // 成功時のみバージョンを増加
          schemaVersion.version++;
          schemaVersion.operations.push(op.id);
        }
      }
      break;
  }
}

// テーブルカラムのパース
function parseTableColumns(columnsStr: string): Record<string, any> {
  const columns: Record<string, any> = {};
  const parts = columnsStr.split(',');
  
  for (const part of parts) {
    const trimmed = part.trim();
    // PRIMARY KEY以外のカラム定義を探す
    const columnMatch = trimmed.match(/^(\w+)\s+(\w+)/);
    if (columnMatch && !trimmed.includes('PRIMARY KEY')) {
      const [, columnName, columnType] = columnMatch;
      columns[columnName] = { type: columnType };
    }
  }
  
  return columns;
}

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
          
          // Handle DDL operations to update server schema
          if (op.type === 'DDL') {
            handleServerDDL(op);
          }
          
          // Get sender client
          const senderClientId = message.clientId || op.clientId;
          const senderClient = Array.from(clients.values()).find(c => c.id === senderClientId);
          
          // Broadcast operation to all clients (respecting partitions)
          const broadcastMsg = JSON.stringify({
            type: "operation",
            operation: op
          });
          
          // DDL操作の場合、すべてのクライアントにスキーマ更新を送信
          if (op.type === 'DDL') {
            // まず操作をブロードキャスト
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
            
            // その後、パーティションを考慮してスキーマを送信
            setTimeout(() => {
              const schemaMsg = JSON.stringify({
                type: "schema_update",
                schema: schemaVersion
              });
              
              for (const [id, client] of clients) {
                if (client.ws.readyState === WebSocket.OPEN) {
                  // パーティションルールをチェック
                  let canSend = true;
                  
                  // 送信者がパーティション中の場合
                  if (senderClient && senderClient.isPartitioned) {
                    canSend = senderClient.partitionAllowedClients.has(client.id);
                  }
                  
                  // 受信者がパーティション中の場合
                  if (client.isPartitioned && senderClientId) {
                    canSend = canSend && client.partitionAllowedClients.has(senderClientId);
                  }
                  
                  if (canSend) {
                    client.ws.send(schemaMsg);
                  }
                }
              }
            }, 50); // 少し遅延を入れて操作が処理されるのを待つ
          } else {
            // 非DDL操作の場合は通常のブロードキャスト
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
          }
          break;

        case "partition":
          // Set partition for the client
          const partitionClient = Array.from(clients.values()).find(c => c.id === message.clientId);
          if (partitionClient) {
            partitionClient.isPartitioned = true;
            partitionClient.partitionAllowedClients = new Set(message.allowedClients || []);
            console.log(`Client ${message.clientId} partitioned. Allowed clients: ${[...partitionClient.partitionAllowedClients].join(', ')}`);
          }
          break;

        case "heal_partition":
          // Heal partition for the client
          const healClient = Array.from(clients.values()).find(c => c.id === message.clientId);
          if (healClient) {
            healClient.isPartitioned = false;
            healClient.partitionAllowedClients.clear();
            console.log(`Client ${message.clientId} partition healed`);
            
            // Send current schema to healed client
            healClient.ws.send(JSON.stringify({
              type: "schema_update",
              schema: schemaVersion
            }));
          }
          break;

        case "query":
          // Handle query requests
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
  // Simple query handler for demonstration
  return { success: true, data: [] };
}