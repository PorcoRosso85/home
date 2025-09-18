import { describe, it, expect } from "vitest";
import { existsSync } from "fs";
import { resolve } from "path";

describe("RSC Entry Point", () => {
  it("should have RSC entry file", () => {
    const entryPath = resolve(__dirname, "../src/framework/entry.rsc.tsx");
    expect(existsSync(entryPath)).toBe(true);
  });

  it("should have SSR entry file", () => {
    const entryPath = resolve(__dirname, "../src/framework/entry.ssr.tsx");
    expect(existsSync(entryPath)).toBe(true);
  });

  it("should have browser entry file", () => {
    const entryPath = resolve(__dirname, "../src/framework/entry.browser.tsx");
    expect(existsSync(entryPath)).toBe(true);
  });

  it("should have App component", () => {
    const appPath = resolve(__dirname, "../src/app/App.tsx");
    expect(existsSync(appPath)).toBe(true);
  });

  it("should have Counter component", () => {
    const counterPath = resolve(__dirname, "../src/app/Counter.tsx");
    expect(existsSync(counterPath)).toBe(true);
  });
});