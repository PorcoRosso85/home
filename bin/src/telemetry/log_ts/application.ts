/**
 * Application layer for log module - orchestrates use cases
 * 
 * This module implements the logging use case by combining domain logic
 * with infrastructure components.
 */

import type { LogData } from "./domain.ts";
import { toJsonl } from "./domain.ts";
import { stdoutWriter } from "./infrastructure.ts";

/**
 * ログを標準出力に出力
 * 
 * Application layer function that orchestrates the logging use case:
 * 1. Combines level with log data
 * 2. Converts to JSONL format using domain logic
 * 3. Outputs to stdout using infrastructure
 * 
 * @param level ログレベル（任意の文字列）
 * @param data ログデータ（uri, messageは必須）
 */
export function log(level: string, data: LogData): void {
  // Combine level with log data
  const output = {
    level,
    ...data,
  };
  
  // Convert to JSONL format using domain logic
  const jsonlOutput = toJsonl(output);
  
  // Output using infrastructure
  stdoutWriter(jsonlOutput);
}