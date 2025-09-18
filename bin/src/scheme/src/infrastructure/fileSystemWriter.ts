/**
 * ファイルシステムへのファイル書き込みを行うクラス
 */
export class FileSystemWriter {
  /**
   * テキストをファイルに書き込む
   * 
   * @param path 書き込み先のファイルパス
   * @param content 書き込む内容
   * @throws 書き込みエラーが発生した場合
   */
  async writeTextFile(path: string, content: string): Promise<void> {
    try {
      await Deno.writeTextFile(path, content);
    } catch (error) {
      throw new Error(`ファイル '${path}' の書き込みに失敗しました: ${error.message}`);
    }
  }
  
  /**
   * JSONオブジェクトをファイルに書き込む
   * 
   * @param path 書き込み先のファイルパス
   * @param data 書き込むJSONオブジェクト
   * @param space インデントスペース数（デフォルト：2）
   * @throws 書き込みエラーが発生した場合
   */
  async writeJsonFile(path: string, data: any, space: number = 2): Promise<void> {
    try {
      const content = JSON.stringify(data, null, space);
      await this.writeTextFile(path, content);
    } catch (error) {
      throw new Error(`ファイル '${path}' の書き込みに失敗しました: ${error.message}`);
    }
  }
  
  /**
   * ディレクトリを作成する（既に存在する場合は何もしない）
   * 
   * @param path 作成するディレクトリのパス
   * @param recursive 親ディレクトリも作成するかどうか（デフォルト：true）
   * @throws ディレクトリ作成エラーが発生した場合
   */
  async ensureDir(path: string, recursive: boolean = true): Promise<void> {
    try {
      await Deno.mkdir(path, { recursive });
    } catch (error) {
      if (!(error instanceof Deno.errors.AlreadyExists)) {
        throw new Error(`ディレクトリ '${path}' の作成に失敗しました: ${error.message}`);
      }
    }
  }
}
