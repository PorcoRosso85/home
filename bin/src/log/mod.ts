/**
 * 全言語共通ログAPI規約 - TypeScript実装
 * 
 * @module log
 */

// 公開APIのエクスポート - DDD層構造から
export { log } from "./application.ts";
export { toJsonl } from "./domain.ts";
export type { LogData } from "./domain.ts";