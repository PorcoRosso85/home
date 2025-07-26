/**
 * DDL Templates Test Suite
 * DDLテンプレートのテストスイート
 */

import { assertEquals, assertThrows } from "jsr:@std/assert@^1.0.0";
import {
  generateCreateNodeTableQuery,
  generateCreateEdgeTableQuery,
  generateAddColumnQuery,
  generateDropColumnQuery,
  generateRenameColumnQuery,
  generateRenameTableQuery,
  generateDropTableQuery,
  generateCreateIndexQuery,
  generateDropIndexQuery,
  generateCommentQuery,
  validateTableName,
  validateColumnName,
  validateDataType,
  validateDDLParams,
  buildDDLQuery,
  DDLTemplateRegistry,
} from "./ddl_templates.ts";
import type {
  CreateNodeTableParams,
  CreateEdgeTableParams,
  AddColumnParams,
  DropColumnParams,
  RenameColumnParams,
  RenameTableParams,
  DropTableParams,
  CreateIndexParams,
  DropIndexParams,
  CommentParams,
} from "./ddl_types.ts";

// ========== Query Generation Tests ==========

Deno.test("generateCreateNodeTableQuery - basic table", () => {
  const params: CreateNodeTableParams = {
    tableName: "User",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING" },
      { name: "age", type: "INT32" }
    ],
    primaryKey: ["id"]
  };
  
  const query = generateCreateNodeTableQuery(params);
  assertEquals(query, "CREATE NODE TABLE User (id STRING, name STRING, age INT32, PRIMARY KEY (id))");
});

Deno.test("generateCreateNodeTableQuery - with IF NOT EXISTS", () => {
  const params: CreateNodeTableParams = {
    tableName: "Product",
    columns: [
      { name: "id", type: "STRING" },
      { name: "price", type: "DOUBLE" }
    ],
    primaryKey: ["id"],
    ifNotExists: true
  };
  
  const query = generateCreateNodeTableQuery(params);
  assertEquals(query, "CREATE NODE TABLE IF NOT EXISTS Product (id STRING, price DOUBLE, PRIMARY KEY (id))");
});

Deno.test("generateCreateNodeTableQuery - with nullable and default values", () => {
  const params: CreateNodeTableParams = {
    tableName: "Article",
    columns: [
      { name: "id", type: "STRING", nullable: false },
      { name: "title", type: "STRING", nullable: false },
      { name: "views", type: "INT64", defaultValue: 0 },
      { name: "published", type: "BOOL", defaultValue: false }
    ],
    primaryKey: ["id"]
  };
  
  const query = generateCreateNodeTableQuery(params);
  assertEquals(
    query,
    "CREATE NODE TABLE Article (id STRING NOT NULL, title STRING NOT NULL, views INT64 DEFAULT 0, published BOOL DEFAULT false, PRIMARY KEY (id))"
  );
});

Deno.test("generateCreateEdgeTableQuery - basic edge table", () => {
  const params: CreateEdgeTableParams = {
    tableName: "FOLLOWS",
    fromTable: "User",
    toTable: "User"
  };
  
  const query = generateCreateEdgeTableQuery(params);
  assertEquals(query, "CREATE REL TABLE FOLLOWS (FROM User TO User)");
});

Deno.test("generateCreateEdgeTableQuery - with properties", () => {
  const params: CreateEdgeTableParams = {
    tableName: "LIKES",
    fromTable: "User",
    toTable: "Post",
    columns: [
      { name: "timestamp", type: "TIMESTAMP" },
      { name: "reaction", type: "STRING", defaultValue: "like" }
    ]
  };
  
  const query = generateCreateEdgeTableQuery(params);
  assertEquals(query, "CREATE REL TABLE LIKES (FROM User TO Post, timestamp TIMESTAMP, reaction STRING DEFAULT 'like')");
});

Deno.test("generateAddColumnQuery - basic column", () => {
  const params: AddColumnParams = {
    tableName: "User",
    columnName: "email",
    dataType: "STRING"
  };
  
  const query = generateAddColumnQuery(params);
  assertEquals(query, "ALTER TABLE User ADD email STRING");
});

Deno.test("generateAddColumnQuery - with all options", () => {
  const params: AddColumnParams = {
    tableName: "Product",
    columnName: "stock",
    dataType: "INT32",
    nullable: false,
    defaultValue: 0,
    ifNotExists: true
  };
  
  const query = generateAddColumnQuery(params);
  assertEquals(query, "ALTER TABLE Product ADD IF NOT EXISTS stock INT32 NOT NULL DEFAULT 0");
});

