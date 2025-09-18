import { Command } from "./command.ts";
import { MetaSchemaRegistryService } from "./metaSchemaRegistryService.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";

/**
 * メタスキーマ登録コマンドハンドラー
 */
export class RegisterCommand implements Command {
  constructor(
    private registryService: MetaSchemaRegistryService,
    private fileReader: FileSystemReader
  ) {}
  
  /**
   * コマンドを実行する
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const metaSchemaPath = args._[1] as string;
    if (!metaSchemaPath) {
      throw new Error("メタスキーマファイルのパスが必要です");
    }
    
    // ファイル名の命名規則をチェック
    if (!metaSchemaPath.endsWith(".meta.json")) {
      throw new Error(`メタスキーマファイルは '.meta.json' で終わる必要があります: ${metaSchemaPath}`);
    }
    
    // メタスキーマの読み込み
    const metaSchema = await this.fileReader.readJsonFile(metaSchemaPath);
    const metaSchemaId = metaSchema.title;
    
    if (!metaSchemaId) {
      throw new Error("メタスキーマに 'title' プロパティがありません");
    }
    
    // メタスキーマの登録
    await this.registryService.registerMetaSchema({
      id: metaSchemaId,
      title: metaSchemaId,
      schema: metaSchema,
      type: metaSchema.type || "unknown"
    });
    
    console.log(`メタスキーマ '${metaSchemaId}' を登録しました`);
  }
}
