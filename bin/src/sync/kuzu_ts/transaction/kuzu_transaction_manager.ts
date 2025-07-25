/**
 * KuzuTransactionManager - KuzuDB Transaction Integration
 * KuzuDBのトランザクション統合実装
 */

import type { 
  TransactionManager, 
  Transaction, 
  TransactionStatus,
  TransactionOptions,
  TransactionContext,
  TransactionResult
} from "./types.ts";
import type { TemplateEvent, EventGroup, EventGroupStatus } from "../event_sourcing/types.ts";
import type { BrowserKuzuClient } from "../types.ts";
import type { BrowserKuzuClientImpl } from "../core/client/browser_kuzu_client.ts";
import { TransactionError, TransactionErrorCode } from "./types.ts";
import { EventGroupManager } from "../event_sourcing/event_group_manager.ts";

/**
 * Transaction context implementation
 * トランザクションコンテキストの実装
 */
class KuzuTransactionContext implements TransactionContext {
  constructor(
    public readonly transactionId: string,
    private client: BrowserKuzuClient,
    private eventGroupManager: EventGroupManager,
    private manager: KuzuTransactionManager
  ) {}

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    const event: TemplateEvent = {
      id: `evt_${crypto.randomUUID()}`,
      template,
      params,
      timestamp: Date.now(),
    };

    // Create single event group
    const eventGroup = await this.eventGroupManager.createEventGroup([event]);
    
    // Execute template through client (which should use the transaction)
    await this.client.executeTemplate(template, params);
    
    // Mark as committed in event group
    await this.eventGroupManager.commit(eventGroup.id, {
      addEvent: () => {},
      committedEvents: []
    });

    return event;
  }

  async executeEventGroup(events: TemplateEvent[]): Promise<EventGroup> {
    // Create event group
    const eventGroup = await this.eventGroupManager.createEventGroup(events);
    
    // Execute all events
    for (const event of events) {
      await this.client.executeTemplate(event.template, event.params);
    }
    
    // Mark as committed
    await this.eventGroupManager.commit(eventGroup.id, {
      addEvent: () => {},
      committedEvents: []
    });

    return eventGroup;
  }

  async query(cypher: string, params?: Record<string, any>): Promise<any> {
    return await this.client.executeQuery(cypher, params);
  }

  getStatus(): TransactionStatus {
    return this.manager.getTransactionStatus(this.transactionId) || "active";
  }
}

/**
 * KuzuDB Transaction Manager Implementation
 * KuzuDBトランザクションマネージャー実装
 */
export class KuzuTransactionManager implements TransactionManager {
  private transactions: Map<string, Transaction> = new Map();
  private activeTransactions: Set<string> = new Set();
  private transactionHistory: Transaction[] = [];
  private eventGroupManager: EventGroupManager;
  private timeoutHandlers: Map<string, number> = new Map();

  constructor(private client: BrowserKuzuClient) {
    this.eventGroupManager = new EventGroupManager();
  }

  async beginTransaction(options?: TransactionOptions): Promise<Transaction> {
    const transactionId = `tx_${crypto.randomUUID()}`;
    
    // Execute BEGIN TRANSACTION
    await this.client.executeQuery("BEGIN TRANSACTION");
    
    const transaction: Transaction = {
      id: transactionId,
      status: "active",
      startTime: Date.now(),
    };

    this.transactions.set(transactionId, transaction);
    this.activeTransactions.add(transactionId);
    this.transactionHistory.push(transaction);

    // Don't set timeout here - it will be handled in executeInTransaction

    return transaction;
  }

  async commitTransaction(transactionId: string): Promise<void> {
    const transaction = this.transactions.get(transactionId);
    
    if (!transaction) {
      throw new TransactionError(
        `Transaction not found: ${transactionId}`,
        transactionId,
        TransactionErrorCode.NOT_FOUND
      );
    }

    if (transaction.status === "committed") {
      throw new TransactionError(
        `Transaction already committed: ${transactionId}`,
        transactionId,
        TransactionErrorCode.ALREADY_COMMITTED
      );
    }

    if (transaction.status === "rolled_back") {
      throw new TransactionError(
        `Transaction already rolled back: ${transactionId}`,
        transactionId,
        TransactionErrorCode.ALREADY_ROLLED_BACK
      );
    }

    // Clear timeout if exists
    this.clearTimeout(transactionId);

    // Execute COMMIT
    await this.client.executeQuery("COMMIT");
    
    // Update transaction status
    transaction.status = "committed";
    transaction.endTime = Date.now();
    this.activeTransactions.delete(transactionId);
  }

