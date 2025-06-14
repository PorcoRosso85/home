// main.ts - ライブラリのメインエントリポイント

// コア機能をエクスポート
export * from './core/types.ts';
export * from './core/parser/schemaParser.ts';
export * from './core/formatter/dependencyFormatter.ts';
export * from './core/output/outputHandler.ts';

// プラットフォーム別の実装
export * as denoImpl from './platform/deno/index.ts';
export * as browserImpl from './platform/browser/index.ts';

/**
 * JSONスキーマの依存関係を解析するための統一インターフェース
 * 
 * 使用例:
 * ```typescript
 * // Deno環境
 * import { analyzeDependencies, denoImpl } from './main.ts';
 * 
 * const dependencies = await analyzeDependencies(
 *   '/path/to/schemas',
 *   'root-schema.json',
 *   denoImpl.fileSystem,
 *   denoImpl.pathUtils
 * );
 * 
 * // ブラウザ環境
 * import { analyzeDependencies, browserImpl } from './main.ts';
 * 
 * const dependencies = await analyzeDependencies(
 *   '/schemas',
 *   'root-schema.json',
 *   browserImpl.fetchFileSystem,
 *   browserImpl.pathUtils
 * );
 * ```
 */
export { extractDependencies as analyzeDependencies } from './core/parser/schemaParser.ts';
