/**
 * Schema Manager Integration Example
 * スキーママネージャー統合の例
 * 
 * This example demonstrates how to integrate SchemaManager with
 * ServerKuzuClient and BrowserKuzuClient for distributed schema management.
 */

import { SchemaManager } from "../core/schema_manager.ts";
import { ServerKuzuClient } from "../core/server/server_kuzu_client.ts";
import { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import { DDLOperationType } from "../event_sourcing/ddl_types.ts";
import { WebSocketSyncAdapter } from "../core/websocket/sync.ts";

/**
 * Extended ServerKuzuClient with SchemaManager integration
 * SchemaManager統合を持つ拡張ServerKuzuClient
 */
class ManagedServerKuzuClient extends ServerKuzuClient {
  private schemaManager: SchemaManager;
  
  constructor(clientId: string) {
    super();
    this.schemaManager = new SchemaManager(clientId);
  }
  
  async initialize(): Promise<void> {
    await super.initialize();
    
    // Initialize schema manager with existing events
    const events = this.getEvents();
    await this.schemaManager.initializeFromSnapshot(
      events,
      (query) => this.executeQuery(query)
    );
  }
  
  /**
   * Execute DDL operation through SchemaManager
   * SchemaManagerを通じてDDL操作を実行
   */
  async executeDDL(
    ddlType: DDLOperationType,
    params: Record<string, any>
  ): Promise<void> {
    // Create DDL event
    const event = this.schemaManager.createDDLEvent(ddlType, params);
    
    // Validate before applying
    const validation = this.schemaManager.validateDDL(event);
    if (!validation.valid) {
      throw new Error(`DDL validation failed: ${validation.errors.join(", ")}`);
    }
    
    // Apply through schema manager
    await this.schemaManager.applyDDLEvent(
      event,
      (query) => this.executeQuery(query)
    );
    
    // Store the event
    await this.applyEvent(event);
  }
  
  /**
   * Get current schema information
   * 現在のスキーマ情報を取得
   */
  getSchemaInfo() {
    return {
      version: this.schemaManager.getSchemaVersion(),
      schema: this.schemaManager.getCurrentSchema(),
      appliedDDLs: this.schemaManager.getAppliedDDLs().length,
      pendingDDLs: this.schemaManager.getPendingDDLs().length
    };
  }
  
  /**
   * Check table/column existence
   * テーブル/カラムの存在確認
   */
  hasTable(tableName: string): boolean {
    return this.schemaManager.hasTable(tableName);
  }
  
  hasColumn(tableName: string, columnName: string): boolean {
    return this.schemaManager.hasColumn(tableName, columnName);
  }
}

/**
 * Extended BrowserKuzuClient with SchemaManager integration
 * SchemaManager統合を持つ拡張BrowserKuzuClient
 */
class ManagedBrowserKuzuClient extends BrowserKuzuClientImpl {
  private schemaManager: SchemaManager;
  
  constructor(clientId: string) {
    super();
    this.schemaManager = new SchemaManager(clientId);
  }
  
  async initialize(): Promise<void> {
    await super.initialize();
  }
  
  async initializeFromSnapshot(snapshot: any): Promise<void> {
    await super.initializeFromSnapshot(snapshot);
    
    // Initialize schema manager
    await this.schemaManager.initializeFromSnapshot(
      snapshot.events,
      (query) => this.executeQuery(query)
    );
  }
  
  /**
   * Execute DDL with schema management
   * スキーマ管理付きDDL実行
   */
  async executeDDL(
    ddlType: DDLOperationType,
    params: Record<string, any>
  ): Promise<void> {
    const event = this.schemaManager.createDDLEvent(ddlType, params);
    
    // Validate
    const validation = this.schemaManager.validateDDL(event);
    if (!validation.valid) {
      throw new Error(`DDL validation failed: ${validation.errors.join(", ")}`);
    }
    
    // Apply locally
    await this.schemaManager.applyDDLEvent(
      event,
      (query) => this.executeQuery(query)
    );
    
    // The event will be synchronized through WebSocket
    return event;
  }
  
  getSchemaState() {
    return this.schemaManager.getSyncState();
  }
}

/**
 * Example usage demonstrating schema evolution
 * スキーマ進化を示す使用例
 */
async function demonstrateSchemaEvolution() {
  console.log("=== Schema Manager Integration Demo ===\n");
  
  // Initialize server with schema management
  const server = new ManagedServerKuzuClient("server");
  await server.initialize();
  
  console.log("1. Creating initial schema...");
  
  // Create User table
  await server.executeDDL("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "username", type: "STRING", nullable: false },
      { name: "created_at", type: "TIMESTAMP", nullable: false }
    ],
    primaryKey: ["id"]
  });
  
  // Create Post table
  await server.executeDDL("CREATE_NODE_TABLE", {
    tableName: "Post",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "title", type: "STRING", nullable: false },
      { name: "content", type: "STRING", nullable: true },
      { name: "author_id", type: "STRING", nullable: false },
      { name: "created_at", type: "TIMESTAMP", nullable: false }
    ],
    primaryKey: ["id"]
  });
  
  // Create AUTHORED relationship
  await server.executeDDL("CREATE_EDGE_TABLE", {
    tableName: "AUTHORED",
    fromTable: "User",
    toTable: "Post",
    columns: [
      { name: "published_at", type: "TIMESTAMP" }
    ]
  });
  
  console.log("\nServer schema info:", server.getSchemaInfo());
  
  console.log("\n2. Evolving schema...");
  
  // Add email column to User table
  await server.executeDDL("ADD_COLUMN", {
    tableName: "User",
    columnName: "email",
    dataType: "STRING",
    nullable: true
  });
  
  // Add tags column to Post table
  await server.executeDDL("ADD_COLUMN", {
    tableName: "Post",
    columnName: "tags",
    dataType: "LIST",
    nullable: true
  });
  
  console.log("\nUpdated schema info:", server.getSchemaInfo());
  
  // Demonstrate validation
  console.log("\n3. Testing schema validation...");
  
  try {
    // Try to create duplicate table
    await server.executeDDL("CREATE_NODE_TABLE", {
      tableName: "User",
      columns: [{ name: "id", type: "STRING" }],
      primaryKey: ["id"]
    });
  } catch (error) {
    console.log("Expected validation error:", error.message);
  }
  
  try {
    // Try to add column to non-existent table
    await server.executeDDL("ADD_COLUMN", {
      tableName: "NonExistent",
      columnName: "field",
      dataType: "STRING"
    });
  } catch (error) {
    console.log("Expected validation error:", error.message);
  }
  
  // Check table/column existence
  console.log("\n4. Checking schema state...");
  console.log("Has User table:", server.hasTable("User"));
  console.log("Has Post table:", server.hasTable("Post"));
  console.log("Has NonExistent table:", server.hasTable("NonExistent"));
  console.log("User has email column:", server.hasColumn("User", "email"));
  console.log("Post has tags column:", server.hasColumn("Post", "tags"));
  
  console.log("\n=== Demo Complete ===");
}

