/**
 * Configuration module for X/Twitter API
 * Loads and validates environment variables
 */

export interface Config {
  bearerToken: string;
}

/**
 * Load configuration from environment variables
 * @returns Configuration object with validated settings
 * @throws Error if required environment variables are missing
 */
export function getConfig(): Config {
  const bearerToken = process.env.X_BEARER_TOKEN;
  
  if (!bearerToken) {
    throw new Error(
      'X_BEARER_TOKEN environment variable is required but not set. ' +
      'Please set X_BEARER_TOKEN to your Twitter API Bearer Token.'
    );
  }
  
  return {
    bearerToken
  };
}