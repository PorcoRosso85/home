/**
 * Template-based Event Sourcing Implementation
 * テンプレートベースのイベントソーシング実装
 */

import { join, dirname } from "jsr:@std/path@^1.0.0";
import { ensureDir } from "jsr:@std/fs@^1.0.0";

// ========== 型定義 ==========

export interface TemplateMetadata {
  requiredParams: string[];
  paramTypes?: Record<string, string>;
  impact: "CREATE_NODE" | "UPDATE_NODE" | "DELETE_NODE" | "CREATE_EDGE" | "UPDATE_EDGE" | "DELETE_EDGE";
  validation?: Record<string, any>;
}

export interface TemplateEvent {
  id: string;
  template: string;
  params: Record<string, any>;
  timestamp: number;
  clientId?: string;
  checksum?: string;
}

export interface Impact {
  addedNodes: number;
  addedEdges: number;
  deletedNodes: number;
  deletedEdges?: number;
  edgeType?: string;
  warning?: string;
}

export interface Conflict {
  type: string;
  events: TemplateEvent[];
}

// ========== 1. テンプレート管理 ==========

export class TemplateLoader {
  private basePath: string;

  constructor(basePath = "./templates") {
    this.basePath = basePath;
  }

  async loadTemplate(filename: string): Promise<string> {
    try {
      const path = join(this.basePath, filename);
      const content = await Deno.readTextFile(path);
      return content;
    } catch (error) {
      throw new Error(`Template not found: ${filename}`);
    }
  }
}

export class TemplateRegistry {
  private metadata: Record<string, TemplateMetadata> = {
    CREATE_USER: {
      requiredParams: ["id", "name"],
      impact: "CREATE_NODE",
      paramTypes: {
        id: "string",
        name: "string",
        email: "string"
      }
    },
    UPDATE_USER: {
      requiredParams: ["id"],
      impact: "UPDATE_NODE"
    },
    FOLLOW_USER: {
      requiredParams: ["followerId", "targetId"],
      impact: "CREATE_EDGE"
    },
    CREATE_POST: {
      requiredParams: ["id", "content"],
      impact: "CREATE_NODE"
    },
    DELETE_OLD_POSTS: {
      requiredParams: ["beforeDate"],
      impact: "DELETE_NODE"
    }
  };

  getTemplateMetadata(templateName: string): TemplateMetadata {
    const metadata = this.metadata[templateName];
    if (!metadata) {
      throw new Error(`Unknown template: ${templateName}`);
    }
    return metadata;
  }

  isValidTemplate(templateName: string): boolean {
    return templateName in this.metadata;
  }
}

export class TemplateValidator {
  private registry = new TemplateRegistry();

  validateTemplate(templateName: string, params: Record<string, any>): void {
    const metadata = this.registry.getTemplateMetadata(templateName);
    
    for (const required of metadata.requiredParams) {
      if (!(required in params)) {
        throw new Error(`Missing required parameter: ${required}`);
      }
    }
  }
}

// ========== 2. イベント生成 ==========

export class TemplateEventFactory {
  private registry = new TemplateRegistry();
  private validator = new TemplateValidator();

  createTemplateEvent(templateName: string, params: Record<string, any>): TemplateEvent {
    if (!this.registry.isValidTemplate(templateName)) {
      throw new Error(`Unknown template: ${templateName}`);
    }

    this.validator.validateTemplate(templateName, params);

    const event: TemplateEvent = {
      id: `evt_${crypto.randomUUID()}`,
      template: templateName,
      params: { ...params },
      timestamp: Date.now()
    };

    // Calculate checksum
    const content = JSON.stringify({ template: event.template, params: event.params });
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    event.checksum = Math.abs(hash).toString(16);

    return event;
  }

}

// ========== 3. パラメータ検証 ==========

