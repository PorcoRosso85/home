import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { getConfig } from "../src/config";

describe("Config Module", () => {
  let originalEnv: string | undefined;

  beforeEach(() => {
    // Save original environment variable
    originalEnv = process.env.X_BEARER_TOKEN;
  });

  afterEach(() => {
    // Restore original environment variable
    if (originalEnv !== undefined) {
      process.env.X_BEARER_TOKEN = originalEnv;
    } else {
      delete process.env.X_BEARER_TOKEN;
    }
  });

  it("should return config when X_BEARER_TOKEN is set", () => {
    process.env.X_BEARER_TOKEN = "test_bearer_token_123";
    
    const config = getConfig();
    
    expect(config).toBeDefined();
    expect(config.bearerToken).toBe("test_bearer_token_123");
  });

  it("should throw error when X_BEARER_TOKEN is not set", () => {
    delete process.env.X_BEARER_TOKEN;
    
    expect(() => getConfig()).toThrow(
      "X_BEARER_TOKEN environment variable is required but not set"
    );
  });

  it("should throw error when X_BEARER_TOKEN is empty string", () => {
    process.env.X_BEARER_TOKEN = "";
    
    expect(() => getConfig()).toThrow(
      "X_BEARER_TOKEN environment variable is required but not set"
    );
  });
});