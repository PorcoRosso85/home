/**
 * メールモジュールの公開API
 * 外部からはこのファイルのみを参照
 */

// 型定義のエクスポート
export type {
  Account,
  Email,
  Draft,
  AuthenticationError,
  MailFetchOptions,
  DraftCreateOptions,
  SyncStatus
} from "./types.ts";

// コアロジックのエクスポート
export {
  createReplySubject,
  validateAccount,
  isValidEmail,
  validateDraft,
  filterEmails,
  createReplyDraft
} from "./core.ts";

// アダプターインターフェースのエクスポート
export type {
  DatabaseAdapter,
  MailServerAdapter,
  EncryptionAdapter,
  AutoSaveAdapter,
  NetworkAdapter,
  SyncQueueAdapter
} from "./adapters.ts";

// アプリケーション層のエクスポート
export { MailService } from "./application/mail_service.ts";

// インフラストラクチャ層のエクスポート
export { GmailClient } from "./infrastructure/gmail_client.ts";
export { InMemoryDatabaseAdapter, MockMailServerAdapter } from "./infrastructure/mock_adapters.ts";