  async rollbackTransaction(transactionId: string, reason?: string): Promise<void> {
    const transaction = this.transactions.get(transactionId);
    
    if (!transaction) {
      throw new TransactionError(
        `Transaction not found: ${transactionId}`,
        transactionId,
        TransactionErrorCode.NOT_FOUND
      );
    }

    if (transaction.status !== "active") {
      return; // Already committed or rolled back
    }

    // Clear timeout if exists
    this.clearTimeout(transactionId);

    // Execute ROLLBACK
    await this.client.executeQuery("ROLLBACK");
    
    // Update transaction status
    transaction.status = "rolled_back";
    transaction.endTime = Date.now();
    this.activeTransactions.delete(transactionId);
  }

  async executeInTransaction<T>(
    callback: (tx: TransactionContext) => Promise<T>,
    options?: TransactionOptions
  ): Promise<TransactionResult<T>> {
    const transaction = await this.beginTransaction(options);
    const context = new KuzuTransactionContext(
      transaction.id,
      this.client,
      this.eventGroupManager,
      this
    );

    let timeoutId: number | undefined;

    try {
      // Execute the callback
      let data: T;
      
      if (options?.timeout) {
        // Create a promise that will reject on timeout
        const timeoutPromise = new Promise<never>((_, reject) => {
          timeoutId = setTimeout(() => {
            reject(new TransactionError(
              "Transaction timeout",
              transaction.id,
              TransactionErrorCode.TIMEOUT
            ));
          }, options.timeout);
        });

        // Race between the callback and the timeout
        data = await Promise.race([
          callback(context),
          timeoutPromise
        ]);
      } else {
        // No timeout, just execute normally
        data = await callback(context);
      }

      // Clear the timeout if it exists
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Check if transaction was rolled back by timeout handler
      const currentStatus = this.getTransactionStatus(transaction.id);
      if (currentStatus === "rolled_back") {
        return {
          success: false,
          error: new TransactionError(
            "Transaction timeout",
            transaction.id,
            TransactionErrorCode.TIMEOUT
          ),
          transaction: this.transactions.get(transaction.id)!,
        };
      }

      await this.commitTransaction(transaction.id);
      
      return {
        success: true,
        data,
        transaction: this.transactions.get(transaction.id)!,
      };
    } catch (error) {
      // Clear the timeout if it exists
      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      // Check if transaction already rolled back
      const currentStatus = this.getTransactionStatus(transaction.id);
      if (currentStatus !== "rolled_back") {
        // Check if it's a serialization conflict
        if (error instanceof Error && error.message.includes("conflict")) {
          await this.rollbackTransaction(transaction.id, error.message);
          
          return {
            success: false,
            error: new TransactionError(
              error.message,
              transaction.id,
              TransactionErrorCode.SERIALIZATION_FAILURE
            ),
            transaction: this.transactions.get(transaction.id)!,
          };
        }

        // Regular error - rollback
        await this.rollbackTransaction(transaction.id, error instanceof Error ? error.message : String(error));
      }

      // Return the error
      if (error instanceof TransactionError) {
        return {
          success: false,
          error,
          transaction: this.transactions.get(transaction.id)!,
        };
      }
      
      return {
        success: false,
        error: error instanceof Error ? error : new Error(String(error)),
        transaction: this.transactions.get(transaction.id)!,
      };
    }
  }

  getTransactionStatus(transactionId: string): TransactionStatus | undefined {
    return this.transactions.get(transactionId)?.status;
  }

  getActiveTransactions(): Transaction[] {
    return Array.from(this.activeTransactions).map(id => this.transactions.get(id)!);
  }

  getTransactionHistory(): Transaction[] {
    return [...this.transactionHistory];
  }

  private async handleTimeout(transactionId: string): Promise<void> {
    const transaction = this.transactions.get(transactionId);
    if (transaction && transaction.status === "active") {
      // Mark transaction as timed out
      transaction.status = "rolled_back";
      transaction.endTime = Date.now();
      this.activeTransactions.delete(transactionId);
      
      // Execute rollback
      try {
        await this.client.executeQuery("ROLLBACK");
      } catch (error) {
        // Ignore rollback errors in timeout handler
      }
    }
  }

  private clearTimeout(transactionId: string): void {
    const timeoutId = this.timeoutHandlers.get(transactionId);
    if (timeoutId) {
      clearTimeout(timeoutId);
      this.timeoutHandlers.delete(transactionId);
    }
  }
}