/**
 * 階層型トレーサビリティモデル - 結果整形関数
 * 
 * このファイルはテスト結果の整形に関する共通関数を提供します。
 * - 型定義
 * - 整形関数
 */

// ===== 型定義 =====

/**
 * コードから要件への逆引き結果型
 */
export interface RequirementResult {
  requirement_id: string;
  requirement_title: string;
  requirement_type: string;
  requirement_priority: string;
  implementation_type: string;
  requirement_location: string;
  relation_type: string;
}

/**
 * 要件の実装状況型
 */
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

/**
 * 未実装要件結果型
 */
export interface UnimplementedResult {
  requirement_id: string;
  title: string;
}

/**
 * 要件の検証状況型
 */
export interface VerificationResult {
  requirement_id: string;
  requirement_title: string;
  verification_id: string;
  verification_name: string;
  verification_type: string;
  status: string;
}

/**
 * コード参照結果型
 */
export interface ReferenceResult {
  source_id: string;
  source_name: string;
  source_type: string;
  target_id: string;
  target_name: string;
  target_type: string;
  ref_type: string;
}

/**
 * バージョン追跡結果型
 */
export interface VersionTrackingResult {
  version_id: string;
  entity_id: string;
  entity_name: string;
  entity_type: string;
  change_type: string;
  timestamp: string;
}

/**
 * 集計ビュー結果型
 */
export interface AggregationViewResult {
  view_id: string;
  view_type: string;
  target_id: string;
  target_type: string;
  aggregation_value: string;
}

// ===== 整形関数 =====

/**
 * クエリ結果を単純にフォーマットする関数
 * @param result クエリ結果オブジェクト
 */
