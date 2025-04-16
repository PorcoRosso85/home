#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-read --allow-write

/**
 * 要件間の依存関係を解析し、グラフ構造として表示するスクリプト
 * 
 * 使用方法:
 *   deno run --allow-read --allow-write requirementsDepsUsecase.ts <コマンド> [オプション]
 * 
 * コマンド:
 *   list              全ての要件を一覧表示
 *   deps <要件ID>     指定した要件の依存関係を表示
 *   graph             全ての要件の依存関係をグラフとして表示
 * 
 * オプション:
 *   --dir=<ディレクトリ>   要件JSONファイルが格納されているディレクトリを指定（デフォルト: ./data/requirements）
 *   --format=<形式>       出力形式を指定 (text, json, mermaid) （デフォルト: text）
 */

import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";
import { join } from "https://deno.land/std@0.220.1/path/mod.ts";

/**
 * 要件の依存関係を表すインターフェース
 */
interface RequirementDependency {
  id: string;
  title: string;
  description: string;
  outputType: string;
  dependencies: RequirementDependency[];
  status?: string;
  priority?: string;
  tags?: string[];
}

/**
 * メイン関数
 */
async function main() {
  // コマンドライン引数を解析
  const args = parse(Deno.args, {
    string: ["dir", "format"],
    default: {
      dir: "./data/requirements",
      format: "text"
    }
  });

  // 最初の引数をコマンドとして取得
  const command = args._[0] as string;
  
  // コマンドによって処理を分岐
  switch (command) {
    case "list":
      await listRequirements(args.dir);
      break;
    case "deps":
      const requirementId = args._[1] as string;
      if (!requirementId) {
        console.error("エラー: 要件IDを指定してください");
        console.log("使用例: deno run --allow-read --allow-write requirementsDepsUsecase.ts deps UserManager");
        Deno.exit(1);
      }
      await showDependencies(requirementId, args.dir, args.format);
      break;
    case "graph":
      await generateDependencyGraph(args.dir, args.format);
      break;
    default:
      showHelp();
      break;
  }
}

/**
 * ヘルプメッセージを表示
 */
function showHelp() {
  console.log(`
要件間の依存関係を解析し、グラフ構造として表示するスクリプト

使用方法:
  deno run --allow-read --allow-write requirementsDepsUsecase.ts <コマンド> [オプション]

コマンド:
  list              全ての要件を一覧表示
  deps <要件ID>     指定した要件の依存関係を表示
  graph             全ての要件の依存関係をグラフとして表示

オプション:
  --dir=<ディレクトリ>   要件JSONファイルが格納されているディレクトリを指定（デフォルト: ./data/requirements）
  --format=<形式>       出力形式を指定 (text, json, mermaid) （デフォルト: text）
  `);
}

/**
 * ディレクトリ内の全ての要件ファイルを読み込む
 * 
 * @param dirPath 要件ファイルが格納されているディレクトリパス
 * @returns 要件オブジェクトの配列
 */
async function loadAllRequirements(dirPath: string): Promise<any[]> {
  const requirements: any[] = [];
  
  try {
    // ディレクトリ内のファイル一覧を取得
    const entries = Deno.readDirSync(dirPath);
    
    // JSONファイルをフィルタリングして読み込む
    for (const entry of entries) {
      if (entry.isFile && entry.name.endsWith('.json')) {
        try {
          const filePath = join(dirPath, entry.name);
          const content = await Deno.readTextFile(filePath);
          const requirement = JSON.parse(content);
          requirements.push(requirement);
        } catch (error) {
          console.error(`ファイル ${entry.name} の読み込み/解析に失敗しました: ${error.message}`);
        }
      }
    }
  } catch (error) {
    console.error(`ディレクトリ ${dirPath} の読み込みに失敗しました: ${error.message}`);
    Deno.exit(1);
  }
  
  return requirements;
}

/**
 * 全ての要件を一覧表示
 * 
 * @param dirPath 要件ファイルが格納されているディレクトリパス
 */
