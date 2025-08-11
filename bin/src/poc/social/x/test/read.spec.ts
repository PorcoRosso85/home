/**
 * Tests for read module
 */

import { describe, it, expect, beforeEach, afterEach, mock } from "bun:test";
import { getTweet } from "../src/read";
import { createClient } from "../src/client";

// Mock the client module
mock.module("../src/client", () => ({
  createClient: mock(() => ({
    tweets: {
      findTweetById: mock()
    }
  }))
}));

describe("getTweet", () => {
  let originalEnv: string | undefined;
  let mockClient: any;

  beforeEach(() => {
    originalEnv = process.env.X_BEARER_TOKEN;
    process.env.X_BEARER_TOKEN = "test-bearer-token";
    
    mockClient = {
      tweets: {
        findTweetById: mock()
      }
    };
    
    (createClient as any).mockReturnValue(mockClient);
  });

  afterEach(() => {
    if (originalEnv) {
      process.env.X_BEARER_TOKEN = originalEnv;
    } else {
      delete process.env.X_BEARER_TOKEN;
    }
    mock.restore();
  });

  it("should fetch and return tweet data successfully", async () => {
    const mockTweetData = {
      id: "123456789",
      text: "Hello, world!",
      author_id: "987654321",
      created_at: "2023-01-01T12:00:00.000Z",
      public_metrics: {
        retweet_count: 10,
        like_count: 50,
        reply_count: 5,
        quote_count: 2
      }
    };

    mockClient.tweets.findTweetById.mockResolvedValue({
      data: mockTweetData
    });

    const result = await getTweet("123456789");

    expect(mockClient.tweets.findTweetById).toHaveBeenCalledWith("123456789", {
      'tweet.fields': ['author_id', 'created_at', 'public_metrics']
    });
    expect(result).toEqual(mockTweetData);
  });

  it("should throw error when tweet ID is empty", async () => {
    await expect(getTweet("")).rejects.toThrow("Tweet ID must be a non-empty string");
    await expect(getTweet("  ")).rejects.toThrow("Tweet ID must be a non-empty string");
  });

  it("should throw error when tweet ID is not a string", async () => {
    await expect(getTweet(null as any)).rejects.toThrow("Tweet ID must be a non-empty string");
    await expect(getTweet(123 as any)).rejects.toThrow("Tweet ID must be a non-empty string");
  });

  it("should throw error when tweet is not found", async () => {
    mockClient.tweets.findTweetById.mockResolvedValue({
      data: null
    });

    await expect(getTweet("nonexistent")).rejects.toThrow("Tweet with ID nonexistent not found");
  });

  it("should handle API errors gracefully", async () => {
    const apiError = new Error("API rate limit exceeded");
    mockClient.tweets.findTweetById.mockRejectedValue(apiError);

    await expect(getTweet("123456789")).rejects.toThrow("API rate limit exceeded");
  });

  it("should handle unknown errors", async () => {
    mockClient.tweets.findTweetById.mockRejectedValue("Unknown error");

    await expect(getTweet("123456789")).rejects.toThrow("Failed to fetch tweet: Unknown error");
  });

  it("should fetch tweet with minimal data", async () => {
    const mockTweetData = {
      id: "123456789",
      text: "Simple tweet"
    };

    mockClient.tweets.findTweetById.mockResolvedValue({
      data: mockTweetData
    });

    const result = await getTweet("123456789");

    expect(result).toEqual({
      id: "123456789",
      text: "Simple tweet",
      author_id: undefined,
      created_at: undefined,
      public_metrics: undefined
    });
  });
});