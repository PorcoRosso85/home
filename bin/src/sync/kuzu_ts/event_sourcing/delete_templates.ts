/**
 * GDPR Logical Delete Handler
 * GDPR準拠の論理削除ハンドラー
 */

import type { TemplateEvent } from "./types.ts";
import type { TemplateEventStore } from "./template_event_store.ts";

// ========== Type Definitions ==========

export interface LogicalDeleteEvent extends TemplateEvent {
  deletionTimestamp: number;
}

export interface DeletionInfo {
  userId: string;
  reason: string;
  deletionTimestamp: number;
  isLogicalDelete: boolean;
}

export interface DeletionResult {
  isDeleted: boolean;
  deletionReason: string;
  deletionTimestamp: number;
  isDuplicate?: boolean;
  previousDeletionTimestamp?: number;
  cascadedEntities?: Array<{ type: string; id: string }>;
}

// ========== Logical Delete Handler ==========

export class LogicalDeleteHandler {
  private deletedEntities: Map<string, DeletionInfo> = new Map();

  processLogicalDelete(event: LogicalDeleteEvent, store: TemplateEventStore): DeletionResult {
    const userId = event.params.userId as string;
    const reason = event.params.reason as string;
    const cascade = event.params.cascade as boolean || false;

    // Check if already deleted
    const existingDeletion = this.deletedEntities.get(userId);
    if (existingDeletion) {
      return {
        isDeleted: true,
        deletionReason: reason,
        deletionTimestamp: event.deletionTimestamp,
        isDuplicate: true,
        previousDeletionTimestamp: existingDeletion.deletionTimestamp
      };
    }

    // Mark as deleted
    const deletionInfo: DeletionInfo = {
      userId,
      reason,
      deletionTimestamp: event.deletionTimestamp,
      isLogicalDelete: true
    };
    this.deletedEntities.set(userId, deletionInfo);

    // Append deletion event to store
    store.appendTemplateEvent(event);

    const result: DeletionResult = {
      isDeleted: true,
      deletionReason: reason,
      deletionTimestamp: event.deletionTimestamp
    };

    // Handle cascade if requested
    if (cascade) {
      const cascadedEntities = this.processCascadeDeletion(userId, store);
      result.cascadedEntities = cascadedEntities;
    }

    return result;
  }

  private processCascadeDeletion(userId: string, store: TemplateEventStore): Array<{ type: string; id: string }> {
    const cascadedEntities: Array<{ type: string; id: string }> = [];
    
    // Find all events related to this user
    const allEvents = store.getEventsSince(0);
    
    for (const event of allEvents) {
      // Find posts created by the user
      if (event.template === "CREATE_POST" && event.params.userId === userId) {
        const postId = event.params.id as string;
        if (!this.isEntityDeleted(postId)) {
          cascadedEntities.push({ type: "POST", id: postId });
          // Mark post as logically deleted
          this.deletedEntities.set(postId, {
            userId: postId,
            reason: `Cascaded deletion from user ${userId}`,
            deletionTimestamp: Date.now(),
            isLogicalDelete: true
          });
        }
      }
    }

    return cascadedEntities;
  }

  getActiveEntities(store: TemplateEventStore, entityType: string): Array<{ id: string; [key: string]: any }> {
    const activeEntities: Array<{ id: string; [key: string]: any }> = [];
    const allEvents = store.getEventsSince(0);
    
    for (const event of allEvents) {
      if (event.template === `CREATE_${entityType}`) {
        const entityId = event.params.id as string;
        if (!this.isEntityDeleted(entityId)) {
          activeEntities.push({ id: entityId, ...event.params });
        }
      }
    }

    return activeEntities;
  }

  private isEntityDeleted(entityId: string): boolean {
    return this.deletedEntities.has(entityId);
  }

  getDeletionInfo(event: LogicalDeleteEvent): DeletionInfo {
    return {
      userId: event.params.userId as string,
      reason: event.params.reason as string,
      deletionTimestamp: event.deletionTimestamp,
      isLogicalDelete: true
    };
  }
}