/**
 * DDL Event Handler Test Suite
 * DDLイベントハンドラーのテストスイート
 */

import { assertEquals, assertThrows, assertRejects } from "jsr:@std/assert@^1.0.0";
import {
  DDLEventHandler,
  ExtendedTemplateRegistry,
  createUnifiedEvent
} from "./ddl_event_handler.ts";
import { isDDLEvent } from "./ddl_types.ts";

Deno.test("DDLEventHandler - create DDL event", () => {
  const handler = new DDLEventHandler();
  
  const event = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "User",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" }
    ],
    primaryKey: ["id"]
  });
  
  assertEquals(event.type, "DDL");
  assertEquals(event.template, "CREATE_NODE_TABLE");
  assertEquals(event.params.tableName, "User");
  assertEquals(event.dependsOn, []);
  assertEquals(event.payload?.ddlType, "CREATE_NODE_TABLE");
  assertEquals(
    event.payload?.query,
    "CREATE NODE TABLE User (id STRING, name STRING, PRIMARY KEY (id))"
  );
});

Deno.test("DDLEventHandler - create DDL event with dependencies", () => {
  const handler = new DDLEventHandler();
  
  const event = handler.createDDLEvent(
    "CREATE_EDGE_TABLE",
    {
      tableName: "FOLLOWS",
      fromTable: "User",
      toTable: "User"
    },
    ["ddl_user_table_123"]
  );
  
  assertEquals(event.dependsOn, ["ddl_user_table_123"]);
});

Deno.test("DDLEventHandler - validate DDL parameters", () => {
  const handler = new DDLEventHandler();
  
  // Invalid table name
  assertThrows(
    () => handler.createDDLEvent("CREATE_NODE_TABLE", {
      tableName: "Invalid Table",
      columns: [{ name: "id", type: "STRING" }],
      primaryKey: ["id"]
    }),
    Error,
    "Invalid table name"
  );
  
  // Missing required parameters
  assertThrows(
    () => handler.createDDLEvent("CREATE_NODE_TABLE", {
      tableName: "User"
    }),
    Error,
    "At least one column is required"
  );
});

Deno.test("DDLEventHandler - apply DDL event", async () => {
  const handler = new DDLEventHandler();
  const executedQueries: string[] = [];
  
  const mockExecuteQuery = async (query: string) => {
    executedQueries.push(query);
    return {};
  };
  
  const event = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Product",
    columns: [
      { name: "id", type: "STRING" },
      { name: "price", type: "DOUBLE" }
    ],
    primaryKey: ["id"]
  });
  
  await handler.applyDDLEvent(event, mockExecuteQuery);
  
  assertEquals(executedQueries.length, 1);
  assertEquals(
    executedQueries[0],
    "CREATE NODE TABLE Product (id STRING, price DOUBLE, PRIMARY KEY (id))"
  );
  assertEquals(handler.isDDLApplied(event.id), true);
  assertEquals(handler.getSchemaVersion(), 1);
});

Deno.test("DDLEventHandler - dependency check", async () => {
  const handler = new DDLEventHandler();
  const mockExecuteQuery = async (_: string) => ({});
  
  const event = handler.createDDLEvent(
    "CREATE_EDGE_TABLE",
    {
      tableName: "LIKES",
      fromTable: "User",
      toTable: "Post"
    },
    ["ddl_missing_dependency"]
  );
  
  // Use assertRejects for async functions
  await assertRejects(
    async () => await handler.applyDDLEvent(event, mockExecuteQuery),
    Error,
    "Dependency not satisfied"
  );
});

Deno.test("DDLEventHandler - schema version tracking", async () => {
  const handler = new DDLEventHandler();
  const mockExecuteQuery = async (_: string) => ({});
  
  assertEquals(handler.getSchemaVersion(), 0);
  
  // Apply schema-modifying operation
  const createTable = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Test",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  await handler.applyDDLEvent(createTable, mockExecuteQuery);
  assertEquals(handler.getSchemaVersion(), 1);
  
  // Apply another schema-modifying operation
  const addColumn = handler.createDDLEvent("ADD_COLUMN", {
    tableName: "Test",
    columnName: "name",
    dataType: "STRING"
  });
  await handler.applyDDLEvent(addColumn, mockExecuteQuery);
  assertEquals(handler.getSchemaVersion(), 2);
  
  // Apply non-schema-modifying operation (comment)
  const addComment = handler.createDDLEvent("COMMENT_ON_TABLE", {
    tableName: "Test",
    comment: "Test table"
  });
  await handler.applyDDLEvent(addComment, mockExecuteQuery);
  assertEquals(handler.getSchemaVersion(), 2); // Should not increment
});

