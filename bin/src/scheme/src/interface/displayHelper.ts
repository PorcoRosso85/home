/**
 * 表示関連のヘルパー関数
 */
export class DisplayHelper {
  /**
   * ヘルプメッセージを表示
   */
  showHelp(): void {
    console.log(`
メタスキーマ管理CLI - 使用方法:

  register <metaSchemaPath> - メタスキーマを登録
  generate <metaSchemaId> <configPath> <outputPath> - スキーマを生成
  validate <schemaPath> - スキーマを検証
  diagnose meta <metaSchemaPath> - メタスキーマを診断
  diagnose config <configPath> <metaSchemaId> [<metaSchemaPath>] - 設定ファイルを診断
  list - 登録済みのメタスキーマ一覧を表示
  deps <型名.メタスキーマ> - 型の依存関係を再帰的に表示
  req-deps <サブコマンド> - 要件間の依存関係を解析
  req-to-function <要件ID> - 要件から関数定義JSONを生成

オプション:
  --help, -h     このヘルプを表示
  --verbose, -v  詳細な出力を表示

例:
  deno run --allow-read --allow-write cli.ts register ./data/meta/String.meta.json
  deno run --allow-read --allow-write cli.ts generate StringTypeMetaSchema ./data/config/UserId.String.config.json ./data/generated/UserId.String.schema.json
  deno run --allow-read --allow-write cli.ts validate ./data/generated/UserId.String.schema.json
  deno run --allow-read --allow-write cli.ts diagnose meta ./data/meta/String.meta.json
  deno run --allow-read --allow-write cli.ts diagnose config ./data/config/UserId.String.config.json StringTypeMetaSchema
  deno run --allow-read --allow-write cli.ts list
  deno run --allow-read --allow-write cli.ts deps User.Struct
  deno run --allow-read --allow-write cli.ts req-deps deps UserAuthentication
  deno run --allow-read --allow-write cli.ts req-to-function UserAuthentication
  `);
  }
  
  /**
   * エラーメッセージを表示
   * 
   * @param message エラーメッセージ
   */
  displayError(message: string): void {
    console.error(`エラー: ${message}`);
  }
  
  /**
   * バナーを表示
   * 
   * @param title バナータイトル
   */
  showBanner(title: string): void {
    console.log("");
    console.log("========================================================");
    console.log(`   ${title}`);
    console.log("========================================================");
    console.log("");
  }
}
