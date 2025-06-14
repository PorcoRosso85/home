import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { loadPathsFromDirectory, buildDirectoryTree, extractDependencyPaths } from "../utils/pathExtractor.ts";
import { join } from "https://deno.land/std@0.178.0/path/mod.ts";
import { getDependencies } from "../domain/service/typeDependencyAnalyzer.ts";
import { SchemaReferenceResolver } from "../domain/service/schemaReferenceResolver.ts";
import { DISPLAY_CONFIG } from "../infrastructure/variables.ts";

/**
 * 要件ファイルからoutputPathを抽出して表示するコマンド
 */
export class OutputPathsCommand implements Command {
  private fileReader: FileSystemReader;
  private requirementsDir: string;
  private generatedDir: string;
  private typeIdToPathMap: Map<string, string> = new Map<string, string>();
  private pathToTypeIdMap: Map<string, string> = new Map<string, string>();

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイルシステムリーダー
   * @param requirementsDir 要件ファイルが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, requirementsDir: string, generatedDir: string = "./data/generated") {
    this.fileReader = fileReader;
    this.requirementsDir = requirementsDir;
    this.generatedDir = generatedDir;
  }

  /**
   * コマンドの説明を取得
   */
  getDescription(): string {
    return "要件ファイルからoutputPathを抽出して表示します";
  }

  /**
   * コマンドの使用方法を取得
   */
  getUsage(): string {
    return "output-paths [--format=<text|json|mermaid>] [--dir=<要件ディレクトリパス>] [--show-deps] [--generated-dir=<生成済みスキーマディレクトリパス>]";
  }

  /**
   * 型のIDと出力パスの関係を結びつける
   * 
   * @param typeId 型のID(例: User.Struct)
   * @param paths すべての出力パス
   * @returns 対応する出力パス（見つからない場合はnull）
   */
  private findPathForTypeId(typeId: string, paths: string[]): string | null {
    // 単純なパスマッチングを試行
    const [typeName, schema] = typeId.split('.');
    
    // パスを探す
    for (const path of paths) {
      // パスの最後の部分から型名を抽出
      const pathParts = path.split('/');
      const fileName = pathParts[pathParts.length - 1];
      const baseName = fileName.replace(/\.js$|\.ts$|\.json$|\..*$/, '');
      
      if (baseName.toLowerCase() === typeName.toLowerCase()) {
        return path;
      }
    }
    
    return null;
  }

  /**
   * 依存関係を再帰的に表示する
   * 
   * @param path パス
   * @param deps 依存関係情報
   * @param dependencyMap 依存関係マップ
   * @param visited 訪問済みノードセット（循環検出用）
   * @param depth 再帰の深さ（インデント用）
   * @param paths すべての出力パス
   */
  private displayDependencyTree(
    path: string,
    deps: { depender: string[], dependee: string[] },
    dependencyMap: Map<string, { depender: string[], dependee: string[] }>,
    visited: Set<string>,
    depth: number = 0,
    paths: string[] = []
  ): void {
    // 循環参照を防止
    if (visited.has(path)) {
      return;
    }
    visited.add(path);
    
    // 重複表示防止のためのセット
    const displayedDeps = new Set<string>();
    
    if (depth === 0) {
      // 最初のパスでは依存先を表示
      if (deps.dependee.length > 0) {
        for (const dependee of deps.dependee) {
          if (displayedDeps.has(dependee)) continue;
          displayedDeps.add(dependee);
          
          // パスの右側に依存関係を表示
          const indent = ' '.repeat(DISPLAY_CONFIG.DEPENDENCY_INDENT_WIDTH);
          console.log(`${path}${' '.repeat(Math.max(1, 40 - path.length))}${DISPLAY_CONFIG.DEPENDENCY_SEPARATOR}${indent}<${dependee}>`);
          
          // 依存先の型が定義されているパスを探す
          const findPath = this.findPathForTypeId(dependee, paths);
          const depPath = findPath || this.typeIdToPathMap.get(dependee);
          
          if (depPath) {
            const depInfo = dependencyMap.get(depPath);
            if (depInfo) {
              // 再帰的に依存先の依存関係を表示
              this.displayDependencyTree(depPath, depInfo, dependencyMap, new Set(visited), depth + 1, paths);
            }
          }
        }
      }
    } else {
      // 2階層目以降の依存関係表示
      if (deps.dependee.length > 0) {
        // インデントを深さに応じて設定
        const indent = ' '.repeat(DISPLAY_CONFIG.DEPENDENCY_INDENT_WIDTH * (depth + 1));
        const padding = ' '.repeat(40 + 2); // パス長 + セパレータ長
        
        for (const dependee of deps.dependee) {
          if (displayedDeps.has(dependee)) continue;
          displayedDeps.add(dependee);
          
          // インデントされた依存関係表示
          console.log(`${padding}${indent}<${dependee}>`);
          
          // 依存先の型が定義されているパスを探す
          const findPath = this.findPathForTypeId(dependee, paths);
          const depPath = findPath || this.typeIdToPathMap.get(dependee);
          
          if (depPath) {
            const depInfo = dependencyMap.get(depPath);
            if (depInfo) {
              // 再帰的に依存先の依存関係を表示
              this.displayDependencyTree(depPath, depInfo, dependencyMap, new Set(visited), depth + 1, paths);
            }
          }
        }
      }
    }
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const format = args.format || "text";
    const dir = args.dir || this.requirementsDir;
    const verbose = args.verbose || false;
    this.verbose = verbose; // verboseフラグをクラス変数に保存
    // showDepsオプションの処理 (--show-depsまたは-dから取得)
    // デフォルトは非表示（false）
    const showDeps = args["show-deps"] === true ? true : false;
    const generatedDir = args.generatedDir || this.generatedDir;
    
    if (verbose) {
    console.log(`実行パラメータ:
- 出力形式: ${format}
- ディレクトリ: ${dir}
- 詳細モード: ${verbose}
- 依存関係表示: ${showDeps}
- 生成スキーマディレクトリ: ${generatedDir}
`);
      }
    
    try {
      // ファイル情報を読み込む
      const files = await loadPathsFromDirectory(dir);
      
      if (files.length === 0) {
        console.log(`指定されたディレクトリ (${dir}) にJSONファイルが見つかりません`);
        return;
      }
      
      if (verbose) {
        console.log(`${files.length}個のJSONファイルを読み込みました`);
      }
      
      // ディレクトリツリーを構築
      const tree = buildDirectoryTree(files);
      
      // パスを抽出
      const paths = extractDependencyPaths(tree);
      
      // 依存関係の取得（必要な場合）
      let dependencyMap = new Map<string, { depender: string[], dependee: string[] }>();
      
      if (showDeps) {
        // 依存関係の情報を構築する
        dependencyMap = await this.buildDependencyMap(paths, generatedDir);
        
        if (verbose) {
          console.log(`依存関係情報を構築しました（${dependencyMap.size}個のエントリ）`);
        }
      }

      // 結果を出力
      switch (format.toLowerCase()) {
        case "json":
          console.log(JSON.stringify(paths, null, 2));
          break;
        
        case "mermaid":
          console.log("```mermaid");
          console.log("graph TD;");
          
          // パスからノードを生成
          const nodes = new Set<string>();
          
          for (const path of paths) {
            // パスを分解
            const parts = path.split('/').filter(p => p);
            
            if (parts.length === 0) continue;
            
            // 各階層のノードを追加
            let currentPath = "";
            
            for (let i = 0; i < parts.length; i++) {
              const part = parts[i];
              const prevPath = currentPath;
              
              // パスを更新
              currentPath = currentPath ? `${currentPath}/${part}` : `/${part}`;
              
              // ノードIDを作成（スラッシュを除去）
              const nodeId = currentPath.replace(/\//g, '_').replace(/\./g, '_');
              const prevNodeId = prevPath.replace(/\//g, '_').replace(/\./g, '_');
              
              // ノードを追加
              if (!nodes.has(nodeId)) {
                nodes.add(nodeId);
                
                // 最後の部分の場合はファイルとして、それ以外はディレクトリとして表示
                if (i === parts.length - 1) {
                  console.log(`  ${nodeId}["📄 ${part}"];`);
                } else {
                  console.log(`  ${nodeId}["📁 ${part}"];`);
                }
              }
              
              // エッジを追加（最初のノード以外）
              if (prevPath && !prevPath.startsWith(currentPath)) {
                console.log(`  ${prevNodeId} --> ${nodeId};`);
              }
            }
          }
          
          console.log("```");
          break;
        
        case "text":
        default:
          if (paths.length === 0) {
            console.log("出力パスが見つかりませんでした");
          } else {
            console.log("出力パス一覧:");
            if (showDeps) {
              for (const path of paths) {
                const deps = dependencyMap.get(path) || { depender: [], dependee: [] };
                console.log(path);
                
                // 依存関係のデバッグ出力
                if (verbose) {
                  console.log(`\tデバッグ: path=${path}, 依存数=${deps.depender.length + deps.dependee.length}`);
                }
                
                // 依存関係を再帰的に表示
                this.displayDependencyTree(path, deps, dependencyMap, new Set<string>(), 0, paths);
              }
            } else {
              for (const path of paths) {
                console.log(path);
              }
            }
            console.log(`\n合計: ${paths.length}個のパスが見つかりました`);
          }
          break;
      }
    } catch (error) {
      console.error(`エラー: ${error.message}`);
    }
  }

  /**
   * パスから依存関係マップを構築する
   * 
   * @param paths 出力パスの配列
   * @param generatedDir 生成スキーマディレクトリ
   * @returns 依存関係マップ
   */
  private async buildDependencyMap(
    paths: string[], 
    generatedDir: string
  ): Promise<Map<string, { depender: string[], dependee: string[] }>> {
    const result = new Map<string, { depender: string[], dependee: string[] }>();
    const schemaReferenceResolver = new SchemaReferenceResolver(this.fileReader, generatedDir);
    
    // マップを初期化
    this.typeIdToPathMap.clear();
    this.pathToTypeIdMap.clear();
    
    if (this.verbose) {
      console.log(`依存関係マップの構築を開始します (パス数: ${paths.length}, 生成ディレクトリ: ${generatedDir})`);
    }
    
    // 各パスを処理
    for (const path of paths) {
      // 基本構造を初期化
      if (!result.has(path)) {
        result.set(path, { depender: [], dependee: [] });
      }
      
      try {
        // パスから要件ファイル名を検討
        const pathParts = path.split('/');
        // 最後のセグメントがファイル名
        const fileName = pathParts[pathParts.length - 1];
        // ファイル名から拡張子を取り除く
        const baseName = fileName.replace(/\.js$|\.ts$|\.json$|\..*$/, '');
        // ベース名から型名を取得
        const typeName = baseName;
        
        if (this.verbose) {
          console.log(`パス分析: ${path} -> 型名: ${typeName}`);
        }
        
        if (typeName) {
          // ボリュームデータから実際の型情報を取得
          // 生成ディレクトリには、User.Struct.schema.json のように存在
          // スキーマファイルの候補を探す
          const possibleSchemaFiles = [];
          
          // StructとFunctionメタスキーマの候補を確認
          const metaSchemas = ['Struct', 'Function'];
          
          for (const schema of metaSchemas) {
            const schemaPath = `${generatedDir}/${typeName}.${schema}.schema.json`;
            try {
              // ファイルの存在確認
              await Deno.stat(schemaPath);
              possibleSchemaFiles.push({
                path: schemaPath,
                typeName,
                metaSchema: schema
              });
              if (this.verbose) {
                console.log(`抽出された型定義: ${typeName}.${schema}`);
              }
            } catch (e) {
              // ファイルが存在しない場合はスキップ
            }
          }
          
          // 候補が見つかった場合、依存関係を取得
          for (const schemaFile of possibleSchemaFiles) {
            
            // 依存関係を取得
            const dependencies = await getDependencies(
              schemaFile.typeName, 
              schemaFile.metaSchema, 
              this.fileReader, 
              generatedDir
            );
            
            // 依存関係をマップに追加
            if (dependencies) {
              // 型IDを作成
              const fullTypeId = `${schemaFile.typeName}.${schemaFile.metaSchema}`;
              
              // この型のマッピングを記録
              this.typeIdToPathMap.set(fullTypeId, path);
              this.pathToTypeIdMap.set(path, fullTypeId);
              
              // この型が依存している型（Dependee）
              for (const dep of dependencies.dependencies) {
                const depId = `${dep.name}.${dep.metaSchema}`;
                const depPath = `${dep.path}`;
                
                // 依存先の型の情報も記録
                this.typeIdToPathMap.set(depId, depPath);
                
                // 依存関係情報を出力
                if (this.verbose) {
                  console.log(`依存関係発見: ${fullTypeId} -> ${depId}`);
                }
                
                // この型のDependeeリストに追加
                if (!result.get(path)?.dependee.includes(depId)) {
                  result.get(path)?.dependee.push(depId);
                }
                
                // 依存先の型のDependerリストに追加
                if (!result.has(depPath)) {
                  result.set(depPath, { depender: [], dependee: [] });
                }
                
                if (!result.get(depPath)?.depender.includes(fullTypeId)) {
                  result.get(depPath)?.depender.push(fullTypeId);
                }
              }
            }
          }
        }
      } catch (e) {
        // エラーが発生した場合は依存関係情報をスキップ
        if (this.verbose) {
          console.error(`エラー: ${e.message}`);
        }
      }
    }
    
    return result;
  }
  
  // メンバー変数として追加
  private verbose = false;
}
