/**
 * Structured logging utility for Cloudflare Workers
 * Complies with conventions/logging.md
 */

export type LogLevel = "INFO" | "WARN" | "ERROR" | "DEBUG" | "METRIC";

export interface LogData {
  timestamp: string;
  level: LogLevel;
  event: string;
  message: string;
  [key: string]: any;
}

/**
 * Structured log output for production monitoring
 * @param level - Log severity level
 * @param event - Event identifier for filtering
 * @param message - Human-readable message
 * @param data - Additional structured data
 */
export function log(
  level: LogLevel,
  event: string, 
  message: string,
  data?: Record<string, any>
): void {
  const logData: LogData = {
    timestamp: new Date().toISOString(),
    level,
    event,
    message,
    ...data
  };
  
  // Use console.error for ERROR level, console.log for others
  // This is the ONLY place console methods are allowed
  if (level === "ERROR") {
    console.error(JSON.stringify(logData));
  } else {
    console.log(JSON.stringify(logData));
  }
}

// Convenience functions for common log levels
export const logInfo = (event: string, message: string, data?: Record<string, any>) => 
  log("INFO", event, message, data);

export const logError = (event: string, message: string, data?: Record<string, any>) => 
  log("ERROR", event, message, data);

export const logWarn = (event: string, message: string, data?: Record<string, any>) => 
  log("WARN", event, message, data);

export const logDebug = (event: string, message: string, data?: Record<string, any>) => 
  log("DEBUG", event, message, data);

export const logMetric = (event: string, message: string, data?: Record<string, any>) => 
  log("METRIC", event, message, data);