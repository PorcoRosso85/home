import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { getConfig } from "../src/config";

describe("Config Module", () => {
  let originalEnv: { [key: string]: string | undefined } = {};

  beforeEach(() => {
    // Save original environment variables
    originalEnv = {
      X_BEARER_TOKEN: process.env.X_BEARER_TOKEN
    };
  });

  afterEach(() => {
    // Restore original environment variables
    Object.keys(originalEnv).forEach(key => {
      if (originalEnv[key] !== undefined) {
        process.env[key] = originalEnv[key];
      } else {
        delete process.env[key];
      }
    });
  });

  describe("Bearer Token Authentication", () => {
    it("should return config when X_BEARER_TOKEN is set", () => {
      process.env.X_BEARER_TOKEN = "test_bearer_token_123";
      
      const config = getConfig();
      
      expect(config).toBeDefined();
      expect(config.bearerToken).toBe("test_bearer_token_123");
      expect(config.authType).toBe("bearer_token");
    });

    it("should trim whitespace from bearer token", () => {
      process.env.X_BEARER_TOKEN = "  test_bearer_token_123  ";
      
      const config = getConfig();
      
      expect(config.bearerToken).toBe("test_bearer_token_123");
      expect(config.authType).toBe("bearer_token");
    });

    it("should reject empty bearer token", () => {
      process.env.X_BEARER_TOKEN = "";
      
      expect(() => getConfig()).toThrow("Authentication required");
    });

    it("should reject whitespace-only bearer token", () => {
      process.env.X_BEARER_TOKEN = "   ";
      
      expect(() => getConfig()).toThrow("Authentication required");
    });
  });

  describe("Error Cases", () => {
    it("should throw error when no authentication is provided", () => {
      delete process.env.X_BEARER_TOKEN;
      
      expect(() => getConfig()).toThrow(
        "Authentication required. Please provide X_BEARER_TOKEN"
      );
    });

    it("should provide helpful error message with Developer Portal reference", () => {
      delete process.env.X_BEARER_TOKEN;
      
      const error = () => getConfig();
      expect(error).toThrow();
      
      try {
        error();
      } catch (e) {
        const message = (e as Error).message;
        expect(message).toContain("X_BEARER_TOKEN");
        expect(message).toContain("developer.x.com");
      }
    });
  });
});