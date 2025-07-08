/**
 * アダプターインターフェース定義
 * 
 * @module mail/adapters
 * @description Infrastructure層が実装すべきインターフェース
 */

import type { Account, Email, Draft, MailFetchOptions, DraftCreateOptions } from "./types.ts";

/**
 * データベースアダプター
 * 
 * @description アカウント情報の永続化を担当
 */
export type DatabaseAdapter = {
  // アカウント操作
  saveAccount: (account: Account) => Promise<void>;
  getAccount: (email: string) => Promise<Account | null>;
  listAccounts: () => Promise<Account[]>;
  deleteAccount: (email: string) => Promise<void>;
  
  // メール操作
  saveEmails: (emails: Email[]) => Promise<void>;
  getEmails: (accountId: string, options?: { limit?: number }) => Promise<Email[]>;
  markEmailAsRead: (emailId: string) => Promise<void>;
  
  // 下書き操作
  saveDraft: (draft: Draft) => Promise<void>;
  getDraft: (draftId: string) => Promise<Draft | null>;
  listDrafts: (accountId: string) => Promise<Draft[]>;
  deleteDraft: (draftId: string) => Promise<void>;
  updateDraft: (draftId: string, updates: Partial<Draft>) => Promise<void>;
};

/**
 * メールサーバーアダプター
 * 
 * @description メールサーバーとの通信を担当
 */
export type MailServerAdapter = {
  // 認証
  authenticate: (account: Account) => Promise<{ success: boolean; error?: string }>;
  
  // メール取得
  fetchEmails: (account: Account, options: MailFetchOptions) => Promise<Email[]>;
  
  // メール送信
  sendEmail: (account: Account, draft: Draft) => Promise<{ success: boolean; messageId?: string }>;
};

/**
 * 暗号化アダプター
 */
export type EncryptionAdapter = {
  encrypt: (data: string) => Promise<string>;
  decrypt: (encryptedData: string) => Promise<string>;
};

/**
 * 自動保存アダプター
 */
export type AutoSaveAdapter = {
  startAutoSave: (
    draftId: string,
    intervalSeconds: number,
    onSave: () => Promise<void>
  ) => void;
  stopAutoSave: (draftId: string) => void;
};

/**
 * ネットワーク状態アダプター
 */
export type NetworkAdapter = {
  isOnline: () => boolean;
  onOnline: (callback: () => void) => void;
  onOffline: (callback: () => void) => void;
};

/**
 * 同期キューアダプター
 */
export type SyncQueueAdapter = {
  addOperation: (operation: {
    type: "markAsRead" | "deleteEmail" | "sendDraft";
    data: unknown;
  }) => Promise<void>;
  
  getPendingOperations: () => Promise<Array<{
    id: string;
    type: string;
    data: unknown;
  }>>;
  
  removeOperation: (operationId: string) => Promise<void>;
  
  processQueue: () => Promise<{ success: number; failed: number }>;
};