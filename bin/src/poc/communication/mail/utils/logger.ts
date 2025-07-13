/**
 * 構造化ログ実装
 * ロギング規約に準拠
 */

export type LogLevel = "trace" | "debug" | "info" | "warn" | "error" | "fatal";

export interface LogContext {
  service: string;
  trace_id?: string;
  user_id?: string;
  [key: string]: unknown;
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  context: LogContext;
  error?: {
    code: string;
    stack?: string;
  };
}

export class Logger {
  constructor(
    private service: string,
    private defaultContext: Partial<LogContext> = {}
  ) {}

  private log(level: LogLevel, message: string, context?: Partial<LogContext>): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message,
      context: {
        service: this.service,
        ...this.defaultContext,
        ...context
      }
    };

    console.log(JSON.stringify(entry));
  }

  trace(message: string, context?: Partial<LogContext>): void {
    this.log("trace", message, context);
  }

  debug(message: string, context?: Partial<LogContext>): void {
    this.log("debug", message, context);
  }

  info(message: string, context?: Partial<LogContext>): void {
    this.log("info", message, context);
  }

  warn(message: string, context?: Partial<LogContext>): void {
    this.log("warn", message, context);
  }

  error(message: string, error?: Error | unknown, context?: Partial<LogContext>): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: "error",
      message,
      context: {
        service: this.service,
        ...this.defaultContext,
        ...context
      }
    };

    if (error instanceof Error) {
      entry.error = {
        code: error.name,
        stack: error.stack
      };
    }

    console.log(JSON.stringify(entry));
  }

  fatal(message: string, error?: Error | unknown, context?: Partial<LogContext>): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: "fatal",
      message,
      context: {
        service: this.service,
        ...this.defaultContext,
        ...context
      }
    };

    if (error instanceof Error) {
      entry.error = {
        code: error.name,
        stack: error.stack
      };
    }

    console.log(JSON.stringify(entry));
  }

  child(additionalContext: Partial<LogContext>): Logger {
    return new Logger(this.service, {
      ...this.defaultContext,
      ...additionalContext
    });
  }
}