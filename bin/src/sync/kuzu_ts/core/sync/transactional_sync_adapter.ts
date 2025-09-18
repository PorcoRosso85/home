/**
 * TransactionalSyncAdapter - Transaction-aware WebSocket Sync
 * トランザクション対応WebSocket同期アダプター
 */

import type { WebSocketSync } from "../websocket/types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";

/**
 * Transaction state for buffering events
 * イベントバッファリング用のトランザクション状態
 */
type TransactionState = {
  id: string;
  events: TemplateEvent[];
  parentId?: string;
};

/**
 * TransactionalSyncAdapter wraps WebSocketSync to provide transaction support
 * WebSocketSyncをラップしてトランザクションサポートを提供
 */
export class TransactionalSyncAdapter implements WebSocketSync {
  private transactions: Map<string, TransactionState> = new Map();
  private currentTransactionId?: string;
  private transactionStack: string[] = [];

  constructor(private webSocketSync: WebSocketSync) {}

  /**
   * Connect to WebSocket server
   * WebSocketサーバーに接続
   */
  async connect(url: string): Promise<void> {
    return this.webSocketSync.connect(url);
  }

  /**
   * Send event - buffers if in transaction, sends immediately otherwise
   * イベント送信 - トランザクション中はバッファリング、それ以外は即座に送信
   */
  async sendEvent(event: TemplateEvent): Promise<void> {
    const activeTransactionId = this.getActiveTransactionId();
    
    if (activeTransactionId) {
      // Buffer event in active transaction
      const transaction = this.transactions.get(activeTransactionId);
      if (transaction) {
        transaction.events.push(event);
      }
    } else {
      // No active transaction - send immediately
      return this.webSocketSync.sendEvent(event);
    }
  }

  /**
   * Register event handler
   * イベントハンドラーを登録
   */
  onEvent(handler: (event: TemplateEvent) => void): void {
    this.webSocketSync.onEvent(handler);
  }

  /**
   * Disconnect from WebSocket server
   * WebSocketサーバーから切断
   */
  disconnect(): void {
    this.webSocketSync.disconnect();
  }

  /**
   * Check if connected
   * 接続状態を確認
   */
  isConnected(): boolean {
    return this.webSocketSync.isConnected();
  }

  /**
   * Get pending events
   * 保留中のイベントを取得
   */
  async getPendingEvents(): Promise<TemplateEvent[]> {
    return this.webSocketSync.getPendingEvents();
  }

  // ========== Transaction Management ==========

  /**
   * Begin a new transaction
   * 新しいトランザクションを開始
   */
  beginTransaction(transactionId?: string): string {
    const txId = transactionId || `tx_${crypto.randomUUID()}`;
    const parentId = this.currentTransactionId;

    const transaction: TransactionState = {
      id: txId,
      events: [],
      parentId,
    };

    this.transactions.set(txId, transaction);
    
    // Push to stack for nested transactions
    this.transactionStack.push(txId);
    this.currentTransactionId = txId;

    return txId;
  }

  /**
   * Commit a transaction - sends all buffered events
   * トランザクションをコミット - バッファリングされた全イベントを送信
   */
  async commitTransaction(transactionId: string): Promise<void> {
    const transaction = this.transactions.get(transactionId);
    
    if (!transaction) {
      throw new Error(`Transaction not found: ${transactionId}`);
    }

    // Remove from stack
    const stackIndex = this.transactionStack.indexOf(transactionId);
    if (stackIndex >= 0) {
      this.transactionStack.splice(stackIndex, 1);
    }

    // Update current transaction to parent or previous in stack
    if (this.currentTransactionId === transactionId) {
      this.currentTransactionId = this.transactionStack[this.transactionStack.length - 1];
    }

    // If this transaction has a parent, move events to parent
    if (transaction.parentId) {
      const parentTransaction = this.transactions.get(transaction.parentId);
      if (parentTransaction) {
        parentTransaction.events.push(...transaction.events);
      }
    } else {
      // No parent - send all events
      for (const event of transaction.events) {
        await this.webSocketSync.sendEvent(event);
      }
    }

    // Clean up
    this.transactions.delete(transactionId);
  }

  /**
   * Rollback a transaction - discards all buffered events
   * トランザクションをロールバック - バッファリングされた全イベントを破棄
   */
  async rollbackTransaction(transactionId: string): Promise<void> {
    const transaction = this.transactions.get(transactionId);
    
    if (!transaction) {
      throw new Error(`Transaction not found: ${transactionId}`);
    }

    // Remove from stack
    const stackIndex = this.transactionStack.indexOf(transactionId);
    if (stackIndex >= 0) {
      this.transactionStack.splice(stackIndex, 1);
    }

    // Update current transaction to parent or previous in stack
    if (this.currentTransactionId === transactionId) {
      this.currentTransactionId = this.transactionStack[this.transactionStack.length - 1];
    }

    // Simply discard the transaction and its events
    this.transactions.delete(transactionId);
  }

  /**
   * Set transaction context (for integration with TransactionManager)
   * トランザクションコンテキストを設定（TransactionManagerとの統合用）
   */
  setTransactionContext(transactionId: string): void {
    if (!this.transactions.has(transactionId)) {
      // Create transaction state if it doesn't exist
      this.beginTransaction(transactionId);
    } else {
      // Set as current transaction
      this.currentTransactionId = transactionId;
      if (!this.transactionStack.includes(transactionId)) {
        this.transactionStack.push(transactionId);
      }
    }
  }

  /**
   * Clear transaction context
   * トランザクションコンテキストをクリア
   */
  clearTransactionContext(): void {
    this.currentTransactionId = undefined;
    // Keep transactions in map for later commit/rollback
  }

  /**
   * Get the currently active transaction ID
   * 現在アクティブなトランザクションIDを取得
   */
  private getActiveTransactionId(): string | undefined {
    return this.currentTransactionId;
  }

  /**
   * Get all active transactions (for debugging)
   * すべてのアクティブなトランザクションを取得（デバッグ用）
   */
  getActiveTransactions(): string[] {
    return Array.from(this.transactions.keys());
  }

  /**
   * Get transaction state (for debugging)
   * トランザクション状態を取得（デバッグ用）
   */
  getTransactionState(transactionId: string): TransactionState | undefined {
    return this.transactions.get(transactionId);
  }
}