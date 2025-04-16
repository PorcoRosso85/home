#!/usr/bin/env /home/nixos/.nix-profile/bin/node
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { FileSystemWriter } from "../infrastructure/fileSystemWriter.ts";
import { SchemaReferenceResolver, SchemaSourceType } from "../domain/service/schemaReferenceResolver.ts";

/**
 * スキーマの$ref参照を旧形式から新形式に変換するツール
 */
class SchemaRefConverter {
  private fileReader: FileSystemReader;
  private fileWriter: FileSystemWriter;
  private schemaDir: string;
  private refResolver: SchemaReferenceResolver;

  /**
   * コンストラクタ
   * 
   * @param schemaDir スキーマファイルが格納されているディレクトリパス
   */
  constructor(schemaDir: string = "./data/generated") {
    this.fileReader = new FileSystemReader();
    this.fileWriter = new FileSystemWriter();
    this.schemaDir = schemaDir;
    this.refResolver = new SchemaReferenceResolver(this.fileReader, schemaDir);
  }

  /**
   * ディレクトリ内のすべてのスキーマファイルを変換する
   */
  public async convertDirectory(): Promise<void> {
    try {
      // ディレクトリ内のファイル一覧を取得
      const entries = [...Deno.readDirSync(this.schemaDir)];
      
      // スキーマファイルだけをフィルタリング
      const schemaFiles = entries.filter(entry => 
        entry.isFile && entry.name.endsWith('.schema.json')
      );
      
      console.log(`${schemaFiles.length}件のスキーマファイルを処理します...`);
      
      // 各ファイルを変換
      let converted = 0;
      for (const fileEntry of schemaFiles) {
        const result = await this.convertFile(`${this.schemaDir}/${fileEntry.name}`);
        if (result) {
          converted++;
        }
      }
      
      console.log(`変換完了: ${converted}件のファイルを変換しました`);
      
    } catch (error) {
      console.error(`エラー: ディレクトリの処理中にエラーが発生しました: ${error.message}`);
    }
  }

  /**
   * 単一のスキーマファイルを変換する
   * 
   * @param filePath スキーマファイルのパス
   * @returns 変換が行われたかどうか
   */
  public async convertFile(filePath: string): Promise<boolean> {
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
      console.error(`エラー: ファイル ${filePath} の処理中にエラーが発生しました: ${error.message}`);
      return false;
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
    
    // オブジェクト内の各プロパティを処理
    for (const [key, value] of Object.entries(obj)) {
      // $ref属性を検出した場合
      if (key === '$ref' && typeof value === 'string') {
        // 旧形式のファイルパス参照の場合のみ変換
        if (value.endsWith('.schema.json') && !value.startsWith('scheme://')) {
          const newRef = this.refResolver.convertFileRefToUri(value);
          if (newRef) {
            obj[key] = newRef;
            hasChanges = true;
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

// スクリプトとして実行された場合
if (import.meta.main) {
  const schemaDir = Deno.args[0] || "./data/generated";
  const converter = new SchemaRefConverter(schemaDir);
  
  if (Deno.args.length > 1 && Deno.args[1] !== '--all') {
    // 特定のファイルを変換
    await converter.convertFile(Deno.args[1]);
  } else {
    // ディレクトリ内のすべてのファイルを変換
    await converter.convertDirectory();
  }
}

export { SchemaRefConverter };
