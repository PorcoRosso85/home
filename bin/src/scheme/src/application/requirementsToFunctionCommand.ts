import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { FileSystemWriter } from "../infrastructure/fileSystemWriter.ts";
import { parse } from "https://deno.land/std@0.220.1/flags/mod.ts";
import { join } from "https://deno.land/std@0.220.1/path/mod.ts";

/**
 * 要件定義JSONから関数定義JSONを生成するコマンド
 */
export class RequirementsToFunctionCommand implements Command {
  private fileReader: FileSystemReader;
  private fileWriter: FileSystemWriter;
  private requirementsDir: string;
  private outputDir: string; // configDirから変更
  private metaDir: string;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイルシステムリーダー
   * @param fileWriter ファイルシステムライター
   * @param requirementsDir 要件ディレクトリパス
   * @param outputDir 出力ディレクトリパス
   * @param metaDir メタスキーマディレクトリパス
   */
  constructor(
    fileReader: FileSystemReader,
    fileWriter: FileSystemWriter,
    requirementsDir: string,
    outputDir: string,
    metaDir: string
  ) {
    this.fileReader = fileReader;
    this.fileWriter = fileWriter;
    this.requirementsDir = requirementsDir;
    this.outputDir = outputDir;
    this.metaDir = metaDir;
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const requirementId = args._[1] as string;
    
    if (!requirementId) {
      console.log(`
要件定義JSONから関数定義JSONを生成します

使用方法:
  convert-to-function <要件ID> [オプション]

オプション:
  --force             既存の出力ファイルを上書き
  --dryRun            実際に出力せずに内容を表示
      `);
      return;
    }

    const force = args.force || false;
    const dryRun = args.dryRun || false;

    try {
      // メタスキーマの読み込み
      const functionMetaSchema = await this.loadFunctionMetaSchema();
      
      // 要件ファイルの読み込み
      const requirementFilePath = join(this.requirementsDir, `${requirementId}.require.json`);
      let requirement;
      
      try {
        const content = await Deno.readTextFile(requirementFilePath);
        requirement = JSON.parse(content);
      } catch (error) {
        throw new Error(`要件ファイル ${requirementFilePath} の読み込みに失敗しました: ${error.message}`);
      }
      
      // 指定された要件が関数型でない場合はエラー
      if (requirement.implementationType !== "function") {
        throw new Error(`要件 ${requirementId} は関数型ではありません (${requirement.implementationType})`);
      }
      
      // 関数定義JSONへ変換
      const functionJson = this.convertRequirementToFunction(requirement, functionMetaSchema);
      
      // 出力ファイルパスの生成
      const outputFilePath = join(this.outputDir, `${requirementId}.Function.schema.json`);
      
      // 既存ファイルの存在チェック
      try {
        await Deno.stat(outputFilePath);
        if (!force) {
          throw new Error(`出力ファイル ${outputFilePath} は既に存在します。上書きするには --force オプションを使用してください`);
        }
      } catch (error) {
        // ファイルが存在しない場合は問題なし
        if (!(error instanceof Deno.errors.NotFound)) {
          throw error;
        }
      }
      
      // 結果の出力
      const jsonString = JSON.stringify(functionJson, null, 2);
      
      if (dryRun) {
        console.log("生成される関数定義JSON:");
        console.log(jsonString);
      } else {
        await Deno.writeTextFile(outputFilePath, jsonString);
        console.log(`関数定義JSONを ${outputFilePath} に出力しました`);
        console.log(`注: 出力先ディレクトリが存在しない場合は自動生成します`);
        
        // 出力先ディレクトリが存在しない場合は作成
        try {
          await Deno.mkdir(this.outputDir, { recursive: true });
        } catch (error) {
          // ディレクトリが既に存在する場合は無視
          if (!(error instanceof Deno.errors.AlreadyExists)) {
            throw new Error(`出力先ディレクトリの作成に失敗しました: ${error.message}`);
          }
        }
      }
    } catch (error) {
      throw new Error(`処理中にエラーが発生しました: ${error.message}`);
    }
  }

  /**
   * 関数メタスキーマを読み込む
   * 
   * @returns 関数メタスキーマオブジェクト
   */
  private async loadFunctionMetaSchema(): Promise<any> {
    const metaSchemaPath = join(this.metaDir, "Function.meta.json");
    try {
      const content = await Deno.readTextFile(metaSchemaPath);
      return JSON.parse(content);
    } catch (error) {
      throw new Error(`関数メタスキーマ ${metaSchemaPath} の読み込みに失敗しました: ${error.message}`);
    }
  }

  /**
   * 要件定義から関数定義JSONを生成
   * 
   * @param requirement 要件定義オブジェクト
   * @param metaSchema 関数メタスキーマオブジェクト
   * @returns 関数定義JSONオブジェクト
   */
  private convertRequirementToFunction(requirement: any, metaSchema: any): any {
    // 基本構造の作成
    const functionJson: any = {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "$metaSchema": "Function",
      "title": requirement.title,
      "description": requirement.description,
      "type": "function"
    };
    
    // implementation.functionから関数情報をコピー
    if (requirement.implementation && requirement.implementation.function) {
      const functionInfo = requirement.implementation.function;
      
      // パラメータ情報
      if (functionInfo.parameters) {
        functionJson.parameters = functionInfo.parameters;
      }
      
      // 戻り値情報
      if (functionInfo.returnType) {
        functionJson.returnType = functionInfo.returnType;
      }
      
      // 非同期フラグ
      if (functionInfo.async !== undefined) {
        functionJson.async = functionInfo.async;
      }

      // 例外情報
      if (functionInfo.exceptions) {
        functionJson.exceptions = functionInfo.exceptions;
      }

      // 副作用フラグ
      if (functionInfo.sideEffects !== undefined) {
        functionJson.sideEffects = functionInfo.sideEffects;
      }
    }
    
    // タグ情報
    if (requirement.tags && Array.isArray(requirement.tags)) {
      functionJson.tags = requirement.tags;
    }
    
    // その他のメタデータを追加
    if (functionJson.sideEffects === undefined) {
      functionJson.sideEffects = true;  // デフォルトでは副作用ありとする
    }
    
    functionJson.deprecated = requirement.deprecated || false;  // デフォルトでは非推奨でない
    
    // 例がある場合は例も含める
    if (requirement.examples && Array.isArray(requirement.examples)) {
      functionJson.examples = requirement.examples;
    }
    
    return functionJson;
  }
}
