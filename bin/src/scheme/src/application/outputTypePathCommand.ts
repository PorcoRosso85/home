import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { loadPathsFromDirectory, buildDirectoryTree, extractDependencyPaths } from "../utils/pathExtractor.ts";
import { getDependencies } from "../domain/service/typeDependencyAnalyzer.ts";
import { SchemaReferenceResolver } from "../domain/service/schemaReferenceResolver.ts";

/**
 * 要件ファイルから型のパスを抽出して表示するコマンド
 * シンプルな形式（path/to/file.xxx:::TypeName.Schema）で出力する
 */
export class OutputTypePathCommand implements Command {
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
   * @param generatedDir 生成されたスキーマが格納されているディレクトリパス
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
    return "要件ファイルから型とそのパスを抽出して表示します（path/to/file.xxx:::TypeName.Schema形式）";
  }

  /**
   * コマンドの使用方法を取得
   */
  getUsage(): string {
    return "output-type-path [--dir=<要件ディレクトリパス>] [--generated-dir=<生成済みスキーマディレクトリパス>]";
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const dir = args.dir || this.requirementsDir;
    const verbose = args.verbose || false;
    this.verbose = verbose; // verboseフラグをクラス変数に保存
    const generatedDir = args.generatedDir || this.generatedDir;
    
    if (verbose) {
      console.log(`実行パラメータ:
- ディレクトリ: ${dir}
- 詳細モード: ${verbose}
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
      
      // 型の情報を構築
      await this.buildTypeMapping(paths, generatedDir);
      
      // 結果を出力 (path/to/file.xxx:::TypeName.Schema形式)
      const results = this.getTypePathPairs();
      
      for (const result of results) {
        console.log(result);
      }
      
      if (verbose) {
        console.log(`\n合計: ${results.length}個の型とパスの組み合わせが見つかりました`);
      }
    } catch (error) {
      console.error(`エラー: ${error.message}`);
    }
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
        
        if (this.verbose) {
          console.log(`パス分析: ${path} -> 型名: ${typeName}`);
        }
        
        if (typeName) {
          // ボリュームデータから実際の型情報を取得
          // 生成ディレクトリには、User.Struct.schema.json のように存在
          // スキーマファイルの候補を探す
          
          // StructとFunctionメタスキーマの候補を確認
          const metaSchemas = ['Struct', 'Function', 'String'];
          
          for (const schema of metaSchemas) {
            const schemaPath = `${generatedDir}/${typeName}.${schema}.schema.json`;
            try {
              // ファイルの存在確認
              await Deno.stat(schemaPath);
              
              // 型IDを作成
              const fullTypeId = `${typeName}.${schema}`;
              
              // この型のマッピングを記録
              this.typeIdToPathMap.set(fullTypeId, path);
              
              // パスから型への逆マッピングを記録（複数の型が同じパスを持つ可能性あり）
              if (!this.pathToTypeIdMap.has(path)) {
                // 配列形式で保存（複数型対応）
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

  /**
   * 型とパスのペアをpath/to/file.xxx:::TypeName.Schema形式で取得
   * 
   * @returns 型とパスのペアの配列
   */
  private getTypePathPairs(): string[] {
    const results: string[] = [];
    
    // 型からパスへのマッピングを使用
    for (const [typeId, path] of this.typeIdToPathMap.entries()) {
      results.push(`${path}:::${typeId}`);
    }
    
    return results;
  }
  
  // メンバー変数として追加
  private verbose = false;
}
