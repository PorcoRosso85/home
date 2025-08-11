/**
 * Tests for CLI interface
 */

import { describe, it, expect, beforeEach, afterEach, mock } from 'bun:test';
import { main, formatTweetOutput, formatErrorOutput, showUsage, EXIT_CODES } from '../src/cli';

// Mock the read module
mock.module('../src/read', () => ({
  getTweet: mock()
}));

// Mock console methods
const originalConsoleLog = console.log;
const originalConsoleError = console.error;
const originalProcessExit = process.exit;
const originalProcessArgv = process.argv;

let consoleLogOutput: string[] = [];
let consoleErrorOutput: string[] = [];
let exitCode: number | null = null;

describe('CLI Interface', () => {
  let mockGetTweet: any;

  beforeEach(async () => {
    // Reset mocks
    consoleLogOutput = [];
    consoleErrorOutput = [];
    exitCode = null;
    
    // Get the mocked getTweet function
    const readModule = await import('../src/read');
    mockGetTweet = readModule.getTweet;
    mockGetTweet.mockReset();
    
    // Mock console methods
    console.log = mock((message: string) => {
      consoleLogOutput.push(message);
    });
    
    console.error = mock((message: string) => {
      consoleErrorOutput.push(message);
    });
    
    // Mock process.exit
    process.exit = mock((code: number) => {
      exitCode = code;
      throw new Error(`Process exit with code ${code}`); // Prevent actual exit
    }) as any;
  });
  
  afterEach(() => {
    // Restore original methods
    console.log = originalConsoleLog;
    console.error = originalConsoleError;
    process.exit = originalProcessExit;
    process.argv = originalProcessArgv;
  });

  describe('formatTweetOutput', () => {
    it('should format tweet data as success JSON', () => {
      const tweet = {
        id: '123',
        text: 'Hello World',
        author_id: '456'
      };
      
      const result = formatTweetOutput(tweet);
      const parsed = JSON.parse(result);
      
      expect(parsed.success).toBe(true);
      expect(parsed.data).toEqual(tweet);
    });
    
    it('should produce properly formatted JSON', () => {
      const tweet = { id: '123', text: 'Test' };
      const result = formatTweetOutput(tweet);
      
      // Should be valid JSON
      expect(() => JSON.parse(result)).not.toThrow();
      
      // Should be pretty-printed (contains newlines and spaces)
      expect(result).toContain('\n');
      expect(result).toContain('  ');
    });
  });

  describe('formatErrorOutput', () => {
    it('should format error message as failure JSON', () => {
      const message = 'Something went wrong';
      const result = formatErrorOutput(message);
      const parsed = JSON.parse(result);
      
      expect(parsed.success).toBe(false);
      expect(parsed.error).toBe(message);
    });
    
    it('should produce properly formatted JSON', () => {
      const result = formatErrorOutput('Test error');
      
      // Should be valid JSON
      expect(() => JSON.parse(result)).not.toThrow();
      
      // Should be pretty-printed
      expect(result).toContain('\n');
      expect(result).toContain('  ');
    });
  });

  describe('showUsage', () => {
    it('should display usage information to stderr', () => {
      showUsage();
      
      expect(consoleErrorOutput.length).toBeGreaterThan(0);
      expect(consoleErrorOutput.join('\n')).toContain('Usage:');
      expect(consoleErrorOutput.join('\n')).toContain('Examples:');
    });
  });

  describe('main function', () => {
    it('should exit with error when no arguments provided', async () => {
      process.argv = ['node', 'cli.ts']; // No tweet ID
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(exitCode).toBe(EXIT_CODES.INVALID_ARGS);
      expect(consoleErrorOutput.length).toBeGreaterThan(0);
      
      const errorOutput = consoleErrorOutput.join('\n');
      expect(errorOutput).toContain('No tweet ID provided');
    });
    
    it('should exit with error when too many arguments provided', async () => {
      process.argv = ['node', 'cli.ts', '123', '456']; // Too many args
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(exitCode).toBe(EXIT_CODES.INVALID_ARGS);
      expect(consoleErrorOutput.length).toBeGreaterThan(0);
      
      const errorOutput = consoleErrorOutput.join('\n');
      expect(errorOutput).toContain('Too many arguments provided');
    });
    
    it('should exit with error when tweet ID is empty', async () => {
      process.argv = ['node', 'cli.ts', '']; // Empty tweet ID
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(exitCode).toBe(EXIT_CODES.INVALID_ARGS);
      expect(consoleErrorOutput.length).toBeGreaterThan(0);
      
      const errorOutput = consoleErrorOutput.join('\n');
      expect(errorOutput).toContain('Tweet ID cannot be empty');
    });
    
    it('should exit with error when tweet ID is whitespace only', async () => {
      process.argv = ['node', 'cli.ts', '   ']; // Whitespace only
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(exitCode).toBe(EXIT_CODES.INVALID_ARGS);
      expect(consoleErrorOutput.length).toBeGreaterThan(0);
    });
    
    it('should successfully fetch and display tweet', async () => {
      const mockTweet = {
        id: '123456789',
        text: 'Hello Twitter!',
        author_id: '987654321',
        created_at: '2023-01-01T00:00:00.000Z',
        public_metrics: {
          retweet_count: 10,
          like_count: 50,
          reply_count: 5,
          quote_count: 2
        }
      };
      
      // Mock getTweet to return successful response
      mockGetTweet.mockResolvedValue(mockTweet);
      
      process.argv = ['node', 'cli.ts', '123456789'];
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(mockGetTweet).toHaveBeenCalledWith('123456789');
      expect(exitCode).toBe(EXIT_CODES.SUCCESS);
      expect(consoleLogOutput.length).toBe(1);
      
      const output = JSON.parse(consoleLogOutput[0]);
      expect(output.success).toBe(true);
      expect(output.data).toEqual(mockTweet);
    });
    
    it('should handle tweet not found error', async () => {
      const error = new Error('Tweet with ID 123456789 not found');
      
      // Mock getTweet to throw not found error
      mockGetTweet.mockRejectedValue(error);
      
      process.argv = ['node', 'cli.ts', '123456789'];
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(mockGetTweet).toHaveBeenCalledWith('123456789');
      expect(exitCode).toBe(EXIT_CODES.INVALID_ARGS);
      expect(consoleErrorOutput.length).toBe(1);
      
      const errorOutput = JSON.parse(consoleErrorOutput[0]);
      expect(errorOutput.success).toBe(false);
      expect(errorOutput.error).toContain('not found');
    });
    
    it('should handle API errors', async () => {
      const error = new Error('API rate limit exceeded');
      
      // Mock getTweet to throw API error
      mockGetTweet.mockRejectedValue(error);
      
      process.argv = ['node', 'cli.ts', '123456789'];
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(mockGetTweet).toHaveBeenCalledWith('123456789');
      expect(exitCode).toBe(EXIT_CODES.API_ERROR);
      expect(consoleErrorOutput.length).toBe(1);
      
      const errorOutput = JSON.parse(consoleErrorOutput[0]);
      expect(errorOutput.success).toBe(false);
      expect(errorOutput.error).toBe('API rate limit exceeded');
    });
    
    it('should handle validation errors', async () => {
      const error = new Error('Tweet ID must be a non-empty string');
      
      // Mock getTweet to throw validation error
      mockGetTweet.mockRejectedValue(error);
      
      process.argv = ['node', 'cli.ts', '123456789'];
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(mockGetTweet).toHaveBeenCalledWith('123456789');
      expect(exitCode).toBe(EXIT_CODES.INVALID_ARGS);
      expect(consoleErrorOutput.length).toBe(1);
      
      const errorOutput = JSON.parse(consoleErrorOutput[0]);
      expect(errorOutput.success).toBe(false);
      expect(errorOutput.error).toContain('non-empty string');
    });
    
    it('should handle unknown errors', async () => {
      const error = 'Unknown error type';
      
      // Mock getTweet to throw non-Error type
      mockGetTweet.mockRejectedValue(error);
      
      process.argv = ['node', 'cli.ts', '123456789'];
      
      try {
        await main();
      } catch (error) {
        // Expected due to mocked process.exit
      }
      
      expect(mockGetTweet).toHaveBeenCalledWith('123456789');
      expect(exitCode).toBe(EXIT_CODES.UNKNOWN_ERROR);
      expect(consoleErrorOutput.length).toBe(1);
      
      const errorOutput = JSON.parse(consoleErrorOutput[0]);
      expect(errorOutput.success).toBe(false);
      expect(errorOutput.error).toContain('Unexpected error');
    });
  });

  describe('EXIT_CODES', () => {
    it('should have all expected exit codes defined', () => {
      expect(EXIT_CODES.SUCCESS).toBe(0);
      expect(EXIT_CODES.INVALID_ARGS).toBe(1);
      expect(EXIT_CODES.API_ERROR).toBe(2);
      expect(EXIT_CODES.UNKNOWN_ERROR).toBe(3);
    });
  });
});