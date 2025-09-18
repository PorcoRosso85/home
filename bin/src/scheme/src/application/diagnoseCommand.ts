import { Command } from "./command.ts";
import { MetaSchemaRegistryService } from "./metaSchemaRegistryService.ts";
import { FileSystemReader } from "../infrastructure/fileSystemReader.ts";

/**
 * 診断コマンドハンドラー
 */
export class DiagnoseCommand implements Command {
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
    const type = args._[1] as string;
    const filePath = args._[2] as string;
    
    if (!type || !filePath) {
      throw new Error("診断タイプ(meta/config)とファイルパスが必要です");
    }
    
    if (type === "meta") {
      await this.diagnoseMetaSchema(filePath);
    } else if (type === "config") {
      const metaSchemaId = args._[3] as string;
      if (!metaSchemaId) {
        throw new Error("設定ファイルの診断にはメタスキーマIDが必要です");
      }
      
      await this.diagnoseConfigFile(metaSchemaId, filePath);
    } else {
      throw new Error(`未知の診断タイプ: ${type}。'meta'または'config'を指定してください`);
    }
  }
  
  /**
   * メタスキーマの診断
   * 
   * @param metaSchemaPath メタスキーマファイルのパス
   */
  private async diagnoseMetaSchema(metaSchemaPath: string): Promise<void> {
    try {
      const metaSchema = await this.fileReader.readJsonFile(metaSchemaPath);
      
      console.log(`メタスキーマ '${metaSchemaPath}' の診断結果:`);
      
      // 基本プロパティの確認
      if (!metaSchema.title) {
        console.log("- 警告: 'title' プロパティがありません");
      } else {
        console.log(`- title: ${metaSchema.title}`);
      }
      
      if (!metaSchema.type) {
        console.log("- 警告: 'type' プロパティがありません");
      } else {
        console.log(`- type: ${metaSchema.type}`);
      }
      
      // required フィールドの確認
      if (!metaSchema.required || !Array.isArray(metaSchema.required)) {
        console.log("- 警告: 'required' フィールドがないか、配列ではありません");
      } else {
        console.log(`- required: ${metaSchema.required.join(', ')}`);
      }
      
      // properties の確認
      if (!metaSchema.properties || typeof metaSchema.properties !== 'object') {
        console.log("- 警告: 'properties' オブジェクトがありません");
      } else {
        console.log(`- properties: ${Object.keys(metaSchema.properties).length}個のプロパティが定義されています`);
      }
      
    } catch (error) {
      console.error(`エラー: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * 設定ファイルの診断
   * 
   * @param metaSchemaId メタスキーマID
   * @param configPath 設定ファイルのパス
   */
  private async diagnoseConfigFile(metaSchemaId: string, configPath: string): Promise<void> {
    try {
      const config = await this.fileReader.readJsonFile(configPath);
      
      console.log(`設定ファイル '${configPath}' の診断結果:`);
      
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
      
    } catch (error) {
      console.error(`エラー: ${error.message}`);
      throw error;
    }
  }
}
