/**
 * Telemetry logging wrapper for log_ts module
 * This module provides a type-safe wrapper around the log_ts module
 * 
 * Now uses the generic telemetry wrapper for consistent logging behavior
 * while maintaining backward compatibility with the existing API.
 */

import { createTelemetryWrapper } from "./telemetry_wrapper.ts";
import { log } from "../../telemetry/log_ts/mod.ts";

// Create a telemetry wrapper instance with the base URI
const telemetry = createTelemetryWrapper("sync/kuzu_ts");

/**
 * Check if telemetry is available
 */
export async function isAvailable(): Promise<boolean> {
  return typeof log === "function";
}

/**
 * Log a debug message
 */
export function debug(message: string, attributes?: Record<string, unknown>): void {
  telemetry.log("DEBUG", {
    message,
    ...attributes
  });
}

/**
 * Log an info message
 */
export function info(message: string, attributes?: Record<string, unknown>): void {
  telemetry.log("INFO", {
    message,
    ...attributes
  });
}

/**
 * Log a warning message
 */
export function warn(message: string, attributes?: Record<string, unknown>): void {
  telemetry.log("WARN", {
    message,
    ...attributes
  });
}

/**
 * Log an error message
 */
export function error(message: string, attributes?: Record<string, unknown>): void {
  telemetry.log("ERROR", {
    message,
    ...attributes
  });
}

/**
 * Log a fatal message
 */
export function fatal(message: string, attributes?: Record<string, unknown>): void {
  telemetry.log("FATAL", {
    message,
    ...attributes
  });
}