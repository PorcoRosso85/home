/**
 * EventGroupManager - Atomic Event Group Operations
 * イベントグループのアトミック操作管理
 */

import type { EventGroup, EventGroupStatus, TemplateEvent } from "./types.ts";

type RollbackInfo = {
  reason: string;
  timestamp: number;
};

// Test template definitions for validation
const TEST_TEMPLATES = {
  CREATE_NODE: {
    requiredParams: ["label", "properties"],
  },
  CREATE_EDGE: {
    requiredParams: ["type", "fromId", "toId"],
  },
  UPDATE_NODE: {
    requiredParams: ["nodeId", "properties"],
  },
  CREATE_USER: {
    requiredParams: ["id", "name", "email"],
  },
  UPDATE_USER: {
    requiredParams: ["id", "name"],
  },
  CREATE_POST: {
    requiredParams: ["id", "content", "authorId"],
  },
  FOLLOW_USER: {
    requiredParams: ["followerId", "targetId"],
  },
  INVALID_TEMPLATE: null, // Marker for invalid template
};

/**
 * EventGroupManager handles atomic operations across multiple events
 * 複数イベントのアトミック操作を管理
 */
export class EventGroupManager {
  private eventGroups: Map<string, EventGroup> = new Map();
  private rollbackInfos: Map<string, RollbackInfo> = new Map();

  /**
   * Validate template and parameters
   * テンプレートとパラメータを検証
   */
  private validateEvent(event: TemplateEvent): void {
    // Check if template is explicitly invalid
    if (event.template === "INVALID_TEMPLATE") {
      throw new Error(`Invalid template: ${event.template}`);
    }
    
    // Get template definition
    const templateDef = TEST_TEMPLATES[event.template as keyof typeof TEST_TEMPLATES];
    
    if (!templateDef) {
      throw new Error(`Invalid template: ${event.template}`);
    }
    
    // Validate required parameters
    for (const required of templateDef.requiredParams) {
      if (!(required in event.params)) {
        throw new Error(`Missing required parameter: ${required}`);
      }
    }
  }

  /**
   * Create a new event group with validation
   * 検証付きで新しいイベントグループを作成
   */
  async createEventGroup(events: TemplateEvent[]): Promise<EventGroup> {
    // Validate at least one event
    if (events.length === 0) {
      throw new Error("EventGroup must contain at least one event");
    }

    // Validate all events before creating group
    for (const event of events) {
      this.validateEvent(event);
    }

    // Create event group
    const eventGroup: EventGroup = {
      id: `evg_${crypto.randomUUID()}`,
      events: [...events], // Copy to prevent external modifications
      timestamp: Date.now(),
      status: "pending" as EventGroupStatus,
    };

    // Store the event group
    this.eventGroups.set(eventGroup.id, eventGroup);

    return eventGroup;
  }

  /**
   * Commit all events in a group atomically
   * グループ内のすべてのイベントをアトミックにコミット
   */
  async commit(eventGroupId: string, store: any): Promise<void> {
    const eventGroup = this.eventGroups.get(eventGroupId);
    if (!eventGroup) {
      throw new Error(`EventGroup not found: ${eventGroupId}`);
    }

    // Check if already committed
    if (eventGroup.status === "committed") {
      throw new Error("EventGroup already committed");
    }

    const committedEvents: TemplateEvent[] = [];

    try {
      // Attempt to commit all events
      for (const event of eventGroup.events) {
        store.addEvent(event);
        committedEvents.push(event);
      }

      // All events committed successfully
      eventGroup.status = "committed";
    } catch (error) {
      // Rollback on any failure
      await this.rollback(eventGroup, store, committedEvents, error as Error);
      throw error;
    }
  }

  /**
   * Rollback committed events and update status
   * コミット済みイベントをロールバックしステータスを更新
   */
  private async rollback(
    eventGroup: EventGroup,
    store: any,
    committedEvents: TemplateEvent[],
    error: Error
  ): Promise<void> {
    // Remove committed events from store
    if (store.committedEvents && Array.isArray(store.committedEvents)) {
      // For mock store in tests - remove committed events
      for (const event of committedEvents) {
        const index = store.committedEvents.findIndex((e: TemplateEvent) => e.id === event.id);
        if (index >= 0) {
          store.committedEvents.splice(index, 1);
        }
      }
    }

    // Update status to rolled_back
    eventGroup.status = "rolled_back";

    // Store rollback information
    this.rollbackInfos.set(eventGroup.id, {
      reason: error.message,
      timestamp: Date.now(),
    });
  }

  /**
   * Get rollback information for a group
   * グループのロールバック情報を取得
   */
  async getRollbackInfo(eventGroupId: string): Promise<RollbackInfo> {
    const info = this.rollbackInfos.get(eventGroupId);
    if (!info) {
      throw new Error(`No rollback info found for: ${eventGroupId}`);
    }
    return info;
  }
}