/**
 * R2 Connection Manifest Schema
 *
 * This schema defines the structure for R2 environment-specific connection manifests.
 * These manifests are used to configure S3-compatible clients and Cloudflare Workers
 * for R2 bucket access across different environments (dev, staging, prod).
 */

/** Supported R2 regions */
export type R2Region = 'auto' | 'eeur' | 'enam' | 'apac' | 'weur' | 'wnam';

/** Connection mode for R2 access */
export type R2ConnectionMode = 'workers-binding' | 's3-api' | 'hybrid';

/** R2 bucket configuration */
export interface R2BucketConfig {
  /** Bucket name */
  name: string;
  /** Optional bucket-specific configuration */
  public?: boolean;
  /** Custom domain for public bucket access */
  custom_domain?: string;
  /** CORS configuration if needed */
  cors_origins?: string[];
}

/** R2 API credentials for S3-compatible access */
export interface R2Credentials {
  /** R2 Access Key ID */
  access_key_id: string;
  /** R2 Secret Access Key */
  secret_access_key: string;
  /** Optional session token */
  session_token?: string;
}

/** Metadata about the manifest */
export interface R2ManifestMeta {
  /** Environment name */
  environment: string;
  /** Manifest version */
  version: string;
  /** Creation timestamp */
  created_at: string;
  /** Last updated timestamp */
  updated_at?: string;
  /** Description of this configuration */
  description?: string;
}

/** Complete R2 Connection Manifest */
export interface R2ConnectionManifest {
  /** Cloudflare Account ID (required) */
  account_id: string;

  /** S3-compatible API endpoint */
  endpoint: string;

  /** R2 region */
  region: R2Region;

  /** List of R2 buckets with their configuration */
  buckets: R2BucketConfig[];

  /** Connection mode */
  connection_mode: R2ConnectionMode;

  /** S3 API credentials (optional - required for s3-api and hybrid modes) */
  credentials?: R2Credentials;

  /** Manifest metadata */
  meta: R2ManifestMeta;
}

/** Validation result for R2 manifest */
export interface R2ManifestValidationResult {
  /** Whether the manifest is valid */
  valid: boolean;
  /** List of validation errors */
  errors: string[];
  /** List of warnings */
  warnings: string[];
}

/** Options for generating R2 client configurations */
export interface R2ClientConfigOptions {
  /** Whether to include credentials in the output */
  include_credentials?: boolean;
  /** Target client type */
  client_type?: 'aws-sdk-v3' | 'aws-sdk-v2' | 'boto3' | 'generic';
  /** Whether to use SSL */
  use_ssl?: boolean;
}

/** Generated R2 client configuration */
export interface R2ClientConfig {
  /** S3-compatible endpoint URL */
  endpoint: string;
  /** Region */
  region: string;
  /** Access credentials (if included) */
  credentials?: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
  };
  /** Whether to force path-style addressing */
  forcePathStyle: boolean;
  /** Additional client-specific configuration */
  [key: string]: any;
}

/**
 * Utility type for environment-specific manifest file naming
 * Expected naming pattern: r2.<environment>.json
 */
export type R2ManifestFileName = `r2.${string}.json`;

/**
 * Type guard to check if an object is a valid R2ConnectionManifest
 */
export function isR2ConnectionManifest(obj: any): obj is R2ConnectionManifest {
  return (
    obj &&
    typeof obj.account_id === 'string' &&
    typeof obj.endpoint === 'string' &&
    typeof obj.region === 'string' &&
    Array.isArray(obj.buckets) &&
    typeof obj.connection_mode === 'string' &&
    obj.meta &&
    typeof obj.meta.environment === 'string' &&
    typeof obj.meta.version === 'string' &&
    typeof obj.meta.created_at === 'string'
  );
}

/**
 * Generate S3-compatible endpoint URL from account ID
 */
export function generateR2Endpoint(accountId: string): string {
  return `https://${accountId}.r2.cloudflarestorage.com`;
}

/**
 * Validate bucket name according to S3 naming rules
 */
export function isValidBucketName(name: string): boolean {
  // S3 bucket naming rules
  const bucketNameRegex = /^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$/;
  return (
    name.length >= 3 &&
    name.length <= 63 &&
    bucketNameRegex.test(name) &&
    !name.includes('..') &&
    !name.match(/^\d+\.\d+\.\d+\.\d+$/) // Not an IP address
  );
}

/**
 * Default configuration values
 */
export const R2_DEFAULTS = {
  region: 'auto' as R2Region,
  connection_mode: 'workers-binding' as R2ConnectionMode,
  manifest_version: '1.0.0',
  force_path_style: true,
  use_ssl: true,
} as const;