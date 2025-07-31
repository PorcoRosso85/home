/**
 * Bun runtime implementation for KuzuDB
 * 
 * This module provides a minimal wrapper around the kuzu npm package
 * that's compatible with Bun's module system, bypassing Deno-specific code.
 */

// Import directly from npm package
import kuzu from "kuzu";

// Re-export the simple wrapper API
export * from "./simple_wrapper.ts";
export { kuzu };