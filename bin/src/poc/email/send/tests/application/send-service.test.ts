/**
 * Test suite for SendService
 * Tests the application service that integrates storage and email sending
 */

import { describe, test, expect, beforeEach } from 'bun:test';
import { Email, createEmail } from '../../src/domain/email.js';
import { EmailSenderPort, StoragePort, SendOptions, SendResult, StorageResult } from '../../src/domain/ports.js';
import { SendService } from '../../src/application/send-service.js';

// Mock implementations for testing
class MockEmailSender implements EmailSenderPort {
  private shouldFail: boolean = false;
  private sentEmails: Array<{ email: Email; options?: SendOptions }> = [];

  setShouldFail(fail: boolean): void {
    this.shouldFail = fail;
  }

  getSentEmails(): Array<{ email: Email; options?: SendOptions }> {
    return this.sentEmails;
  }

  async send(email: Email, options?: SendOptions): Promise<SendResult> {
    this.sentEmails.push({ email, options });
    
    if (this.shouldFail) {
      return { success: false, error: 'Failed to send email' };
    }

    if (options?.dryRun) {
      return { success: true, messageId: 'dry-run-message-id' };
    }

    return { success: true, messageId: 'message-123' };
  }
}

class MockStorage implements StoragePort {
  private drafts: Map<string, Email> = new Map();
  private shouldFailOnGet: boolean = false;

  setShouldFailOnGet(fail: boolean): void {
    this.shouldFailOnGet = fail;
  }

  addDraft(id: string, email: Email): void {
    this.drafts.set(id, email);
  }

  async getDraft(draftId: string): Promise<StorageResult<Email>> {
    if (this.shouldFailOnGet) {
      return { success: false, error: 'Storage error' };
    }

    const email = this.drafts.get(draftId);
    if (!email) {
      return { success: false, error: 'Draft not found' };
    }

    return { success: true, data: email };
  }

  async saveDraft(email: Email, draftId?: string): Promise<StorageResult<string>> {
    const id = draftId || `draft-${Date.now()}`;
    this.drafts.set(id, email);
    return { success: true, data: id };
  }

  async deleteDraft(draftId: string): Promise<StorageResult<void>> {
    this.drafts.delete(draftId);
    return { success: true, data: undefined };
  }

  async listDrafts(): Promise<StorageResult<Array<{ id: string; email: Email }>>> {
    const result = Array.from(this.drafts.entries()).map(([id, email]) => ({ id, email }));
    return { success: true, data: result };
  }
}

describe('SendService', () => {
  let mockStorage: MockStorage;
  let mockSender: MockEmailSender;
  let sendService: SendService;
  let testEmail: Email;

  beforeEach(() => {
    mockStorage = new MockStorage();
    mockSender = new MockEmailSender();
    sendService = new SendService(mockStorage, mockSender);

    // Create a valid test email
    const emailResult = createEmail({
      to: 'test@example.com',
      subject: 'Test Subject',
      body: 'Test body content',
      from: 'sender@example.com'
    });

    if (!emailResult.success) {
      throw new Error('Failed to create test email');
    }
    testEmail = emailResult.email;
  });

  describe('sendDraft', () => {
    test('should successfully send a draft email from storage', async () => {
      // Arrange
      const draftId = 'draft-123';
      mockStorage.addDraft(draftId, testEmail);

      // Act
      const result = await sendService.sendDraft(draftId);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.messageId).toBe('message-123');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(1);
      expect(sentEmails[0].email).toEqual(testEmail);
      expect(sentEmails[0].options).toBeUndefined();
    });

    test('should successfully send draft in dry run mode', async () => {
      // Arrange
      const draftId = 'draft-456';
      mockStorage.addDraft(draftId, testEmail);

      // Act
      const result = await sendService.sendDraft(draftId, { dryRun: true });

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.messageId).toBe('dry-run-message-id');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(1);
      expect(sentEmails[0].email).toEqual(testEmail);
      expect(sentEmails[0].options).toEqual({ dryRun: true });
    });

    test('should handle missing draft error', async () => {
      // Arrange
      const nonExistentDraftId = 'non-existent-draft';

      // Act
      const result = await sendService.sendDraft(nonExistentDraftId);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBe('Draft not found');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(0);
    });

    test('should handle storage retrieval error', async () => {
      // Arrange
      const draftId = 'draft-789';
      mockStorage.setShouldFailOnGet(true);

      // Act
      const result = await sendService.sendDraft(draftId);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBe('Storage error');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(0);
    });

    test('should handle email sender error', async () => {
      // Arrange
      const draftId = 'draft-error';
      mockStorage.addDraft(draftId, testEmail);
      mockSender.setShouldFail(true);

      // Act
      const result = await sendService.sendDraft(draftId);

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBe('Failed to send email');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(1); // Email was attempted to be sent
    });

    test('should handle empty draft ID', async () => {
      // Act
      const result = await sendService.sendDraft('');

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBe('Draft ID is required');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(0);
    });

    test('should handle null/undefined draft ID', async () => {
      // Act
      const result1 = await sendService.sendDraft(null as any);
      const result2 = await sendService.sendDraft(undefined as any);

      // Assert
      expect(result1.success).toBe(false);
      expect(result2.success).toBe(false);
      
      if (!result1.success) {
        expect(result1.error).toBe('Draft ID is required');
      }
      if (!result2.success) {
        expect(result2.error).toBe('Draft ID is required');
      }

      const sentEmails = mockSender.getSentEmails();
      expect(sentEmails).toHaveLength(0);
    });
  });

  describe('constructor', () => {
    test('should create service with storage and sender dependencies', () => {
      // Act
      const service = new SendService(mockStorage, mockSender);

      // Assert - service should be created without errors
      expect(service).toBeDefined();
      expect(service).toBeInstanceOf(SendService);
    });
  });
});