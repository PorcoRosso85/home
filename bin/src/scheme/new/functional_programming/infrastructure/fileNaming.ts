/**
 * fileNaming.ts
 * 
 * ファイル命名規則に関するユーティリティ関数
 * ファイル名のフォーマットを標準化するための関数群を提供
 */

/**
 * 関数スキーマファイル名を生成する
 * 
 * @param functionName 関数名
 * @returns 関数スキーマファイル名（新形式）
 */
export function generateFunctionSchemaFileName(functionName: string): string {
  return `${functionName}__Function.json`;
}

/**
 * メタスキーマファイル名を取得する
 * 
 * @returns メタスキーマファイル名（新形式）
 */
export function getMetaSchemaFileName(): string {
  return 'Function__Meta.json';
}
