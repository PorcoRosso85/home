/**
 * Version export tests
 * 
 * Verifies that KUZU_VERSION is properly exported and accessible
 */

import { assertEquals } from "https://deno.land/std@0.218.0/assert/mod.ts";
import { KUZU_VERSION } from "../version.ts";

Deno.test("KUZU_VERSION is defined correctly", () => {
  assertEquals(typeof KUZU_VERSION, "string");
  assertEquals(KUZU_VERSION, "0.10.0");
});

Deno.test("KUZU_VERSION matches expected format", () => {
  // Version should be in semantic versioning format
  const versionPattern = /^\d+\.\d+\.\d+$/;
  assertEquals(versionPattern.test(KUZU_VERSION), true);
});