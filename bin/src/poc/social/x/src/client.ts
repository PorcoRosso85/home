/**
 * Twitter API Client module
 * Provides initialized Client instance using configuration
 */

import { Client } from 'twitter-api-sdk';
import { getConfig } from './config';

/**
 * Create and return an initialized Twitter API client
 * @returns Configured Client instance
 * @throws Error if configuration is invalid
 */
export function createClient(): Client {
  const config = getConfig();
  
  return new Client({
    bearerToken: config.bearerToken
  });
}