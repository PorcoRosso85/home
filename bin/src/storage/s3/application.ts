/**
 * Application layer for S3 operations
 * Now uses the Storage Adapter pattern for flexibility
 */

import type { S3Command, S3Result, S3Config, HelpResult, ErrorResult } from './domain.ts';
import { createStorageAdapter, type StorageAdapter, type StorageConfig } from './adapter.ts';

/**
 * Execute an S3 command with the given configuration
 * This function now uses the adapter pattern to support multiple storage backends
 */
export async function executeS3Command(
  command: S3Command,
  config: S3Config
): Promise<S3Result> {
  try {
    // Handle help command without storage adapter
    if (command.action === 'help') {
      return generateHelp();
    }

    // Convert S3Config to StorageConfig
    const storageConfig: StorageConfig = config.endpoint ? {
      type: 's3',
      endpoint: config.endpoint,
      region: config.region,
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
      bucket: config.bucket
    } : {
      type: 'auto'  // Will use in-memory adapter as default
    };

    // Create storage adapter
    const adapter = createStorageAdapter(storageConfig);

    // Execute command based on action
    switch (command.action) {
      case 'list':
        const listResult = await adapter.list({
          prefix: command.prefix,
          maxKeys: command.maxKeys,
          continuationToken: command.continuationToken
        });
        return {
          type: 'list',
          objects: listResult.objects,
          continuationToken: listResult.continuationToken,
          isTruncated: listResult.isTruncated
        };
      
      case 'upload':
        const uploadResult = await adapter.upload(command.key, command.content, {
          contentType: command.contentType,
          metadata: command.metadata
        });
        return {
          type: 'upload',
          key: uploadResult.key,
          etag: uploadResult.etag,
          versionId: uploadResult.versionId
        };
      
      case 'download':
        const downloadResult = await adapter.download(command.key, {
          outputPath: command.outputPath
        });
        
        // If outputPath was specified, the adapter should have saved the file
        if (command.outputPath) {
          return {
            type: 'download',
            key: downloadResult.key,
            savedTo: command.outputPath,
            contentType: downloadResult.contentType,
            metadata: downloadResult.metadata
          };
        } else {
          // Return content as string
          const content = new TextDecoder().decode(downloadResult.content);
          return {
            type: 'download',
            key: downloadResult.key,
            content,
            contentType: downloadResult.contentType,
            metadata: downloadResult.metadata
          };
        }
      
      case 'delete':
        const deleteResult = await adapter.delete(command.keys);
        return {
          type: 'delete',
          deleted: deleteResult.deleted,
          errors: deleteResult.errors
        };
      
      case 'info':
        const infoResult = await adapter.info(command.key);
        return {
          type: 'info',
          key: infoResult.key,
          exists: infoResult.exists,
          size: infoResult.size,
          lastModified: infoResult.lastModified,
          contentType: infoResult.contentType,
          metadata: infoResult.metadata
        };
      
      default:
        // @ts-expect-error - exhaustive check
        return { type: 'error', message: `Unknown action: ${command.action}` };
    }
  } catch (error) {
    return {
      type: 'error',
      message: error instanceof Error ? error.message : 'Unknown error occurred',
      details: error
    } as ErrorResult;
  }
}

/**
 * Generate help information
 */
function generateHelp(): HelpResult {
  return {
    type: 'help',
    message: 'S3 Storage Module - Available Commands',
    examples: [
      {
        description: 'List objects in a bucket',
        command: {
          action: 'list',
          prefix: 'photos/',
          maxKeys: 100
        }
      },
      {
        description: 'Upload a file',
        command: {
          action: 'upload',
          key: 'documents/report.pdf',
          content: 'base64-encoded-content-here',
          contentType: 'application/pdf'
        }
      },
      {
        description: 'Download a file',
        command: {
          action: 'download',
          key: 'documents/report.pdf',
          outputPath: './downloads/report.pdf'
        }
      },
      {
        description: 'Delete objects',
        command: {
          action: 'delete',
          keys: ['temp/file1.txt', 'temp/file2.txt']
        }
      },
      {
        description: 'Get object information',
        command: {
          action: 'info',
          key: 'documents/report.pdf'
        }
      }
    ]
  };
}