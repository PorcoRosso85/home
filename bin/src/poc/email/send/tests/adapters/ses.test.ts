/**
 * Tests for SES Email Sender Adapter
 */

import { describe, it, expect, beforeEach, mock, spyOn } from 'bun:test';
import { SESEmailSender } from '../../src/adapters/sender/ses.js';
import { createEmail } from '../../src/domain/email.js';
import type { SendOptions } from '../../src/domain/ports.js';
import type { Email } from '../../src/domain/email.js';

// Mock AWS SDK
const mockSend = mock();
const mockSESClient = {
  send: mockSend
};

// Mock the AWS SDK module
mock.module('@aws-sdk/client-ses', () => ({
  SESClient: mock(() => mockSESClient),
  SendEmailCommand: mock((params: any) => ({ input: params }))
}));

describe('SESEmailSender', () => {
  let sesEmailSender: SESEmailSender;
  let testEmail: Email;

  beforeEach(() => {
    // Reset mocks
    mockSend.mockRestore();
    
    // Create test email
    const result = createEmail({
      to: 'test@example.com',
      subject: 'Test Subject',
      body: 'Test Body',
      from: 'sender@example.com'
    });
    
    if (!result.success) {
      throw new Error('Failed to create test email');
    }
    
    testEmail = result.email;
    
    // Create SES sender with test config
    sesEmailSender = new SESEmailSender({
      region: 'us-east-1',
      credentials: {
        accessKeyId: 'test-access-key',
        secretAccessKey: 'test-secret-key'
      }
    });
  });

  describe('constructor', () => {
    it('should create SES client with provided configuration', () => {
      const config = {
        region: 'us-west-2',
        credentials: {
          accessKeyId: 'test-key',
          secretAccessKey: 'test-secret'
        }
      };

      const sender = new SESEmailSender(config);
      expect(sender).toBeInstanceOf(SESEmailSender);
    });

    it('should throw error for invalid region', () => {
      expect(() => {
        new SESEmailSender({
          region: '',
          credentials: {
            accessKeyId: 'test-key',
            secretAccessKey: 'test-secret'
          }
        });
      }).toThrow('Region is required');
    });

    it('should throw error for missing credentials', () => {
      expect(() => {
        new SESEmailSender({
          region: 'us-east-1',
          credentials: {
            accessKeyId: '',
            secretAccessKey: 'test-secret'
          }
        });
      }).toThrow('Access key ID is required');

      expect(() => {
        new SESEmailSender({
          region: 'us-east-1',
          credentials: {
            accessKeyId: 'test-key',
            secretAccessKey: ''
          }
        });
      }).toThrow('Secret access key is required');
    });
  });

  describe('send method', () => {
    describe('dry run mode', () => {
      it('should log email details and return mock messageId in dry run mode', async () => {
        const consoleSpy = spyOn(console, 'log').mockImplementation(() => {});
        
        const options: SendOptions = { dryRun: true };
        const result = await sesEmailSender.send(testEmail, options);

        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.messageId).toMatch(/^ses-dry-run-/);
          expect(result.messageId.length).toBeGreaterThanOrEqual(13); // At least 'ses-dry-run-' + some ID
        }

        expect(consoleSpy).toHaveBeenCalledWith(
          '[SES Dry Run] Email would be sent:',
          expect.objectContaining({
            to: testEmail.to,
            subject: testEmail.subject,
            body: testEmail.body,
            from: testEmail.from
          })
        );

        // Ensure SES client was not called
        expect(mockSend).not.toHaveBeenCalled();
        
        consoleSpy.mockRestore();
      });

      it('should include optional fields in dry run log when present', async () => {
        const consoleSpy = spyOn(console, 'log').mockImplementation(() => {});
        
        const emailResult = createEmail({
          to: 'test@example.com',
          subject: 'Test Subject',
          body: 'Test Body',
          from: 'sender@example.com',
          cc: 'cc@example.com',
          bcc: 'bcc@example.com',
          replyTo: 'reply@example.com'
        });
        
        if (!emailResult.success) {
          throw new Error('Failed to create test email');
        }

        const options: SendOptions = { dryRun: true };
        const result = await sesEmailSender.send(emailResult.email, options);

        expect(result.success).toBe(true);
        expect(consoleSpy).toHaveBeenCalledWith(
          '[SES Dry Run] Email would be sent:',
          expect.objectContaining({
            to: 'test@example.com',
            subject: 'Test Subject',
            body: 'Test Body',
            from: 'sender@example.com',
            cc: 'cc@example.com',
            bcc: 'bcc@example.com',
            replyTo: 'reply@example.com'
          })
        );
        
        consoleSpy.mockRestore();
      });
    });

    describe('real mode', () => {
      it('should send email via SES client and return messageId', async () => {
        const mockMessageId = 'ses-message-id-12345';
        mockSend.mockResolvedValue({
          MessageId: mockMessageId
        });

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(testEmail, options);

        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.messageId).toBe(mockMessageId);
        }

        expect(mockSend).toHaveBeenCalledTimes(1);
        const sendCommand = mockSend.mock.calls[0][0];
        expect(sendCommand.input).toEqual(
          expect.objectContaining({
            Source: testEmail.from,
            Destination: {
              ToAddresses: [testEmail.to]
            },
            Message: {
              Subject: {
                Data: testEmail.subject,
                Charset: 'UTF-8'
              },
              Body: {
                Text: {
                  Data: testEmail.body,
                  Charset: 'UTF-8'
                }
              }
            }
          })
        );
      });

      it('should send email with default from address when not provided', async () => {
        const emailResult = createEmail({
          to: 'test@example.com',
          subject: 'Test Subject',
          body: 'Test Body'
        });
        
        if (!emailResult.success) {
          throw new Error('Failed to create test email');
        }

        const mockMessageId = 'ses-message-id-67890';
        mockSend.mockResolvedValue({
          MessageId: mockMessageId
        });

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(emailResult.email, options);

        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.messageId).toBe(mockMessageId);
        }

        expect(mockSend).toHaveBeenCalledTimes(1);
        const sendCommand = mockSend.mock.calls[0][0];
        expect(sendCommand.input).toEqual(
          expect.objectContaining({
            Source: 'noreply@example.com', // Default from address
            Destination: {
              ToAddresses: [emailResult.email.to]
            }
          })
        );
      });

      it('should handle CC and BCC recipients', async () => {
        const emailResult = createEmail({
          to: 'test@example.com',
          subject: 'Test Subject',
          body: 'Test Body',
          from: 'sender@example.com',
          cc: 'cc@example.com',
          bcc: 'bcc@example.com'
        });
        
        if (!emailResult.success) {
          throw new Error('Failed to create test email');
        }

        const mockMessageId = 'ses-message-id-cc-bcc';
        mockSend.mockResolvedValue({
          MessageId: mockMessageId
        });

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(emailResult.email, options);

        expect(result.success).toBe(true);

        expect(mockSend).toHaveBeenCalledTimes(1);
        const sendCommand = mockSend.mock.calls[0][0];
        expect(sendCommand.input).toEqual(
          expect.objectContaining({
            Destination: {
              ToAddresses: [emailResult.email.to],
              CcAddresses: [emailResult.email.cc],
              BccAddresses: [emailResult.email.bcc]
            }
          })
        );
      });

      it('should handle ReplyTo address', async () => {
        const emailResult = createEmail({
          to: 'test@example.com',
          subject: 'Test Subject',
          body: 'Test Body',
          from: 'sender@example.com',
          replyTo: 'reply@example.com'
        });
        
        if (!emailResult.success) {
          throw new Error('Failed to create test email');
        }

        const mockMessageId = 'ses-message-id-reply';
        mockSend.mockResolvedValue({
          MessageId: mockMessageId
        });

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(emailResult.email, options);

        expect(result.success).toBe(true);

        expect(mockSend).toHaveBeenCalledTimes(1);
        const sendCommand = mockSend.mock.calls[0][0];
        expect(sendCommand.input).toEqual(
          expect.objectContaining({
            ReplyToAddresses: [emailResult.email.replyTo]
          })
        );
      });
    });

    describe('error handling', () => {
      it('should handle SES service errors', async () => {
        const sesError = new Error('MessageRejected: Email address not verified');
        sesError.name = 'MessageRejected';
        mockSend.mockRejectedValue(sesError);

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(testEmail, options);

        expect(result.success).toBe(false);
        if (!result.success) {
          expect(result.error).toBe('SES Error: Email address not verified');
        }

        expect(mockSend).toHaveBeenCalledTimes(1);
      });

      it('should handle network errors', async () => {
        const networkError = new Error('Network timeout');
        mockSend.mockRejectedValue(networkError);

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(testEmail, options);

        expect(result.success).toBe(false);
        if (!result.success) {
          expect(result.error).toBe('Failed to send email: Network timeout');
        }
      });

      it('should handle missing MessageId in response', async () => {
        mockSend.mockResolvedValue({}); // Response without MessageId

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(testEmail, options);

        expect(result.success).toBe(false);
        if (!result.success) {
          expect(result.error).toBe('SES did not return a MessageId');
        }
      });

      it('should handle unexpected response format', async () => {
        mockSend.mockResolvedValue(null);

        const options: SendOptions = { dryRun: false };
        const result = await sesEmailSender.send(testEmail, options);

        expect(result.success).toBe(false);
        if (!result.success) {
          expect(result.error).toBe('Invalid response from SES');
        }
      });
    });

    describe('default options', () => {
      it('should default to real mode when no options provided', async () => {
        const mockMessageId = 'ses-message-id-default';
        mockSend.mockResolvedValue({
          MessageId: mockMessageId
        });

        const result = await sesEmailSender.send(testEmail); // No options

        expect(result.success).toBe(true);
        if (result.success) {
          expect(result.messageId).toBe(mockMessageId);
        }

        expect(mockSend).toHaveBeenCalledTimes(1);
      });
    });
  });
});