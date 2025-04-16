import { MetaSchema, ValidationResult } from "./metaSchema.ts";
import { Schema } from "./schema.ts";
import { Config } from "./config.ts";

/**
 * スキーマと設定のバリデーションを行うサービスのインターフェース
 */
export interface ValidationService {
  /**
   * スキーマをメタスキーマに対して検証する
   * 
   * @param schema 検証対象のスキーマ
   * @param metaSchema 検証に使用するメタスキーマ
   * @returns 検証結果
   */
  validateSchema(schema: Schema, metaSchema: MetaSchema): ValidationResult;
  
  /**
   * 設定ファイルをメタスキーマに対して検証する
   * 
   * @param config 検証対象の設定
   * @param metaSchema 検証に使用するメタスキーマ
   * @returns 検証結果
   */
  validateConfig(config: Config, metaSchema: MetaSchema): ValidationResult;
}

/**
 * バリデーションサービスの実装クラス
 */
export class ValidationServiceImpl implements ValidationService {
  validateSchema(schema: Schema, metaSchema: MetaSchema): ValidationResult {
    const errors: string[] = [];
    
    // スキーマの検証ロジック
    // メタスキーマのタイプによって異なる検証を行う
    switch (metaSchema.type) {
      case "string":
        this.validateStringSchema(schema, errors);
        break;
      case "struct":
        this.validateStructSchema(schema, errors);
        break;
      case "function":
        this.validateFunctionSchema(schema, errors);
        break;
      default:
        errors.push(`未対応のメタスキーマタイプ: ${metaSchema.type}`);
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  validateConfig(config: Config, metaSchema: MetaSchema): ValidationResult {
    const errors: string[] = [];
    
    // 設定ファイルの検証ロジック
    // メタスキーマのタイプによって異なる検証を行う
    switch (metaSchema.type) {
      case "string":
        this.validateStringConfig(config, errors);
        break;
      case "struct":
        this.validateStructConfig(config, errors);
        break;
      case "function":
        this.validateFunctionConfig(config, errors);
        break;
      default:
        errors.push(`未対応のメタスキーマタイプ: ${metaSchema.type}`);
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  private validateStringSchema(schema: Schema, errors: string[]): void {
    // 文字列型スキーマの検証ロジック
    if (!schema.title) {
      errors.push("必須フィールド 'title' がありません");
    }
    
    if (schema.type !== "string") {
      errors.push("'type' は 'string' である必要があります");
    }
    
    // patternが正規表現として有効か検証
    if (schema.pattern) {
      try {
        new RegExp(schema.pattern);
      } catch (e) {
        errors.push(`'pattern' は有効な正規表現である必要があります: ${e.message}`);
      }
    }
    
    // minLengthとmaxLengthの整合性を検証
    if (schema.minLength !== undefined && schema.maxLength !== undefined) {
      if (schema.minLength > schema.maxLength) {
        errors.push("'minLength' は 'maxLength' 以下である必要があります");
      }
    }
  }
  
  private validateStructSchema(schema: Schema, errors: string[]): void {
    // 構造体型スキーマの検証ロジック
    if (!schema.title) {
      errors.push("必須フィールド 'title' がありません");
    }
    
    if (schema.type !== "object") {
      errors.push("'type' は 'object' である必要があります");
    }
    
    // propertiesオブジェクトが存在するか検証
    if (!schema.properties || typeof schema.properties !== 'object') {
      errors.push("構造体スキーマには 'properties' オブジェクトが必要です");
    }
  }
  
  private validateFunctionSchema(schema: Schema, errors: string[]): void {
    // 関数型スキーマの検証ロジック
    if (!schema.title) {
      errors.push("必須フィールド 'title' がありません");
    }
    
    // パラメータが定義されているか検証
    if (!schema.parameters || !Array.isArray(schema.parameters)) {
      errors.push("関数スキーマには 'parameters' 配列が必要です");
    }
    
    // 戻り値の型が定義されているか検証
    if (!schema.returns) {
      errors.push("関数スキーマには 'returns' が必要です");
    }
  }
  
  private validateStringConfig(config: Config, errors: string[]): void {
    // 文字列型設定の検証ロジック
    if (!config.title) {
      errors.push("設定に必須フィールド 'title' がありません");
    } else if (typeof config.title !== 'string') {
      errors.push("'title' は文字列である必要があります");
    }
    
    // patternが指定されている場合、有効な正規表現か検証
    if (config.pattern !== undefined) {
      if (typeof config.pattern !== 'string') {
        errors.push("'pattern' は文字列である必要があります");
      } else {
        try {
          new RegExp(config.pattern);
        } catch (e) {
          errors.push(`'pattern' は有効な正規表現である必要があります: ${e.message}`);
        }
      }
    }
    
    // minLengthが指定されている場合、数値か検証
    if (config.minLength !== undefined) {
      if (typeof config.minLength !== 'number' || config.minLength < 0 || !Number.isInteger(config.minLength)) {
        errors.push("'minLength' は0以上の整数である必要があります");
      }
    }
    
    // maxLengthが指定されている場合、数値か検証
    if (config.maxLength !== undefined) {
      if (typeof config.maxLength !== 'number' || config.maxLength < 0 || !Number.isInteger(config.maxLength)) {
        errors.push("'maxLength' は0以上の整数である必要があります");
      }
    }
    
    // minLengthとmaxLengthの整合性を検証
    if (config.minLength !== undefined && config.maxLength !== undefined) {
      if (config.minLength > config.maxLength) {
        errors.push("'minLength' は 'maxLength' 以下である必要があります");
      }
    }
    
    // formatが指定されている場合、有効な値か検証
    if (config.format !== undefined) {
      const validFormats = ["email", "hostname", "ipv4", "ipv6", "uri", "date", "date-time", "uuid"];
      if (!validFormats.includes(config.format)) {
        errors.push(`'format' は次のいずれかである必要があります: ${validFormats.join(', ')}`);
      }
    }
    
    // examplesが指定されている場合、配列か検証
    if (config.examples !== undefined) {
      if (!Array.isArray(config.examples)) {
        errors.push("'examples' は配列である必要があります");
      } else {
        // 各例が文字列であることを検証
        for (let i = 0; i < config.examples.length; i++) {
          if (typeof config.examples[i] !== 'string') {
            errors.push(`'examples[${i}]' は文字列である必要があります`);
          }
        }
      }
    }
    
    // enumが指定されている場合、配列か検証
    if (config.enum !== undefined) {
      if (!Array.isArray(config.enum)) {
        errors.push("'enum' は配列である必要があります");
      } else {
        // 各値が文字列であることを検証
        for (let i = 0; i < config.enum.length; i++) {
          if (typeof config.enum[i] !== 'string') {
            errors.push(`'enum[${i}]' は文字列である必要があります`);
          }
        }
      }
    }
    
    // defaultが指定されている場合、文字列か検証
    if (config.default !== undefined && typeof config.default !== 'string') {
      errors.push("'default' は文字列である必要があります");
    }
    
    // 未知のプロパティがないか検証
    const knownProps = ['$metaSchema', 'type', 'title', 'description', 'pattern', 'minLength', 'maxLength', 
                       'format', 'examples', 'enum', 'default'];
    const unknownProps = Object.keys(config).filter(key => !knownProps.includes(key));
    
    if (unknownProps.length > 0) {
      errors.push(`未知のプロパティが含まれています: ${unknownProps.join(', ')}`);
    }
  }
  
  private validateStructConfig(config: Config, errors: string[]): void {
    // 構造体型設定の検証ロジック
    if (!config.title) {
      errors.push("設定に必須フィールド 'title' がありません");
    } else if (typeof config.title !== 'string') {
      errors.push("'title' は文字列である必要があります");
    }
    
    // propertiesオブジェクトが存在するか検証
    if (!config.properties || typeof config.properties !== 'object') {
      errors.push("構造体設定には 'properties' オブジェクトが必要です");
    } else {
      // 各プロパティの検証
      for (const [propName, propDef] of Object.entries(config.properties)) {
        if (typeof propDef !== 'object' || propDef === null) {
          errors.push(`プロパティ '${propName}' の定義はオブジェクトである必要があります`);
          continue;
        }
        
        // プロパティの型が指定されているか検証
        if (!('type' in propDef) || typeof propDef.type !== 'string') {
          errors.push(`プロパティ '${propName}' には 'type' フィールドが必要です`);
        }
      }
    }
    
    // 必須プロパティが配列であるか検証
    if (config.required !== undefined) {
      if (!Array.isArray(config.required)) {
        errors.push("'required' は配列である必要があります");
      } else {
        // 各必須プロパティが文字列であるか検証
        for (let i = 0; i < config.required.length; i++) {
          if (typeof config.required[i] !== 'string') {
            errors.push(`'required[${i}]' は文字列である必要があります`);
          }
          
          // 必須プロパティがpropertiesに定義されているか検証
          if (config.properties && !config.properties[config.required[i]]) {
            errors.push(`必須プロパティ '${config.required[i]}' が 'properties' に定義されていません`);
          }
        }
      }
    }
    
    // 未知のプロパティがないか検証
    const knownProps = ['$metaSchema', 'type', 'title', 'description', 'properties', 'required', 'additionalProperties'];
    const unknownProps = Object.keys(config).filter(key => !knownProps.includes(key));
    
    if (unknownProps.length > 0) {
      errors.push(`未知のプロパティが含まれています: ${unknownProps.join(', ')}`);
    }
  }
  
  private validateFunctionConfig(config: Config, errors: string[]): void {
    // 関数型設定の検証ロジック
    if (!config.title) {
      errors.push("設定に必須フィールド 'title' がありません");
    } else if (typeof config.title !== 'string') {
      errors.push("'title' は文字列である必要があります");
    }
    
    // パラメータが定義されているか検証
    if (!config.parameters) {
      errors.push("関数設定には 'parameters' が必要です");
    } else if (!Array.isArray(config.parameters)) {
      errors.push("'parameters' は配列である必要があります");
    } else {
      // 各パラメータの検証
      for (let i = 0; i < config.parameters.length; i++) {
        const param = config.parameters[i];
        if (typeof param !== 'object' || param === null) {
          errors.push(`'parameters[${i}]' はオブジェクトである必要があります`);
          continue;
        }
        
        // パラメータ名が指定されているか検証
        if (!param.name || typeof param.name !== 'string') {
          errors.push(`'parameters[${i}]' には 'name' フィールドが必要です`);
        }
        
        // パラメータの型が指定されているか検証
        if (!param.type || typeof param.type !== 'string') {
          errors.push(`'parameters[${i}]' には 'type' フィールドが必要です`);
        }
      }
    }
    
    // 戻り値の型が定義されているか検証
    if (!config.returns) {
      errors.push("関数設定には 'returns' が必要です");
    } else if (typeof config.returns !== 'object' || config.returns === null) {
      errors.push("'returns' はオブジェクトである必要があります");
    } else if (!config.returns.type || typeof config.returns.type !== 'string') {
      errors.push("'returns' には 'type' フィールドが必要です");
    }
    
    // 未知のプロパティがないか検証
    const knownProps = ['$metaSchema', 'type', 'title', 'description', 'parameters', 'returns'];
    const unknownProps = Object.keys(config).filter(key => !knownProps.includes(key));
    
    if (unknownProps.length > 0) {
      errors.push(`未知のプロパティが含まれています: ${unknownProps.join(', ')}`);
    }
  }
}
