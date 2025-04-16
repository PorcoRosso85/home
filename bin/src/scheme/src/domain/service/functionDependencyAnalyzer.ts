import { FileSystemReader } from "../../infrastructure/fileSystemReader.ts";

/**
 * 関数の機能的依存関係を表すインターフェース
 */
export interface FunctionDependency {
  functionId: string;
  metaSchema: string;
  dependencies: FunctionDependency[];
  description?: string;
  executionOrder?: number;
  isOptional?: boolean;
}

/**
 * 関数型の機能的依存関係を解析するためのサービス
 */
export class FunctionDependencyAnalyzer {
  private fileReader: FileSystemReader;
  private schemaDir: string;
  private dependencyCache: Map<string, FunctionDependency> = new Map<string, FunctionDependency>();

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイル読み込みオブジェクト
   * @param schemaDir スキーマファイルが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, schemaDir: string = "./data/generated") {
    this.fileReader = fileReader;
    this.schemaDir = schemaDir;
  }

  /**
   * 関数型の機能的依存関係を取得する
   * 
   * @param functionId 関数ID
   * @param visitedFunctions 循環参照検出用の訪問済み関数セット（内部再帰用）
   * @returns 機能的依存関係
   */
  public async getFunctionDependency(
    functionId: string,
    visitedFunctions: Set<string> = new Set<string>()
  ): Promise<FunctionDependency | null> {
    // 循環参照の検出
    if (visitedFunctions.has(functionId)) {
      return {
        functionId,
        metaSchema: "Function",
        dependencies: [],
        description: "循環参照を検出: " + functionId
      };
    }

    // キャッシュにあればそれを返す
    if (this.dependencyCache.has(functionId)) {
      return this.dependencyCache.get(functionId)!;
    }

    // 訪問済み関数に追加
    visitedFunctions.add(functionId);

    try {
      // 依存関係スキーマのパス
      const depSchemaPath = `${this.schemaDir}/${functionId}.FunctionDependency.schema.json`;

      // スキーマを読み込む
      const schema = await this.fileReader.readJsonFile(depSchemaPath);

      if (!schema || !schema.dependencies || !Array.isArray(schema.dependencies)) {
        return {
          functionId,
          metaSchema: "Function",
          dependencies: [],
          description: schema?.description || `${functionId} の機能的依存関係`
        };
      }

      // 実行順序でソート
      const sortedDeps = [...schema.dependencies].sort(
        (a, b) => (a.executionOrder || 0) - (b.executionOrder || 0)
      );

      // 依存関係の配列を構築
      const dependencies: FunctionDependency[] = [];

      // 各依存関係を再帰的に解析
      for (const dep of sortedDeps) {
        if (dep.functionId) {
          // 依存先の関数の依存関係を再帰的に取得
          const depDependency = await this.getFunctionDependency(
            dep.functionId,
            new Set(visitedFunctions) // 新しいセットを作成して渡す（参照渡しの問題を回避）
          );

          if (depDependency) {
            // 結果に追加
            dependencies.push({
              ...depDependency,
              description: dep.description,
              executionOrder: dep.executionOrder,
              isOptional: dep.isOptional
            });
          }
        }
      }

      // 結果を構築
      const result: FunctionDependency = {
        functionId,
        metaSchema: "Function",
        dependencies,
        description: schema.description || `${functionId} の機能的依存関係`
      };

      // キャッシュに追加
      this.dependencyCache.set(functionId, result);

      return result;
    } catch (error) {
      console.warn(`${functionId} の機能的依存関係を取得できませんでした: ${error.message}`);
      return null;
    }
  }

  /**
   * 関数型の機能的依存関係を取得する（フラット形式）
   * 
   * @param functionId 関数ID
   * @returns 依存関係のフラットなリスト（直接依存のみ）
   */
  public async getFlatFunctionDependencies(functionId: string): Promise<string[]> {
    try {
      // 依存関係スキーマのパス
      const depSchemaPath = `${this.schemaDir}/${functionId}.FunctionDependency.schema.json`;

      // スキーマを読み込む
      const schema = await this.fileReader.readJsonFile(depSchemaPath);

      if (!schema || !schema.dependencies || !Array.isArray(schema.dependencies)) {
        return [];
      }

      // 実行順序でソート
      const sortedDeps = [...schema.dependencies].sort(
        (a, b) => (a.executionOrder || 0) - (b.executionOrder || 0)
      );

      // 依存関係の配列を構築
      const dependencies: string[] = [];

      // 各依存関係を収集
      for (const dep of sortedDeps) {
        if (dep.functionId) {
          dependencies.push(dep.functionId);
        }
      }

      return dependencies;
    } catch (error) {
      console.warn(`${functionId} の機能的依存関係を取得できませんでした: ${error.message}`);
      return [];
    }
  }

  /**
   * 依存関係をツリー形式の文字列に変換
   * 
   * @param dependency 依存関係
   * @param indent インデントレベル
   * @returns フォーマットされた文字列
   */
  public dependencyToString(dependency: FunctionDependency, indent: number = 0): string {
    const indentStr = '  '.repeat(indent);
    let result = `${indentStr}${dependency.functionId} [${dependency.metaSchema}]`;
    
    if (dependency.description) {
      result += ` - ${dependency.description}`;
    }
    
    if (dependency.isOptional) {
      result += ' (オプション)';
    }
    
    result += '\n';
    
    for (const dep of dependency.dependencies) {
      result += this.dependencyToString(dep, indent + 1);
    }
    
    return result;
  }

  /**
   * 関数間の依存関係マップを構築
   * 
   * @param functionIds 解析対象の関数ID配列
   * @returns 依存関係マップ（関数ID -> 依存先関数ID配列）
   */
  public async buildDependencyMap(functionIds: string[]): Promise<Map<string, string[]>> {
    const depMap = new Map<string, string[]>();
    
    for (const functionId of functionIds) {
      const deps = await this.getFlatFunctionDependencies(functionId);
      depMap.set(functionId, deps);
      
      // 依存先の関数も依存マップに追加（存在しない場合は空配列で）
      for (const depFunc of deps) {
        if (!depMap.has(depFunc)) {
          depMap.set(depFunc, []);
        }
      }
    }
    
    return depMap;
  }
}
