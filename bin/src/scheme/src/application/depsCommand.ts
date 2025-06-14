import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { getDependencies, dependencyToString } from "../domain/service/typeDependencyAnalyzer.ts";

/**
 * 型の依存関係を表示するコマンド
 */
export class DepsCommand implements Command {
  private fileReader: FileSystemReader;
  private generatedDir: string;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイル読み込みオブジェクト
   * @param generatedDir 生成されたスキーマファイルが格納されているディレクトリパス
   */
  constructor(fileReader: FileSystemReader, generatedDir: string = "./data/generated") {
    this.fileReader = fileReader;
    this.generatedDir = generatedDir;
  }

  /**
   * コマンドの説明を取得
   */
  getDescription(): string {
    return "指定された型の依存関係を表示します";
  }

  /**
   * コマンドの使用方法を取得
   */
  getUsage(): string {
    return "deps <型名.メタスキーマ>";
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンド引数
   */
  async execute(args: any): Promise<void> {
    // argsが単純な引数の配列の場合と、オブジェクトとして处理された場合の両方に対応
    const cmdArgs = Array.isArray(args) ? args : args._ ? args._.slice(1) : [];
    const isDebug = Array.isArray(args) ? args.includes('--debug') : args.debug;
    
    if (isDebug) {
      console.log(`DepsCommand 実行 - 引数: ${JSON.stringify(args)}`);
      console.log(`コマンド引数: ${JSON.stringify(cmdArgs)}`);
      console.log(`生成スキーマディレクトリ: ${this.generatedDir}`);
    }
    
    if (cmdArgs.length < 1 || (!cmdArgs[0].includes('.') && !cmdArgs[1])) {
      console.error("エラー: 型名の指定が必要です");
      console.log(`使用法: ${this.getUsage()}`);
      console.log("例: deps User.Struct");
      return;
    }

    // 型名とメタスキーマの取得
    let typeName, metaSchema;
    
    // depsの引数として、1つ目の引数が実際の型名なので、それをパース
    const typeArg = cmdArgs[0];
    if (typeArg.includes('.')) {
      [typeName, metaSchema] = typeArg.split('.');
    } else {
      typeName = cmdArgs[0];
      metaSchema = cmdArgs[1];
      if (!metaSchema) {
        console.error('エラー: メタスキーマも指定する必要があります');
        console.log('例: deps User Struct または deps User.Struct');
        return;
      }
    }

    if (isDebug) {
      console.log(`型名: ${typeName}, メタスキーマ: ${metaSchema}`);
    }

    try {
      // ファイルパスの確認
      const schemaPath = `${this.generatedDir}/${typeName}.${metaSchema}.schema.json`;
      if (isDebug) {
        console.log(`スキーマファイルを確認: ${schemaPath}`);
      }
      
      // スキーマファイルが存在するか確認
      try {
        await Deno.stat(schemaPath);
      } catch (e) {
        console.error(`エラー: スキーマファイル '${schemaPath}' が見つかりません`);
        console.log(`生成済みのスキーマがあるか確認してください`);
        return;
      }
      
      // 型の依存関係を取得
      const dependencies = await getDependencies(typeName, metaSchema, this.fileReader, this.generatedDir);
      
      // 結果を表示
      console.log(`${typeName}.${metaSchema} の依存関係:\n`);
      console.log(dependencyToString(dependencies));
      
      // 依存している型の総数を表示
      const totalDeps = countTotalDependencies(dependencies) - 1; // 自身をカウントから除外
      console.log(`\n合計: ${totalDeps}個の型に依存しています`);
    } catch (error) {
      console.error(`エラー: ${error.message}`);
    }
  }
}

/**
 * 総依存型数をカウント
 * 
 * @param dependency 型依存関係
 * @param counted カウント済みの型（重複を避けるため）
 * @returns 依存型の総数
 */
function countTotalDependencies(
  dependency: { name: string; metaSchema: string; dependencies: any[] },
  counted: Set<string> = new Set<string>()
): number {
  // 型の識別子
  const typeId = `${dependency.name}.${dependency.metaSchema}`;
  
  // 既にカウント済みならスキップ
  if (counted.has(typeId)) {
    return 0;
  }
  
  // この型をカウント済みに追加
  counted.add(typeId);
  
  // 自身を1としてカウント
  let count = 1;
  
  // 依存先をすべて再帰的にカウント
  for (const dep of dependency.dependencies) {
    count += countTotalDependencies(dep, counted);
  }
  
  return count;
}
