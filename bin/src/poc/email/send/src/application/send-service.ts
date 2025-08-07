/**
 * SendService - Application service that coordinates email sending and storage operations
 * Integrates StoragePort and EmailSenderPort to provide draft email sending functionality
 */

import { StoragePort, EmailSenderPort, SendOptions, SendResult } from '../domain/ports.js';

export class SendService {
  private readonly storage: StoragePort;
  private readonly emailSender: EmailSenderPort;

  /**
   * Initialize SendService with storage and email sender dependencies
   */
  constructor(storage: StoragePort, emailSender: EmailSenderPort) {
    this.storage = storage;
    this.emailSender = emailSender;
  }

  /**
   * Send a draft email from storage
   * @param draftId - The unique identifier for the draft email
   * @param options - Optional send options (e.g., dryRun mode)
   * @returns Promise resolving to send result with messageId on success
   */
  async sendDraft(draftId: string, options?: SendOptions): Promise<SendResult> {
    // Validate input
    if (!draftId || typeof draftId !== 'string' || draftId.trim() === '') {
      return { success: false, error: 'Draft ID is required' };
    }

    try {
      // Retrieve draft from storage
      const draftResult = await this.storage.getDraft(draftId);
      if (!draftResult.success) {
        return { success: false, error: draftResult.error };
      }

      // Send the email
      const sendResult = await this.emailSender.send(draftResult.data, options);
      return sendResult;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      return { success: false, error: errorMessage };
    }
  }
}