Deno.test("generateDropColumnQuery - basic drop", () => {
  const params: DropColumnParams = {
    tableName: "User",
    columnName: "temp_field"
  };
  
  const query = generateDropColumnQuery(params);
  assertEquals(query, "ALTER TABLE User DROP temp_field");
});

Deno.test("generateDropColumnQuery - with cascade", () => {
  const params: DropColumnParams = {
    tableName: "Product",
    columnName: "deprecated_field",
    ifExists: true,
    cascade: true
  };
  
  const query = generateDropColumnQuery(params);
  assertEquals(query, "ALTER TABLE Product DROP IF EXISTS deprecated_field CASCADE");
});

Deno.test("generateRenameColumnQuery", () => {
  const params: RenameColumnParams = {
    tableName: "User",
    oldColumnName: "username",
    newColumnName: "display_name"
  };
  
  const query = generateRenameColumnQuery(params);
  assertEquals(query, "ALTER TABLE User RENAME username TO display_name");
});

Deno.test("generateRenameTableQuery", () => {
  const params: RenameTableParams = {
    oldTableName: "OldUser",
    newTableName: "User"
  };
  
  const query = generateRenameTableQuery(params);
  assertEquals(query, "ALTER TABLE OldUser RENAME TO User");
});

Deno.test("generateDropTableQuery", () => {
  const params: DropTableParams = {
    tableName: "TempTable",
    ifExists: true,
    cascade: true
  };
  
  const query = generateDropTableQuery(params);
  assertEquals(query, "DROP TABLE IF EXISTS TempTable CASCADE");
});

Deno.test("generateCreateIndexQuery", () => {
  const params: CreateIndexParams = {
    indexName: "idx_user_email",
    tableName: "User",
    columns: ["email"],
    unique: true,
    ifNotExists: true
  };
  
  const query = generateCreateIndexQuery(params);
  assertEquals(query, "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email ON User (email)");
});

Deno.test("generateDropIndexQuery", () => {
  const params: DropIndexParams = {
    indexName: "idx_old_index",
    ifExists: true
  };
  
  const query = generateDropIndexQuery(params);
  assertEquals(query, "DROP INDEX IF EXISTS idx_old_index");
});

Deno.test("generateCommentQuery - table comment", () => {
  const params: CommentParams = {
    targetType: "TABLE",
    tableName: "User",
    comment: "User information table"
  };
  
  const query = generateCommentQuery(params);
  assertEquals(query, "COMMENT ON TABLE User IS 'User information table'");
});

Deno.test("generateCommentQuery - column comment with quotes", () => {
  const params: CommentParams = {
    targetType: "COLUMN",
    tableName: "User",
    columnName: "email",
    comment: "User's email address"
  };
  
  const query = generateCommentQuery(params);
  assertEquals(query, "COMMENT ON COLUMN User.email IS 'User''s email address'");
});

Deno.test("generateCommentQuery - remove comment", () => {
  const params: CommentParams = {
    targetType: "TABLE",
    tableName: "TempTable",
    comment: null
  };
  
  const query = generateCommentQuery(params);
  assertEquals(query, "COMMENT ON TABLE TempTable IS NULL");
});

// ========== Validation Tests ==========

Deno.test("validateTableName - valid names", () => {
  validateTableName("User");
  validateTableName("user_profile");
  validateTableName("_temp_table");
  validateTableName("Table123");
});

Deno.test("validateTableName - invalid names", () => {
  assertThrows(() => validateTableName(""), Error, "Table name cannot be empty");
  assertThrows(() => validateTableName("123Table"), Error, "Invalid table name");
  assertThrows(() => validateTableName("user-profile"), Error, "Invalid table name");
  assertThrows(() => validateTableName("user profile"), Error, "Invalid table name");
  assertThrows(() => validateTableName("TABLE"), Error, "reserved word");
});

Deno.test("validateColumnName - valid names", () => {
  validateColumnName("id");
  validateColumnName("first_name");
  validateColumnName("_internal_id");
  validateColumnName("column123");
});

Deno.test("validateColumnName - invalid names", () => {
  assertThrows(() => validateColumnName(""), Error, "Column name cannot be empty");
  assertThrows(() => validateColumnName("123column"), Error, "Invalid column name");
  assertThrows(() => validateColumnName("column-name"), Error, "Invalid column name");
});

Deno.test("validateDataType - valid types", () => {
  validateDataType("STRING");
  validateDataType("INT32");
  validateDataType("DOUBLE");
  validateDataType("BOOL");
  validateDataType("TIMESTAMP");
});