/**
 * Example of schema synchronization between clients
 * クライアント間のスキーマ同期の例
 */
async function demonstrateSchemaSynchronization() {
  console.log("\n=== Schema Synchronization Demo ===\n");
  
  // Initialize server
  const server = new ManagedServerKuzuClient("server");
  await server.initialize();
  
  // Create initial schema
  await server.executeDDL("CREATE_NODE_TABLE", {
    tableName: "Product",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "name", type: "STRING", nullable: false },
      { name: "price", type: "DOUBLE", nullable: false }
    ],
    primaryKey: ["id"]
  });
  
  // Get snapshot for client initialization
  const snapshot = {
    events: server.getEvents(),
    timestamp: Date.now()
  };
  
  // Initialize browser client from snapshot
  console.log("1. Initializing browser client from server snapshot...");
  const client = new ManagedBrowserKuzuClient("browser1");
  await client.initialize();
  await client.initializeFromSnapshot(snapshot);
  
  console.log("Client schema state:", client.getSchemaState());
  
  // Client adds a column
  console.log("\n2. Client adding inventory column...");
  const ddlEvent = await client.executeDDL("ADD_COLUMN", {
    tableName: "Product",
    columnName: "inventory",
    dataType: "INT32",
    nullable: true,
    defaultValue: 0
  });
  
  // Simulate synchronization to server
  console.log("\n3. Synchronizing DDL to server...");
  await server.applyEvent(ddlEvent);
  
  console.log("Server schema after sync:", server.getSchemaInfo());
  
  // Demonstrate conflict handling
  console.log("\n4. Testing concurrent schema modifications...");
  
  // Both try to add the same column
  const serverDDL = server.schemaManager.createDDLEvent("ADD_COLUMN", {
    tableName: "Product",
    columnName: "category",
    dataType: "STRING"
  });
  
  const clientDDL = client.schemaManager.createDDLEvent("ADD_COLUMN", {
    tableName: "Product", 
    columnName: "category",
    dataType: "STRING"
  });
  
  // Server applies first
  await server.schemaManager.applyDDLEvent(
    serverDDL,
    (query) => server.executeQuery(query)
  );
  
  // Client sync state shows pending/conflicts
  const syncState = client.getSchemaState();
  console.log("Client sync state:", {
    version: syncState.version,
    pendingDDLs: syncState.pendingDDLs.length,
    conflicts: syncState.conflicts.length
  });
  
  console.log("\n=== Synchronization Demo Complete ===");
}

// Run examples
if (import.meta.main) {
  await demonstrateSchemaEvolution();
  await demonstrateSchemaSynchronization();
}