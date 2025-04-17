/**
 * コマンドインターフェース
 * 全てのコマンドハンドラーの基本インターフェース
 */
export interface Command {
  /**
   * コマンドを実行する
   * 
   * @param args コマンドライン引数
   * @returns 処理結果
   */
  execute(args: any): Promise<void>;
}
