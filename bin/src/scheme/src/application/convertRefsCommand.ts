import { Command } from "./command.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { FileSystemWriter } from "../infrastructure/fileSystemWriter.ts";
import { SchemaReferenceResolver } from "../domain/service/schemaReferenceResolver.ts";
import { DIRECTORIES } from "../infrastructure/variables.ts";

/**
 * スキーマの$ref参照を新形式に変換するコマンド
 */
export class ConvertRefsCommand implements Command {
  private fileReader: FileSystemReader;
  private fileWriter: FileSystemWriter;
  private schemaDir: string;

  /**
   * コンストラクタ
   * 
   * @param fileReader ファイル読み込みオブジェクト
   * @param fileWriter ファイル書き込みオブジェクト
   * @param schemaDir スキーマファイルが格納されているディレクトリパス
   */
  constructor(
    fileReader: FileSystemReader,
    fileWriter: FileSystemWriter,
    schemaDir: string = DIRECTORIES.GENERATED
  ) {
    this.fileReader = fileReader;
    this.fileWriter = fileWriter;
    this.schemaDir = schemaDir;
  }

  /**
   * コマンドの説明を取得
   */
  getDescription(): string {
    return "スキーマファイル内の$ref参照を旧形式から新形式に変換します";
  }

  /**
   * コマンドの使用方法を取得
   */
  getUsage(): string {
    return "convert-refs [--dir=<ディレクトリパス>] [<ファイルパス>]";
  }

  /**
   * コマンドを実行
   * 
   * @param args コマンド引数
   */
  async execute(args: any): Promise<void> {
    const cmdArgs = Array.isArray(args) ? args : args._ ? args._.slice(1) : [];
    const isDebug = Array.isArray(args) ? args.includes('--debug') : args.debug;
    
    // ディレクトリの指定
    const dirArg = Array.isArray(args) ? 
      cmdArgs.find(arg => arg.startsWith('--dir='))?.substring(6) : 
      args.dir;
    
    const targetDir = dirArg || this.schemaDir;
    
    if (isDebug) {
      console.log(`ConvertRefsCommand 実行 - 引数: ${JSON.stringify(args)}`);
      console.log(`対象ディレクトリ: ${targetDir}`);
    }
    
    // 特定のファイルが指定された場合
    const specificFile = cmdArgs.find(arg => !arg.startsWith('--'));
    
    try {
      if (specificFile) {
        // 特定のファイルを変換
        const filePath = specificFile.includes('/') ? specificFile : `${targetDir}/${specificFile}`;
        await this.convertFile(filePath);
      } else {
        // ディレクトリ内のすべてのファイルを変換
        await this.convertDirectory(targetDir);
      }
    } catch (error) {
      console.error(`エラー: ${error.message}`);
    }
  }

  /**
   * ディレクトリ内のすべてのスキーマファイルを変換する
   * 
   * @param dirPath スキーマファイルが格納されているディレクトリパス
   */
  private async convertDirectory(dirPath: string): Promise<void> {
    try {
      // ディレクトリ内のファイル一覧を取得
      const entries = [...Deno.readDirSync(dirPath)];
      
      // スキーマファイルだけをフィルタリング
      const schemaFiles = entries.filter(entry => 
        entry.isFile && entry.name.endsWith('.schema.json')
      );
      
      console.log(`${schemaFiles.length}件のスキーマファイルを処理します...`);
      
      // 各ファイルを変換
      let converted = 0;
      for (const fileEntry of schemaFiles) {
        const result = await this.convertFile(`${dirPath}/${fileEntry.name}`);
        if (result) {
          converted++;
        }
      }
      
      console.log(`変換完了: ${converted}件のファイルを変換しました`);
      
    } catch (error) {
      throw new Error(`ディレクトリの処理中にエラーが発生しました: ${error.message}`);
    }
  }

  /**
   * 単一のスキーマファイルを変換する
   * 
   * @param filePath スキーマファイルのパス
   * @returns 変換が行われたかどうか
   */
  private async convertFile(filePath: string): Promise<boolean> {
    try {
      console.log(`ファイルを処理中: ${filePath}`);
      
      // スキーマを読み込む
      const schema = await this.fileReader.readJsonFile(filePath);
      
      // $ref参照を変換
      const converted = await this.convertReferences(schema);
      
      // 変換があった場合のみ書き込む
      if (converted) {
        // 変換後のスキーマを書き込む
        await this.fileWriter.writeJsonFile(filePath, schema);
        console.log(`ファイルを更新しました: ${filePath}`);
        return true;
      } else {
        console.log(`変換不要: ${filePath}`);
        return false;
      }
      
    } catch (error) {
      throw new Error(`ファイル ${filePath} の処理中にエラーが発生しました: ${error.message}`);
    }
  }

  /**
   * オブジェクト内の$ref参照を再帰的に変換する
   * 
   * @param obj 変換対象のオブジェクト
   * @returns 変換が行われたかどうか
   */
  private async convertReferences(obj: any): Promise<boolean> {
    // nullまたは未定義の場合は処理しない
    if (obj === null || obj === undefined) {
      return false;
    }
    
    // オブジェクト型でない場合は処理しない
    if (typeof obj !== 'object') {
      return false;
    }
    
    let hasChanges = false;
    
    // 配列の場合は各要素を再帰的に処理
    if (Array.isArray(obj)) {
      for (const item of obj) {
        const itemChanged = await this.convertReferences(item);
        hasChanges = hasChanges || itemChanged;
      }
      return hasChanges;
    }
    
    const refResolver = new SchemaReferenceResolver(this.fileReader, this.schemaDir);
    
    // オブジェクト内の各プロパティを処理
    for (const [key, value] of Object.entries(obj)) {
      // $ref属性を検出した場合
      if (key === '$ref' && typeof value === 'string') {
        // 旧形式のファイルパス参照の場合のみ変換
        if (value.endsWith('.schema.json') && !value.startsWith('scheme://')) {
          const newRef = refResolver.convertFileRefToUri(value);
          if (newRef) {
            obj[key] = newRef;
            hasChanges = true;
            console.log(`変換: ${value} -> ${newRef}`);
          }
        }
      }
      // オブジェクト型の値は再帰的に変換
      else if (typeof value === 'object' && value !== null) {
        const nestedChanged = await this.convertReferences(value);
        hasChanges = hasChanges || nestedChanged;
      }
    }
    
    return hasChanges;
  }
}
