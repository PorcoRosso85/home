/**
 * Domain ports for email sending and storage operations
 * These interfaces define contracts that adapters must implement
 */

import { Email } from './email.js';

/**
 * Options for email sending operations
 */
export type SendOptions = {
  readonly dryRun: boolean;
}

/**
 * Result type for send operations
 */
export type SendResult = 
  | { success: true; messageId: string }
  | { success: false; error: string };

/**
 * Result type for storage operations
 */
export type StorageResult<T> = 
  | { success: true; data: T }
  | { success: false; error: string };

/**
 * Port interface for email sending operations
 * Implementations should handle the actual email delivery
 */
export type EmailSenderPort = {
  /**
   * Send an email with optional send options
   * @param email - The email to send
   * @param options - Optional send options (e.g., dryRun mode)
   * @returns Promise resolving to send result with messageId on success
   */
  send(email: Email, options?: SendOptions): Promise<SendResult>;
}

/**
 * Port interface for email storage operations
 * Implementations should handle draft email persistence and retrieval
 */
export type StoragePort = {
  /**
   * Retrieve a draft email by ID
   * @param draftId - The unique identifier for the draft
   * @returns Promise resolving to the draft email or error
   */
  getDraft(draftId: string): Promise<StorageResult<Email>>;

  /**
   * Save a draft email
   * @param email - The email to save as draft
   * @param draftId - Optional ID for the draft (generated if not provided)
   * @returns Promise resolving to the draft ID or error
   */
  saveDraft(email: Email, draftId?: string): Promise<StorageResult<string>>;

  /**
   * Delete a draft email
   * @param draftId - The unique identifier for the draft to delete
   * @returns Promise resolving to success status or error
   */
  deleteDraft(draftId: string): Promise<StorageResult<void>>;

  /**
   * List all draft emails
   * @returns Promise resolving to array of draft emails with their IDs or error
   */
  listDrafts(): Promise<StorageResult<Array<{ id: string; email: Email }>>>;
}