Deno.test("validateDataType - invalid types", () => {
  assertThrows(() => validateDataType("VARCHAR"), Error, "Invalid data type");
  assertThrows(() => validateDataType("INTEGER"), Error, "Invalid data type");
  assertThrows(() => validateDataType(""), Error, "Invalid data type");
});

// ========== Integration Tests ==========

Deno.test("buildDDLQuery - CREATE_NODE_TABLE", () => {
  const params: CreateNodeTableParams = {
    tableName: "Customer",
    columns: [
      { name: "id", type: "STRING" },
      { name: "name", type: "STRING", nullable: false },
      { name: "balance", type: "DOUBLE", defaultValue: 0.0 }
    ],
    primaryKey: ["id"]
  };
  
  const query = buildDDLQuery("CREATE_NODE_TABLE", params);
  assertEquals(
    query,
    "CREATE NODE TABLE Customer (id STRING, name STRING NOT NULL, balance DOUBLE DEFAULT 0, PRIMARY KEY (id))"
  );
});

Deno.test("buildDDLQuery - validation errors", () => {
  // Missing required params
  assertThrows(
    () => buildDDLQuery("CREATE_NODE_TABLE", { tableName: "Test" }),
    Error,
    "At least one column is required"
  );
  
  // Invalid table name
  assertThrows(
    () => buildDDLQuery("CREATE_NODE_TABLE", {
      tableName: "Invalid Table",
      columns: [{ name: "id", type: "STRING" }],
      primaryKey: ["id"]
    }),
    Error,
    "Invalid table name"
  );
  
  // Invalid data type
  assertThrows(
    () => buildDDLQuery("CREATE_NODE_TABLE", {
      tableName: "Test",
      columns: [{ name: "id", type: "INVALID_TYPE" }],
      primaryKey: ["id"]
    }),
    Error,
    "Invalid data type"
  );
});

// ========== Template Registry Tests ==========

Deno.test("DDLTemplateRegistry - has default templates", () => {
  const registry = new DDLTemplateRegistry();
  
  // Check node table templates
  assertEquals(registry.hasTemplate("CREATE_NODE_TABLE"), true);
  assertEquals(registry.hasTemplate("CREATE_TABLE"), true);
  assertEquals(registry.hasTemplate("DROP_NODE_TABLE"), true);
  
  // Check edge table templates
  assertEquals(registry.hasTemplate("CREATE_EDGE_TABLE"), true);
  assertEquals(registry.hasTemplate("DROP_EDGE_TABLE"), true);
  
  // Check column templates
  assertEquals(registry.hasTemplate("ADD_COLUMN"), true);
  assertEquals(registry.hasTemplate("DROP_COLUMN"), true);
  assertEquals(registry.hasTemplate("RENAME_COLUMN"), true);
  
  // Check index templates
  assertEquals(registry.hasTemplate("CREATE_INDEX"), true);
  assertEquals(registry.hasTemplate("DROP_INDEX"), true);
});

Deno.test("DDLTemplateRegistry - get template metadata", () => {
  const registry = new DDLTemplateRegistry();
  
  const metadata = registry.getTemplateMetadata("CREATE_NODE_TABLE");
  assertEquals(metadata.requiredParams, ["tableName", "columns", "primaryKey"]);
  assertEquals(metadata.impact, "CREATE_SCHEMA");
  assertEquals(metadata.requiresExclusiveLock, true);
});

Deno.test("DDLTemplateRegistry - register custom template", () => {
  const registry = new DDLTemplateRegistry();
  
  // Initially doesn't have custom constraint operations
  assertThrows(
    () => registry.getTemplateMetadata("ADD_CONSTRAINT"),
    Error,
    "DDL template not found"
  );
  
  // Register custom template
  registry.registerTemplate("ADD_CONSTRAINT", {
    requiredParams: ["tableName", "constraintName", "constraintType"],
    paramTypes: {
      tableName: "string",
      constraintName: "string",
      constraintType: "string"
    },
    impact: "ALTER_SCHEMA",
    requiresExclusiveLock: true
  });
  
  // Now it should exist
  assertEquals(registry.hasTemplate("ADD_CONSTRAINT"), true);
  const metadata = registry.getTemplateMetadata("ADD_CONSTRAINT");
  assertEquals(metadata.requiredParams, ["tableName", "constraintName", "constraintType"]);
});

Deno.test("DDLTemplateRegistry - get all templates", () => {
  const registry = new DDLTemplateRegistry();
  const allTemplates = registry.getAllTemplates();
  
  // Should have all default templates
  assertEquals(allTemplates.size >= 15, true); // At least 15 default templates
  assertEquals(allTemplates.has("CREATE_NODE_TABLE"), true);
  assertEquals(allTemplates.has("CREATE_INDEX"), true);
});