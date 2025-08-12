/**
 * Legacy tests for read module - DEPRECATED
 * 
 * These tests have been replaced with better organized tests:
 * - Domain logic tests: test/domain/Tweet.spec.ts
 * - Integration tests: test/integration/read_tweet.spec.ts
 * 
 * This file now contains only a minimal smoke test to ensure
 * the basic function export works correctly.
 */

import { describe, it, expect } from "bun:test";
import { getTweet } from "../src/read";

describe("read module exports", () => {
  it("should export getTweet function", () => {
    expect(typeof getTweet).toBe("function");
  });

  it("should reject invalid input immediately (smoke test)", async () => {
    // This is a basic smoke test to ensure the function validates input
    // Detailed validation tests are in test/domain/Tweet.spec.ts
    // Integration scenarios are in test/integration/read_tweet.spec.ts
    await expect(getTweet("")).rejects.toThrow("Tweet ID must be a non-empty string");
  });
});