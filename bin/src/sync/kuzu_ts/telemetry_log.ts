/**
 * Telemetry logging wrapper for log_ts module
 * This module provides a type-safe wrapper around the log_ts module
 */

import { log, type LogData } from "../../telemetry/log_ts/mod.ts";

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
  const data: LogData = {
    uri: "sync/kuzu_ts",
    message,
    ...attributes
  };
  log("DEBUG", data);
}

/**
 * Log an info message
 */
export function info(message: string, attributes?: Record<string, unknown>): void {
  const data: LogData = {
    uri: "sync/kuzu_ts",
    message,
    ...attributes
  };
  log("INFO", data);
}

/**
 * Log a warning message
 */
export function warn(message: string, attributes?: Record<string, unknown>): void {
  const data: LogData = {
    uri: "sync/kuzu_ts",
    message,
    ...attributes
  };
  log("WARN", data);
}

/**
 * Log an error message
 */
export function error(message: string, attributes?: Record<string, unknown>): void {
  const data: LogData = {
    uri: "sync/kuzu_ts",
    message,
    ...attributes
  };
  log("ERROR", data);
}

/**
 * Log a fatal message
 */
export function fatal(message: string, attributes?: Record<string, unknown>): void {
  const data: LogData = {
    uri: "sync/kuzu_ts",
    message,
    ...attributes
  };
  log("FATAL", data);
}