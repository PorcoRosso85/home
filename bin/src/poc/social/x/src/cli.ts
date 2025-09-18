#!/usr/bin/env bun

/**
 * Command Line Interface for X/Twitter API POC
 * Usage: bun run src/cli.ts <tweet_id>
 */

import { getTweet } from './read';

/**
 * CLI error exit codes
 */
const EXIT_CODES = {
  SUCCESS: 0,
  INVALID_ARGS: 1,
  API_ERROR: 2,
  UNKNOWN_ERROR: 3
} as const;

/**
 * Display usage information
 */
function showUsage(): void {
  console.error('Usage: bun run src/cli.ts <tweet_id>');
  console.error('');
  console.error('Examples:');
  console.error('  bun run src/cli.ts 1234567890123456789');
  console.error('  bun run src/cli.ts "1234567890123456789"');
}

/**
 * Format tweet data for output
 */
function formatTweetOutput(tweet: any): string {
  return JSON.stringify({
    success: true,
    data: tweet
  }, null, 2);
}

/**
 * Format error output
 */
function formatErrorOutput(message: string): string {
  return JSON.stringify({
    success: false,
    error: message
  }, null, 2);
}

/**
 * Main CLI function
 */
async function main(): Promise<void> {
  try {
    // Parse command line arguments
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
      console.error(formatErrorOutput('No tweet ID provided'));
      showUsage();
      process.exit(EXIT_CODES.INVALID_ARGS);
    }
    
    if (args.length > 1) {
      console.error(formatErrorOutput('Too many arguments provided'));
      showUsage();
      process.exit(EXIT_CODES.INVALID_ARGS);
    }
    
    const tweetId = args[0].trim();
    
    if (!tweetId) {
      console.error(formatErrorOutput('Tweet ID cannot be empty'));
      showUsage();
      process.exit(EXIT_CODES.INVALID_ARGS);
    }
    
    // Fetch tweet data
    const tweet = await getTweet(tweetId);
    
    // Output formatted result
    console.log(formatTweetOutput(tweet));
    process.exit(EXIT_CODES.SUCCESS);
    
  } catch (error) {
    if (error instanceof Error) {
      // Handle known API errors
      console.error(formatErrorOutput(error.message));
      
      // Determine appropriate exit code
      if (error.message.includes('not found') || 
          error.message.includes('non-empty string')) {
        process.exit(EXIT_CODES.INVALID_ARGS);
      } else {
        process.exit(EXIT_CODES.API_ERROR);
      }
    } else {
      // Handle unknown errors
      console.error(formatErrorOutput(`Unexpected error: ${String(error)}`));
      process.exit(EXIT_CODES.UNKNOWN_ERROR);
    }
  }
}

// Run main function if this file is executed directly
if (import.meta.main) {
  main();
}

// Export for testing
export { main, formatTweetOutput, formatErrorOutput, showUsage, EXIT_CODES };