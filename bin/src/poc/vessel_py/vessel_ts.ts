#!/usr/bin/env bun
/**
 * TypeScript Vessel for Bun
 * Uses file-based execution for proper TypeScript support
 */
import { tmpdir } from "os";
import { join } from "path";
import { unlink } from "fs/promises";

const script = await Bun.stdin.text();

// Create temporary file for TypeScript execution
const tempFile = join(tmpdir(), `vessel_${Date.now()}_${Math.random().toString(36).substring(7)}.ts`);

try {
  // Write script to temp file
  await Bun.write(tempFile, script);
  
  // Import and execute the file
  // Bun will transpile TypeScript automatically
  await import(tempFile);
} catch (error) {
  console.error("Error executing script:", error);
  process.exit(1);
} finally {
  // Clean up temp file
  try {
    await unlink(tempFile);
  } catch {}
}