import type { LogData } from "./types.ts";

/**
 * 辞書型データをJSONL形式の文字列に変換
 * @param data 変換対象のデータ
 * @returns 改行を含まない1行のJSON文字列
 */
export function toJsonl(data: Record<string, unknown>): string {
  return JSON.stringify(data);
}

/**
 * ログを標準出力に出力
 * @param level ログレベル（任意の文字列）
 * @param data ログデータ（uri, messageは必須）
 */
export function log(level: string, data: LogData): void {
  const output = {
    level,
    ...data,
  };
  console.log(toJsonl(output));
}