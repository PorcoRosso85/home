/**
 * AWS S3 Storage Adapter Implementation
 * Provides S3 and S3-compatible storage operations
 */

import { S3Client } from "../infrastructure.ts";
import { validateS3Key, validateS3ObjectSize, validateS3BucketName } from "../domain.ts";
import { 
  StorageAdapter, 
  StorageConfig,
  StorageListOptions,
  StorageListResult,
  StorageUploadOptions,
  StorageUploadResult,
  StorageDownloadOptions,
  StorageDownloadResult,
  StorageDeleteResult,
  StorageInfoResult
} from "../adapter.ts";

export class S3CompatibleAdapter implements StorageAdapter {
  private s3Client: S3Client;
  
  constructor(private config: Extract<StorageConfig, { type: "s3" }>) {
    // Validate bucket name before creating client
    validateS3BucketName(config.bucket);
    
    // Import and use the existing S3Client
    this.s3Client = new S3Client({
      endpoint: config.endpoint,
      region: config.region,
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
      bucket: config.bucket
    });
  }
  
  async list(options?: StorageListOptions): Promise<StorageListResult> {
    const result = await this.s3Client.listObjects({
      action: 'list',
      prefix: options?.prefix,
      maxKeys: options?.maxKeys,
      continuationToken: options?.continuationToken
    });
    
    return {
      objects: result.objects.map(obj => ({
        key: obj.key,
        lastModified: obj.lastModified,
        size: obj.size,
        etag: obj.etag
      })),
      continuationToken: result.continuationToken,
      isTruncated: result.isTruncated
    };
  }
  
  async upload(key: string, content: string | Uint8Array, options?: StorageUploadOptions): Promise<StorageUploadResult> {
    // Validate key before upload
    validateS3Key(key);
    
    // Calculate content size and validate
    const contentBytes = typeof content === "string" 
      ? new TextEncoder().encode(content)
      : content;
    validateS3ObjectSize(contentBytes.length);
    
    const result = await this.s3Client.uploadObject({
      action: 'upload',
      key,
      content,
      contentType: options?.contentType,
      metadata: options?.metadata
    });
    
    return {
      key: result.key,
      etag: result.etag,
      versionId: result.versionId
    };
  }
  
  async download(key: string, options?: StorageDownloadOptions): Promise<StorageDownloadResult> {
    // Validate key before download
    validateS3Key(key);
    
    const result = await this.s3Client.downloadObject({
      action: 'download',
      key,
      outputPath: options?.outputPath
    });
    
    // Convert content to Uint8Array if it's a string
    const content = result.content 
      ? new TextEncoder().encode(result.content)
      : new Uint8Array();
    
    return {
      key: result.key,
      content,
      contentType: result.contentType,
      metadata: result.metadata
    };
  }
  
  async delete(keys: string[]): Promise<StorageDeleteResult> {
    // Validate all keys before delete
    for (const key of keys) {
      validateS3Key(key);
    }
    
    const result = await this.s3Client.deleteObjects({
      action: 'delete',
      keys
    });
    
    return {
      deleted: result.deleted,
      errors: result.errors
    };
  }
  
  async info(key: string): Promise<StorageInfoResult> {
    // Validate key before getting info
    validateS3Key(key);
    
    const result = await this.s3Client.getObjectInfo({
      action: 'info',
      key
    });
    
    return {
      key: result.key,
      exists: result.exists,
      size: result.size,
      lastModified: result.lastModified,
      contentType: result.contentType,
      metadata: result.metadata
    };
  }
  
  getType(): string {
    // Detect provider based on endpoint
    const endpoint = this.config.endpoint.toLowerCase();
    if (endpoint.includes("amazonaws.com")) return "s3";
    if (endpoint.includes("localhost") || endpoint.includes("127.0.0.1")) return "minio";
    if (endpoint.includes("r2.cloudflarestorage.com")) return "r2";
    if (endpoint.includes("backblazeb2.com")) return "b2";
    return "s3-compatible";
  }
  
  async isHealthy(): Promise<boolean> {
    try {
      // Try to list with a very small limit to check connectivity
      await this.s3Client.listObjects({
        action: 'list',
        maxKeys: 1
      });
      return true;
    } catch (error) {
      return false;
    }
  }
}