/**
 * DDL Template Definitions for Event Sourcing
 * DDL操作のためのテンプレート定義
 */

import type {
  DDLOperationType,
  DDLTemplateMetadata,
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
  KuzuDataType,
} from "./ddl_types.ts";

// ========== Template Query Generators ==========

/**
 * Generate CREATE NODE TABLE query
 * ノードテーブル作成クエリの生成
 */
export function generateCreateNodeTableQuery(params: CreateNodeTableParams): string {
  const ifNotExists = params.ifNotExists ? "IF NOT EXISTS " : "";
  
  // Build column definitions
  const columnDefs = params.columns.map(col => {
    let def = `${col.name} ${col.type}`;
    
    // Handle nullable (KuzuDB columns are nullable by default)
    if (col.nullable === false) {
      def += " NOT NULL";
    }
    
    // Handle default value
    if (col.defaultValue !== undefined) {
      if (typeof col.defaultValue === "string") {
        def += ` DEFAULT '${col.defaultValue}'`;
      } else {
        def += ` DEFAULT ${col.defaultValue}`;
      }
    }
    
    return def;
  }).join(", ");
  
  // Build primary key constraint
  const primaryKeyDef = params.primaryKey.length > 0 
    ? `, PRIMARY KEY (${params.primaryKey.join(", ")})`
    : "";
  
  return `CREATE NODE TABLE ${ifNotExists}${params.tableName} (${columnDefs}${primaryKeyDef})`;
}

/**
 * Generate CREATE REL TABLE query (edge table)
 * エッジテーブル作成クエリの生成
 */
export function generateCreateEdgeTableQuery(params: CreateEdgeTableParams): string {
  const ifNotExists = params.ifNotExists ? "IF NOT EXISTS " : "";
  
  // Base definition with FROM and TO
  let query = `CREATE REL TABLE ${ifNotExists}${params.tableName} (FROM ${params.fromTable} TO ${params.toTable}`;
  
  // Add columns if specified
  if (params.columns && params.columns.length > 0) {
    const columnDefs = params.columns.map(col => {
      let def = `${col.name} ${col.type}`;
      
      if (col.nullable === false) {
        def += " NOT NULL";
      }
      
      if (col.defaultValue !== undefined) {
        if (typeof col.defaultValue === "string") {
          def += ` DEFAULT '${col.defaultValue}'`;
        } else {
          def += ` DEFAULT ${col.defaultValue}`;
        }
      }
      
      return def;
    }).join(", ");
    
    query += `, ${columnDefs}`;
  }
  
  query += ")";
  return query;
}

/**
 * Generate ALTER TABLE ADD COLUMN query
 * カラム追加クエリの生成
 */
export function generateAddColumnQuery(params: AddColumnParams): string {
  let query = `ALTER TABLE ${params.tableName} ADD `;
  
  if (params.ifNotExists) {
    query += "IF NOT EXISTS ";
  }
  
  query += `${params.columnName} ${params.dataType}`;
  
  if (params.nullable === false) {
    query += " NOT NULL";
  }
  
  if (params.defaultValue !== undefined) {
    if (typeof params.defaultValue === "string") {
      query += ` DEFAULT '${params.defaultValue}'`;
    } else {
      query += ` DEFAULT ${params.defaultValue}`;
    }
  }
  
  return query;
}

/**
 * Generate ALTER TABLE DROP COLUMN query
 * カラム削除クエリの生成
 */
export function generateDropColumnQuery(params: DropColumnParams): string {
  let query = `ALTER TABLE ${params.tableName} DROP `;
  
  if (params.ifExists) {
    query += "IF EXISTS ";
  }
  
  query += params.columnName;
  
  if (params.cascade) {
    query += " CASCADE";
  }
  
  return query;
}

/**
 * Generate ALTER TABLE RENAME COLUMN query
 * カラム名変更クエリの生成
 */
export function generateRenameColumnQuery(params: RenameColumnParams): string {
  return `ALTER TABLE ${params.tableName} RENAME ${params.oldColumnName} TO ${params.newColumnName}`;
}

/**
 * Generate ALTER TABLE RENAME TO query
 * テーブル名変更クエリの生成
 */