async function listRequirements(dirPath: string) {
  const requirements = await loadAllRequirements(dirPath);
  
  console.log(`\n要件一覧 (${requirements.length}件):\n`);
  requirements.forEach(req => {
    console.log(`ID: ${req.id}`);
    console.log(`タイトル: ${req.title}`);
    console.log(`出力タイプ: ${req.outputType}`);
    console.log(`状態: ${req.status || '未設定'}`);
    if (req.dependencies && req.dependencies.length > 0) {
      console.log(`依存要件: ${req.dependencies.join(', ')}`);
    }
    console.log('-'.repeat(40));
  });
}

/**
 * 指定した要件IDの要件を取得
 * 
 * @param requirementId 要件ID
 * @param dirPath 要件ファイルが格納されているディレクトリパス
 * @returns 要件オブジェクト、存在しない場合はnull
 */
async function getRequirement(requirementId: string, dirPath: string): Promise<any | null> {
  try {
    // 要件ファイルのパス
    const filePath = join(dirPath, `${requirementId}.json`);
    
    // ファイルの存在確認
    try {
      await Deno.stat(filePath);
    } catch (error) {
      // ファイルが存在しない場合は全要件から検索
      const allRequirements = await loadAllRequirements(dirPath);
      return allRequirements.find(req => req.id === requirementId) || null;
    }
    
    // ファイルを読み込んでパース
    const content = await Deno.readTextFile(filePath);
    return JSON.parse(content);
  } catch (error) {
    console.error(`要件 ${requirementId} の取得に失敗しました: ${error.message}`);
    return null;
  }
}

/**
 * 要件の依存関係を再帰的に取得
 * 
 * @param requirementId 要件ID
 * @param dirPath 要件ファイルが格納されているディレクトリパス
 * @param visitedIds 訪問済み要件ID（循環参照対策）
 * @returns 依存関係情報
 */
async function getRequirementDependencies(
  requirementId: string,
  dirPath: string,
  visitedIds: Set<string> = new Set<string>()
): Promise<RequirementDependency | null> {
  // 循環参照チェック
  if (visitedIds.has(requirementId)) {
    return {
      id: requirementId,
      title: "[循環参照]",
      description: "",
      outputType: "",
      dependencies: []
    };
  }
  
  // 訪問済みに追加
  visitedIds.add(requirementId);
  
  // 要件を取得
  const requirement = await getRequirement(requirementId, dirPath);
  if (!requirement) {
    return null;
  }
  
  // 依存要件の取得
  const dependencies: RequirementDependency[] = [];
  
  // 依存配列が存在する場合、各依存要件を再帰的に取得
  if (requirement.dependencies && Array.isArray(requirement.dependencies)) {
    for (const depId of requirement.dependencies) {
      const depRequirement = await getRequirementDependencies(depId, dirPath, new Set(visitedIds));
      if (depRequirement) {
        dependencies.push(depRequirement);
      }
    }
  }
  
  // 結果を返す
  return {
    id: requirement.id,
    title: requirement.title,
    description: requirement.description,
    outputType: requirement.outputType,
    dependencies: dependencies,
    status: requirement.status,
    priority: requirement.priority,
    tags: requirement.tags
  };
}

/**
 * 要件の依存関係を表示
 * 
 * @param requirementId 要件ID
 * @param dirPath 要件ファイルが格納されているディレクトリパス
 * @param format 出力形式
 */
async function showDependencies(requirementId: string, dirPath: string, format: string) {
  const dependency = await getRequirementDependencies(requirementId, dirPath);
  
  if (!dependency) {
    console.error(`要件 ${requirementId} が見つかりませんでした`);
    Deno.exit(1);
  }
  
  // 出力形式によって表示方法を変更
  switch (format.toLowerCase()) {
    case "json":
      console.log(JSON.stringify(dependency, null, 2));
      break;
    case "mermaid":
      console.log("```mermaid");
      console.log("graph TD;");
      generateMermaidGraph(dependency);
      console.log("```");
      break;
    case "text":
    default:
      console.log(`要件 ${requirementId} の依存関係:\n`);
      console.log(dependencyToString(dependency));
      // 総依存数を表示
      const totalDeps = countTotalDependencies(dependency) - 1; // 自身を除外
      console.log(`\n総依存数: ${totalDeps}個\n`);
      break;
  }
}

