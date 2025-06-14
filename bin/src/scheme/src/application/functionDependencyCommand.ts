import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { loadPathsFromDirectory, buildDirectoryTree, extractDependencyPaths } from "../utils/pathExtractor.ts";
import { FunctionDependencyAnalyzer } from "../domain/service/functionDependencyAnalyzer.ts";
import { DependencyGraphVisualizer } from "../domain/service/dependencyGraphVisualizer.ts";

/**
 * 関数型の機能的依存関係を表示するコマンド
 */
export class FunctionDependencyCommand implements Command {
  private fileReader: FileSystemReader;
  private requirementsDir: string;
  private generatedDir: string;
  private typeIdToPathMap: Map<string, string> = new Map<string, string>();
  private pathToTypeIdMap: Map<string, string> = new Map<string, string>();
  private dependencyAnalyzer: FunctionDependencyAnalyzer;
  private verbose = false;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイルシステムリーダー
   * @param requirementsDir 要件ファイルが格納されているディレクトリパス
   * @param generatedDir 生成されたスキーマが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, requirementsDir: string, generatedDir: string = "./data/generated") {
    this.fileReader = fileReader;
    this.requirementsDir = requirementsDir;
    this.generatedDir = generatedDir;
    this.dependencyAnalyzer = new FunctionDependencyAnalyzer(fileReader, generatedDir);
  }

  /**
   * コマンドの説明を取得
   */
  getDescription(): string {
    return "関数型の機能的依存関係を表示します";
  }

  /**
   * コマンドの使用方法を取得
   */
  getUsage(): string {
    return "function-deps [--format=<grid|tree|list>] [--dir=<要件ディレクトリパス>] [--generated-dir=<生成済みスキーマディレクトリパス>]";
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const dir = args.dir || this.requirementsDir;
    this.verbose = args.verbose || false;
    const generatedDir = args.generatedDir || this.generatedDir;
    const format = args.format || "grid"; // デフォルトはグリッド形式
    
    // 特定の関数を指定するケース
    const specificFunction = args._?.length > 1 ? args._[1] : null;
    
    if (this.verbose) {
      console.log(`実行パラメータ:
- ディレクトリ: ${dir}
- 詳細モード: ${this.verbose}
- 生成スキーマディレクトリ: ${generatedDir}
- 出力形式: ${format}
- 指定関数: ${specificFunction || "なし"}
`);
    }
    
    try {
      if (specificFunction) {
        // 特定の関数の依存関係を表示
        await this.displaySingleFunctionDependency(specificFunction, format);
      } else {
        // すべての関数型から機能的依存関係を持つものを表示
        await this.displayAllFunctionDependencies(dir, generatedDir, format);
      }
    } catch (error) {
      console.error(`エラー: ${error.message}`);
    }
  }

  /**
   * 特定の関数の依存関係を表示
   * 
   * @param functionId 関数ID
   * @param format 出力形式
   */
  private async displaySingleFunctionDependency(functionId: string, format: string): Promise<void> {
    console.log(`関数 "${functionId}" の機能的依存関係:\n`);
    
    if (format === "tree") {
      const dependency = await this.dependencyAnalyzer.getFunctionDependency(functionId);
      if (dependency) {
        console.log(this.dependencyAnalyzer.dependencyToString(dependency));
      } else {
        console.log(`関数 "${functionId}" の機能的依存関係は定義されていません。`);
      }
    } else if (format === "list") {
      const deps = await this.dependencyAnalyzer.getFlatFunctionDependencies(functionId);
      if (deps.length > 0) {
        console.log(`${functionId} は以下の関数に依存しています:`);
        for (let i = 0; i < deps.length; i++) {
          console.log(`${i + 1}. ${deps[i]}`);
        }
      } else {
        console.log(`関数 "${functionId}" は他の関数に依存していないか、依存関係が定義されていません。`);
      }
    } else {
      // グリッド形式の表示はスキップ（1関数の場合はあまり意味がない）
      const deps = await this.dependencyAnalyzer.getFlatFunctionDependencies(functionId);
      if (deps.length > 0) {
        console.log(`${functionId} -> [${deps.join(', ')}]`);
      } else {
        console.log(`関数 "${functionId}" は他の関数に依存していないか、依存関係が定義されていません。`);
      }
    }
  }

  /**
   * すべての関数型の依存関係を表示
   * 
   * @param dir 要件ディレクトリ
   * @param generatedDir 生成スキーマディレクトリ
   * @param format 出力形式
   */
  private async displayAllFunctionDependencies(dir: string, generatedDir: string, format: string): Promise<void> {
    // ファイル情報を読み込む
    const files = await loadPathsFromDirectory(dir);
    
    if (files.length === 0) {
      console.log(`指定されたディレクトリ (${dir}) にJSONファイルが見つかりません`);
      return;
    }
    
    // ディレクトリツリーを構築
    const tree = buildDirectoryTree(files);
    
    // パスを抽出
    const paths = extractDependencyPaths(tree);
    
    // 型の情報を構築
    await this.buildTypeMapping(paths, generatedDir);
    
    // 関数型の一覧を取得
    const functionTypes: string[] = [];
    for (const [typeId] of this.typeIdToPathMap.entries()) {
      if (typeId.endsWith('.Function')) {
        functionTypes.push(typeId.split('.')[0]); // 関数名部分のみ抽出
      }
    }
    
    if (functionTypes.length === 0) {
      console.log("関数型が見つかりませんでした。");
      return;
    }
    
    if (this.verbose) {
      console.log(`${functionTypes.length}個の関数型が見つかりました: ${functionTypes.join(', ')}`);
    }
    
    // 出力形式に応じた表示
    if (format === "tree") {
      await this.displayDependencyTrees(functionTypes);
    } else if (format === "list") {
      await this.displayDependencyLists(functionTypes);
    } else {
      // デフォルトはグリッド形式
      await this.displayDependencyGrid(functionTypes);
    }
  }

  /**
   * ツリー形式で依存関係を表示
   * 
   * @param functionTypes 関数型リスト
   */
  private async displayDependencyTrees(functionTypes: string[]): Promise<void> {
    console.log("関数型の機能的依存関係ツリー:\n");
    
    let foundDependencies = false;
    
    for (const functionId of functionTypes) {
      const dependency = await this.dependencyAnalyzer.getFunctionDependency(functionId);
      if (dependency && dependency.dependencies.length > 0) {
        console.log(this.dependencyAnalyzer.dependencyToString(dependency));
        console.log(); // 空行で区切る
        foundDependencies = true;
      }
    }
    
    if (!foundDependencies) {
      console.log("機能的依存関係が定義された関数型はありません。");
    }
  }

  /**
   * リスト形式で依存関係を表示
   * 
   * @param functionTypes 関数型リスト
   */
  private async displayDependencyLists(functionTypes: string[]): Promise<void> {
    console.log("関数型の機能的依存関係リスト:\n");
    
    let foundDependencies = false;
    
    for (const functionId of functionTypes) {
      const deps = await this.dependencyAnalyzer.getFlatFunctionDependencies(functionId);
      if (deps.length > 0) {
        console.log(`${functionId}:`);
        for (let i = 0; i < deps.length; i++) {
          console.log(`  ${i + 1}. ${deps[i]}`);
        }
        console.log(); // 空行で区切る
        foundDependencies = true;
      }
    }
    
    if (!foundDependencies) {
      console.log("機能的依存関係が定義された関数型はありません。");
    }
  }

  /**
   * グリッド形式で依存関係を表示
   * 
   * @param functionTypes 関数型リスト
   */
  private async displayDependencyGrid(functionTypes: string[]): Promise<void> {
    // 依存関係マップを構築
    const depMap = await this.dependencyAnalyzer.buildDependencyMap(functionTypes);
    
    // 実行順序情報を取得
    const executionOrderMap = await this.buildExecutionOrderMap(functionTypes);
    
    // 依存関係があるかチェック
    let hasAnyDependencies = false;
    for (const deps of depMap.values()) {
      if (deps.length > 0) {
        hasAnyDependencies = true;
        break;
      }
    }
    
    if (!hasAnyDependencies) {
      console.log("機能的依存関係が定義された関数型はありません。");
      return;
    }
    
    console.log("\n関数型の機能的依存関係マップ:\n");
    
    // 依存関係グラフの可視化
    const visualizer = new DependencyGraphVisualizer(depMap, executionOrderMap);
    const grid = visualizer.visualize(80); // 幅を広げて表示を改善
    
    // 関数のパス情報を追加
    const sortedFuncs = this.getSortedFunctions(depMap);
    const maxPathLength = this.getMaxPathLength(sortedFuncs);
    
    // グラフを表示
    for (let i = 0; i < sortedFuncs.length; i++) {
      if (i < grid.length) {
        const func = sortedFuncs[i];
        const funcTypeId = `${func}.Function`;
        
        // パス情報を取得 - 空でも関数名をデフォルトとして使用
        let path = this.typeIdToPathMap.get(funcTypeId) || "";
        
        // パス情報が空の場合は、関数名をファイルパスとして使用
        if (!path) {
          // 存在するパスの形式に合わせてパスを生成
          path = `/src/${func.toLowerCase()}/${func}.js`;
          if (this.verbose) {
            console.log(`注意: ${func} のファイルパスが見つからなかったため、推定パスを使用: ${path}`);
          }
        }
        
        // パス情報を表示用にフォーマット
        const displayInfo = `${path}:::${funcTypeId}`.padEnd(maxPathLength);
        
        // パス情報とグラフを結合
        grid[i][0] = displayInfo;
        console.log(grid[i].join(""));
      }
    }
  }

  /**
   * 実行順序マップを構築
   * 
   * @param functionTypes 関数型リスト
   * @returns 実行順序マップ
   */
  private async buildExecutionOrderMap(
    functionTypes: string[]
  ): Promise<Map<string, Map<string, number>>> {
    const orderMap = new Map<string, Map<string, number>>();
    
    for (const func of functionTypes) {
      try {
        // 依存関係スキーマのパス
        const depSchemaPath = `${this.generatedDir}/${func}.FunctionDependency.schema.json`;
        
        // スキーマを読み込む
        const schema = await this.fileReader.readJsonFile(depSchemaPath);
        
        if (schema && schema.dependencies && Array.isArray(schema.dependencies)) {
          const funcOrderMap = new Map<string, number>();
          
          // 各依存関係の実行順序を取得
          for (let i = 0; i < schema.dependencies.length; i++) {
            const dep = schema.dependencies[i];
            if (dep.functionId) {
              // 実行順序が指定されていればそれを使用、なければ配列インデックスを使用
              const order = dep.executionOrder !== undefined ? dep.executionOrder : i;
              funcOrderMap.set(dep.functionId, order);
            }
          }
          
          orderMap.set(func, funcOrderMap);
        }
      } catch (error) {
        // ファイルが見つからない場合はスキップ
        if (this.verbose) {
          console.log(`${func} の実行順序情報が取得できませんでした: ${error.message}`);
        }
      }
    }
    
    return orderMap;
  }
  
  /**
   * 関数を依存関係の複雑さでソート
   * 
   * @param depMap 依存関係マップ
   * @returns ソートされた関数配列
   */
  private getSortedFunctions(depMap: Map<string, string[]>): string[] {
    return [...depMap.keys()].sort((a, b) => {
      const aSize = depMap.get(a)?.length || 0;
      const bSize = depMap.get(b)?.length || 0;
      return bSize - aSize; // 依存数で降順
    });
  }
  
  /**
   * 最大パス長を計算
   * 
   * @param functions 関数リスト
   * @returns 最大パス長
   */
  private getMaxPathLength(functions: string[]): number {
    let maxLength = 0;
    
    for (const func of functions) {
      const funcTypeId = `${func}.Function`;
      const path = this.typeIdToPathMap.get(funcTypeId) || "";
      const displayPath = path ? `${path}:::${funcTypeId}` : `${func}:::${funcTypeId}`;
      
      if (displayPath.length > maxLength) {
        maxLength = displayPath.length;
      }
    }
    
    return maxLength + 2; // 余白を追加
  }

  /**
   * パスから型情報マッピングを構築する
   * 
   * @param paths 出力パスの配列
   * @param generatedDir 生成スキーマディレクトリ
   */
  private async buildTypeMapping(
    paths: string[], 
    generatedDir: string
  ): Promise<void> {
    // マップを初期化
    this.typeIdToPathMap.clear();
    this.pathToTypeIdMap.clear();
    
    if (this.verbose) {
      console.log(`型とパスのマッピング構築を開始します (パス数: ${paths.length}, 生成ディレクトリ: ${generatedDir})`);
    }
    
    // 各パスを処理
    for (const path of paths) {
      try {
        // パスから要件ファイル名を抽出
        const pathParts = path.split('/');
        // 最後のセグメントがファイル名
        const fileName = pathParts[pathParts.length - 1];
        // ファイル名から拡張子を取り除く
        const baseName = fileName.replace(/\.js$|\.ts$|\.json$|\..*$/, '');
        // ベース名から型名を取得
        const typeName = baseName;
        
        // フルパスを保存
        const fullPath = path;
        
        if (this.verbose) {
          console.log(`パス分析: ${path} -> 型名: ${typeName}`);
        }
        
        if (typeName) {
          // 主に Function メタスキーマの型を探す
          const metaSchemas = ['Function']; // 関数型のみに注目
          
          for (const schema of metaSchemas) {
            const schemaPath = `${generatedDir}/${typeName}.${schema}.schema.json`;
            try {
              // ファイルの存在確認
              await Deno.stat(schemaPath);
              
              // 型IDを作成
              const fullTypeId = `${typeName}.${schema}`;
              
              // この型のマッピングを記録
              this.typeIdToPathMap.set(fullTypeId, fullPath);
              
              // パスから型への逆マッピングを記録
              if (!this.pathToTypeIdMap.has(path)) {
                this.pathToTypeIdMap.set(path, fullTypeId);
              }
              
              if (this.verbose) {
                console.log(`型パスマッピング追加: ${path} -> ${fullTypeId}`);
              }
            } catch (e) {
              // ファイルが存在しない場合はスキップ
              if (this.verbose) {
                console.log(`スキーマファイルなし: ${schemaPath}`);
              }
            }
          }
        }
      } catch (e) {
        if (this.verbose) {
          console.error(`エラー: ${e.message}`);
        }
      }
    }
  }
}
