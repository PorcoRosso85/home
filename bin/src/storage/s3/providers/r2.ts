/**
 * Cloudflare R2 specific provider configuration
 */

import { S3CompatibleAdapter } from "./aws.ts";
import { StorageConfig } from "../adapter.ts";
import type { S3Config } from "../domain.ts";

export interface R2Config {
  accountId: string;
  accessKeyId: string;
  secretAccessKey: string;
  bucket: string;
}

/**
 * Generate R2 endpoint URL from account ID
 */
export function getR2EndpointUrl(accountId: string): string {
  if (!accountId) {
    throw new Error("Account ID is required");
  }
  return `https://${accountId}.r2.cloudflarestorage.com`;
}

/**
 * Validate R2 configuration
 */
export function validateR2Config(config: R2Config): void {
  // Validate accountId
  if (!config.accountId || config.accountId.trim() === '') {
    throw new Error('R2 configuration error: accountId is required and cannot be empty');
  }

  // Validate accessKeyId
  if (!config.accessKeyId || config.accessKeyId.trim() === '') {
    throw new Error('R2 configuration error: accessKeyId is required and cannot be empty');
  }

  // Validate secretAccessKey
  if (!config.secretAccessKey || config.secretAccessKey.trim() === '') {
    throw new Error('R2 configuration error: secretAccessKey is required and cannot be empty');
  }

  // Validate bucket
  if (!config.bucket || config.bucket.trim() === '') {
    throw new Error('R2 configuration error: bucket name is required and cannot be empty');
  }

  // Validate bucket name against S3 naming rules
  const bucketName = config.bucket;
  
  // Must be 3-63 characters
  if (bucketName.length < 3 || bucketName.length > 63) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" must be between 3 and 63 characters long`);
  }

  // Must start and end with lowercase letter or number
  if (!/^[a-z0-9]/.test(bucketName)) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" must start with a lowercase letter or number`);
  }
  if (!/[a-z0-9]$/.test(bucketName)) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" must end with a lowercase letter or number`);
  }

  // Can only contain lowercase letters, numbers, hyphens, and dots
  if (!/^[a-z0-9.-]+$/.test(bucketName)) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" can only contain lowercase letters, numbers, hyphens, and dots`);
  }

  // Cannot be formatted as an IP address
  if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(bucketName)) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" cannot be formatted as an IP address`);
  }

  // Cannot contain consecutive dots or hyphens
  if (/\.\./.test(bucketName) || /--/.test(bucketName)) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" cannot contain consecutive dots or hyphens`);
  }

  // Cannot have dots adjacent to hyphens
  if (/\.-|-\./.test(bucketName)) {
    throw new Error(`R2 configuration error: bucket name "${bucketName}" cannot have dots adjacent to hyphens`);
  }
}

/**
 * Create R2 client configuration
 */
export function createR2Config(config: R2Config): {
  endpoint: string;
  region: string;
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
  };
  bucket: string;
} {
  // Validate configuration before creating
  validateR2Config(config);
  
  return {
    endpoint: getR2EndpointUrl(config.accountId),
    region: 'auto',
    credentials: {
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
    },
    bucket: config.bucket,
  };
}

/**
 * R2 Storage Adapter implementation
 * Extends S3CompatibleAdapter with R2-specific configuration
 */
export class R2StorageAdapter extends S3CompatibleAdapter {
  constructor(config: R2Config) {
    // Validate R2 configuration
    validateR2Config(config);
    
    // Convert R2Config to S3Config
    const s3Config: Extract<StorageConfig, { type: "s3" }> = {
      type: "s3",
      endpoint: getR2EndpointUrl(config.accountId),
      region: "auto",
      accessKeyId: config.accessKeyId,
      secretAccessKey: config.secretAccessKey,
      bucket: config.bucket
    };
    
    // Call parent constructor with S3-compatible config
    super(s3Config);
  }
  
  override getType(): string {
    return "r2";
  }
}