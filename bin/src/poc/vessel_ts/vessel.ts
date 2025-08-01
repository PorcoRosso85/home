#!/usr/bin/env bun
/**
 * Vessel for Bun - Dynamic script execution container
 * For TypeScript support, use .ts files or transpile first
 */

const script = await Bun.stdin.text();

// Simple approach - eval for JavaScript only
// For TypeScript, use Bun's file-based execution
try {
  // For JavaScript, use eval with async wrapper for top-level await
  const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
  const func = new AsyncFunction(script);
  await func();
} catch (error) {
  console.error("Error executing script:", error);
  process.exit(1);
}