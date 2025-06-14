// core/output/outputHandler.ts - 出力処理を扱うモジュール

import { FileSystem } from '../types.ts';

/**
 * 標準出力に表示する
 */
export function printToConsole(content: string): void {
  console.log(content);
}

/**
 * 標準エラー出力に表示する
 */
export function printError(message: string): void {
  console.error(`エラー: ${message}`);
}

/**
 * 情報メッセージを標準出力に表示する
 */
export function printInfo(message: string): void {
  console.log(message);
}

/**
 * デバッグメッセージを表示する（デバッグモードが有効な場合のみ）
 */
export function printDebug(message: string, debug = false): void {
  if (debug) {
    console.log(`[DEBUG] ${message}`);
  }
}

/**
 * 成功メッセージを表示する
 */
export function printSuccess(message: string): void {
  console.log(`✓ ${message}`);
}
