/**
 * Tests for environment variables
 */

import { assertThrows, assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { getS3Config, validateS3Environment } from "./variables.ts";

Deno.test("getS3Config should throw error when required variables are missing", () => {
  // Save original env values
  const originalEnv = {
    S3_REGION: Deno.env.get("S3_REGION"),
    S3_ACCESS_KEY_ID: Deno.env.get("S3_ACCESS_KEY_ID"),
    S3_SECRET_ACCESS_KEY: Deno.env.get("S3_SECRET_ACCESS_KEY"),
    S3_BUCKET: Deno.env.get("S3_BUCKET"),
  };

  // Clear all S3 env vars
  Deno.env.delete("S3_REGION");
  Deno.env.delete("S3_ACCESS_KEY_ID");
  Deno.env.delete("S3_SECRET_ACCESS_KEY");
  Deno.env.delete("S3_BUCKET");

  try {
    // Test missing S3_REGION
    assertThrows(
      () => getS3Config(),
      Error,
      "S3_REGION environment variable is required"
    );

    // Test missing S3_ACCESS_KEY_ID
    Deno.env.set("S3_REGION", "us-east-1");
    assertThrows(
      () => getS3Config(),
      Error,
      "S3_ACCESS_KEY_ID environment variable is required"
    );

    // Test missing S3_SECRET_ACCESS_KEY
    Deno.env.set("S3_ACCESS_KEY_ID", "test-key");
    assertThrows(
      () => getS3Config(),
      Error,
      "S3_SECRET_ACCESS_KEY environment variable is required"
    );

    // Test missing S3_BUCKET
    Deno.env.set("S3_SECRET_ACCESS_KEY", "test-secret");
    assertThrows(
      () => getS3Config(),
      Error,
      "S3_BUCKET environment variable is required"
    );
  } finally {
    // Restore original env values
    Object.entries(originalEnv).forEach(([key, value]) => {
      if (value) {
        Deno.env.set(key, value);
      } else {
        Deno.env.delete(key);
      }
    });
  }
});

Deno.test("getS3Config should return config when all required variables are set", () => {
  // Save original env values
  const originalEnv = {
    S3_REGION: Deno.env.get("S3_REGION"),
    S3_ACCESS_KEY_ID: Deno.env.get("S3_ACCESS_KEY_ID"),
    S3_SECRET_ACCESS_KEY: Deno.env.get("S3_SECRET_ACCESS_KEY"),
    S3_BUCKET: Deno.env.get("S3_BUCKET"),
    S3_ENDPOINT: Deno.env.get("S3_ENDPOINT"),
  };

  try {
    // Set test values
    Deno.env.set("S3_REGION", "us-west-2");
    Deno.env.set("S3_ACCESS_KEY_ID", "test-access-key");
    Deno.env.set("S3_SECRET_ACCESS_KEY", "test-secret-key");
    Deno.env.set("S3_BUCKET", "test-bucket");
    Deno.env.set("S3_ENDPOINT", "http://localhost:9000");

    const config = getS3Config();

    assertEquals(config.S3_REGION, "us-west-2");
    assertEquals(config.S3_ACCESS_KEY_ID, "test-access-key");
    assertEquals(config.S3_SECRET_ACCESS_KEY, "test-secret-key");
    assertEquals(config.S3_BUCKET, "test-bucket");
    assertEquals(config.S3_ENDPOINT, "http://localhost:9000");
  } finally {
    // Restore original env values
    Object.entries(originalEnv).forEach(([key, value]) => {
      if (value) {
        Deno.env.set(key, value);
      } else {
        Deno.env.delete(key);
      }
    });
  }
});

Deno.test("validateS3Environment should not throw when all variables are set", () => {
  // Save original env values
  const originalEnv = {
    S3_REGION: Deno.env.get("S3_REGION"),
    S3_ACCESS_KEY_ID: Deno.env.get("S3_ACCESS_KEY_ID"),
    S3_SECRET_ACCESS_KEY: Deno.env.get("S3_SECRET_ACCESS_KEY"),
    S3_BUCKET: Deno.env.get("S3_BUCKET"),
  };

  try {
    // Set test values
    Deno.env.set("S3_REGION", "us-west-2");
    Deno.env.set("S3_ACCESS_KEY_ID", "test-access-key");
    Deno.env.set("S3_SECRET_ACCESS_KEY", "test-secret-key");
    Deno.env.set("S3_BUCKET", "test-bucket");

    // Should not throw
    validateS3Environment();
  } finally {
    // Restore original env values
    Object.entries(originalEnv).forEach(([key, value]) => {
      if (value) {
        Deno.env.set(key, value);
      } else {
        Deno.env.delete(key);
      }
    });
  }
});