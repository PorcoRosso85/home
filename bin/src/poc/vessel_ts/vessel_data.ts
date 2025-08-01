#!/usr/bin/env bun
/**
 * Data-aware Vessel for Bun - Receives data from stdin
 * Usage: echo "data" | bun vessel_data.ts 'console.log(data)'
 */

// Get script from command line argument
const script = process.argv[2];
if (!script) {
  console.error("Usage: bun vessel_data.ts 'script'");
  process.exit(1);
}

// Read data from stdin
const data = await Bun.stdin.text();

// Execution context with data
const context = {
  vessel: true,
  data: data.trim(),
  console,
  process,
  Bun,
  Buffer,
  fetch,
  JSON,
  $: Bun.$,
};

try {
  // Create async function with data in scope
  const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
  const func = new AsyncFunction('data', 'console', 'JSON', 'process', 'Bun', '$', script);
  await func(context.data, console, JSON, process, Bun, Bun.$);
} catch (error) {
  console.error("Error executing script:", error);
  process.exit(1);
}