import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";
import { join } from "https://deno.land/std@0.220.1/path/mod.ts";

/**
 * 要件間の依存関係を解析するコマンド
 */
export class RequirementsDepsCommand implements Command {
  private fileReader: FileSystemReader;
  private requirementsDir: string;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイルシステムリーダー
   * @param requirementsDir 要件ディレクトリパス
   */
  constructor(fileReader: FileSystemReader, requirementsDir: string) {
    this.fileReader = fileReader;
    this.requirementsDir = requirementsDir;
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const subCommand = args._[1] as string;
    
    if (!subCommand) {
      console.log(`
要件間の依存関係を解析し、グラフ構造として表示します

サブコマンド:
  list              全ての要件を一覧表示
  deps <要件ID>     指定した要件の依存関係を表示
  graph             全ての要件の依存関係をグラフとして表示

オプション:
  --format=<形式>   出力形式を指定 (text, json, mermaid) （デフォルト: text）
      `);
      return;
    }

    const format = args.format || "text";
    const dir = this.requirementsDir;

    switch (subCommand) {
      case "list":
        await this.listRequirements(dir);
        break;
      case "deps":
        const requirementId = args._[2] as string;
        if (!requirementId) {
          throw new Error("要件IDを指定してください");
        }
        await this.showDependencies(requirementId, dir, format);
        break;
      case "graph":
        await this.generateDependencyGraph(dir, format);
        break;
      default:
        throw new Error(`未知のサブコマンド: ${subCommand}`);
    }
  }

  /**
   * 全ての要件を一覧表示
   * 
   * @param dirPath 要件ファイルが格納されているディレクトリパス
   */
  private async listRequirements(dirPath: string): Promise<void> {
    try {
      const requirements = await this.loadAllRequirements(dirPath);
      
      console.log(`\n要件一覧 (${requirements.length}件):\n`);
      requirements.forEach(req => {
        console.log(`ID: ${req.id}`);
        console.log(`タイトル: ${req.title}`);
        console.log(`出力タイプ: ${req.outputType || req.implementationType}`);
        console.log(`状態: ${req.status || '未設定'}`);
        if (req.dependencies && req.dependencies.length > 0) {
          console.log(`依存要件: ${req.dependencies.join(', ')}`);
        }
        console.log('-'.repeat(40));
      });
    } catch (error) {
      throw new Error(`要件一覧の取得に失敗しました: ${error.message}`);
    }
  }

