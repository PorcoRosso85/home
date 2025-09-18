/**
 * Archive Executor Implementation
 * Handles transactional archiving with rollback capabilities
 */

import type { StorageAdapter } from "../../../storage/s3/mod.ts";
import type { TemplateEvent } from "./types.ts";

export interface ArchiveOperation {
  event: TemplateEvent;
  localPath: string;
}

export interface ArchiveResult {
  successful: ArchiveOperation[];
  failed: Array<{
    operation: ArchiveOperation;
    error: Error;
  }>;
}

export interface ArchiveExecutorOptions {
  verifyAfterUpload?: boolean;
  deleteLocalAfterVerify?: boolean;
  batchSize?: number;
}

export class ArchiveExecutor {
  private readonly bucketPrefix = "events/";
  
  constructor(
    private storageAdapter: StorageAdapter,
    private options: ArchiveExecutorOptions = {}
  ) {}

  /**
   * Execute archive operations with partial failure handling
   * Successful operations proceed, failed operations are reported
   */
  async execute(operations: ArchiveOperation[]): Promise<ArchiveResult> {
    const result: ArchiveResult = {
      successful: [],
      failed: []
    };

    for (const operation of operations) {
      try {
        await this.processOperation(operation);
        result.successful.push(operation);
      } catch (error) {
        result.failed.push({
          operation,
          error: error instanceof Error ? error : new Error(String(error))
        });
      }
    }

    return result;
  }

  /**
   * Execute archive operations transactionally
   * All operations must succeed or all are rolled back
   */
  async executeTransactional(operations: ArchiveOperation[]): Promise<void> {
    const uploadedKeys: string[] = [];
    const processedOperations: ArchiveOperation[] = [];

    try {
      // Process operations in batches if batchSize is specified
      const batchSize = this.options.batchSize || operations.length;
      
      for (let i = 0; i < operations.length; i += batchSize) {
        const batch = operations.slice(i, Math.min(i + batchSize, operations.length));
        
        for (const operation of batch) {
          const key = await this.uploadToS3(operation);
          uploadedKeys.push(key);
          
          if (this.options.verifyAfterUpload) {
            await this.verifyUpload(key, operation.event);
          }
          
          processedOperations.push(operation);
        }
      }

      // Delete local files only after all uploads and verifications succeed
      if (this.options.deleteLocalAfterVerify) {
        for (const operation of processedOperations) {
          await this.deleteLocalFile(operation.localPath);
        }
      }
    } catch (error) {
      // Rollback: delete all uploaded files from S3
      if (uploadedKeys.length > 0) {
        try {
          await this.storageAdapter.delete(uploadedKeys);
        } catch (rollbackError) {
          console.error("Rollback failed:", rollbackError);
        }
      }
      
      throw new Error(`Transaction failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async processOperation(operation: ArchiveOperation): Promise<void> {
    // Upload to S3 (this will also read the local file)
    const key = await this.uploadToS3(operation);
    
    // Verify if requested
    if (this.options.verifyAfterUpload) {
      await this.verifyUpload(key, operation.event);
    }
    
    // Delete local file if requested
    if (this.options.deleteLocalAfterVerify) {
      await this.deleteLocalFile(operation.localPath);
    }
  }

  private async readLocalFile(path: string): Promise<string> {
    try {
      return await Deno.readTextFile(path);
    } catch (error) {
      throw new Error(`Failed to read local file ${path}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async uploadToS3(operation: ArchiveOperation): Promise<string> {
    // Validate event has required fields
    if (!operation.event.id) {
      throw new Error("Event ID is required");
    }

    // Read the local file first to ensure it exists
    const content = await this.readLocalFile(operation.localPath);

    const key = `${this.bucketPrefix}${operation.event.timestamp}/${operation.event.id}.json`;
    
    try {
      await this.storageAdapter.upload(key, content, {
        contentType: "application/json",
        metadata: {
          template: operation.event.template,
          clientId: operation.event.clientId || "",
          timestamp: operation.event.timestamp.toString()
        }
      });
      
      return key;
    } catch (error) {
      throw new Error(`Failed to upload to S3: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async verifyUpload(key: string, expectedEvent: TemplateEvent): Promise<void> {
    try {
      const result = await this.storageAdapter.download(key);
      const content = new TextDecoder().decode(result.content);
      const actualEvent = JSON.parse(content) as TemplateEvent;
      
      // Verify key fields match
      if (actualEvent.id !== expectedEvent.id || 
          actualEvent.timestamp !== expectedEvent.timestamp ||
          actualEvent.template !== expectedEvent.template) {
        throw new Error("Verification failed: uploaded event does not match");
      }
    } catch (error) {
      throw new Error(`Verification failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  private async deleteLocalFile(path: string): Promise<void> {
    try {
      await Deno.remove(path);
    } catch (error) {
      throw new Error(`Failed to delete local file ${path}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}