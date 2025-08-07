/**
 * AWS SES Email Sender Adapter
 * Implements EmailSenderPort using AWS Simple Email Service
 */

import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';
import type { Email } from '../../domain/email.js';
import type { EmailSenderPort, SendOptions, SendResult } from '../../domain/ports.js';

/**
 * Configuration for AWS SES client
 */
export type SESConfig = {
  readonly region: string;
  readonly credentials: {
    readonly accessKeyId: string;
    readonly secretAccessKey: string;
  };
}

/**
 * Result type for SES Email Sender factory function
 */
export type SESEmailSenderResult = 
  | { success: true; sender: SESEmailSender }
  | { success: false; error: string };

/**
 * SES Email Sender implementation
 * Handles email sending via AWS SES with dry run support
 */
export class SESEmailSender implements EmailSenderPort {
  private readonly sesClient: SESClient;
  private readonly defaultFromAddress = 'noreply@example.com';

  /**
   * Create SES Email Sender with AWS configuration
   * @param config - AWS SES configuration including region and credentials
   */
  constructor(config: SESConfig) {
    this.validateConfig(config);
    
    this.sesClient = new SESClient({
      region: config.region,
      credentials: {
        accessKeyId: config.credentials.accessKeyId,
        secretAccessKey: config.credentials.secretAccessKey
      }
    });
  }

  /**
   * Validate SES configuration
   * @param config - Configuration to validate
   * @throws Error if configuration is invalid
   */
  private validateConfig(config: SESConfig): void {
    if (!config.region || config.region.trim() === '') {
      throw new Error('Region is required');
    }
    
    if (!config.credentials.accessKeyId || config.credentials.accessKeyId.trim() === '') {
      throw new Error('Access key ID is required');
    }
    
    if (!config.credentials.secretAccessKey || config.credentials.secretAccessKey.trim() === '') {
      throw new Error('Secret access key is required');
    }
  }

  /**
   * Send email with optional dry run support
   * @param email - Email to send
   * @param options - Send options including dry run mode
   * @returns Promise resolving to send result
   */
  async send(email: Email, options: SendOptions = { dryRun: false }): Promise<SendResult> {
    try {
      if (options.dryRun) {
        return this.handleDryRun(email);
      }
      
      return await this.sendViaAWS(email);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Handle dry run mode - log email details and return mock message ID
   * @param email - Email that would be sent
   * @returns Mock send result
   */
  private handleDryRun(email: Email): SendResult {
    const emailDetails = {
      to: email.to,
      subject: email.subject,
      body: email.body,
      ...(email.from && { from: email.from }),
      ...(email.cc && { cc: email.cc }),
      ...(email.bcc && { bcc: email.bcc }),
      ...(email.replyTo && { replyTo: email.replyTo })
    };

    console.log('[SES Dry Run] Email would be sent:', emailDetails);
    
    // Generate mock message ID
    const randomId = Math.random().toString(36).substring(2, 14);
    const mockMessageId = `ses-dry-run-${randomId}`;
    
    return { success: true, messageId: mockMessageId };
  }

  /**
   * Send email via AWS SES
   * @param email - Email to send
   * @returns Send result with message ID from SES
   */
  private async sendViaAWS(email: Email): Promise<SendResult> {
    const sendEmailCommand = new SendEmailCommand({
      Source: email.from || this.defaultFromAddress,
      Destination: {
        ToAddresses: [email.to],
        ...(email.cc && { CcAddresses: [email.cc] }),
        ...(email.bcc && { BccAddresses: [email.bcc] })
      },
      Message: {
        Subject: {
          Data: email.subject,
          Charset: 'UTF-8'
        },
        Body: {
          Text: {
            Data: email.body,
            Charset: 'UTF-8'
          }
        }
      },
      ...(email.replyTo && { ReplyToAddresses: [email.replyTo] })
    });

    const response = await this.sesClient.send(sendEmailCommand);
    
    if (!response || !response.MessageId) {
      if (!response) {
        return { success: false, error: 'Invalid response from SES' };
      }
      return { success: false, error: 'SES did not return a MessageId' };
    }
    
    return { success: true, messageId: response.MessageId };
  }

  /**
   * Handle errors that occur during email sending
   * @param error - Error that occurred
   * @returns Error send result
   */
  private handleError(error: unknown): SendResult {
    if (error instanceof Error) {
      // Handle specific SES errors
      if (error.name && error.name.includes('MessageRejected')) {
        return { 
          success: false, 
          error: `SES Error: ${error.message.replace('MessageRejected: ', '')}` 
        };
      }
      
      // Handle other AWS SES errors
      if (error.name && (error.name.includes('SES') || error.name.includes('AWS'))) {
        return { 
          success: false, 
          error: `SES Error: ${error.message}` 
        };
      }
      
      // Handle general errors
      return { 
        success: false, 
        error: `Failed to send email: ${error.message}` 
      };
    }
    
    return { 
      success: false, 
      error: 'Unknown error occurred while sending email' 
    };
  }
}

/**
 * Factory function to create SESEmailSender with validation
 * Returns Result type instead of throwing exceptions
 * @param config - AWS SES configuration including region and credentials
 * @returns Result with SESEmailSender instance or error message
 */
export function createSESEmailSender(config: SESConfig): SESEmailSenderResult {
  try {
    // Validate configuration before creating instance
    if (!config.region || config.region.trim() === '') {
      return { success: false, error: 'Region is required' };
    }
    
    if (!config.credentials.accessKeyId || config.credentials.accessKeyId.trim() === '') {
      return { success: false, error: 'Access key ID is required' };
    }
    
    if (!config.credentials.secretAccessKey || config.credentials.secretAccessKey.trim() === '') {
      return { success: false, error: 'Secret access key is required' };
    }

    // Create SESEmailSender instance
    const sender = new SESEmailSender(config);
    
    return { success: true, sender };
  } catch (error) {
    if (error instanceof Error) {
      return { success: false, error: error.message };
    }
    
    return { success: false, error: 'Unknown error occurred while creating SES Email Sender' };
  }
}