import { describe, it, expect } from "bun:test";

describe("Dependencies", () => {
  it("should be able to import twitter-api-sdk", async () => {
    const { Client } = await import("twitter-api-sdk");
    expect(Client).toBeDefined();
    expect(typeof Client).toBe("function");
  });

  it("should be able to create Client instance", async () => {
    const { Client } = await import("twitter-api-sdk");
    // Create instance without bearer token for testing import only
    const api = new Client();
    expect(api).toBeDefined();
    expect(api).toBeInstanceOf(Client);
  });
});