/**
 * 全要件の依存関係グラフを生成
 * 
 * @param dirPath 要件ファイルが格納されているディレクトリパス
 * @param format 出力形式
 */
async function generateDependencyGraph(dirPath: string, format: string) {
  const requirements = await loadAllRequirements(dirPath);
  
  // 出力形式によって表示方法を変更
  switch (format.toLowerCase()) {
    case "json":
      const graph: Record<string, string[]> = {};
      
      for (const req of requirements) {
        graph[req.id] = req.dependencies || [];
      }
      
      console.log(JSON.stringify(graph, null, 2));
      break;
    case "mermaid":
      console.log("```mermaid");
      console.log("graph TD;");
      
      for (const req of requirements) {
        if (req.dependencies && Array.isArray(req.dependencies)) {
          for (const depId of req.dependencies) {
            console.log(`  ${depId} --> ${req.id};`);
          }
        }
        // 依存関係がない要件も表示
        if (!req.dependencies || req.dependencies.length === 0) {
          console.log(`  ${req.id};`);
        }
      }
      
      console.log("```");
      break;
    case "text":
    default:
      console.log(`要件依存関係グラフ (${requirements.length}件):\n`);
      
      for (const req of requirements) {
        console.log(`${req.id} (${req.outputType})`);
        if (req.dependencies && Array.isArray(req.dependencies)) {
          console.log(`  依存: ${req.dependencies.join(", ")}`);
        } else {
          console.log("  依存: なし");
        }
        console.log();
      }
      break;
  }
}

/**
 * 要件依存関係を文字列形式で表示（ツリー形式）
 * 
 * @param dependency 要件依存関係
 * @param indent インデントレベル（再帰呼び出し用）
 * @returns 文字列表現
 */
function dependencyToString(dependency: RequirementDependency, indent: number = 0): string {
  // インデント文字列
  const indentStr = "  ".repeat(indent);
  
  // 基本情報
  let result = `${indentStr}${dependency.id} (${dependency.outputType}): ${dependency.title}\n`;
  
  // 依存関係を再帰的に表示
  for (const dep of dependency.dependencies) {
    result += dependencyToString(dep, indent + 1);
  }
  
  return result;
}

/**
 * Mermaidグラフを生成する（再帰処理）
 * 
 * @param dependency 要件依存関係
 * @param processed 処理済み要件ID（循環参照対策）
 */
function generateMermaidGraph(
  dependency: RequirementDependency,
  processed: Set<string> = new Set<string>()
) {
  // 既に処理済みの場合はスキップ（循環参照対策）
  if (processed.has(dependency.id)) {
    return;
  }
  
  // 処理済みに追加
  processed.add(dependency.id);
  
  // このノードのスタイル定義
  console.log(`  ${dependency.id}["${dependency.id}\n(${dependency.outputType})"];`);
  
  // 依存関係の表示
  for (const dep of dependency.dependencies) {
    console.log(`  ${dep.id} --> ${dependency.id};`);
    generateMermaidGraph(dep, processed);
  }
}

/**
 * 総依存要件数をカウント
 * 
 * @param dependency 要件依存関係
 * @param counted カウント済みの要件（重複を避けるため）
 * @returns 依存要件の総数
 */
function countTotalDependencies(
  dependency: RequirementDependency,
  counted: Set<string> = new Set<string>()
): number {
  // 既にカウント済みならスキップ
  if (counted.has(dependency.id)) {
    return 0;
  }
  
  // この要件をカウント済みに追加
  counted.add(dependency.id);
  
  // 自身を1としてカウント
  let count = 1;
  
  // 依存先をすべて再帰的にカウント
  for (const dep of dependency.dependencies) {
    count += countTotalDependencies(dep, counted);
  }
  
  return count;
}

// メイン関数を実行
if (import.meta.main) {
  main().catch(err => {
    console.error(`エラーが発生しました: ${err.message}`);
    Deno.exit(1);
  });
}
