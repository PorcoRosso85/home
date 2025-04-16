import { Command } from "./command.ts";
import { MetaSchemaRegistryService } from "./metaSchemaRegistryService.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";
import { FileSystemWriter } from "../infrastructure/fileSystemWriter.ts";

/**
 * スキーマ生成コマンドハンドラー
 */
export class GenerateCommand implements Command {
  constructor(
    private registryService: MetaSchemaRegistryService,
    private fileReader: FileSystemReader,
    private fileWriter: FileSystemWriter
  ) {}
  
  /**
   * コマンドを実行する
   * 
   * @param args コマンドライン引数
   */
  async execute(args: any): Promise<void> {
    const metaSchemaId = args._[1] as string;
    const configPath = args._[2] as string;
    const outputPath = args._[3] as string;
    
    if (!metaSchemaId || !configPath || !outputPath) {
      throw new Error("メタスキーマID、設定ファイルパス、出力ファイルパスが必要です");
    }
    
    // 設定ファイルの読み込み
    const config = await this.fileReader.readJsonFile(configPath);
    
    // 詳細モードの場合、設定ファイルの診断結果を表示
    if (args.verbose) {
      await this.diagnoseConfig(metaSchemaId, config);
    }
    
    try {
      // スキーマの生成
      const schema = await this.registryService.generateSchema(metaSchemaId, config);
      
      // スキーマの書き込み
      await this.fileWriter.writeJsonFile(outputPath, schema);
      console.log(`スキーマを '${outputPath}' に生成しました`);
    } catch (error) {
      console.error(`スキーマの生成に失敗しました: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * 設定ファイルの診断結果を表示
   * 
   * @param metaSchemaId メタスキーマID
   * @param config 設定ファイル
   */
  private async diagnoseConfig(metaSchemaId: string, config: any): Promise<void> {
    console.log(`設定ファイルの診断結果:`);
    
    // メタスキーマに対する検証
    const validationResult = await this.registryService.validateConfig(metaSchemaId, config);
    
    if (validationResult.valid) {
      console.log("- 設定は有効です");
      
      // 設定の概要を表示
      console.log("\n設定の概要:");
      Object.keys(config).forEach(key => {
        const value = config[key];
        if (Array.isArray(value)) {
          console.log(`- ${key}: [${value.length}個の要素]`);
        } else if (typeof value === 'object' && value !== null) {
          console.log(`- ${key}: {${Object.keys(value).length}個のプロパティ}`);
        } else {
          console.log(`- ${key}: ${value}`);
        }
      });
    } else {
      console.log("- 設定に以下の問題があります:");
      validationResult.errors.forEach(error => {
        console.log(`  - ${error}`);
      });
      
      console.log("\n問題のある設定:");
      console.log(JSON.stringify(config, null, 2));
    }
  }
}
