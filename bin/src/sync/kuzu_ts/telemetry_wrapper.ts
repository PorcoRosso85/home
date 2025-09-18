/**
 * Generic telemetry wrapper for KuzuDB Sync modules
 * 
 * Provides a wrapper around the telemetry/log_ts module that allows
 * dynamic URI setting for different contexts within the sync system.
 */

import { log as telemetryLog, type LogData } from "../../telemetry/log_ts/mod.ts";

/**
 * Telemetry wrapper interface
 */
export interface TelemetryWrapper {
  /**
   * Log a message with the current URI
   * @param level Log level (e.g., "info", "debug", "error")
   * @param data Log data excluding URI (which is managed by the wrapper)
   */
  log(level: string, data: Omit<LogData, "uri">): void;
  
  /**
   * Update the URI for future log messages
   * @param uri New URI to use
   * @returns The wrapper instance for method chaining
   */
  setUri(uri: string): TelemetryWrapper;
}

/**
 * Create a telemetry wrapper with a specific base URI
 * 
 * @param baseUri Initial URI for log messages
 * @returns TelemetryWrapper instance
 * 
 * @example
 * ```typescript
 * const telemetry = createTelemetryWrapper("kuzu:sync:websocket");
 * telemetry.log("info", { message: "WebSocket connected" });
 * 
 * // Change context
 * telemetry.setUri("kuzu:sync:websocket:error")
 *   .log("error", { message: "Connection failed", error: err.message });
 * ```
 */
export function createTelemetryWrapper(baseUri: string): TelemetryWrapper {
  let currentUri = baseUri;
  
  return {
    log(level: string, data: Omit<LogData, "uri">): void {
      // Add the current URI to the log data
      const fullData: LogData = {
        uri: currentUri,
        ...data,
      } as LogData;
      
      // Use the telemetry log function
      telemetryLog(level, fullData);
    },
    
    setUri(uri: string): TelemetryWrapper {
      currentUri = uri;
      return this; // Return self for method chaining
    },
  };
}