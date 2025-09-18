#!/usr/bin/env bun
/**
 * Vessel structured logging for TypeScript/Bun
 * 規約準拠のJSON形式ログ出力
 */

interface LogEntry {
  timestamp: string;
  level: string;
  vessel_type: string;
  message: string;
  [key: string]: any;
}

export class VesselLogger {
  private vesselType: string;
  private debugMode: boolean;

  constructor(vesselType: string = "vessel") {
    this.vesselType = vesselType;
    this.debugMode = ["1", "true", "yes"].includes(
      (process.env.VESSEL_DEBUG || "").toLowerCase()
    );
  }

  private formatLog(level: string, message: string, extra: Record<string, any> = {}): string {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      vessel_type: this.vesselType,
      message,
      ...extra
    };
    return JSON.stringify(logEntry);
  }

  debug(message: string, extra?: Record<string, any>): void {
    if (this.debugMode) {
      console.error(this.formatLog("debug", message, extra));
    }
  }

  info(message: string, extra?: Record<string, any>): void {
    console.error(this.formatLog("info", message, extra));
  }

  error(message: string, error?: Error | any, extra?: Record<string, any>): void {
    const errorInfo = error ? {
      error: error.toString(),
      error_type: error.constructor.name,
      ...extra
    } : extra;
    
    console.error(this.formatLog("error", message, errorInfo));
  }

  output(data: any): void {
    // 通常の出力は標準出力へ
    console.log(data);
  }
}

// Export for use in vessels
export const logger = new VesselLogger();