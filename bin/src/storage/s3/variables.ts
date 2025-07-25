/**
 * Environment variables and configuration for S3 module
 */

export interface S3EnvironmentVariables {
  S3_ENDPOINT?: string;          // Optional: For S3-compatible services like MinIO
  S3_REGION: string;             // Required: AWS region
  S3_ACCESS_KEY_ID: string;      // Required: AWS access key
  S3_SECRET_ACCESS_KEY: string;  // Required: AWS secret key
  S3_BUCKET: string;             // Required: Default bucket name
}

/**
 * Get S3 configuration from environment variables
 */
export function getS3Config(): S3EnvironmentVariables {
  const region = Deno.env.get('S3_REGION');
  const accessKeyId = Deno.env.get('S3_ACCESS_KEY_ID');
  const secretAccessKey = Deno.env.get('S3_SECRET_ACCESS_KEY');
  const bucket = Deno.env.get('S3_BUCKET');
  
  if (!region) {
    throw new Error('S3_REGION environment variable is required');
  }
  if (!accessKeyId) {
    throw new Error('S3_ACCESS_KEY_ID environment variable is required');
  }
  if (!secretAccessKey) {
    throw new Error('S3_SECRET_ACCESS_KEY environment variable is required');
  }
  if (!bucket) {
    throw new Error('S3_BUCKET environment variable is required');
  }
  
  return {
    S3_ENDPOINT: Deno.env.get('S3_ENDPOINT'),
    S3_REGION: region,
    S3_ACCESS_KEY_ID: accessKeyId,
    S3_SECRET_ACCESS_KEY: secretAccessKey,
    S3_BUCKET: bucket,
  };
}

/**
 * Validate that all required environment variables are set
 */
export function validateS3Environment(): void {
  try {
    getS3Config();
  } catch (error) {
    console.error('S3 configuration error:', error.message);
    console.error('\nRequired environment variables:');
    console.error('  S3_REGION          - AWS region (e.g., us-east-1)');
    console.error('  S3_ACCESS_KEY_ID   - AWS access key ID');
    console.error('  S3_SECRET_ACCESS_KEY - AWS secret access key');
    console.error('  S3_BUCKET          - Default S3 bucket name');
    console.error('\nOptional environment variables:');
    console.error('  S3_ENDPOINT        - Custom endpoint for S3-compatible services');
    throw error;
  }
}