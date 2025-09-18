#!/usr/bin/env bun
/**
 * Simple Vessel for Bun - Direct eval approach
 */

const script = await Bun.stdin.text();

try {
  // Bunはevalで直接TypeScriptを実行できる
  await eval(script);
} catch (error) {
  console.error("Error executing script:", error);
  process.exit(1);
}