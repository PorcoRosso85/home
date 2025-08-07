/**
 * Test suite for InMemoryStorage adapter
 */

import { describe, test, expect, beforeEach } from 'bun:test';
import { Email, createEmail } from '../../../src/domain/email.js';
import { InMemoryStorage } from '../../../src/adapters/storage/memory.js';

describe('InMemoryStorage', () => {
  let storage: InMemoryStorage;
  let testEmail: Email;

  beforeEach(() => {
    storage = new InMemoryStorage();

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

  describe('saveDraft', () => {
    test('should save draft and return generated ID', async () => {
      // Act
      const result = await storage.saveDraft(testEmail);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toMatch(/^draft-\d+-\d+$/);
      }
      expect(storage.size()).toBe(1);
    });

    test('should save draft with provided ID', async () => {
      // Arrange
      const customId = 'custom-draft-id';

      // Act
      const result = await storage.saveDraft(testEmail, customId);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toBe(customId);
      }
      expect(storage.size()).toBe(1);
    });
  });

  describe('getDraft', () => {
    test('should retrieve saved draft', async () => {
      // Arrange
      const saveResult = await storage.saveDraft(testEmail);
      expect(saveResult.success).toBe(true);
      const draftId = saveResult.success ? saveResult.data : '';

      // Act
      const result = await storage.getDraft(draftId);

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual(testEmail);
      }
    });

    test('should return error for non-existent draft', async () => {
      // Act
      const result = await storage.getDraft('non-existent');

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBe('Draft not found');
      }
    });
  });

  describe('deleteDraft', () => {
    test('should delete existing draft', async () => {
      // Arrange
      const saveResult = await storage.saveDraft(testEmail);
      expect(saveResult.success).toBe(true);
      const draftId = saveResult.success ? saveResult.data : '';

      // Act
      const result = await storage.deleteDraft(draftId);

      // Assert
      expect(result.success).toBe(true);
      expect(storage.size()).toBe(0);
    });

    test('should return error when deleting non-existent draft', async () => {
      // Act
      const result = await storage.deleteDraft('non-existent');

      // Assert
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error).toBe('Draft not found');
      }
    });
  });

  describe('listDrafts', () => {
    test('should return empty array when no drafts exist', async () => {
      // Act
      const result = await storage.listDrafts();

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toEqual([]);
      }
    });

    test('should list all saved drafts', async () => {
      // Arrange
      const email2Result = createEmail({
        to: 'test2@example.com',
        subject: 'Test Subject 2',
        body: 'Test body content 2'
      });
      expect(email2Result.success).toBe(true);
      const email2 = email2Result.success ? email2Result.email : testEmail;

      await storage.saveDraft(testEmail, 'draft-1');
      await storage.saveDraft(email2, 'draft-2');

      // Act
      const result = await storage.listDrafts();

      // Assert
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data).toHaveLength(2);
        expect(result.data).toContainEqual({ id: 'draft-1', email: testEmail });
        expect(result.data).toContainEqual({ id: 'draft-2', email: email2 });
      }
    });
  });

  describe('clear', () => {
    test('should clear all drafts', async () => {
      // Arrange
      await storage.saveDraft(testEmail);
      expect(storage.size()).toBe(1);

      // Act
      storage.clear();

      // Assert
      expect(storage.size()).toBe(0);
    });
  });
});