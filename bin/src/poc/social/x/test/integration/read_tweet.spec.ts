/**
 * Integration tests for tweet reading functionality
 * Tests the actual flow from config → client → API call with minimal mocking
 * Focuses on observable outcomes rather than implementation details
 */

import { describe, it, expect, beforeEach, afterEach, mock } from "bun:test";
import { getTweet } from "../../src/read";
import { Tweet } from "../../src/domain/Tweet";

// Mock only the external network call - the twitter-api-sdk
// This allows testing the real flow while controlling external dependencies
const mockFindTweetById = mock();

mock.module("twitter-api-sdk", () => ({
  Client: class MockClient {
    constructor(config: any) {
      // Verify that config is passed through correctly
      if (!config.bearerToken) {
        throw new Error("bearerToken is required");
      }
    }

    tweets = {
      findTweetById: mockFindTweetById
    }
  }
}));

describe("Tweet Reading Integration", () => {
  let originalEnv: string | undefined;

  beforeEach(() => {
    originalEnv = process.env.X_BEARER_TOKEN;
    process.env.X_BEARER_TOKEN = "test-bearer-token";
  });

  afterEach(() => {
    if (originalEnv) {
      process.env.X_BEARER_TOKEN = originalEnv;
    } else {
      delete process.env.X_BEARER_TOKEN;
    }
    mock.restore();
  });

  describe("Successful tweet fetching", () => {
    it("should fetch tweet and return domain object", async () => {
      // Arrange - Mock the external API response
      const mockApiResponse = {
        data: {
          id: "123456789",
          text: "Hello, integration test!",
          author_id: "987654321",
          created_at: "2023-01-01T12:00:00.000Z",
          public_metrics: {
            retweet_count: 10,
            like_count: 50,
            reply_count: 5,
            quote_count: 2
          }
        }
      };

      // Configure the mock to return our test data
      mockFindTweetById.mockResolvedValue(mockApiResponse);

      // Act - Call the actual function which goes through the full flow
      const result = await getTweet("123456789");

      // Assert - Verify observable outcomes
      expect(result).toEqual({
        id: "123456789",
        text: "Hello, integration test!",
        author_id: "987654321",
        created_at: "2023-01-01T12:00:00.000Z",
        public_metrics: {
          retweet_count: 10,
          like_count: 50,
          reply_count: 5,
          quote_count: 2
        }
      });

      // Verify the correct API call was made
      expect(mockFindTweetById).toHaveBeenCalledWith("123456789", {
        'tweet.fields': ['author_id', 'created_at', 'public_metrics']
      });
    });

    it("should handle minimal tweet data", async () => {
      const mockApiResponse = {
        data: {
          id: "simple123",
          text: "Simple tweet"
        }
      };

      mockFindTweetById.mockResolvedValue(mockApiResponse);

      const result = await getTweet("simple123");

      expect(result).toEqual({
        id: "simple123",
        text: "Simple tweet",
        author_id: undefined,
        created_at: undefined,
        public_metrics: undefined
      });
    });
  });

  describe("Error scenarios", () => {
    it("should fail when X_BEARER_TOKEN is not set", async () => {
      delete process.env.X_BEARER_TOKEN;

      await expect(getTweet("123456789")).rejects.toThrow(
        "X_BEARER_TOKEN environment variable is required but not set"
      );
    });

    it("should handle API not found response", async () => {
      const mockApiResponse = {
        data: null
      };

      mockFindTweetById.mockResolvedValue(mockApiResponse);

      await expect(getTweet("nonexistent")).rejects.toThrow(
        "Tweet with ID nonexistent not found"
      );
    });

    it("should handle API errors", async () => {
      const apiError = new Error("Rate limit exceeded");

      mockFindTweetById.mockRejectedValue(apiError);

      await expect(getTweet("123456789")).rejects.toThrow("Rate limit exceeded");
    });

    it("should validate input before making API call", async () => {
      // These should fail validation before any API call
      await expect(getTweet("")).rejects.toThrow("Tweet ID must be a non-empty string");
      await expect(getTweet("   ")).rejects.toThrow("Tweet ID must be a non-empty string");
      await expect(getTweet(null as any)).rejects.toThrow("Tweet ID must be a non-empty string");

      // Verify no API calls were made for invalid input
      expect(mockFindTweetById).not.toHaveBeenCalled();
    });
  });

  describe("Configuration and client integration", () => {
    it("should properly initialize client with bearer token", async () => {
      const customToken = "custom-bearer-token-123";
      process.env.X_BEARER_TOKEN = customToken;

      const mockApiResponse = {
        data: {
          id: "test123",
          text: "Test tweet"
        }
      };

      mockFindTweetById.mockResolvedValue(mockApiResponse);

      await getTweet("test123");

      // Verify Client was instantiated (constructor would throw if bearerToken missing)
      // The fact that we got here means the client was properly configured
      expect(mockFindTweetById).toHaveBeenCalled();
    });
  });

  describe("Data transformation integrity", () => {
    it("should preserve all API response fields in result", async () => {
      const mockApiResponse = {
        data: {
          id: "preserve123",
          text: "Preserve all fields",
          author_id: "author999",
          created_at: "2023-12-01T10:30:00.000Z",
          public_metrics: {
            retweet_count: 100,
            like_count: 500,
            reply_count: 25,
            quote_count: 10
          }
        }
      };

      mockFindTweetById.mockResolvedValue(mockApiResponse);

      const result = await getTweet("preserve123");

      // Verify every field is preserved exactly
      expect(result.id).toBe(mockApiResponse.data.id);
      expect(result.text).toBe(mockApiResponse.data.text);
      expect(result.author_id).toBe(mockApiResponse.data.author_id);
      expect(result.created_at).toBe(mockApiResponse.data.created_at);
      expect(result.public_metrics).toEqual(mockApiResponse.data.public_metrics);
    });
  });
});