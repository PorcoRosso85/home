/**
 * In-memory storage adapter for testing and development
 * Implements StoragePort interface with simple Map-based storage
 */

import { Email } from '../../domain/email.js';
import { StoragePort, StorageResult } from '../../domain/ports.js';

export class InMemoryStorage implements StoragePort {
  private drafts: Map<string, Email> = new Map();
  private counter: number = 0;

  /**
   * Retrieve a draft email by ID
   */
  async getDraft(draftId: string): Promise<StorageResult<Email>> {
    try {
      const email = this.drafts.get(draftId);
      if (!email) {
        return { success: false, error: 'Draft not found' };
      }
      return { success: true, data: email };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown storage error'
      };
    }
  }

  /**
   * Save a draft email
   */
  async saveDraft(email: Email, draftId?: string): Promise<StorageResult<string>> {
    try {
      const id = draftId || this.generateDraftId();
      this.drafts.set(id, email);
      return { success: true, data: id };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown storage error'
      };
    }
  }

  /**
   * Delete a draft email
   */
  async deleteDraft(draftId: string): Promise<StorageResult<void>> {
    try {
      const existed = this.drafts.delete(draftId);
      if (!existed) {
        return { success: false, error: 'Draft not found' };
      }
      return { success: true, data: undefined };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown storage error'
      };
    }
  }

  /**
   * List all draft emails
   */
  async listDrafts(): Promise<StorageResult<Array<{ id: string; email: Email }>>> {
    try {
      const result = Array.from(this.drafts.entries()).map(([id, email]) => ({ id, email }));
      return { success: true, data: result };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown storage error'
      };
    }
  }

  /**
   * Generate a unique draft ID
   */
  private generateDraftId(): string {
    return `draft-${Date.now()}-${++this.counter}`;
  }

  /**
   * Clear all drafts (useful for testing)
   */
  clear(): void {
    this.drafts.clear();
    this.counter = 0;
  }

  /**
   * Get the current number of stored drafts (useful for testing)
   */
  size(): number {
    return this.drafts.size;
  }
}