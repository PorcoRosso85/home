import { describe, it, expect } from "bun:test";

describe("Basic Test Setup", () => {
  it("should run a sanity test", () => {
    expect(1 + 1).toBe(2);
  });

  it("should verify TypeScript compilation", () => {
    const message: string = "Hello, Vite RSC!";
    expect(message).toBe("Hello, Vite RSC!");
  });

  it("should confirm test environment is working", () => {
    expect(typeof process).toBe("object");
    expect(process.env).toBeDefined();
  });
});