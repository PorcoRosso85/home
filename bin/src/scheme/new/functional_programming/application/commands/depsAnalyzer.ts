/**
 * depsAnalyzer.ts
 * 
 * スキーマの依存関係解析のためのアプリケーションサービス
 * 
 * 依存処理解析の実装構成：
 * 
 * 1. 探索先指定処理
 *    - ファイル: /interface/depsCommand.ts
 *    - 関数: parseDepsCommandOptions
 *    - 役割: コマンドライン引数から解析対象のスキーマファイルパスを解析
 * 
 * 2. 指定探索先解決とエラーハンドリング
 *    - ファイル: /application/commands/depsAnalyzer.ts (当ファイル)
 *    - 関数: analyzeDependencies
 *    - 役割: スキーマファイルの読み込みと依存関係解析の実行、エラー処理
 * 
 * 3. 再帰処理ハンドリング
 *    - ファイル: /domain/service/dependencyAnalyzer.ts
 *    - 関数: findReferences, buildDependencyTree
 *    - 役割: スキーマ内の$ref参照を再帰的に検索し、依存関係ツリーを構築
 * 
 * 4. レンダリング処理
 *    - ファイル: /application/commands/depsAnalyzer.ts (当ファイル)
 *    - 関数: formatDependencyAnalysisResult
 *    - 役割: 依存関係解析結果を整形された文字列として返す
 * 
 * これらの処理は全て独立した関数として実装されており、単一責任の原則に従っています。
 * 関数型プログラミングのアプローチに沿って、副作用を最小限に抑え、
 * 入力から出力への変換として実装されています。
 */

import { readJsonFile } from "../../infrastructure/fileSystem.ts";
import { buildDependencyTree, findUnresolvedDependencies } from "../../domain/service/dependencyAnalyzer.ts";
import { TypeDependency, dependencyToString } from "../../domain/service/referenceAnalyzer.ts";

/**
 * 依存関係解析結果
 */
export interface DependencyAnalysisResult {
  /** 成功フラグ */
  success: boolean;
  /** メッセージ */
  message: string;
  /** 依存関係ツリー（成功時のみ） */
  dependencyTree?: TypeDependency;
  /** 未解決の依存関係（成功時のみ） */
  unresolvedDependencies?: string[];
}

/**
 * スキーマファイルの依存関係を解析する
 * 
 * @param schemaPath 解析対象のスキーマファイルパス
 * @returns 依存関係解析結果
 */
export async function analyzeDependencies(schemaPath: string): Promise<DependencyAnalysisResult> {
  try {
    // スキーマファイルを読み込む
    const schema = await readJsonFile(schemaPath) as any;
    
    // スキーマのタイトルまたはファイル名を取得
    const schemaName = schema.title || schemaPath.split('/').pop() || "unknown";
    
    // 依存関係ツリーを構築
    const dependencyTree = buildDependencyTree(schema, schemaName);
    
    // 現時点では利用可能な型のセットは空と仮定
    // 将来的には、利用可能な型のレジストリを実装する予定
    const availableTypes = new Set<string>();
    
    // 未解決の依存関係を検出
    const unresolvedDependencies = findUnresolvedDependencies(dependencyTree, availableTypes);
    
    return {
      success: true,
      message: "依存関係の解析が完了しました",
      dependencyTree,
      unresolvedDependencies
    };
  } catch (error) {
    return {
      success: false,
      message: `依存関係の解析に失敗しました: ${error instanceof Error ? error.message : '不明なエラー'}`
    };
  }
}

/**
 * 依存関係解析結果を整形された文字列として返す
 * 
 * @param result 依存関係解析結果
 * @returns 整形された文字列
 */
export function formatDependencyAnalysisResult(result: DependencyAnalysisResult): string {
  if (!result.success) {
    return `エラー: ${result.message}`;
  }
  
  let output = "依存関係解析結果:\n\n";
  
  if (result.dependencyTree) {
    output += "【依存関係ツリー】\n";
    output += dependencyToString(result.dependencyTree);
    output += "\n\n";
  }
  
  if (result.unresolvedDependencies && result.unresolvedDependencies.length > 0) {
    output += "【未解決の依存関係】\n";
    output += result.unresolvedDependencies.map(dep => `- ${dep}`).join('\n');
    output += "\n\n";
  } else {
    output += "未解決の依存関係はありません。\n\n";
  }
  
  return output;
}
