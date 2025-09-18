/**
 * System integration tests - No mocking, only module loading and basic functionality
 */

import { describe, it, expect, beforeEach } from 'bun:test';

describe('System Integration Tests', () => {
  let originalEnv: string | undefined;
  
  beforeEach(() => {
    // Set up environment
    originalEnv = process.env.X_BEARER_TOKEN;
    process.env.X_BEARER_TOKEN = 'test-bearer-token';
  });

  it('should have required files in place', async () => {
    // Test that all required modules can be imported
    const { getTweet } = await import('../src/read');
    const { createClient } = await import('../src/client');
    const { getConfig } = await import('../src/config');
    
    expect(typeof getTweet).toBe('function');
    expect(typeof createClient).toBe('function');
    expect(typeof getConfig).toBe('function');
  });

  it('should export CLI functions', async () => {
    const { main, formatTweetOutput, formatErrorOutput, EXIT_CODES } = await import('../src/cli');
    
    expect(typeof main).toBe('function');
    expect(typeof formatTweetOutput).toBe('function');
    expect(typeof formatErrorOutput).toBe('function');
    expect(typeof EXIT_CODES).toBe('object');
    expect(EXIT_CODES.SUCCESS).toBe(0);
    expect(EXIT_CODES.INVALID_ARGS).toBe(1);
  });

  it('should format tweet output correctly', async () => {
    const { formatTweetOutput } = await import('../src/cli');
    
    const tweet = {
      id: '123',
      text: 'Test tweet'
    };
    
    const result = formatTweetOutput(tweet);
    const parsed = JSON.parse(result);
    
    expect(parsed.success).toBe(true);
    expect(parsed.data).toEqual(tweet);
  });

  it('should format error output correctly', async () => {
    const { formatErrorOutput } = await import('../src/cli');
    
    const message = 'Test error';
    const result = formatErrorOutput(message);
    const parsed = JSON.parse(result);
    
    expect(parsed.success).toBe(false);
    expect(parsed.error).toBe(message);
  });
});