export function generateRenameTableQuery(params: RenameTableParams): string {
  return `ALTER TABLE ${params.oldTableName} RENAME TO ${params.newTableName}`;
}

/**
 * Generate DROP TABLE query
 * テーブル削除クエリの生成
 */
export function generateDropTableQuery(params: DropTableParams): string {
  let query = "DROP TABLE ";
  
  if (params.ifExists) {
    query += "IF EXISTS ";
  }
  
  query += params.tableName;
  
  if (params.cascade) {
    query += " CASCADE";
  }
  
  return query;
}

/**
 * Generate CREATE INDEX query
 * インデックス作成クエリの生成
 */
export function generateCreateIndexQuery(params: CreateIndexParams): string {
  let query = "CREATE ";
  
  if (params.unique) {
    query += "UNIQUE ";
  }
  
  query += "INDEX ";
  
  if (params.ifNotExists) {
    query += "IF NOT EXISTS ";
  }
  
  query += `${params.indexName} ON ${params.tableName} (${params.columns.join(", ")})`;
  
  return query;
}

/**
 * Generate DROP INDEX query
 * インデックス削除クエリの生成
 */
export function generateDropIndexQuery(params: DropIndexParams): string {
  let query = "DROP INDEX ";
  
  if (params.ifExists) {
    query += "IF EXISTS ";
  }
  
  query += params.indexName;
  
  return query;
}

/**
 * Generate COMMENT ON query
 * コメント設定クエリの生成
 */
export function generateCommentQuery(params: CommentParams): string {
  const target = params.targetType === "TABLE" 
    ? params.tableName 
    : `${params.tableName}.${params.columnName}`;
  
  const comment = params.comment === null 
    ? "NULL" 
    : `'${params.comment.replace(/'/g, "''")}'`;
  
  return `COMMENT ON ${params.targetType} ${target} IS ${comment}`;
}

// ========== Validation Functions ==========

/**
 * Validate table name
 * テーブル名の検証
 */
export function validateTableName(name: string): void {
  if (!name || name.trim() === "") {
    throw new Error("Table name cannot be empty");
  }
  
  // Check for valid identifier (alphanumeric and underscore)
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
    throw new Error(`Invalid table name: ${name}. Must start with letter or underscore and contain only alphanumeric characters and underscores`);
  }
  
  // Check for reserved words (simplified list)
  const reservedWords = ["CREATE", "DROP", "ALTER", "TABLE", "INDEX", "FROM", "TO", "WHERE", "MATCH", "RETURN"];
  if (reservedWords.includes(name.toUpperCase())) {
    throw new Error(`Table name cannot be a reserved word: ${name}`);
  }
}

/**
 * Validate column name
 * カラム名の検証
 */
export function validateColumnName(name: string): void {
  if (!name || name.trim() === "") {
    throw new Error("Column name cannot be empty");
  }
  
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) {
    throw new Error(`Invalid column name: ${name}. Must start with letter or underscore and contain only alphanumeric characters and underscores`);
  }
}

/**
 * Validate data type
 * データ型の検証
 */
export function validateDataType(type: string): void {
  const validTypes: KuzuDataType[] = [
    "BOOL", "INT8", "INT16", "INT32", "INT64",
    "UINT8", "UINT16", "UINT32", "UINT64",
    "FLOAT", "DOUBLE", "STRING", "DATE", "TIMESTAMP",
    "INTERVAL", "LIST", "STRUCT", "MAP", "UNION", "NODE", "REL"
  ];
  
  if (!validTypes.includes(type as KuzuDataType)) {
    throw new Error(`Invalid data type: ${type}. Valid types are: ${validTypes.join(", ")}`);
  }
}

/**
 * Validate DDL parameters based on operation type
 * DDL操作タイプに基づくパラメータの検証
 */
