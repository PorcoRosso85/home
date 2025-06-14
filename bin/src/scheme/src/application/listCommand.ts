import { Command } from "./command.ts";
import { MetaSchemaRegistryService } from "./metaSchemaRegistryService.ts";

/**
 * メタスキーマ一覧表示コマンドハンドラー
 */
export class ListCommand implements Command {
  constructor(
    private registryService: MetaSchemaRegistryService
  ) {}
  
  /**
   * コマンドを実行する
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const ids = await this.registryService.getRegisteredMetaSchemaIds();
    
    if (ids.length === 0) {
      console.log("登録済みのメタスキーマはありません");
      return;
    }
    
    console.log("登録済みのメタスキーマ一覧:");
    ids.forEach(id => {
      console.log(`- ${id}`);
    });
  }
}
