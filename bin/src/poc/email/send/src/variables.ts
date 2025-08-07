/**
 * Environment variables management for Email Send Service
 * Provides type-safe access to environment variables with defaults
 */

/**
 * Type definition for AWS environment variables
 */
export type AWSEnvironmentVariables = {
  readonly AWS_REGION?: string;
  readonly AWS_ACCESS_KEY_ID?: string;
  readonly AWS_SECRET_ACCESS_KEY?: string;
  // Allow other environment variables to coexist
  readonly [key: string]: string | undefined;
};

/**
 * Result type for AWS SES configuration retrieval
 */
export type AWSSESConfigResult = 
  | { success: true; config: { region: string; credentials: { accessKeyId: string; secretAccessKey: string } } }
  | { success: false; error: string; missingVariables: string[] };

/**
 * Default AWS region if not specified in environment
 */
const DEFAULT_AWS_REGION = 'us-east-1';

/**
 * Safely get AWS region from environment variables
 * @param env - Environment variables object (defaults to process.env)
 * @returns AWS region string or default
 */
export function getAWSRegion(env: AWSEnvironmentVariables = process.env): string {
  return env.AWS_REGION?.trim() || DEFAULT_AWS_REGION;
}

/**
 * Safely get AWS access key ID from environment variables
 * @param env - Environment variables object (defaults to process.env)
 * @returns AWS access key ID string or undefined if not set
 */
export function getAWSAccessKeyId(env: AWSEnvironmentVariables = process.env): string | undefined {
  const value = env.AWS_ACCESS_KEY_ID?.trim();
  return value && value.length > 0 ? value : undefined;
}

/**
 * Safely get AWS secret access key from environment variables
 * @param env - Environment variables object (defaults to process.env)
 * @returns AWS secret access key string or undefined if not set
 */
export function getAWSSecretAccessKey(env: AWSEnvironmentVariables = process.env): string | undefined {
  const value = env.AWS_SECRET_ACCESS_KEY?.trim();
  return value && value.length > 0 ? value : undefined;
}

/**
 * Get complete AWS SES configuration from environment variables
 * @param env - Environment variables object (defaults to process.env)
 * @returns Result with complete SES config or error details
 */
export function getAWSSESConfig(env: AWSEnvironmentVariables = process.env): AWSSESConfigResult {
  const region = getAWSRegion(env);
  const accessKeyId = getAWSAccessKeyId(env);
  const secretAccessKey = getAWSSecretAccessKey(env);
  
  const missingVariables: string[] = [];
  
  if (!accessKeyId) {
    missingVariables.push('AWS_ACCESS_KEY_ID');
  }
  
  if (!secretAccessKey) {
    missingVariables.push('AWS_SECRET_ACCESS_KEY');
  }
  
  if (missingVariables.length > 0) {
    return {
      success: false,
      error: `Missing required AWS environment variables: ${missingVariables.join(', ')}`,
      missingVariables
    };
  }
  
  return {
    success: true,
    config: {
      region,
      credentials: {
        accessKeyId: accessKeyId!,
        secretAccessKey: secretAccessKey!
      }
    }
  };
}

/**
 * Validate that all required AWS environment variables are present
 * @param env - Environment variables object (defaults to process.env)
 * @returns Array of missing variable names (empty if all present)
 */
export function validateAWSEnvironmentVariables(env: AWSEnvironmentVariables = process.env): string[] {
  const missing: string[] = [];
  
  if (!getAWSAccessKeyId(env)) {
    missing.push('AWS_ACCESS_KEY_ID');
  }
  
  if (!getAWSSecretAccessKey(env)) {
    missing.push('AWS_SECRET_ACCESS_KEY');
  }
  
  return missing;
}

/**
 * Check if AWS environment variables are configured for production use
 * @param env - Environment variables object (defaults to process.env)
 * @returns true if all required variables are present and non-empty
 */
export function isAWSConfigured(env: AWSEnvironmentVariables = process.env): boolean {
  return validateAWSEnvironmentVariables(env).length === 0;
}