/**
 * Environment-specific secrets loader for R2 configuration
 * Supports loading and validating encrypted secrets by environment
 */

import { readFileSync, existsSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

export type Environment = 'dev' | 'stg' | 'prod';

export interface R2BucketConfig {
  name: string;
  purpose: string;
  public_access: boolean;
  backup_enabled?: boolean;
  cdn_enabled?: boolean;
  versioning?: boolean;
}

export interface R2SecurityConfig {
  require_auth: boolean;
  rate_limiting: boolean;
  rate_limit_rpm?: number;
  ip_whitelist: string[];
  encryption_at_rest?: boolean;
  audit_logging?: boolean;
}

export interface R2MonitoringConfig {
  enable_metrics: boolean;
  alert_on_errors: boolean;
  alert_on_quota_usage: number;
  log_retention_days: number;
}

export interface R2EnvironmentConfig {
  environment: Environment;
  description: string;
  created_date: string;
  last_updated: string;
  cf_account_id: string;
  r2_buckets: R2BucketConfig[];
  r2_s3_endpoint: string;
  r2_region: string;
  r2_access_key_id?: string;
  r2_secret_access_key?: string;
  security: R2SecurityConfig;
  monitoring?: R2MonitoringConfig;
  [key: string]: any; // Allow environment-specific extensions
}

export class EnvironmentSecretsLoader {
  private secretsDir: string;

  constructor(secretsDir = './secrets/r2') {
    this.secretsDir = secretsDir;
  }

  /**
   * Load and decrypt environment-specific R2 configuration
   */
  async loadR2Config(environment: Environment): Promise<R2EnvironmentConfig> {
    const secretFile = join(this.secretsDir, `${environment}.yaml`);

    if (!existsSync(secretFile)) {
      throw new Error(`Secret file not found: ${secretFile}`);
    }

    try {
      // Use SOPS to decrypt the file
      const decryptedContent = execSync(
        `sops --decrypt ${secretFile}`,
        { encoding: 'utf8', cwd: process.cwd() }
      );

      // Parse YAML content (using a simple parser for now)
      const config = this.parseYaml(decryptedContent);

      // Validate configuration
      this.validateR2Config(config, environment);

      return config as R2EnvironmentConfig;
    } catch (error) {
      throw new Error(`Failed to load R2 config for ${environment}: ${error.message}`);
    }
  }

  /**
   * Check if environment secrets exist
   */
  hasSecrets(environment: Environment): boolean {
    const secretFile = join(this.secretsDir, `${environment}.yaml`);
    return existsSync(secretFile);
  }

  /**
   * List available environment configurations
   */
  getAvailableEnvironments(): Environment[] {
    const environments: Environment[] = [];
    const envFiles = ['dev.yaml', 'stg.yaml', 'prod.yaml'];

    for (const file of envFiles) {
      if (existsSync(join(this.secretsDir, file))) {
        const env = file.replace('.yaml', '') as Environment;
        environments.push(env);
      }
    }

    return environments;
  }

  /**
   * Generate connection manifest for a specific environment
   */
  async generateConnectionManifest(environment: Environment): Promise<object> {
    const config = await this.loadR2Config(environment);

    return {
      cloudflare: {
        account_id: config.cf_account_id,
        r2: {
          endpoint: config.r2_s3_endpoint,
          region: config.r2_region,
          buckets: config.r2_buckets.map(bucket => ({
            name: bucket.name,
            purpose: bucket.purpose,
            public: bucket.public_access
          })),
          credentials: config.r2_access_key_id ? {
            access_key_id: config.r2_access_key_id,
            secret_access_key: config.r2_secret_access_key
          } : null
        }
      },
      environment: {
        name: config.environment,
        description: config.description,
        security_level: this.getSecurityLevel(config),
        monitoring_enabled: config.monitoring?.enable_metrics || false
      }
    };
  }

  /**
   * Validate R2 configuration structure
   */
  private validateR2Config(config: any, environment: Environment): void {
    const required = ['environment', 'cf_account_id', 'r2_buckets', 'r2_s3_endpoint', 'r2_region'];

    for (const field of required) {
      if (!config[field]) {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    if (config.environment !== environment) {
      throw new Error(`Environment mismatch: expected ${environment}, got ${config.environment}`);
    }

    if (!Array.isArray(config.r2_buckets) || config.r2_buckets.length === 0) {
      throw new Error('r2_buckets must be a non-empty array');
    }

    // Validate bucket configurations
    for (const bucket of config.r2_buckets) {
      if (!bucket.name || !bucket.purpose || typeof bucket.public_access !== 'boolean') {
        throw new Error(`Invalid bucket configuration: ${JSON.stringify(bucket)}`);
      }
    }

    // Validate S3 endpoint format
    if (!config.r2_s3_endpoint.includes(config.cf_account_id)) {
      throw new Error('r2_s3_endpoint must contain the cf_account_id');
    }

    if (config.r2_region !== 'auto') {
      throw new Error('r2_region must be "auto" for Cloudflare R2');
    }
  }

  /**
   * Simple YAML parser (minimal implementation)
   */
  private parseYaml(content: string): any {
    const lines = content.split('\n');
    const result: any = {};
    let currentPath: string[] = [];
    let currentObject = result;

    for (const line of lines) {
      const trimmed = line.trim();

      // Skip comments and empty lines
      if (!trimmed || trimmed.startsWith('#')) continue;

      const indentLevel = (line.length - line.trimStart().length) / 2;

      if (trimmed.includes(': ')) {
        const [key, ...valueParts] = trimmed.split(': ');
        const value = valueParts.join(': ').trim();

        // Handle different indentation levels
        while (currentPath.length > indentLevel) {
          currentPath.pop();
        }

        // Navigate to correct object level
        currentObject = result;
        for (const pathKey of currentPath) {
          currentObject = currentObject[pathKey];
        }

        if (value) {
          // Parse value
          currentObject[key] = this.parseValue(value);
        } else {
          // Create new object for nested structure
          currentObject[key] = {};
          currentPath.push(key);
        }
      } else if (trimmed.startsWith('- ')) {
        // Handle array items
        const value = trimmed.substring(2).trim();
        const arrayKey = currentPath[currentPath.length - 1];

        if (!currentObject[arrayKey]) {
          currentObject[arrayKey] = [];
        }

        if (value.includes(': ')) {
          // Object in array
          const obj: any = {};
          const [objKey, objValue] = value.split(': ');
          obj[objKey] = this.parseValue(objValue);
          currentObject[arrayKey].push(obj);
        } else {
          // Simple value in array
          currentObject[arrayKey].push(this.parseValue(value));
        }
      }
    }

    return result;
  }

  /**
   * Parse individual values with type conversion
   */
  private parseValue(value: string): any {
    const trimmed = value.trim();

    // Boolean values
    if (trimmed === 'true') return true;
    if (trimmed === 'false') return false;

    // Numeric values
    if (/^\d+$/.test(trimmed)) return parseInt(trimmed, 10);
    if (/^\d+\.\d+$/.test(trimmed)) return parseFloat(trimmed);

    // Remove quotes if present
    if ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
        (trimmed.startsWith("'") && trimmed.endsWith("'"))) {
      return trimmed.slice(1, -1);
    }

    return trimmed;
  }

  /**
   * Determine security level based on configuration
   */
  private getSecurityLevel(config: R2EnvironmentConfig): string {
    const security = config.security;

    if (security.require_auth && security.rate_limiting && security.encryption_at_rest) {
      return 'high';
    } else if (security.require_auth && security.rate_limiting) {
      return 'medium';
    } else {
      return 'low';
    }
  }
}

// Export singleton instance for convenience
export const environmentSecrets = new EnvironmentSecretsLoader();

// Helper functions for common operations
export async function loadR2ConfigForEnvironment(env: Environment): Promise<R2EnvironmentConfig> {
  return environmentSecrets.loadR2Config(env);
}

export function getAvailableEnvironments(): Environment[] {
  return environmentSecrets.getAvailableEnvironments();
}

export async function generateR2ConnectionManifest(env: Environment): Promise<object> {
  return environmentSecrets.generateConnectionManifest(env);
}