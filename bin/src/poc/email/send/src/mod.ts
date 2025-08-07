/**
 * Module exports for Email Send Service
 * Central export point for all public APIs and factory functions
 */

// Domain layer exports
export type { Email, EmailInput, CreateEmailResult } from './domain/email.js';
export { createEmail } from './domain/email.js';

export type { 
  EmailSenderPort, 
  StoragePort, 
  SendOptions, 
  SendResult, 
  StorageResult 
} from './domain/ports.js';

// Application layer exports
export { SendService } from './application/send-service.js';

// Adapter factory functions (not internal implementation details)
export { createSESEmailSender } from './infrastructure/sender/ses.js';
export type { SESConfig, SESEmailSenderResult } from './infrastructure/sender/ses.js';

export { InMemoryStorage } from './infrastructure/storage/memory.js';

// Environment variables utility
export { 
  getAWSRegion, 
  getAWSAccessKeyId, 
  getAWSSecretAccessKey, 
  getAWSSESConfig,
  type AWSEnvironmentVariables,
  type AWSSESConfigResult
} from './variables.js';