export function formatQueryResult(result: any): void {
  if (!result || result.getNumTuples() === 0) {
    console.log("結果がありません");
    return;
  }

  // 利用可能なメソッドを確認
  try {
    // リセットして先頭から読み取る
    result.resetIterator();
    
    // 結果を一行ずつ処理
    let rowCount = 0;
    while (result.hasNext()) {
      // 次の行を取得
      const row = result.getNextSync();
      
      // 最初の行でヘッダーを表示
      if (rowCount === 0) {
        const headers = Object.keys(row);
        console.log(headers.join(" | "));
        console.log("-".repeat(80));
      }
      
      // 行データを表示
      const values = Object.values(row);
      console.log(values.join(" | "));
      
      rowCount++;
    }
    
    console.log("-".repeat(80));
  } catch (e) {
    // エラーがあった場合はメッセージを表示
    console.error("結果のフォーマット中にエラーが発生しました:", e);
  }
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
    output.push(
      `${result.requirement_id.padEnd(10)} ${(result.requirement_title || "").slice(0, 30).padEnd(30)} ` +
      `${(result.requirement_type || "").padEnd(10)} ${(result.requirement_priority || "").padEnd(10)} ` +
      `${(result.relation_type || "").slice(0, 20).padEnd(20)} ${result.requirement_location || ""}`
    );
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
    output.push(
      `${(result.code_id || "").padEnd(10)} ${(result.code_name || "").padEnd(20)} ${(result.code_type || "").padEnd(10)} ` +
      `${(result.implementation_type || "").padEnd(20)} ${result.code_location || ""}`
    );
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
 * 検証状況の結果を整形する関数
 * @param results 検証状況検索結果の配列
 * @returns 整形された文字列
 */
export function formatVerificationStatus(results: VerificationResult[]): string {
  if (!results.length) {
    return "指定された要件の検証項目は見つかりませんでした。";
  }
  
  const output: string[] = [];
  // 要件情報を取得（結果の最初の要素から）
  const reqInfo = results[0];
  output.push(`要件ID: ${reqInfo.requirement_id}`);
  output.push(`タイトル: ${reqInfo.requirement_title}`);
  output.push("\n検証状況:");
  output.push("=".repeat(80));
  output.push(`${"検証ID".padEnd(10)} ${"名前".padEnd(25)} ${"タイプ".padEnd(15)} ${"状態".padEnd(15)}`);
  output.push("-".repeat(80));
  
  for (const result of results) {
    output.push(
      `${(result.verification_id || "").padEnd(10)} ${(result.verification_name || "").padEnd(25)} ` +
      `${(result.verification_type || "").padEnd(15)} ${(result.status || "").padEnd(15)}`
    );
  }
  
  return output.join("\n");
}

/**
 * コード参照の結果を整形する関数
 * @param results コード参照検索結果の配列
 * @returns 整形された文字列
 */
export function formatReferences(results: ReferenceResult[]): string {
  if (!results.length) {
    return "参照関係は見つかりませんでした。";
  }
  
  const output: string[] = [];
  output.push("\n参照関係:");
  output.push("=".repeat(90));
  output.push(`${"ソースID".padEnd(10)} ${"ソース名".padEnd(20)} ${"参照タイプ".padEnd(15)} ${"ターゲットID".padEnd(10)} ${"ターゲット名".padEnd(20)} ${"ターゲットタイプ".padEnd(10)}`);
  output.push("-".repeat(90));
  
  for (const result of results) {
    output.push(
      `${(result.source_id || "").padEnd(10)} ${(result.source_name || "").padEnd(20)} ` +
      `${(result.ref_type || "").padEnd(15)} ${(result.target_id || "").padEnd(10)} ` +
      `${(result.target_name || "").padEnd(20)} ${(result.target_type || "").padEnd(10)}`
    );
  }
  
  return output.join("\n");
}

/**
 * バージョン追跡の結果を整形する関数
 * @param results バージョン追跡検索結果の配列
 * @returns 整形された文字列
 */
export function formatVersionTracking(results: VersionTrackingResult[]): string {
  if (!results.length) {
    return "バージョン追跡情報は見つかりませんでした。";
  }
  
  const output: string[] = [];
  output.push("\nバージョン追跡:");
  output.push("=".repeat(100));
  output.push(`${"バージョン".padEnd(10)} ${"エンティティID".padEnd(10)} ${"エンティティ名".padEnd(20)} ${"タイプ".padEnd(15)} ${"変更種別".padEnd(15)} ${"タイムスタンプ".padEnd(25)}`);
  output.push("-".repeat(100));
  
  // タイムスタンプでソート
  const sortedResults = [...results].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
  });
  
  for (const result of sortedResults) {
    output.push(
      `${(result.version_id || "").padEnd(10)} ${(result.entity_id || "").padEnd(10)} ` +
      `${(result.entity_name || "").padEnd(20)} ${(result.entity_type || "").padEnd(15)} ` +
      `${(result.change_type || "").padEnd(15)} ${(result.timestamp || "").padEnd(25)}`
    );
  }
  
  return output.join("\n");
}

/**
 * 集計ビューの結果を整形する関数
 * @param results 集計ビュー検索結果の配列
 * @returns 整形された文字列
 */
export function formatAggregationView(results: AggregationViewResult[]): string {
  if (!results.length) {
    return "集計ビュー情報は見つかりませんでした。";
  }
  
  const output: string[] = [];
  output.push("\n集計ビュー:");
  output.push("=".repeat(80));
  output.push(`${"ビューID".padEnd(10)} ${"ビュータイプ".padEnd(15)} ${"ターゲットID".padEnd(10)} ${"ターゲットタイプ".padEnd(15)} ${"集計値"}`);
  output.push("-".repeat(80));
  
  for (const result of results) {
    output.push(
      `${(result.view_id || "").padEnd(10)} ${(result.view_type || "").padEnd(15)} ` +
      `${(result.target_id || "").padEnd(10)} ${(result.target_type || "").padEnd(15)} ` +
      `${result.aggregation_value || ""}`
    );
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