  /**
   * ディレクトリ内の全ての要件ファイルを読み込む
   * 
   * @param dirPath 要件ファイルが格納されているディレクトリパス
   * @returns 要件オブジェクトの配列
   */
  private async loadAllRequirements(dirPath: string): Promise<any[]> {
    const requirements: any[] = [];
    
    try {
      // ディレクトリ内のファイル一覧を取得
      const entries: Deno.DirEntry[] = [];
      for await (const entry of Deno.readDir(dirPath)) {
        entries.push(entry);
      }
      
      // JSONファイルをフィルタリングして読み込む
      for (const entry of entries) {
        if (entry.isFile && entry.name.endsWith('.json') || entry.name.endsWith('.require.json')) {
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
      throw new Error(`ディレクトリ ${dirPath} の読み込みに失敗しました: ${error.message}`);
    }
    
    return requirements;
  }

  /**
   * 指定した要件IDの要件を取得
   * 
   * @param requirementId 要件ID
   * @param dirPath 要件ファイルが格納されているディレクトリパス
   * @returns 要件オブジェクト、存在しない場合はnull
   */
  private async getRequirement(requirementId: string, dirPath: string): Promise<any | null> {
    try {
      // 要件ファイルの可能性のあるパスを作成
      const possiblePaths = [
        join(dirPath, `${requirementId}.json`),
        join(dirPath, `${requirementId}.require.json`)
      ];
      
      // 各パスを試す
      for (const path of possiblePaths) {
        try {
          await Deno.stat(path);
          const content = await Deno.readTextFile(path);
          return JSON.parse(content);
        } catch (error) {
          // ファイルが存在しない場合は次のパスを試す
          if (!(error instanceof Deno.errors.NotFound)) {
            throw error;
          }
        }
      }
      
      // ファイルが見つからない場合は全要件から検索
      const allRequirements = await this.loadAllRequirements(dirPath);
      return allRequirements.find(req => req.id === requirementId) || null;
    } catch (error) {
      throw new Error(`要件 ${requirementId} の取得に失敗しました: ${error.message}`);
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
  private async getRequirementDependencies(
    requirementId: string,
    dirPath: string,
    visitedIds: Set<string> = new Set<string>()
  ): Promise<any | null> {
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
    const requirement = await this.getRequirement(requirementId, dirPath);
    if (!requirement) {
      return null;
    }
    
    // 依存要件の取得
    const dependencies: any[] = [];
    
    // 依存配列が存在する場合、各依存要件を再帰的に取得
    if (requirement.dependencies && Array.isArray(requirement.dependencies)) {
      for (const depId of requirement.dependencies) {
        const depRequirement = await this.getRequirementDependencies(depId, dirPath, new Set(visitedIds));
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
      outputType: requirement.outputType || requirement.implementationType,
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
  private async showDependencies(requirementId: string, dirPath: string, format: string): Promise<void> {
    const dependency = await this.getRequirementDependencies(requirementId, dirPath);
    
    if (!dependency) {
      throw new Error(`要件 ${requirementId} が見つかりませんでした`);
    }
    
    // 出力形式によって表示方法を変更
    switch (format.toLowerCase()) {
      case "json":
        console.log(JSON.stringify(dependency, null, 2));
        break;
      case "mermaid":
        console.log("```mermaid");
        console.log("graph TD;");
        this.generateMermaidGraph(dependency);
        console.log("```");
        break;
      case "text":
      default:
        console.log(`要件 ${requirementId} の依存関係:\n`);
        console.log(this.dependencyToString(dependency));
        // 総依存数を表示
        const totalDeps = this.countTotalDependencies(dependency) - 1; // 自身を除外
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
  private async generateDependencyGraph(dirPath: string, format: string): Promise<void> {
    const requirements = await this.loadAllRequirements(dirPath);
    
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
          console.log(`${req.id} (${req.outputType || req.implementationType || "unknown"})`);
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
  private dependencyToString(dependency: any, indent: number = 0): string {
    // インデント文字列
    const indentStr = "  ".repeat(indent);
    
    // 基本情報
    let result = `${indentStr}${dependency.id} (${dependency.outputType || "unknown"}): ${dependency.title}\n`;
    
    // 依存関係を再帰的に表示
    for (const dep of dependency.dependencies) {
      result += this.dependencyToString(dep, indent + 1);
    }
    
    return result;
  }

  /**
   * Mermaidグラフを生成する（再帰処理）
   * 
   * @param dependency 要件依存関係
   * @param processed 処理済み要件ID（循環参照対策）
   */
  private generateMermaidGraph(
    dependency: any,
    processed: Set<string> = new Set<string>()
  ): void {
    // 既に処理済みの場合はスキップ（循環参照対策）
    if (processed.has(dependency.id)) {
      return;
    }
    
    // 処理済みに追加
    processed.add(dependency.id);
    
    // このノードのスタイル定義
    console.log(`  ${dependency.id}["${dependency.id}\n(${dependency.outputType || "unknown"})"];`);
    
    // 依存関係の表示
    for (const dep of dependency.dependencies) {
      console.log(`  ${dep.id} --> ${dependency.id};`);
      this.generateMermaidGraph(dep, processed);
    }
  }

  /**
   * 総依存要件数をカウント
   * 
   * @param dependency 要件依存関係
   * @param counted カウント済みの要件（重複を避けるため）
   * @returns 依存要件の総数
   */
  private countTotalDependencies(
    dependency: any,
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
      count += this.countTotalDependencies(dep, counted);
    }
    
    return count;
  }
}
