import { MetaSchema } from "./metaSchema.ts";
import { Schema } from "./schema.ts";
import { Config } from "./config.ts";
import { META_SOURCE_TYPE, SCHEMA_CONFIG } from "../infrastructure/variables.ts";

/**
 * スキーマ生成を行うサービスのインターフェース
 */
export interface GenerationService {
  /**
   * 設定ファイルからスキーマを生成する
   * 
   * @param config 設定ファイル
   * @param metaSchema 使用するメタスキーマ
   * @returns 生成されたスキーマ
   */
  generateSchema(config: Config, metaSchema: MetaSchema): Schema;
}

/**
 * スキーマ生成サービスの実装クラス
 */
export class GenerationServiceImpl implements GenerationService {
  generateSchema(config: Config, metaSchema: MetaSchema): Schema {
    // メタスキーマのタイプによって異なるスキーマ生成ロジックを適用
    switch (metaSchema.type) {
      case "string":
        return this.generateStringSchema(config, metaSchema);
      case "struct":
        return this.generateStructSchema(config, metaSchema);
      case "function":
        return this.generateFunctionSchema(config, metaSchema);
      default:
        throw new Error(`未対応のメタスキーマタイプ: ${metaSchema.type}`);
    }
  }
  
  private generateStringSchema(config: Config, metaSchema: MetaSchema): Schema {
    // 文字列型スキーマの生成ロジック
    const baseSchema: Schema = {
      $schema: "http://json-schema.org/draft-07/schema#",
      $metaSchema: metaSchema.id,
      type: "string",
      title: config.title || "Unnamed String Schema"
    };
    
    // 設定からプロパティをコピー
    const schema = { ...baseSchema };
    
    // 各プロパティを設定
    for (const key of Object.keys(config)) {
      if (key !== "$schema" && key !== "$metaSchema" && key !== "type") {
        // オブジェクト型の場合はディープコピーと参照変換
        if (typeof config[key] === 'object' && config[key] !== null) {
          schema[key] = JSON.parse(JSON.stringify(config[key]));
          this.convertReferences(schema[key]);
        } else {
          schema[key] = config[key];
        }
      }
    }
    
    return schema;
  }
  
  private generateStructSchema(config: Config, metaSchema: MetaSchema): Schema {
    // 構造体型スキーマの生成ロジック
    const baseSchema: Schema = {
      $schema: "http://json-schema.org/draft-07/schema#",
      $metaSchema: metaSchema.id,
      type: "object",
      title: config.title || "Unnamed Struct Schema",
      properties: {}
    };
    
    // 設定からプロパティをコピー
    const schema = { ...baseSchema };
    
    // propertiesとrequiredフィールドを特別扱い
    if (config.properties) {
      // プロパティをディープコピー
      schema.properties = JSON.parse(JSON.stringify(config.properties));
      
      // $refの形式を修正（旧形式のパス参照から新形式のURI参照へ）
      this.convertReferences(schema.properties);
    }
    
    if (config.required) {
      schema.required = [...config.required];
    }
    
    // その他のプロパティを設定
    for (const key of Object.keys(config)) {
      if (key !== "$schema" && key !== "$metaSchema" && key !== "type" && key !== "properties" && key !== "required") {
        schema[key] = config[key];
      }
    }
    
    return schema;
  }
  
  /**
   * オブジェクト内の$ref参照を新形式に変換する
   * 
   * @param obj 変換対象のオブジェクト
   */
  private convertReferences(obj: any): void {
    // nullまたは未定義の場合は処理しない
    if (obj === null || obj === undefined) {
      return;
    }
    
    // オブジェクト型でない場合は処理しない
    if (typeof obj !== 'object') {
      return;
    }
    
    // 配列の場合は各要素を再帰的に処理
    if (Array.isArray(obj)) {
      for (const item of obj) {
        this.convertReferences(item);
      }
      return;
    }
    
    // オブジェクト内の各プロパティを処理
    for (const [key, value] of Object.entries(obj)) {
      // $ref属性を検出した場合
      if (key === '$ref' && typeof value === 'string') {
        // 旧形式のファイルパス参照の場合
        if (value.endsWith('.schema.json') && !value.startsWith('scheme://')) {
          // ファイル名から型名とメタスキーマを抽出
          const match = value.match(/([^\/]+)\.([^\/]+)\.schema\.json$/);
          if (match) {
            const typeName = match[1];
            const metaSchema = match[2];
            
            // 新形式のURI参照を設定
            obj[key] = `${SCHEMA_CONFIG.URI_SCHEME}${typeName}/${META_SOURCE_TYPE.LOCAL}:${metaSchema}`;
          }
        }
      }
      // オブジェクト型の値は再帰的に処理
      else if (typeof value === 'object' && value !== null) {
        this.convertReferences(value);
      }
    }
  }
  
  private generateFunctionSchema(config: Config, metaSchema: MetaSchema): Schema {
    // 関数型スキーマの生成ロジック
    const baseSchema: Schema = {
      $schema: "http://json-schema.org/draft-07/schema#",
      $metaSchema: metaSchema.id,
      title: config.title || "Unnamed Function Schema",
      type: "function",
      parameters: [],
      returns: { type: "any" }
    };
    
    // 設定からプロパティをコピー
    const schema = { ...baseSchema };
    
    // パラメータと戻り値を特別扱い
    if (config.parameters) {
      // ディープコピー
      schema.parameters = JSON.parse(JSON.stringify(config.parameters));
      // $refを変換
      this.convertReferences(schema.parameters);
    }
    
    if (config.returns) {
      // ディープコピー
      schema.returns = JSON.parse(JSON.stringify(config.returns));
      // $refを変換
      this.convertReferences(schema.returns);
    }
    
    // その他のプロパティを設定
    for (const key of Object.keys(config)) {
      if (key !== "$schema" && key !== "$metaSchema" && key !== "type" && key !== "parameters" && key !== "returns") {
        schema[key] = config[key];
      }
    }
    
    return schema;
  }
}
