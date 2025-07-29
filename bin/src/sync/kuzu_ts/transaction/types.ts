/**
 * Transaction Management Types
 * KuzuDBのトランザクション管理型定義
 */

import type { TemplateEvent, EventGroup } from "../event_sourcing/types.ts";
import type { KuzuWasmClient } from "../types.ts";

// ========== Transaction Types ==========

export type TransactionStatus = 'active' | 'committed' | 'rolled_back';

export type Transaction = {
  id: string;
  status: TransactionStatus;
  startTime: number;
  endTime?: number;
  eventGroupId?: string;
};

export type TransactionOptions = {
  timeout?: number; // ミリ秒単位でのタイムアウト
  retryCount?: number; // リトライ回数
  isolationLevel?: 'read_committed' | 'serializable'; // 分離レベル
};

export type TransactionResult<T> = {
  success: boolean;
  data?: T;
  error?: Error;
  transaction: Transaction;
};

// ========== TransactionManager Type ==========

export type TransactionManager = {
  /**
   * 新しいトランザクションを開始
   * KuzuDBのBEGINコマンドをラップ
   */
  beginTransaction(options?: TransactionOptions): Promise<Transaction>;

  /**
   * 現在のトランザクションをコミット
   * KuzuDBのCOMMITコマンドをラップ
   */
  commitTransaction(transactionId: string): Promise<void>;

  /**
   * 現在のトランザクションをロールバック
   * KuzuDBのROLLBACKコマンドをラップ
   */
  rollbackTransaction(transactionId: string, reason?: string): Promise<void>;

  /**
   * トランザクション内でイベントグループを実行
   * 失敗時は自動的にロールバック
   */
  executeInTransaction<T>(
    callback: (tx: TransactionContext) => Promise<T>,
    options?: TransactionOptions
  ): Promise<TransactionResult<T>>;

  /**
   * トランザクションの状態を取得
   */
  getTransactionStatus(transactionId: string): TransactionStatus | undefined;

  /**
   * アクティブなトランザクションのリストを取得
   */
  getActiveTransactions(): Transaction[];

  /**
   * トランザクション履歴を取得
   */
  getTransactionHistory(): Transaction[];
};

// ========== Transaction Context ==========

export type TransactionContext = {
  /**
   * トランザクションID
   */
  transactionId: string;

  /**
   * トランザクション内でテンプレートを実行
   */
  executeTemplate(template: string, params: Record<string, unknown>): Promise<TemplateEvent>;

  /**
   * トランザクション内で複数のイベントを実行
   */
  executeEventGroup(events: TemplateEvent[]): Promise<EventGroup>;

  /**
   * トランザクション内でクエリを実行
   */
  query(cypher: string, params?: Record<string, unknown>): Promise<unknown>;

  /**
   * 現在のトランザクション状態を取得
   */
  getStatus(): TransactionStatus;
};

// ========== Error Types ==========

export class TransactionError extends Error {
  constructor(
    message: string,
    public readonly transactionId: string,
    public readonly code: TransactionErrorCode
  ) {
    super(message);
    this.name = 'TransactionError';
  }
}

export enum TransactionErrorCode {
  ALREADY_ACTIVE = 'ALREADY_ACTIVE',
  NOT_FOUND = 'NOT_FOUND',
  ALREADY_COMMITTED = 'ALREADY_COMMITTED',
  ALREADY_ROLLED_BACK = 'ALREADY_ROLLED_BACK',
  TIMEOUT = 'TIMEOUT',
  DEADLOCK = 'DEADLOCK',
  SERIALIZATION_FAILURE = 'SERIALIZATION_FAILURE',
  CONNECTION_LOST = 'CONNECTION_LOST',
}

// ========== Integration Types ==========

export type TransactionalKuzuClient = KuzuWasmClient & {
  /**
   * トランザクションマネージャーを取得
   */
  getTransactionManager(): TransactionManager;

  /**
   * トランザクション内でテンプレートを実行
   * （BrowserKuzuClientのexecuteTemplateをオーバーライド）
   */
  executeTemplate(
    template: string,
    params: Record<string, unknown>,
    transactionId?: string
  ): Promise<TemplateEvent>;
};