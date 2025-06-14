import { MetaSchema, ValidationResult } from "../domain/metaSchema.ts";
import { Schema } from "../domain/schema.ts";
import { Config } from "../domain/config.ts";
import { MetaSchemaRepository } from "../domain/metaSchemaRepository.ts";
import { ValidationService } from "../domain/validationService.ts";
import { GenerationService } from "../domain/generationService.ts";

/**
 * メタスキーマレジストリサービス
 * アプリケーション層でメタスキーマの管理を担当
 */
export class MetaSchemaRegistryService {
  constructor(
    private metaSchemaRepository: MetaSchemaRepository,
    private validationService: ValidationService,
    private generationService: GenerationService,
  ) {}
  
  /**
   * メタスキーマを登録
   * 
   * @param metaSchema 登録するメタスキーマ
   */
  async registerMetaSchema(metaSchema: MetaSchema): Promise<void> {
    await this.metaSchemaRepository.save(metaSchema);
    console.log(`メタスキーマ '${metaSchema.id}' を登録しました`);
  }
  
  /**
   * メタスキーマの存在確認
   * 
   * @param metaSchemaId メタスキーマID
   * @returns 存在するかどうか
   */
  async hasMetaSchema(metaSchemaId: string): Promise<boolean> {
    const metaSchema = await this.metaSchemaRepository.findById(metaSchemaId);
    return !!metaSchema;
  }
  
  /**
   * メタスキーマの取得
   * 
   * @param metaSchemaId メタスキーマID
   * @returns メタスキーマ
   * @throws メタスキーマが存在しない場合
   */
  async getMetaSchema(metaSchemaId: string): Promise<MetaSchema> {
    const metaSchema = await this.metaSchemaRepository.findById(metaSchemaId);
    if (!metaSchema) {
      throw this.createMetaSchemaNotFoundError(metaSchemaId);
    }
    return metaSchema;
  }
  
  /**
   * 登録済みのメタスキーマID一覧を取得
   * 
   * @returns メタスキーマIDの配列
   */
  async getRegisteredMetaSchemaIds(): Promise<string[]> {
    return await this.metaSchemaRepository.getAllIds();
  }
  
  /**
   * 部分一致するメタスキーマIDを検索
   * 
   * @param partialId 部分的なID
   * @returns 部分一致するIDの配列
   */
  async getSimilarMetaSchemaIds(partialId: string): Promise<string[]> {
    return await this.metaSchemaRepository.findSimilarIds(partialId);
  }
  
  /**
   * スキーマを検証
   * 
   * @param schema 検証するスキーマ
   * @returns 検証結果
   */
  async validateSchema(schema: Schema): Promise<ValidationResult> {
    if (!schema.$metaSchema) {
      return { valid: false, errors: ["スキーマに '$metaSchema' プロパティがありません"] };
    }
    
    const metaSchemaId = schema.$metaSchema;
    
    try {
      const metaSchema = await this.getMetaSchema(metaSchemaId);
      return this.validationService.validateSchema(schema, metaSchema);
    } catch (error) {
      if (error.message.includes('未知のメタスキーマ')) {
        return {
          valid: false,
          errors: [error.message]
        };
      }
      throw error;
    }
  }
  
  /**
   * 設定ファイルを検証
   * 
   * @param metaSchemaId 使用するメタスキーマID
   * @param config 検証する設定ファイル
   * @returns 検証結果
   */
  async validateConfig(metaSchemaId: string, config: Config): Promise<ValidationResult> {
    try {
      const metaSchema = await this.getMetaSchema(metaSchemaId);
      return this.validationService.validateConfig(config, metaSchema);
    } catch (error) {
      if (error.message.includes('未知のメタスキーマ')) {
        return {
          valid: false,
          errors: [error.message]
        };
      }
      throw error;
    }
  }
  
  /**
   * スキーマを生成
   * 
   * @param metaSchemaId 使用するメタスキーマID
   * @param config 生成に使用する設定ファイル
   * @returns 生成されたスキーマ
   * @throws メタスキーマが存在しない場合、設定が無効な場合
   */
  async generateSchema(metaSchemaId: string, config: Config): Promise<Schema> {
    try {
      const metaSchema = await this.getMetaSchema(metaSchemaId);
      
      // 設定の検証
      const configValidation = await this.validateConfig(metaSchemaId, config);
      if (!configValidation.valid) {
        throw new Error(`設定ファイルが無効です:\n${configValidation.errors.map(e => `  - ${e}`).join('\n')}`);
      }
      
      // スキーマの生成
      const generatedSchema = this.generationService.generateSchema(config, metaSchema);
      
      // 生成されたスキーマの検証
      const validationResult = await this.validateSchema(generatedSchema);
      if (!validationResult.valid) {
        console.warn("生成されたスキーマが検証に失敗しました:", validationResult.errors);
      }
      
      return generatedSchema;
    } catch (error) {
      if (error.message.includes('未知のメタスキーマ')) {
        // ヒントを追加
        throw new Error(error.message);
      }
      throw error;
    }
  }
  
  /**
   * メタスキーマが存在しない場合のエラー作成
   * 
   * @param metaSchemaId 存在しないメタスキーマID
   * @returns エラーオブジェクト
   */
  private async createMetaSchemaNotFoundError(metaSchemaId: string): Promise<Error> {
    const registeredIds = await this.getRegisteredMetaSchemaIds();
    const suggestions = await this.getSimilarMetaSchemaIds(metaSchemaId);
    
    let errorMsg = `未知のメタスキーマ: ${metaSchemaId}`;
    
    if (registeredIds.length > 0) {
      errorMsg += `\n登録済みのメタスキーマ: ${registeredIds.join(', ')}`;
    }
    
    if (suggestions.length > 0) {
      errorMsg += `\nもしかして: ${suggestions.join(', ')} ですか？`;
    }
    
    return new Error(errorMsg);
  }
}
