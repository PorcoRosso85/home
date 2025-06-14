import { Command } from "./command.ts";
import { MetaSchemaRegistryService } from "./metaSchemaRegistryService.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";

/**
 * スキーマ検証コマンドハンドラー
 */
export class ValidateCommand implements Command {
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
    const schemaPath = args._[1] as string;
    
    if (!schemaPath) {
      throw new Error("検証するスキーマファイルのパスが必要です");
    }
    
    // スキーマの読み込み
    const schema = await this.fileReader.readJsonFile(schemaPath);
    
    // スキーマの検証
    const result = await this.registryService.validateSchema(schema);
    
    if (result.valid) {
      console.log(`スキーマ '${schemaPath}' は有効です`);
    } else {
      console.error(`スキーマ '${schemaPath}' は無効です:`);
      result.errors.forEach(error => console.error(`- ${error}`));
      throw new Error("スキーマの検証に失敗しました");
    }
  }
}
