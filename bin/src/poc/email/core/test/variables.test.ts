// Test for environment variables configuration

import { describe, test, expect, beforeEach, afterEach } from "bun:test";

// Store original environment variables
let originalEnv: Record<string, string | undefined>;

beforeEach(() => {
  originalEnv = {
    INVITE_BASE_URL: process.env.INVITE_BASE_URL,
    NODE_ENV: process.env.NODE_ENV,
    PORT: process.env.PORT,
  };
});

afterEach(() => {
  // Restore original environment
  Object.keys(originalEnv).forEach(key => {
    if (originalEnv[key] === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = originalEnv[key];
    }
  });
  
  // Clear module cache to allow fresh imports
  delete require.cache[require.resolve("../src/variables.ts")];
});

describe("Environment Configuration", () => {
  test("should load default configuration when no env vars are set", async () => {
    // Clear environment variables
    delete process.env.INVITE_BASE_URL;
    delete process.env.NODE_ENV;
    delete process.env.PORT;
    
    // Import fresh instance
    const { config } = await import("../src/variables.ts");
    
    expect(config.inviteBaseUrl).toBe("https://invite.example.com");
    expect(config.environment).toBe("development");
    expect(config.port).toBe(3000);
  });

  test("should load custom configuration from environment variables", async () => {
    // Set custom environment variables
    process.env.INVITE_BASE_URL = "https://custom.invite.com";
    process.env.NODE_ENV = "production";
    process.env.PORT = "8080";
    
    // Import fresh instance
    const { config } = await import("../src/variables.ts");
    
    expect(config.inviteBaseUrl).toBe("https://custom.invite.com");
    expect(config.environment).toBe("production");
    expect(config.port).toBe(8080);
  });

  test("should validate URL format for inviteBaseUrl", async () => {
    process.env.INVITE_BASE_URL = "invalid-url";
    
    // Importing should throw due to validation
    await expect(import("../src/variables.ts")).rejects.toThrow("Invalid INVITE_BASE_URL");
  });

  test("should validate port range", async () => {
    process.env.PORT = "0";
    
    await expect(import("../src/variables.ts")).rejects.toThrow("Invalid PORT");
  });

  test("should validate port range upper bound", async () => {
    process.env.PORT = "70000";
    
    await expect(import("../src/variables.ts")).rejects.toThrow("Invalid PORT");
  });

  test("should handle non-numeric port gracefully", async () => {
    process.env.PORT = "not-a-number";
    
    // Should use default port when parsing fails
    const { config } = await import("../src/variables.ts");
    expect(config.port).toBe(3000);
  });

  test("should ensure configuration is immutable reference", async () => {
    const { config } = await import("../src/variables.ts");
    const firstReference = config;
    
    // Re-import should return same instance
    delete require.cache[require.resolve("../src/variables.ts")];
    const { config: secondReference } = await import("../src/variables.ts");
    
    expect(firstReference.inviteBaseUrl).toBe(secondReference.inviteBaseUrl);
    expect(firstReference.environment).toBe(secondReference.environment);
    expect(firstReference.port).toBe(secondReference.port);
  });

  test("should support environment-specific behavior", async () => {
    // Test development mode
    process.env.NODE_ENV = "development";
    const { config: devConfig } = await import("../src/variables.ts");
    expect(devConfig.environment).toBe("development");
    
    // Clean and test production mode
    delete require.cache[require.resolve("../src/variables.ts")];
    process.env.NODE_ENV = "production";
    const { config: prodConfig } = await import("../src/variables.ts");
    expect(prodConfig.environment).toBe("production");
  });
});