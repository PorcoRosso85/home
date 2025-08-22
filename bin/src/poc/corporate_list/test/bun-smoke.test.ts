import { test, expect } from "bun:test";

test("Bun can run TypeScript", () => {
  const result = 1 + 1;
  expect(result).toBe(2);
});

test("Bun can import TypeScript modules", async () => {
  // Test if we can import our TypeScript files
  const { getConfig } = await import("../src/variables");
  expect(typeof getConfig).toBe("function");
});