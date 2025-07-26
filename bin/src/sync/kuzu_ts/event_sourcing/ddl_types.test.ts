/**
 * Tests for DDL Types
 * DDL型定義のテスト
 */

import { assertEquals, assert } from "https://deno.land/std@0.208.0/assert/mod.ts";
import {
  DDLTemplateEvent,
  DDLOperationType,
  isDDLEvent,
  isSchemaModifyingOperation,
  CreateNodeTableParams,
  AddColumnParams,
  SchemaVersion,
  SchemaState,
} from "./ddl_types.ts";
import { TemplateEvent } from "./types.ts";

Deno.test("DDL Types - Type Guards", async (t) => {
  await t.step("isDDLEvent should correctly identify DDL events", () => {
    const dmlEvent: TemplateEvent = {
      id: "dml-1",
      template: "create_user",
      params: { name: "Alice" },
      timestamp: Date.now(),
    };

    const ddlEvent: DDLTemplateEvent = {
      id: "ddl-1",
      type: "DDL",
      template: "create_table",
      params: {},
      timestamp: Date.now(),
      dependsOn: [],
      payload: {
        ddlType: "CREATE_NODE_TABLE",
        query: "CREATE NODE TABLE User (id STRING, PRIMARY KEY(id))",
      },
    };

    assert(!isDDLEvent(dmlEvent));
    assert(isDDLEvent(ddlEvent));
  });

  await t.step("isSchemaModifyingOperation should identify schema-changing operations", () => {
    const modifyingOps: DDLOperationType[] = [
      "CREATE_NODE_TABLE",
      "DROP_TABLE",
      "ADD_COLUMN",
      "RENAME_TABLE",
    ];

    const nonModifyingOps: DDLOperationType[] = [
      "COMMENT_ON_TABLE",
      "CREATE_INDEX",
      "DROP_INDEX",
    ];

    modifyingOps.forEach(op => {
      assert(isSchemaModifyingOperation(op), `${op} should be schema-modifying`);
    });

    nonModifyingOps.forEach(op => {
      assert(!isSchemaModifyingOperation(op), `${op} should not be schema-modifying`);
    });
  });
});

Deno.test("DDL Types - Event Creation", async (t) => {
  await t.step("should create valid CREATE_NODE_TABLE event", () => {
    const params: CreateNodeTableParams = {
      tableName: "User",
      columns: [
        { name: "id", type: "STRING", nullable: false },
        { name: "name", type: "STRING", nullable: true },
        { name: "age", type: "INT64", nullable: true, defaultValue: 0 },
      ],
      primaryKey: ["id"],
      ifNotExists: true,
    };

    const event: DDLTemplateEvent = {
      id: "create-user-table",
      type: "DDL",
      template: "create_node_table",
      params,
      timestamp: Date.now(),
      dependsOn: [],
      payload: {
        ddlType: "CREATE_NODE_TABLE",
        query: "CREATE NODE TABLE IF NOT EXISTS User (id STRING, name STRING, age INT64 DEFAULT 0, PRIMARY KEY(id))",
        metadata: {
          ifNotExists: true,
        },
      },
    };

    assertEquals(event.type, "DDL");
    assertEquals(event.payload?.ddlType, "CREATE_NODE_TABLE");
    assert(event.dependsOn.length === 0);
  });

  await t.step("should create valid ADD_COLUMN event with dependencies", () => {
    const params: AddColumnParams = {
      tableName: "User",
      columnName: "email",
      dataType: "STRING",
      nullable: true,
      ifNotExists: true,
    };

    const event: DDLTemplateEvent = {
      id: "add-email-column",
      type: "DDL",
      template: "add_column",
      params,
      timestamp: Date.now(),
      dependsOn: ["create-user-table"],
      payload: {
        ddlType: "ADD_COLUMN",
        query: "ALTER TABLE User ADD IF NOT EXISTS email STRING",
        metadata: {
          ifNotExists: true,
        },
      },
    };

    assertEquals(event.dependsOn, ["create-user-table"]);
    assertEquals(event.payload?.ddlType, "ADD_COLUMN");
  });
});

Deno.test("DDL Types - Schema Version Tracking", async (t) => {
  await t.step("should create valid schema version", () => {
    const schemaState: SchemaState = {
      nodeTables: {
        User: {
          name: "User",
          columns: {
            id: { name: "id", type: "STRING", nullable: false },
            name: { name: "name", type: "STRING", nullable: true },
            email: { name: "email", type: "STRING", nullable: true },
          },
          primaryKey: ["id"],
        },
      },
      edgeTables: {},
      indexes: {},
    };

    const schemaVersion: SchemaVersion = {
      version: 1,
      timestamp: Date.now(),
      appliedEvents: ["create-user-table", "add-email-column"],
      schema: schemaState,
    };

    assertEquals(schemaVersion.version, 1);
    assertEquals(schemaVersion.appliedEvents.length, 2);
    assertEquals(Object.keys(schemaVersion.schema.nodeTables).length, 1);
    assert("User" in schemaVersion.schema.nodeTables);
  });
});

Deno.test("DDL Types - Complex DDL Operations", async (t) => {
  await t.step("should handle table rename operation", () => {
    const event: DDLTemplateEvent = {
      id: "rename-user-to-account",
      type: "DDL",
      template: "rename_table",
      params: {
        oldTableName: "User",
        newTableName: "Account",
      },
      timestamp: Date.now(),
      dependsOn: ["create-user-table"],
      payload: {
        ddlType: "RENAME_TABLE",
        query: "ALTER TABLE User RENAME TO Account",
      },
    };

    assertEquals(event.payload?.ddlType, "RENAME_TABLE");
    assert(event.dependsOn.includes("create-user-table"));
  });

  await t.step("should handle edge table creation", () => {
    const event: DDLTemplateEvent = {
      id: "create-follows-edge",
      type: "DDL",
      template: "create_edge_table",
      params: {
        tableName: "Follows",
        fromTable: "User",
        toTable: "User",
        columns: [
          { name: "since", type: "TIMESTAMP", nullable: false },
        ],
      },
      timestamp: Date.now(),
      dependsOn: ["create-user-table"],
      payload: {
        ddlType: "CREATE_EDGE_TABLE",
        query: "CREATE REL TABLE Follows (FROM User TO User, since TIMESTAMP)",
      },
    };

    assertEquals(event.payload?.ddlType, "CREATE_EDGE_TABLE");
  });
});

Deno.test("DDL Types - Migration Events", async (t) => {
  await t.step("should create schema migration event", () => {
    const migrationEvent: DDLTemplateEvent = {
      id: "migration-v1-to-v2",
      type: "DDL",
      template: "schema_migration",
      params: {},
      timestamp: Date.now(),
      dependsOn: [],
      payload: {
        ddlType: "CREATE_NODE_TABLE",
        query: "CREATE NODE TABLE Product (id STRING, name STRING, price DOUBLE, PRIMARY KEY(id))",
        metadata: {
          comment: "Add Product table for e-commerce features",
        },
      },
    };

    // Type assertion to access migration-specific properties
    const migration = migrationEvent as any;
    migration.migrationVersion = "v2";
    migration.description = "Add Product table for e-commerce features";
    migration.reversible = true;
    migration.rollbackDDL = "DROP TABLE Product";

    assertEquals(migration.migrationVersion, "v2");
    assert(migration.reversible);
  });
});