/**
 * DDL Event Handler for Event Sourcing
 * DDLイベントハンドラー - イベントソーシングとの統合
 */

import { TemplateEvent } from "./types.ts";
import { 
  DDLTemplateEvent, 
  DDLOperationType, 
  isDDLEvent,
  isSchemaModifyingOperation 
} from "./ddl_types.ts";
import { 
  buildDDLQuery, 
  DDLTemplateRegistry, 
  validateDDLParams 
} from "./ddl_templates.ts";

/**
 * DDL Event Handler class
 * DDLイベントを処理するクラス
 */
export class DDLEventHandler {
  private registry: DDLTemplateRegistry;
  private schemaVersion: number = 0;
  private appliedDDLs: Map<string, DDLTemplateEvent> = new Map();
  
  constructor() {
    this.registry = new DDLTemplateRegistry();
  }
  
  /**
   * Create a DDL event
   * DDLイベントの作成
   */
  createDDLEvent(
    ddlType: DDLOperationType,
    params: Record<string, any>,
    dependsOn: string[] = []
  ): DDLTemplateEvent {
    // Validate DDL parameters
    validateDDLParams(ddlType, params);
    
    // Get template metadata
    const metadata = this.registry.getTemplateMetadata(ddlType);
    
    // Build the DDL query
    const query = buildDDLQuery(ddlType, params);
    
    // Create the event
    const event: DDLTemplateEvent = {
      id: `ddl_${crypto.randomUUID()}`,
      template: ddlType,
      params,
      timestamp: Date.now(),
      type: "DDL",
      dependsOn,
      payload: {
        ddlType,
        query,
        metadata: {
          ifNotExists: params.ifNotExists,
          ifExists: params.ifExists,
          cascade: params.cascade,
          defaultValue: params.defaultValue,
          comment: params.comment
        }
      }
    };
    
    return event;
  }
  
  /**
   * Apply a DDL event to the database
   * DDLイベントをデータベースに適用
   */
  async applyDDLEvent(
    event: DDLTemplateEvent,
    executeQuery: (query: string) => Promise<any>
  ): Promise<void> {
    if (!isDDLEvent(event)) {
      throw new Error("Not a DDL event");
    }
    
    if (!event.payload) {
      throw new Error("DDL event missing payload");
    }
    
    // Check dependencies
    for (const depId of event.dependsOn) {
      if (!this.appliedDDLs.has(depId)) {
        throw new Error(`Dependency not satisfied: ${depId}`);
      }
    }
    
    // Execute the DDL query
    try {
      await executeQuery(event.payload.query);
      
      // Record successful application
      this.appliedDDLs.set(event.id, event);
      
      // Update schema version if it's a schema-modifying operation
      if (isSchemaModifyingOperation(event.payload.ddlType)) {
        this.schemaVersion++;
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      throw new Error(`Failed to apply DDL event ${event.id}: ${errorMessage}`);
    }
  }
  
  /**
   * Get DDL query from template and params
   * テンプレートとパラメータからDDLクエリを取得
   */
  getDDLQuery(ddlType: DDLOperationType, params: Record<string, any>): string {
    return buildDDLQuery(ddlType, params);
  }
  
  /**
   * Check if a template is a DDL template
   * テンプレートがDDLテンプレートかどうかを確認
   */
  isDDLTemplate(template: string): boolean {
    try {
      this.registry.getTemplateMetadata(template as DDLOperationType);
      return true;
    } catch {
      return false;
    }
  }
  
  /**
   * Get current schema version
   * 現在のスキーマバージョンを取得
   */
  getSchemaVersion(): number {
    return this.schemaVersion;
  }
  
  /**
   * Get applied DDL events
   * 適用済みDDLイベントを取得
   */
  getAppliedDDLs(): DDLTemplateEvent[] {
    return Array.from(this.appliedDDLs.values());
  }
  
  /**
   * Check if a DDL event has been applied
   * DDLイベントが適用済みかどうかを確認
   */
  isDDLApplied(eventId: string): boolean {
    return this.appliedDDLs.has(eventId);
  }
  
  /**
   * Reset the handler state (for testing)
   * ハンドラーの状態をリセット（テスト用）
   */
  reset(): void {
    this.schemaVersion = 0;
    this.appliedDDLs.clear();
  }
}

/**
 * Extended Template Registry that includes DDL templates
 * DDLテンプレートを含む拡張テンプレートレジストリ
 */
export class ExtendedTemplateRegistry {
  private dmlTemplates: Map<string, any> = new Map();
  private ddlRegistry: DDLTemplateRegistry;
  
