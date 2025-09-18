/**
 * Unit tests for Tweet domain object
 * Tests validation rules and behavior without any mocks
 * Follows "Refactoring Wall" principle - tests only public API and behavior
 */

import { describe, it, expect } from "bun:test";
import { Tweet, TweetData } from "../../src/domain/Tweet";

describe("Tweet Domain Object", () => {
  describe("Tweet.isValidId", () => {
    it("should return true for valid string IDs", () => {
      expect(Tweet.isValidId("123456789")).toBe(true);
      expect(Tweet.isValidId("valid_id")).toBe(true);
      expect(Tweet.isValidId("1")).toBe(true);
    });

    it("should return false for invalid IDs", () => {
      expect(Tweet.isValidId("")).toBe(false);
      expect(Tweet.isValidId("   ")).toBe(false);
      expect(Tweet.isValidId(null)).toBe(false);
      expect(Tweet.isValidId(undefined)).toBe(false);
      expect(Tweet.isValidId(123)).toBe(false);
      expect(Tweet.isValidId([])).toBe(false);
      expect(Tweet.isValidId({})).toBe(false);
    });
  });

  describe("Tweet.isValidText", () => {
    it("should return true for valid text", () => {
      expect(Tweet.isValidText("Hello, world!")).toBe(true);
      expect(Tweet.isValidText("A")).toBe(true);
      expect(Tweet.isValidText("Tweet with emojis 🚀")).toBe(true);
    });

    it("should return false for invalid text", () => {
      expect(Tweet.isValidText("")).toBe(false);
      expect(Tweet.isValidText("   ")).toBe(false);
      expect(Tweet.isValidText(null)).toBe(false);
      expect(Tweet.isValidText(undefined)).toBe(false);
      expect(Tweet.isValidText(123)).toBe(false);
      expect(Tweet.isValidText([])).toBe(false);
      expect(Tweet.isValidText({})).toBe(false);
    });
  });

  describe("Tweet.fromData", () => {
    it("should create Tweet from valid minimal data", () => {
      const data: TweetData = {
        id: "123456789",
        text: "Hello, world!"
      };

      const tweet = Tweet.fromData(data);

      expect(tweet.id).toBe("123456789");
      expect(tweet.text).toBe("Hello, world!");
      expect(tweet.author_id).toBeUndefined();
      expect(tweet.created_at).toBeUndefined();
      expect(tweet.public_metrics).toBeUndefined();
    });

    it("should create Tweet from complete data", () => {
      const data: TweetData = {
        id: "123456789",
        text: "Complete tweet",
        author_id: "987654321",
        created_at: "2023-01-01T12:00:00.000Z",
        public_metrics: {
          retweet_count: 10,
          like_count: 50,
          reply_count: 5,
          quote_count: 2
        }
      };

      const tweet = Tweet.fromData(data);

      expect(tweet.id).toBe("123456789");
      expect(tweet.text).toBe("Complete tweet");
      expect(tweet.author_id).toBe("987654321");
      expect(tweet.created_at).toBe("2023-01-01T12:00:00.000Z");
      expect(tweet.public_metrics).toEqual({
        retweet_count: 10,
        like_count: 50,
        reply_count: 5,
        quote_count: 2
      });
    });

    it("should throw error for invalid ID", () => {
      const invalidData = [
        { id: "", text: "Valid text" },
        { id: "   ", text: "Valid text" },
        { id: null as any, text: "Valid text" },
        { id: 123 as any, text: "Valid text" }
      ];

      invalidData.forEach(data => {
        expect(() => Tweet.fromData(data)).toThrow("Tweet ID must be a non-empty string");
      });
    });

    it("should throw error for invalid text", () => {
      const invalidData = [
        { id: "123", text: "" },
        { id: "123", text: "   " },
        { id: "123", text: null as any },
        { id: "123", text: 456 as any }
      ];

      invalidData.forEach(data => {
        expect(() => Tweet.fromData(data)).toThrow("Tweet text must be a non-empty string");
      });
    });
  });

  describe("toJSON", () => {
    it("should convert Tweet to JSON with minimal data", () => {
      const data: TweetData = {
        id: "123456789",
        text: "Hello, world!"
      };

      const tweet = Tweet.fromData(data);
      const json = tweet.toJSON();

      expect(json).toEqual({
        id: "123456789",
        text: "Hello, world!",
        author_id: undefined,
        created_at: undefined,
        public_metrics: undefined
      });
    });

    it("should convert Tweet to JSON with complete data", () => {
      const data: TweetData = {
        id: "123456789",
        text: "Complete tweet",
        author_id: "987654321",
        created_at: "2023-01-01T12:00:00.000Z",
        public_metrics: {
          retweet_count: 10,
          like_count: 50,
          reply_count: 5,
          quote_count: 2
        }
      };

      const tweet = Tweet.fromData(data);
      const json = tweet.toJSON();

      expect(json).toEqual(data);
    });
  });

  describe("equals", () => {
    it("should return true for tweets with same ID", () => {
      const data1: TweetData = { id: "123", text: "First tweet" };
      const data2: TweetData = { id: "123", text: "Different text" };

      const tweet1 = Tweet.fromData(data1);
      const tweet2 = Tweet.fromData(data2);

      expect(tweet1.equals(tweet2)).toBe(true);
    });

    it("should return false for tweets with different IDs", () => {
      const data1: TweetData = { id: "123", text: "Same text" };
      const data2: TweetData = { id: "456", text: "Same text" };

      const tweet1 = Tweet.fromData(data1);
      const tweet2 = Tweet.fromData(data2);

      expect(tweet1.equals(tweet2)).toBe(false);
    });
  });

  describe("immutability", () => {
    it("should be immutable - properties cannot be changed", () => {
      const data: TweetData = {
        id: "123456789",
        text: "Original text"
      };

      const tweet = Tweet.fromData(data);

      // These should not be possible due to readonly properties
      // But we can verify the values don't change
      expect(tweet.id).toBe("123456789");
      expect(tweet.text).toBe("Original text");
      
      // Modifying the original data should not affect the tweet
      data.text = "Modified text";
      expect(tweet.text).toBe("Original text");
    });

    it("should return new object on toJSON() calls", () => {
      const tweet = Tweet.fromData({ id: "123", text: "Test" });
      
      const json1 = tweet.toJSON();
      const json2 = tweet.toJSON();
      
      expect(json1).toEqual(json2);
      expect(json1).not.toBe(json2); // Different object references
    });
  });
});