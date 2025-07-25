/**
 * Storage Adapter Factory
 * Creates appropriate storage adapter based on configuration
 */

import { InMemoryStorageAdapter } from "./in-memory.ts";
import { S3CompatibleAdapter } from "./aws.ts";
import { FilesystemStorageAdapter } from "./filesystem.ts";
import type { StorageAdapter, StorageConfig } from "../adapter.ts";

// Factory function to create appropriate adapter
export function createStorageAdapter(config: Partial<StorageConfig> | {}): StorageAdapter {
  // Handle empty config
  if (!config || Object.keys(config).length === 0) {
    return new InMemoryStorageAdapter();
  }
  
  // Type guard for better type inference
  const typedConfig = config as Partial<StorageConfig>;
  
  // Auto-detect or use specified type
  if (!typedConfig.type || typedConfig.type === "auto") {
    // Check if it looks like S3 config
    const s3Config = typedConfig as any;
    if (!s3Config.endpoint) {
      return new InMemoryStorageAdapter();
    }
    // If endpoint is specified, use S3 adapter
    // Note: bucket validation will happen in S3StorageAdapter constructor
    return new S3CompatibleAdapter({
      type: "s3",
      endpoint: s3Config.endpoint,
      region: s3Config.region || "us-east-1",
      accessKeyId: s3Config.accessKeyId || "",
      secretAccessKey: s3Config.secretAccessKey || "",
      bucket: s3Config.bucket || "default-bucket"  // Provide a default that will be validated
    });
  }
  
  switch (typedConfig.type) {
    case "filesystem":
      const fsConfig = typedConfig as { type: "filesystem"; basePath?: string };
      return new FilesystemStorageAdapter(fsConfig.basePath || "/tmp/storage");
    case "s3":
      const s3Config = typedConfig as Partial<Extract<StorageConfig, { type: "s3" }>>;
      // Note: bucket validation will happen in S3StorageAdapter constructor
      return new S3CompatibleAdapter({
        type: "s3",
        endpoint: s3Config.endpoint || "",
        region: s3Config.region || "us-east-1",
        accessKeyId: s3Config.accessKeyId || "",
        secretAccessKey: s3Config.secretAccessKey || "",
        bucket: s3Config.bucket || "default-bucket"  // Provide a default that will be validated
      });
    default:
      throw new Error(`Unknown storage type: ${(typedConfig as any).type}`);
  }
}