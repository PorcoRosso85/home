/**
 * Schema Manager Tests
 * スキーママネージャーのテスト
 */

import { assertEquals, assertThrows } from "https://deno.land/std/testing/asserts.ts";
import { SchemaManager } from "./schema_manager.ts";
import { DDLOperationType } from "../event_sourcing/ddl_types.ts";

Deno.test("SchemaManager - Initialization", () => {
  const manager = new SchemaManager("client1");
  
  assertEquals(manager.getSchemaVersion(), 0);
  assertEquals(manager.getCurrentSchema(), {
    nodeTables: {},
    edgeTables: {},
    indexes: {}
  });
  assertEquals(manager.getAppliedDDLs().length, 0);
});

Deno.test("SchemaManager - Create Node Table DDL", async () => {
  const manager = new SchemaManager("client1");
  const executedQueries: string[] = [];
  
  const mockExecuteQuery = async (query: string) => {
    executedQueries.push(query);
    return {};
  };
  
  // Create DDL event
  const event = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Person",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "name", type: "STRING", nullable: true },
      { name: "age", type: "INT32", nullable: true }
    ],
    primaryKey: ["id"]
  });
  
  // Apply DDL
  await manager.applyDDLEvent(event, mockExecuteQuery);
  
  // Verify schema state
  assertEquals(manager.getSchemaVersion(), 1);
  assertEquals(manager.hasTable("Person"), true);
  assertEquals(manager.hasColumn("Person", "id"), true);
  assertEquals(manager.hasColumn("Person", "name"), true);
  assertEquals(manager.hasColumn("Person", "age"), true);
  
  // Verify query was executed
  assertEquals(executedQueries.length, 1);
  assertEquals(executedQueries[0].includes("CREATE NODE TABLE"), true);
});

Deno.test("SchemaManager - Create Edge Table with Dependencies", async () => {
  const manager = new SchemaManager("client1");
  const mockExecuteQuery = async (query: string) => ({});
  
  // Create node tables first
  const person = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Person",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  const company = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Company",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  await manager.applyDDLEvent(person, mockExecuteQuery);
  await manager.applyDDLEvent(company, mockExecuteQuery);
  
  // Create edge table
  const worksAt = manager.createDDLEvent("CREATE_EDGE_TABLE", {
    tableName: "WORKS_AT",
    fromTable: "Person",
    toTable: "Company",
    columns: [
      { name: "since", type: "DATE" },
      { name: "position", type: "STRING" }
    ]
  });
  
  // Verify dependencies were set
  assertEquals(worksAt.dependsOn.length, 2);
  
  await manager.applyDDLEvent(worksAt, mockExecuteQuery);
  
  // Verify schema state
  assertEquals(manager.getSchemaVersion(), 3);
  assertEquals(manager.hasTable("WORKS_AT"), true);
  
  const edgeSchema = manager.getTableSchema("WORKS_AT");
  assertEquals(edgeSchema?.name, "WORKS_AT");
  assertEquals("fromTable" in edgeSchema!, true);
});

Deno.test("SchemaManager - Add/Drop Column Operations", async () => {
  const manager = new SchemaManager("client1");
  const mockExecuteQuery = async (query: string) => ({});
  
  // Create table first
  const createTable = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  await manager.applyDDLEvent(createTable, mockExecuteQuery);
  
  // Add column
  const addColumn = manager.createDDLEvent("ADD_COLUMN", {
    tableName: "User",
    columnName: "email",
    dataType: "STRING",
    nullable: true
  });
  
  await manager.applyDDLEvent(addColumn, mockExecuteQuery);
  
  assertEquals(manager.hasColumn("User", "email"), true);
  assertEquals(manager.getSchemaVersion(), 2);
  
  // Drop column
  const dropColumn = manager.createDDLEvent("DROP_COLUMN", {
    tableName: "User",
    columnName: "email"
  });
  
  await manager.applyDDLEvent(dropColumn, mockExecuteQuery);
  
  assertEquals(manager.hasColumn("User", "email"), false);
  assertEquals(manager.getSchemaVersion(), 3);
});

Deno.test("SchemaManager - Validation", async () => {
  const manager = new SchemaManager("client1");
  
  // Create table DDL
  const createTable = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Product",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  // Validate creating same table again
  const duplicateTable = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Product",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  const validation1 = manager.validateDDL(createTable);
  assertEquals(validation1.valid, true);
  assertEquals(validation1.errors.length, 0);
  
  // Apply first table
  await manager.applyDDLEvent(createTable, async () => ({}));
  
  // Now validate duplicate
  const validation2 = manager.validateDDL(duplicateTable);
  assertEquals(validation2.valid, false);
  assertEquals(validation2.errors[0], "Table Product already exists");
});

