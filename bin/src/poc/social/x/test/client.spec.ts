/**
 * Tests for client module
 */

import { describe, it, expect, beforeEach, afterEach } from "bun:test";
import { createClient } from "../src/client";

describe("createClient", () => {
  let originalEnv: string | undefined;

  beforeEach(() => {
    originalEnv = process.env.X_BEARER_TOKEN;
  });

  afterEach(() => {
    if (originalEnv) {
      process.env.X_BEARER_TOKEN = originalEnv;
    } else {
      delete process.env.X_BEARER_TOKEN;
    }
  });

  it("should create a Client instance when valid bearer token is provided", () => {
    process.env.X_BEARER_TOKEN = "test-bearer-token";
    
    const client = createClient();
    
    expect(client).toBeDefined();
    expect(client.constructor.name).toBe("Client");
  });

  it("should throw error when bearer token is missing", () => {
    delete process.env.X_BEARER_TOKEN;
    
    expect(() => createClient()).toThrow(/Authentication required/);
  });

  it("should throw error when bearer token is empty", () => {
    process.env.X_BEARER_TOKEN = "";
    
    expect(() => createClient()).toThrow(/Authentication required/);
  });
});