  constructor() {
    this.ddlRegistry = new DDLTemplateRegistry();
    this.initializeDMLTemplates();
  }
  
  private initializeDMLTemplates(): void {
    // Add existing DML templates
    this.dmlTemplates.set("CREATE_USER", {
      requiredParams: ["id", "name"],
      impact: "CREATE_NODE",
      paramTypes: {
        id: "string",
        name: "string",
        email: "string"
      }
    });
    
    this.dmlTemplates.set("UPDATE_USER", {
      requiredParams: ["id"],
      impact: "UPDATE_NODE"
    });
    
    this.dmlTemplates.set("FOLLOW_USER", {
      requiredParams: ["followerId", "targetId"],
      impact: "CREATE_EDGE"
    });
    
    this.dmlTemplates.set("CREATE_POST", {
      requiredParams: ["id", "content"],
      impact: "CREATE_NODE"
    });
    
    this.dmlTemplates.set("DELETE_OLD_POSTS", {
      requiredParams: ["beforeDate"],
      impact: "DELETE_NODE"
    });
    
    this.dmlTemplates.set("DELETE_USER_DATA", {
      requiredParams: ["userId", "reason"],
      impact: "LOGICAL_DELETE",
      paramTypes: {
        userId: "string",
        reason: "string",
        cascade: "boolean"
      }
    });
    
    this.dmlTemplates.set("INCREMENT_COUNTER", {
      requiredParams: ["counterId"],
      impact: "UPDATE_NODE",
      paramTypes: {
        counterId: "string",
        amount: "number"
      }
    });
  }
  
  /**
   * Check if template exists (DDL or DML)
   * テンプレートが存在するかどうかを確認（DDLまたはDML）
   */
  hasTemplate(template: string): boolean {
    return this.dmlTemplates.has(template) || 
           this.ddlRegistry.hasTemplate(template as DDLOperationType);
  }
  
  /**
   * Get template metadata (DDL or DML)
   * テンプレートメタデータを取得（DDLまたはDML）
   */
  getTemplateMetadata(template: string): any {
    if (this.dmlTemplates.has(template)) {
      return this.dmlTemplates.get(template);
    }
    
    try {
      return this.ddlRegistry.getTemplateMetadata(template as DDLOperationType);
    } catch {
      throw new Error(`Unknown template: ${template}`);
    }
  }
  
  /**
   * Check if template is DDL
   * テンプレートがDDLかどうかを確認
   */
  isDDLTemplate(template: string): boolean {
    return this.ddlRegistry.hasTemplate(template as DDLOperationType);
  }
  
  /**
   * Check if template is DML
   * テンプレートがDMLかどうかを確認
   */
  isDMLTemplate(template: string): boolean {
    return this.dmlTemplates.has(template);
  }
}

/**
 * Create a unified event that can be either DDL or DML
 * DDLまたはDMLの統一イベントを作成
 */
export function createUnifiedEvent(
  template: string,
  params: Record<string, any>,
  clientId?: string
): TemplateEvent | DDLTemplateEvent {
  const registry = new ExtendedTemplateRegistry();
  
  if (registry.isDDLTemplate(template)) {
    const handler = new DDLEventHandler();
    return handler.createDDLEvent(template as DDLOperationType, params);
  } else {
    // Create regular DML event
    const event: TemplateEvent = {
      id: `evt_${crypto.randomUUID()}`,
      template,
      params,
      timestamp: Date.now(),
      clientId
    };
    return event;
  }
}