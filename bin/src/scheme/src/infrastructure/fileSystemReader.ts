/**
 * ファイルシステムからのファイル読み込みを行うクラス
 */
export class FileSystemReader {
  /**
   * ファイルをテキストとして読み込む
   * 
   * @param path ファイルパス
   * @returns ファイルの内容を表すPromise
   * @throws ファイルが存在しない場合や読み込みエラーが発生した場合
   */
  async readTextFile(path: string): Promise<string> {
    try {
      return await Deno.readTextFile(path);
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        throw new Error(`ファイル '${path}' が見つかりません`);
      } else if (error.message.includes('JSON')) {
        throw new Error(`ファイル '${path}' は有効なJSONではありません`);
      } else {
        throw error;
      }
    }
  }
  
  /**
   * ファイルをJSONとして読み込んでパースする
   * 
   * @param path JSONファイルのパス
   * @returns パースされたJSONオブジェクトを表すPromise
   * @throws ファイルが存在しない場合やJSON解析エラーが発生した場合
   */
  async readJsonFile(path: string): Promise<any> {
    try {
      const text = await this.readTextFile(path);
      try {
        return JSON.parse(text);
      } catch (error) {
        throw new Error(`ファイル '${path}' の解析に失敗しました: JSONフォーマットが不正です`);
      }
    } catch (error) {
      if (error instanceof Deno.errors.NotFound) {
        throw new Error(`ファイル '${path}' が見つかりません`);
      }
      throw error;
    }
  }
  
  /**
   * ディレクトリ内のJSONファイルを探す
   * 
   * @param dirPath ディレクトリパス
   * @param predicate 各ファイルに適用するフィルタ関数
   * @returns ファイルパス配列を表すPromise
   */
  async findJsonFiles(dirPath: string, predicate?: (entry: Deno.DirEntry) => boolean): Promise<string[]> {
    const fileEntries: Deno.DirEntry[] = [];
    try {
      for await (const entry of Deno.readDir(dirPath)) {
        if (entry.isFile && entry.name.endsWith(".json")) {
          if (!predicate || predicate(entry)) {
            fileEntries.push(entry);
          }
        }
      }
    } catch (e) {
      console.error(`ディレクトリ読み込みエラー: ${e.message}`);
      return [];
    }
    
    return fileEntries.map(entry => `${dirPath}/${entry.name}`);
  }
}
