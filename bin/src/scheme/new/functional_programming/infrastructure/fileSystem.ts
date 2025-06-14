/**
 * fileSystem.ts
 * 
 * ファイルシステム操作のためのインターフェースと実装
 * クリーンアーキテクチャのインフラストラクチャ層に位置する
 */

/**
 * ファイル読み込みインターフェース
 */
export interface FileReader {
  /**
   * ファイルを非同期に読み込む
   * 
   * @param path ファイルパス
   * @returns ファイルの内容（テキスト）
   */
  readFile(path: string): Promise<string>;
  
  /**
   * JSONファイルを非同期に読み込む
   * 
   * @param path ファイルパス
   * @returns パースされたJSONオブジェクト
   */
  readJsonFile(path: string): Promise<unknown>;
  
  /**
   * ファイルの存在を確認
   * 
   * @param path ファイルパス
   * @returns ファイルが存在する場合はtrue、それ以外はfalse
   */
  exists(path: string): Promise<boolean>;
}

/**
 * Denoファイルシステム実装
 */
export class DenoFileSystem implements FileReader {
  /**
   * ファイルを非同期に読み込む
   * 
   * @param path ファイルパス
   * @returns ファイルの内容（テキスト）
   */
  async readFile(path: string): Promise<string> {
    return await Deno.readTextFile(path);
  }
  
  /**
   * JSONファイルを非同期に読み込む
   * 
   * @param path ファイルパス
   * @returns パースされたJSONオブジェクト
   */
  async readJsonFile(path: string): Promise<unknown> {
    const text = await this.readFile(path);
    return JSON.parse(text);
  }
  
  /**
   * ファイルの存在を確認
   * 
   * @param path ファイルパス
   * @returns ファイルが存在する場合はtrue、それ以外はfalse
   */
  async exists(path: string): Promise<boolean> {
    try {
      await Deno.stat(path);
      return true;
    } catch {
      return false;
    }
  }
}

/**
 * ファイルリーダーのデフォルトインスタンス
 */
export const fileReader: FileReader = new DenoFileSystem();

/**
 * ファイルを非同期に読み込む（関数版）
 * 
 * @param path ファイルパス
 * @returns ファイルの内容（テキスト）
 */
export async function readFile(path: string): Promise<string> {
  return fileReader.readFile(path);
}

/**
 * JSONファイルを非同期に読み込む（関数版）
 * 
 * @param path ファイルパス
 * @returns パースされたJSONオブジェクト
 */
export async function readJsonFile(path: string): Promise<unknown> {
  return fileReader.readJsonFile(path);
}

/**
 * ファイルの存在を確認（関数版）
 * 
 * @param path ファイルパス
 * @returns ファイルが存在する場合はtrue、それ以外はfalse
 */
export async function exists(path: string): Promise<boolean> {
  return fileReader.exists(path);
}

/**
 * ファイルシステム操作ユーティリティ
 * schemaFileRepositoryとの互換性のために必要な実装
 */
export const fileSystem = {
  /**
   * JSONファイルを書き込む
   * 
   * @param path ファイルパス
   * @param data 書き込むデータ
   * @param pretty 整形するかどうか
   */
  writeJsonFile: async (path: string, data: unknown, pretty: boolean = true): Promise<void> => {
    const text = pretty
      ? JSON.stringify(data, null, 2)
      : JSON.stringify(data);
    
    await Deno.writeTextFile(path, text);
  },
  
  /**
   * JSONファイルを読み込む
   * 
   * @param path ファイルパス
   * @returns パースされたJSONオブジェクト
   */
  readJsonFile: async <T>(path: string): Promise<T> => {
    const text = await Deno.readTextFile(path);
    return JSON.parse(text) as T;
  }
};