Deno.test("SchemaManager - Pending DDLs with Missing Dependencies", async () => {
  const manager = new SchemaManager("client1");
  const mockExecuteQuery = async (query: string) => ({});
  
  // Try to add column to non-existent table
  const addColumn = manager.createDDLEvent("ADD_COLUMN", {
    tableName: "NonExistent",
    columnName: "field",
    dataType: "STRING"
  });
  
  // This should fail and be added to pending
  try {
    await manager.applyDDLEvent(addColumn, mockExecuteQuery);
    throw new Error("Should have thrown an error");
  } catch (error) {
    assertEquals(error instanceof Error && error.message.includes("Missing dependencies"), true);
  }
  
  assertEquals(manager.getPendingDDLs().length, 1);
  
  // Now create the table
  const createTable = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "NonExistent",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  await manager.applyDDLEvent(createTable, mockExecuteQuery);
  
  // Pending DDL should have been processed
  assertEquals(manager.getPendingDDLs().length, 0);
  assertEquals(manager.hasColumn("NonExistent", "field"), true);
});

Deno.test("SchemaManager - Schema History", async () => {
  const manager = new SchemaManager("client1");
  const mockExecuteQuery = async (query: string) => ({});
  
  // Create table first
  const createUser = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  const createPost = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Post",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  
  // Apply table creations
  await manager.applyDDLEvent(createUser, mockExecuteQuery);
  await manager.applyDDLEvent(createPost, mockExecuteQuery);
  
  // Now create ADD_COLUMN which will have proper dependency
  const addColumn = manager.createDDLEvent("ADD_COLUMN", {
    tableName: "User",
    columnName: "email",
    dataType: "STRING"
  });
  
  await manager.applyDDLEvent(addColumn, mockExecuteQuery);
  
  const history = manager.getSchemaHistory();
  assertEquals(history.length, 3);
  assertEquals(history[0].version, 1);
  assertEquals(history[1].version, 2);
  assertEquals(history[2].version, 3);
});

Deno.test("SchemaManager - Conflict Detection", async () => {
  const manager = new SchemaManager("client1");
  
  // Mock execute that throws conflict error only for ALTER TABLE
  const mockExecuteWithConflict = async (query: string) => {
    if (query.includes("ALTER TABLE") && query.includes("email")) {
      throw new Error("Column email already exists");
    }
    return {};
  };
  
  // Create table
  const createTable = manager.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [
      { name: "id", type: "STRING" },
      { name: "email", type: "STRING" }
    ],
    primaryKey: ["id"]
  });
  
  await manager.applyDDLEvent(createTable, mockExecuteWithConflict);
  
  // Try to add email column again (simulating concurrent modification)
  const addColumn = manager.createDDLEvent("ADD_COLUMN", {
    tableName: "User",
    columnName: "email",
    dataType: "STRING"
  });
  
  let errorThrown = false;
  try {
    await manager.applyDDLEvent(addColumn, mockExecuteWithConflict);
  } catch (error) {
    errorThrown = true;
    assertEquals(error instanceof Error && error.message.includes("Column email already exists"), true);
  }
  
  assertEquals(errorThrown, true, "Expected error to be thrown");
  
  const syncState = manager.getSyncState();
  assertEquals(syncState.conflicts.length, 1);
  assertEquals(syncState.conflicts[0].type, "CONCURRENT_MODIFICATION");
});

Deno.test("SchemaManager - Initialize from Snapshot", async () => {
  const manager = new SchemaManager("client1");
  const executedQueries: string[] = [];
  
  const mockExecuteQuery = async (query: string) => {
    executedQueries.push(query);
    return {};
  };
  
  // Create some DDL events
  const events = [
    {
      id: "ddl_1",
      template: "CREATE_NODE_TABLE" as DDLOperationType,
      params: {
        tableName: "User",
        columns: [{ name: "id", type: "STRING" }],
        primaryKey: ["id"]
      },
      timestamp: Date.now(),
      type: "DDL" as const,
      dependsOn: [],
      payload: {
        ddlType: "CREATE_NODE_TABLE" as DDLOperationType,
        query: "CREATE NODE TABLE User..."
      }
    },
    {
      id: "ddl_2",
      template: "ADD_COLUMN" as DDLOperationType,
      params: {
        tableName: "User",
        columnName: "name",
        dataType: "STRING"
      },
      timestamp: Date.now(),
      type: "DDL" as const,
      dependsOn: ["ddl_1"],
      payload: {
        ddlType: "ADD_COLUMN" as DDLOperationType,
        query: "ALTER TABLE User ADD COLUMN name..."
      }
    }
  ];
  
  await manager.initializeFromSnapshot(events, mockExecuteQuery);
  
  // Verify state was restored
  assertEquals(manager.getSchemaVersion(), 2);
  assertEquals(manager.hasTable("User"), true);
  assertEquals(manager.hasColumn("User", "name"), true);
  assertEquals(executedQueries.length, 2);
});