export function validateDDLParams(ddlType: DDLOperationType, params: any): void {
  switch (ddlType) {
    case "CREATE_NODE_TABLE":
    case "CREATE_TABLE":
      validateCreateNodeTableParams(params);
      break;
      
    case "CREATE_EDGE_TABLE":
      validateCreateEdgeTableParams(params);
      break;
      
    case "ADD_COLUMN":
    case "ALTER_TABLE_ADD_COLUMN":
      validateAddColumnParams(params);
      break;
      
    case "DROP_COLUMN":
    case "ALTER_TABLE_DROP_COLUMN":
      validateDropColumnParams(params);
      break;
      
    case "RENAME_COLUMN":
      validateRenameColumnParams(params);
      break;
      
    case "RENAME_TABLE":
      validateRenameTableParams(params);
      break;
      
    case "DROP_NODE_TABLE":
    case "DROP_TABLE":
    case "DROP_EDGE_TABLE":
      validateDropTableParams(params);
      break;
      
    case "CREATE_INDEX":
      validateCreateIndexParams(params);
      break;
      
    case "DROP_INDEX":
      validateDropIndexParams(params);
      break;
      
    case "COMMENT_ON_TABLE":
    case "COMMENT_ON_COLUMN":
      validateCommentParams(params);
      break;
      
    default:
      throw new Error(`Unknown DDL operation type: ${ddlType}`);
  }
}

function validateCreateNodeTableParams(params: CreateNodeTableParams): void {
  validateTableName(params.tableName);
  
  if (!params.columns || params.columns.length === 0) {
    throw new Error("At least one column is required");
  }
  
  params.columns.forEach(col => {
    validateColumnName(col.name);
    validateDataType(col.type);
  });
  
  if (!params.primaryKey || params.primaryKey.length === 0) {
    throw new Error("Primary key is required for node tables");
  }
  
  // Verify primary key columns exist
  const columnNames = params.columns.map(c => c.name);
  params.primaryKey.forEach(pk => {
    if (!columnNames.includes(pk)) {
      throw new Error(`Primary key column not found in column list: ${pk}`);
    }
  });
}

function validateCreateEdgeTableParams(params: CreateEdgeTableParams): void {
  validateTableName(params.tableName);
  validateTableName(params.fromTable);
  validateTableName(params.toTable);
  
  if (params.columns) {
    params.columns.forEach(col => {
      validateColumnName(col.name);
      validateDataType(col.type);
    });
  }
}

function validateAddColumnParams(params: AddColumnParams): void {
  validateTableName(params.tableName);
  validateColumnName(params.columnName);
  validateDataType(params.dataType);
}

function validateDropColumnParams(params: DropColumnParams): void {
  validateTableName(params.tableName);
  validateColumnName(params.columnName);
}

function validateRenameColumnParams(params: RenameColumnParams): void {
  validateTableName(params.tableName);
  validateColumnName(params.oldColumnName);
  validateColumnName(params.newColumnName);
}

function validateRenameTableParams(params: RenameTableParams): void {
  validateTableName(params.oldTableName);
  validateTableName(params.newTableName);
}

function validateDropTableParams(params: DropTableParams): void {
  validateTableName(params.tableName);
}

function validateCreateIndexParams(params: CreateIndexParams): void {
  validateTableName(params.tableName);
  validateColumnName(params.indexName);
  
  if (!params.columns || params.columns.length === 0) {
    throw new Error("At least one column is required for index");
  }
  
  params.columns.forEach(col => validateColumnName(col));
}

function validateDropIndexParams(params: DropIndexParams): void {
  validateColumnName(params.indexName);
}

function validateCommentParams(params: CommentParams): void {
  validateTableName(params.tableName);
  
  if (params.targetType === "COLUMN" && !params.columnName) {
    throw new Error("Column name is required for COMMENT ON COLUMN");
  }
  
  if (params.columnName) {
    validateColumnName(params.columnName);
  }
}

// ========== Template Registry ==========

/**
 * DDL Template Registry
 * DDLテンプレートのレジストリ
 */
export class DDLTemplateRegistry {
  private templates: Map<DDLOperationType, DDLTemplateMetadata> = new Map();
  
  constructor() {
    this.registerDefaultTemplates();
  }
  
