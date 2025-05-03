#!/usr/bin/env -S deno run --allow-all

/**
 * 階層型トレーサビリティモデル - 結果整形関数
 * 
 * このファイルはテスト結果の整形に関する共通関数を提供します。
 * - 要件情報の整形
 * - 実装状況の整形
 * - 未実装要件の整形
 */

// 型定義
export interface RequirementResult {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  requirement_priority: string;
  implementation_type: string;
  requirement_location: string;
  relation_type: string;
}

export interface ImplementationResult {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  code_id: string;
  code_name: string;
  code_type: string;
  implementation_type: string;
  code_location: string;
}

export interface UnimplementedResult {
  requirement_id: string;
  title: string;
}

/**
 * コードに関連する要件の結果を整形する関数
 * @param results 要件検索結果の配列
 * @returns 整形された文字列
 */
export function formatRequirementsForCode(results: RequirementResult[]): string {
  if (!results.length) {
    return "指定されたコードに関連する要件は見つかりませんでした。";
  }
  
  const output: string[] = [];
  output.push("\n関連する要件:");
  output.push("=".repeat(80));
  output.push(`${"要件ID".padEnd(10)} ${"タイトル".padEnd(30)} ${"タイプ".padEnd(10)} ${"優先度".padEnd(10)} ${"関連タイプ".padEnd(20)} ${"場所"}`);
  output.push("-".repeat(80));
  
  // 優先度順にソート（HIGH、MEDIUM、LOW）
  const priorityOrder: Record<string, number> = {"HIGH": 0, "MEDIUM": 1, "LOW": 2};
  const sortedResults = [...results].sort((a, b) => {
    return (priorityOrder[a.requirement_priority] || 99) - (priorityOrder[b.requirement_priority] || 99);
  });
  
  for (const result of sortedResults) {
    output.push(`${result.requirement_id.padEnd(10)} ${(result.requirement_title || "").slice(0, 30).padEnd(30)} ` +
               `${(result.requirement_type || "").padEnd(10)} ${(result.requirement_priority || "").padEnd(10)} ` +
               `${(result.relation_type || "").slice(0, 20).padEnd(20)} ${result.requirement_location || ""}`);
  }
  
  return output.join("\n");
}

/**
 * 実装状況結果を整形する関数
 * @param results 実装状況検索結果の配列
 * @returns 整形された文字列
 */
export function formatImplementationStatus(results: ImplementationResult[]): string {
  if (!results.length) {
    return "指定された要件の実装は見つかりませんでした。";
  }
  
  const output: string[] = [];
  // 要件情報を取得（すべての結果で同じ）
  const reqInfo = results[0];
  output.push(`要件ID: ${reqInfo.requirement_id}`);
  output.push(`タイトル: ${reqInfo.requirement_title}`);
  output.push(`タイプ: ${reqInfo.requirement_type}`);
  output.push("\n実装状況:");
  output.push("=".repeat(80));
  output.push(`${"コードID".padEnd(10)} ${"名前".padEnd(20)} ${"種類".padEnd(10)} ${"実装タイプ".padEnd(20)} ${"場所"}`);
  output.push("-".repeat(80));
  
  for (const result of results) {
    output.push(`${(result.code_id || "").padEnd(10)} ${(result.code_name || "").padEnd(20)} ${(result.code_type || "").padEnd(10)} ` +
              `${(result.implementation_type || "").padEnd(20)} ${result.code_location || ""}`);
  }
  
  return output.join("\n");
}

/**
 * 未実装要件の結果を整形する関数
 * @param results 未実装要件検索結果の配列
 * @returns 整形された文字列
 */
export function formatUnimplementedRequirements(results: UnimplementedResult[]): string {
  const output: string[] = [];
  output.push("未実装の要件:");
  
  if (!results.length) {
    output.push("すべての要件が実装されています。");
  } else {
    for (const result of results) {
      output.push(`- ${result.requirement_id}: ${result.title}`);
    }
  }
  
  return output.join("\n");
}

/**
 * 階層構造を視覚的に表現する関数
 * @param items 階層構造のアイテム配列
 * @param level 現在の階層レベル（再帰用）
 * @returns 視覚的に整形された階層構造文字列
 */
export function formatHierarchy(
  items: Array<{id: string, title: string, children?: Array<any>}>, 
  level: number = 0
): string {
  const output: string[] = [];
  const indent = "  ".repeat(level);
  
  for (const item of items) {
    output.push(`${indent}|- ${item.id}: ${item.title}`);
    
    if (item.children && item.children.length > 0) {
      output.push(formatHierarchy(item.children, level + 1));
    }
  }
  
  return output.join("\n");
}

/**
 * 依存関係を視覚的に表現する関数
 * @param dependencies 依存関係の配列
 * @returns 視覚的に整形された依存関係文字列
 */
export function formatDependencies(
  dependencies: Array<{source: string, target: string, type: string}>
): string {
  const output: string[] = [];
  output.push("依存関係:");
  output.push("=".repeat(80));
  output.push(`${"ソース".padEnd(15)} ${"依存タイプ".padEnd(20)} ${"ターゲット".padEnd(15)}`);
  output.push("-".repeat(80));
  
  for (const dep of dependencies) {
    output.push(`${dep.source.padEnd(15)} ${dep.type.padEnd(20)} ${dep.target.padEnd(15)}`);
  }
  
  return output.join("\n");
}
