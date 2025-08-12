/**
 * Configuration module for X/Twitter API
 * Loads and validates environment variables
 * Supports Bearer Token authentication
 */

export interface Config {
  bearerToken: string;
  authType: 'bearer_token';
}

/**
 * Load configuration from environment variables
 * Requires X_BEARER_TOKEN from X Developer Portal
 * @returns Configuration object with validated settings
 * @throws Error if no valid Bearer Token is provided
 */
export function getConfig(): Config {
  const bearerToken = process.env.X_BEARER_TOKEN;

  if (bearerToken && bearerToken.trim()) {
    return {
      bearerToken: bearerToken.trim(),
      authType: 'bearer_token'
    };
  }

  throw new Error(
    'Authentication required. Please provide X_BEARER_TOKEN environment variable.\n' +
    'Get your Bearer Token from the X Developer Portal: https://developer.x.com/'
  );
}