Deno.test("ExtendedTemplateRegistry - has both DDL and DML templates", () => {
  const registry = new ExtendedTemplateRegistry();
  
  // Check DML templates
  assertEquals(registry.hasTemplate("CREATE_USER"), true);
  assertEquals(registry.hasTemplate("INCREMENT_COUNTER"), true);
  assertEquals(registry.isDMLTemplate("CREATE_USER"), true);
  
  // Check DDL templates
  assertEquals(registry.hasTemplate("CREATE_NODE_TABLE"), true);
  assertEquals(registry.hasTemplate("ALTER_TABLE_ADD_COLUMN"), true);
  assertEquals(registry.isDDLTemplate("CREATE_NODE_TABLE"), true);
  
  // Check non-existent template
  assertEquals(registry.hasTemplate("UNKNOWN_TEMPLATE"), false);
});

Deno.test("ExtendedTemplateRegistry - get template metadata", () => {
  const registry = new ExtendedTemplateRegistry();
  
  // Get DML metadata
  const dmlMeta = registry.getTemplateMetadata("CREATE_USER");
  assertEquals(dmlMeta.requiredParams, ["id", "name"]);
  assertEquals(dmlMeta.impact, "CREATE_NODE");
  
  // Get DDL metadata
  const ddlMeta = registry.getTemplateMetadata("CREATE_NODE_TABLE");
  assertEquals(ddlMeta.requiredParams, ["tableName", "columns", "primaryKey"]);
  assertEquals(ddlMeta.impact, "CREATE_SCHEMA");
  
  // Get unknown template
  assertThrows(
    () => registry.getTemplateMetadata("UNKNOWN"),
    Error,
    "Unknown template"
  );
});

Deno.test("createUnifiedEvent - creates DML event", () => {
  const event = createUnifiedEvent("CREATE_USER", {
    id: "user123",
    name: "Alice"
  });
  
  assertEquals(isDDLEvent(event), false);
  assertEquals(event.template, "CREATE_USER");
  assertEquals(event.params.id, "user123");
});

Deno.test("createUnifiedEvent - creates DDL event", () => {
  const event = createUnifiedEvent("CREATE_NODE_TABLE", {
    tableName: "Category",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" }
    ],
    primaryKey: ["id"]
  });
  
  assertEquals(isDDLEvent(event), true);
  assertEquals(event.template, "CREATE_NODE_TABLE");
  if (isDDLEvent(event)) {
    assertEquals(event.type, "DDL");
    assertEquals(event.payload?.ddlType, "CREATE_NODE_TABLE");
    assertEquals(
      event.payload?.query,
      "CREATE NODE TABLE Category (id STRING, name STRING, PRIMARY KEY (id))"
    );
  }
});

Deno.test("DDLEventHandler - get DDL query", () => {
  const handler = new DDLEventHandler();
  
  const query = handler.getDDLQuery("ALTER_TABLE_ADD_COLUMN", {
    tableName: "User",
    columnName: "email",
    dataType: "STRING",
    nullable: false,
    defaultValue: ""
  });
  
  assertEquals(query, "ALTER TABLE User ADD email STRING NOT NULL DEFAULT ''");
});

Deno.test("DDLEventHandler - check if template is DDL", () => {
  const handler = new DDLEventHandler();
  
  assertEquals(handler.isDDLTemplate("CREATE_NODE_TABLE"), true);
  assertEquals(handler.isDDLTemplate("DROP_INDEX"), true);
  assertEquals(handler.isDDLTemplate("CREATE_USER"), false);
  assertEquals(handler.isDDLTemplate("UNKNOWN"), false);
});

Deno.test("DDLEventHandler - reset state", async () => {
  const handler = new DDLEventHandler();
  const mockExecuteQuery = async (_: string) => ({});
  
  // Apply some events
  const event1 = handler.createDDLEvent("CREATE_NODE_TABLE", {
    tableName: "Test1",
    columns: [{ name: "id", type: "STRING" }],
    primaryKey: ["id"]
  });
  await handler.applyDDLEvent(event1, mockExecuteQuery);
  
  assertEquals(handler.getSchemaVersion(), 1);
  assertEquals(handler.getAppliedDDLs().length, 1);
  
  // Reset
  handler.reset();
  
  assertEquals(handler.getSchemaVersion(), 0);
  assertEquals(handler.getAppliedDDLs().length, 0);
  assertEquals(handler.isDDLApplied(event1.id), false);
});