  /**
   * Register default DDL templates
   * デフォルトDDLテンプレートの登録
   */
  private registerDefaultTemplates(): void {
    // Node table operations
    this.registerTemplate("CREATE_NODE_TABLE", {
      requiredParams: ["tableName", "columns", "primaryKey"],
      paramTypes: {
        tableName: "string",
        columns: "array",
        primaryKey: "array",
        ifNotExists: "boolean"
      },
      impact: "CREATE_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 100
    });
    
    this.registerTemplate("CREATE_TABLE", {
      requiredParams: ["tableName", "columns", "primaryKey"],
      paramTypes: {
        tableName: "string",
        columns: "array",
        primaryKey: "array",
        ifNotExists: "boolean"
      },
      impact: "CREATE_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 100
    });
    
    // Edge table operations
    this.registerTemplate("CREATE_EDGE_TABLE", {
      requiredParams: ["tableName", "fromTable", "toTable"],
      paramTypes: {
        tableName: "string",
        fromTable: "string",
        toTable: "string",
        columns: "array",
        ifNotExists: "boolean"
      },
      impact: "CREATE_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 100
    });
    
    // Column operations
    this.registerTemplate("ADD_COLUMN", {
      requiredParams: ["tableName", "columnName", "dataType"],
      paramTypes: {
        tableName: "string",
        columnName: "string",
        dataType: "string",
        nullable: "boolean",
        defaultValue: "any",
        ifNotExists: "boolean"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 50
    });
    
    this.registerTemplate("ALTER_TABLE_ADD_COLUMN", {
      requiredParams: ["tableName", "columnName", "dataType"],
      paramTypes: {
        tableName: "string",
        columnName: "string",
        dataType: "string",
        nullable: "boolean",
        defaultValue: "any",
        ifNotExists: "boolean"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 50
    });
    
    this.registerTemplate("DROP_COLUMN", {
      requiredParams: ["tableName", "columnName"],
      paramTypes: {
        tableName: "string",
        columnName: "string",
        ifExists: "boolean",
        cascade: "boolean"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 50
    });
    
    this.registerTemplate("ALTER_TABLE_DROP_COLUMN", {
      requiredParams: ["tableName", "columnName"],
      paramTypes: {
        tableName: "string",
        columnName: "string",
        ifExists: "boolean",
        cascade: "boolean"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 50
    });
    
    this.registerTemplate("RENAME_COLUMN", {
      requiredParams: ["tableName", "oldColumnName", "newColumnName"],
      paramTypes: {
        tableName: "string",
        oldColumnName: "string",
        newColumnName: "string"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: false,
      estimatedDuration: 10
    });
    
    // Table operations
    this.registerTemplate("RENAME_TABLE", {
      requiredParams: ["oldTableName", "newTableName"],
      paramTypes: {
        oldTableName: "string",
        newTableName: "string"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: false,
      estimatedDuration: 10
    });
    
    this.registerTemplate("DROP_NODE_TABLE", {
      requiredParams: ["tableName"],
      paramTypes: {
        tableName: "string",
        ifExists: "boolean",
        cascade: "boolean"
      },
      impact: "DROP_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 100
    });
    
    this.registerTemplate("DROP_TABLE", {
      requiredParams: ["tableName"],
      paramTypes: {
        tableName: "string",
        ifExists: "boolean",
        cascade: "boolean"
      },
      impact: "DROP_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 100
    });
    
    this.registerTemplate("DROP_EDGE_TABLE", {
      requiredParams: ["tableName"],
      paramTypes: {
        tableName: "string",
        ifExists: "boolean",
        cascade: "boolean"
      },
      impact: "DROP_SCHEMA",
      requiresExclusiveLock: true,
      estimatedDuration: 100
    });
    
    // Index operations
    this.registerTemplate("CREATE_INDEX", {
      requiredParams: ["indexName", "tableName", "columns"],
      paramTypes: {
        indexName: "string",
        tableName: "string",
        columns: "array",
        unique: "boolean",
        ifNotExists: "boolean"
      },
      impact: "CREATE_INDEX",
      requiresExclusiveLock: false,
      estimatedDuration: 500
    });
    
    this.registerTemplate("DROP_INDEX", {
      requiredParams: ["indexName"],
      paramTypes: {
        indexName: "string",
        ifExists: "boolean"
      },
      impact: "DROP_INDEX",
      requiresExclusiveLock: false,
      estimatedDuration: 50
    });
    
    // Comment operations
    this.registerTemplate("COMMENT_ON_TABLE", {
      requiredParams: ["tableName", "comment"],
      paramTypes: {
        tableName: "string",
        comment: "string"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: false,
      estimatedDuration: 10
    });
    
    this.registerTemplate("COMMENT_ON_COLUMN", {
      requiredParams: ["tableName", "columnName", "comment"],
      paramTypes: {
        tableName: "string",
        columnName: "string",
        comment: "string"
      },
      impact: "ALTER_SCHEMA",
      requiresExclusiveLock: false,
      estimatedDuration: 10
    });
  }
  
  /**
   * Register a DDL template
   * DDLテンプレートの登録
   */
  registerTemplate(ddlType: DDLOperationType, metadata: DDLTemplateMetadata): void {
    this.templates.set(ddlType, metadata);
  }
  
  /**
   * Get template metadata
   * テンプレートメタデータの取得
   */
  getTemplateMetadata(ddlType: DDLOperationType): DDLTemplateMetadata {
    const metadata = this.templates.get(ddlType);
    if (!metadata) {
      throw new Error(`DDL template not found: ${ddlType}`);
    }
    return metadata;
  }
  
  /**
   * Check if template exists
   * テンプレートの存在確認
   */
  hasTemplate(ddlType: DDLOperationType): boolean {
    return this.templates.has(ddlType);
  }
  
  /**
   * Get all registered templates
   * 登録済みテンプレートの取得
   */
  getAllTemplates(): Map<DDLOperationType, DDLTemplateMetadata> {
    return new Map(this.templates);
  }
}

// ========== DDL Query Builder ==========

/**
 * Build DDL query from operation type and parameters
 * DDL操作タイプとパラメータからクエリを構築
 */
export function buildDDLQuery(ddlType: DDLOperationType, params: any): string {
  // Validate parameters first
  validateDDLParams(ddlType, params);
  
  switch (ddlType) {
    case "CREATE_NODE_TABLE":
    case "CREATE_TABLE":
      return generateCreateNodeTableQuery(params as CreateNodeTableParams);
      
    case "CREATE_EDGE_TABLE":
      return generateCreateEdgeTableQuery(params as CreateEdgeTableParams);
      
    case "ADD_COLUMN":
    case "ALTER_TABLE_ADD_COLUMN":
      return generateAddColumnQuery(params as AddColumnParams);
      
    case "DROP_COLUMN":
    case "ALTER_TABLE_DROP_COLUMN":
      return generateDropColumnQuery(params as DropColumnParams);
      
    case "RENAME_COLUMN":
      return generateRenameColumnQuery(params as RenameColumnParams);
      
    case "RENAME_TABLE":
      return generateRenameTableQuery(params as RenameTableParams);
      
    case "DROP_NODE_TABLE":
    case "DROP_TABLE":
    case "DROP_EDGE_TABLE":
      return generateDropTableQuery(params as DropTableParams);
      
    case "CREATE_INDEX":
      return generateCreateIndexQuery(params as CreateIndexParams);
      
    case "DROP_INDEX":
      return generateDropIndexQuery(params as DropIndexParams);
      
    case "COMMENT_ON_TABLE":
      return generateCommentQuery({
        ...params,
        targetType: "TABLE"
      } as CommentParams);
      
    case "COMMENT_ON_COLUMN":
      return generateCommentQuery({
        ...params,
        targetType: "COLUMN"
      } as CommentParams);
      
    default:
      throw new Error(`Unknown DDL operation type: ${ddlType}`);
  }
}

// ========== Exports ==========

export {
  type DDLOperationType,
  type DDLTemplateMetadata,
  type CreateNodeTableParams,
  type CreateEdgeTableParams,
  type AddColumnParams,
  type DropColumnParams,
  type RenameColumnParams,
  type RenameTableParams,
  type DropTableParams,
  type CreateIndexParams,
  type DropIndexParams,
  type CommentParams,
  type KuzuDataType,
};