/**
 * メール機能の型定義
 * Domain層：他層に依存しない
 */

export interface Account {
  id: string;
  email: string;
  provider: "gmail" | "outlook" | "custom";
  authType: "oauth2" | "password";
  createdAt: Date;
  updatedAt: Date;
}

export interface Email {
  id: string;
  accountId: string;
  messageId: string;
  subject: string;
  fromAddress: string;
  toAddresses: string[];
  ccAddresses?: string[];
  bodyText?: string;
  bodyHtml?: string;
  headers: Record<string, string>;
  isRead: boolean;
  receivedAt: Date;
  fromCache?: boolean;
}

export interface Draft {
  id: string;
  accountId: string;
  replyToEmailId?: string;
  subject: string;
  toAddresses: string[];
  ccAddresses?: string[];
  body: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface AuthenticationError extends Error {
  code: "INVALID_CREDENTIALS" | "NETWORK_ERROR" | "OAUTH_FAILED";
}

export interface MailFetchOptions {
  account: string;
  unreadOnly?: boolean;
  since?: Date;
  limit?: number;
}

export interface DraftCreateOptions {
  account: string;
  to: string[];
  cc?: string[];
  subject?: string;
  body?: string;
  replyToEmailId?: string;
}

export interface SyncStatus {
  pendingOperations: number;
  lastSyncSuccess: boolean;
  lastSyncAt?: Date;
}