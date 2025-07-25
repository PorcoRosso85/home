/**
 * Tests for application layer
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { executeS3Command } from "./application.ts";
import type { S3Config, HelpCommand, HelpResult, ErrorResult } from "./domain.ts";

Deno.test("executeS3Command should handle help command without S3 client", async () => {
  const helpCommand: HelpCommand = {
    action: "help",
  };

  // Mock config (not used for help command)
  const mockConfig: S3Config = {
    region: "us-east-1",
    accessKeyId: "test",
    secretAccessKey: "test",
    bucket: "test",
  };

  const result = await executeS3Command(helpCommand, mockConfig);
  
  assertEquals(result.type, "help");
  const helpResult = result as HelpResult;
  assertEquals(helpResult.message, "S3 Storage Module - Available Commands");
  assertEquals(helpResult.examples.length > 0, true);
  
  // Verify examples structure
  const listExample = helpResult.examples.find(e => e.command.action === "list");
  assertEquals(listExample?.description, "List objects in a bucket");
});

Deno.test("executeS3Command should return error for invalid commands", async () => {
  const invalidCommand = {
    // @ts-ignore - Testing invalid action
    action: "invalid",
  };

  const mockConfig: S3Config = {
    region: "us-east-1",
    accessKeyId: "test",
    secretAccessKey: "test",
    bucket: "test",
  };

  const result = await executeS3Command(invalidCommand as any, mockConfig);
  
  assertEquals(result.type, "error");
  const errorResult = result as ErrorResult;
  assertEquals(errorResult.message, "Unknown action: invalid");
});

Deno.test("executeS3Command should use in-memory adapter when no endpoint specified", async () => {
  // Test with config that has no endpoint
  const listCommand = {
    action: "list" as const,
  };

  // Config without endpoint - should use in-memory adapter
  const configWithoutEndpoint = {
    region: "us-east-1",
    accessKeyId: "test",
    secretAccessKey: "test",
    bucket: "test",
    // No endpoint specified
  } as S3Config;

  const result = await executeS3Command(listCommand, configWithoutEndpoint);
  
  // Should successfully list (empty) from in-memory adapter
  assertEquals(result.type, "list");
  const listResult = result as any;
  assertEquals(listResult.objects.length, 0);
  assertEquals(listResult.isTruncated, false);
});