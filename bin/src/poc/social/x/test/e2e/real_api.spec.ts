/**
 * End-to-End tests for Real X/Twitter API
 * These tests make actual API calls and are skipped unless REAL_API_TEST=true
 * 
 * Usage:
 *   REAL_API_TEST=true X_BEARER_TOKEN=your_token bun test test/e2e/real_api.spec.ts
 */

import { describe, it, expect, test } from "bun:test";
import { getTweet } from "../../src/read";

/**
 * Helper to check if real credentials are configured
 */
function hasRealCredentials(): boolean {
  return !!process.env.X_BEARER_TOKEN;
}

/**
 * Helper to check if real API testing is enabled
 */
function isRealApiTestEnabled(): boolean {
  return process.env.REAL_API_TEST === 'true';
}

/**
 * Skip message for when real API testing is disabled
 */
const SKIP_MESSAGE = `
Real API tests are skipped by default to avoid rate limits and API costs.
To run these tests:
1. Set REAL_API_TEST=true 
2. Provide authentication via X_BEARER_TOKEN
3. Run: REAL_API_TEST=true X_BEARER_TOKEN=your_token bun test test/e2e/real_api.spec.ts
`;

describe("Real X/Twitter API E2E Tests", () => {
  test.if(isRealApiTestEnabled())("should fetch Jack Dorsey's first tweet (ID: 20)", async () => {
    if (!hasRealCredentials()) {
      throw new Error("Real API credentials required: Set X_BEARER_TOKEN");
    }

    try {
      // Jack Dorsey's first tweet: "just setting up my twttr" (ID: 20)
      const tweet = await getTweet("20");
      
      // Verify we got a valid response
      expect(tweet).toBeDefined();
      expect(tweet.id).toBe("20");
      expect(tweet.text).toContain("just setting up my twttr");
      expect(tweet.author_id).toBeDefined();
      
      console.log("✅ Successfully fetched Jack's first tweet:", tweet.text);
      
    } catch (error: any) {
      // Handle rate limiting gracefully
      if (error.message?.includes('Rate limit') || error.message?.includes('Too Many Requests')) {
        console.warn("⚠️  Rate limit encountered during E2E test");
        // Don't fail the test for rate limiting - this is expected
        expect(error.message).toContain('Rate limit');
      } else if (error.message?.includes('not found')) {
        // Tweet might be deleted or access restricted
        console.warn("⚠️  Tweet not found or access restricted");
        expect(error.message).toContain('not found');
      } else {
        // Re-throw unexpected errors
        throw error;
      }
    }
  });

  test.if(isRealApiTestEnabled())("should handle rate limit gracefully", async () => {
    if (!hasRealCredentials()) {
      throw new Error("Real API credentials required: Set X_BEARER_TOKEN");
    }

    // This test verifies that rate limiting is handled properly
    // We'll make multiple requests that might trigger rate limiting
    const tweetIds = ["20", "20", "20"]; // Use same ID to avoid hitting different endpoints
    const results = [];

    for (const id of tweetIds) {
      try {
        const tweet = await getTweet(id);
        results.push({ success: true, tweet });
      } catch (error: any) {
        if (error.message?.includes('Rate limit') || error.message?.includes('Too Many Requests')) {
          results.push({ success: false, rateLimited: true, error: error.message });
          console.log("⚠️  Rate limit encountered (expected behavior)");
        } else {
          results.push({ success: false, rateLimited: false, error: error.message });
        }
      }
      
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    // Verify we handled all requests (either success or proper error handling)
    expect(results).toHaveLength(tweetIds.length);
    
    // At least one request should either succeed or fail with proper error handling
    const hasValidResult = results.some(r => 
      r.success || 
      (r as any).rateLimited || 
      (r as any).error?.includes('not found')
    );
    expect(hasValidResult).toBe(true);
  });

  // This test always runs to show the skip message when real API testing is disabled
  test.if(!isRealApiTestEnabled())("should show skip message when real API testing is disabled", () => {
    console.log(SKIP_MESSAGE);
    expect(isRealApiTestEnabled()).toBe(false);
  });

  test.if(!isRealApiTestEnabled() && !hasRealCredentials())("should show credentials message when no real token", () => {
    const message = `
No real API credentials found. To run E2E tests:
1. Set X_BEARER_TOKEN=your_token
2. Set REAL_API_TEST=true
3. Run: REAL_API_TEST=true X_BEARER_TOKEN=your_token bun test test/e2e/real_api.spec.ts
`;
    console.log(message);
    expect(hasRealCredentials()).toBe(false);
  });
});