export class ParamValidator {
  validateParams(params: Record<string, any>, metadata: TemplateMetadata): Record<string, any> {
    // Check required params
    for (const required of metadata.requiredParams) {
      if (!(required in params)) {
        throw new Error(`Missing required parameter: ${required}`);
      }
    }

    // Check types if specified
    if (metadata.paramTypes) {
      for (const [param, expectedType] of Object.entries(metadata.paramTypes)) {
        if (param in params) {
          const actualType = typeof params[param];
          if (actualType !== expectedType && expectedType === "number" && actualType === "string") {
            // Try to parse number
            const parsed = Number(params[param]);
            if (isNaN(parsed)) {
              throw new Error(`Invalid type for parameter ${param}: expected ${expectedType}, got ${actualType}`);
            }
          }
        }
      }
    }

    // Sanitize values
    const sanitized: Record<string, any> = {};
    for (const [key, value] of Object.entries(params)) {
      if (typeof value === "string") {
        // Remove SQL injection attempts
        sanitized[key] = value
          .replace(/;/g, "")
          .replace(/--/g, "")
          .replace(/DROP/gi, "")
          .replace(/DELETE/gi, "")
          .replace(/UPDATE/gi, "")
          .replace(/INSERT/gi, "");
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }
}

// ========== 4. イベントストア基本操作 ==========

export class TemplateEventStore {
  protected events: TemplateEvent[] = [];

  appendTemplateEvent(event: TemplateEvent): void {
    this.events.push(event);
  }

  getEventsSince(position: number): TemplateEvent[] {
    return this.events.slice(position);
  }

  getLatestEvents(n: number): TemplateEvent[] {
    const start = Math.max(0, this.events.length - n);
    return this.events.slice(start);
  }

  getEventCount(): number {
    return this.events.length;
  }
}

// ========== 5. スナップショット機能 ==========

interface Snapshot {
  position: number;
  state: any;
  timestamp: number;
}

export class SnapshotableEventStore extends TemplateEventStore {
  private snapshots: Snapshot[] = [];
  private snapshotInterval: number;

  constructor(options: { snapshotInterval?: number } = {}) {
    super();
    this.snapshotInterval = options.snapshotInterval || 100;
  }

  override appendTemplateEvent(event: TemplateEvent): void {
    super.appendTemplateEvent(event);
    
    // Create snapshot if needed
    if (this.getEventCount() % this.snapshotInterval === 0) {
      this.createSnapshot();
    }
  }

  private createSnapshot(): void {
    const snapshot: Snapshot = {
      position: this.getEventCount(),
      state: this.buildState(),
      timestamp: Date.now()
    };
    this.snapshots.push(snapshot);
  }

  private buildState(): any {
    // Simple state building - in real implementation, this would apply events
    return {
      eventCount: this.getEventCount(),
      latestEventId: this.getLatestEvents(1)[0]?.id
    };
  }

  getSnapshots(): Snapshot[] {
    return this.snapshots;
  }

  getSnapshotAt(position: number): Snapshot | undefined {
    return this.snapshots.find(s => s.position === position);
  }

  restoreFromSnapshot(snapshot: Snapshot): void {
    // In real implementation, would restore full state
    // For now, just simulate by clearing and replaying
    const events = this.getEventsSince(0).slice(0, snapshot.position);
    this.events = [];
    for (const event of events) {
      super.appendTemplateEvent(event);
    }
  }

  getStateWithSnapshot(): any {
    const lastSnapshot = this.snapshots[this.snapshots.length - 1];
    if (!lastSnapshot) {
      return {
        fromSnapshot: false,
        state: this.buildState()
      };
    }

    return {
      fromSnapshot: true,
      snapshotPosition: lastSnapshot.position,
      deltaCount: this.getEventCount() - lastSnapshot.position,
      state: this.buildState()
    };
  }
}

// ========== 6. テンプレート実行の影響予測 ==========

export class ImpactPredictor {
  private registry = new TemplateRegistry();

  predictImpact(templateName: string, params: Record<string, any>): Impact {
    const metadata = this.registry.getTemplateMetadata(templateName);
    
    const impact: Impact = {
      addedNodes: 0,
      addedEdges: 0,
      deletedNodes: 0
    };

    switch (metadata.impact) {
      case "CREATE_NODE":
        impact.addedNodes = 1;
        break;
      case "CREATE_EDGE":
        impact.addedEdges = 1;
        if (templateName === "FOLLOW_USER") {
          impact.edgeType = "FOLLOWS";
        }
        break;
      case "DELETE_NODE":
        // For delete operations, we can't know exact count without querying
        impact.deletedNodes = 1; // Minimum
        impact.warning = "Actual count may vary (estimated)";
        break;
    }

    return impact;
  }
}

// ========== 7. 同期とブロードキャスト ==========

export class EventBroadcaster {
  broadcastEvent(event: TemplateEvent, clients: string[]): string[] {
    // Exclude sender if specified
    if (event.clientId) {
      return clients.filter(c => c !== event.clientId);
    }
    return clients;
  }
}

export class EventReceiver {
  private validator = new TemplateValidator();

  receiveTemplateEvent(event: TemplateEvent): void {
    // Validate template exists
    if (!new TemplateRegistry().isValidTemplate(event.template)) {
      throw new Error("Invalid template");
    }
    
    // Validate params
    this.validator.validateTemplate(event.template, event.params);
    
    // In real implementation, would apply the event
  }
}

export class ConcurrentEventHandler {
  detectConflicts(events: TemplateEvent[]): Conflict[] {
    const conflicts: Conflict[] = [];
    
    // Group events by target entity
    const eventsByTarget = new Map<string, TemplateEvent[]>();
    
    for (const event of events) {
      const targetId = event.params.id || `${event.params.followerId}-${event.params.targetId}`;
      if (targetId) {
        const existing = eventsByTarget.get(targetId) || [];
        existing.push(event);
        eventsByTarget.set(targetId, existing);
      }
    }
    
    // Find conflicts
    for (const [targetId, targetEvents] of eventsByTarget) {
      if (targetEvents.length > 1) {
        // Check if events are concurrent (within 100ms)
        const sorted = targetEvents.sort((a, b) => a.timestamp - b.timestamp);
        for (let i = 0; i < sorted.length - 1; i++) {
          if (sorted[i + 1].timestamp - sorted[i].timestamp < 100) {
            conflicts.push({
              type: "CONCURRENT_UPDATE",
              events: [sorted[i], sorted[i + 1]]
            });
          }
        }
      }
    }
    
    return conflicts;
  }
}

// ========== 8. セキュリティ ==========

export class SecureTemplateExecutor {
  private paramValidator = new ParamValidator();
  private registry = new TemplateRegistry();
  private unauthorizedTemplates = new Set(["DELETE_ALL_USERS", "DROP_DATABASE"]);

  sanitizeParams(templateName: string, params: Record<string, any>): Record<string, any> {
    const metadata = this.registry.getTemplateMetadata(templateName);
    return this.paramValidator.validateParams(params, metadata);
  }

  executeTemplate(templateName: string, params: Record<string, any>): void {
    if (this.unauthorizedTemplates.has(templateName)) {
      throw new Error("Unauthorized template");
    }
    
    // In real implementation, would execute the template
  }
}

export class ChecksumValidator {
  validateChecksum(event: TemplateEvent): boolean {
    if (!event.checksum) {
      return false;
    }
    
    // Recalculate checksum using same algorithm
    const content = JSON.stringify({ template: event.template, params: event.params });
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    const calculated = Math.abs(hash).toString(16);
    
    return calculated === event.checksum;
  }
}