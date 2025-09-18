/**
 * SchemaValidator.ts
 * 
 * スキーマバリデーションを行うドメインサービス
 */

import { UriHandlingService } from '../../application/UriHandlingService.ts';

/**
 * バリデーション結果インターフェース
 */
export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  normalizedSchema?: any;
}

/**
 * バリデーションエラーインターフェース
 */
export interface ValidationError {
  message: string;
  path?: string;
  propertyName?: string;
}

/**
 * スキーマバリデーションオプション
 */
export interface SchemaValidationOptions {
  /**
   * resourceUriの正規化を行うかどうか
   */
  normalizeResourceUris?: boolean;
  
  /**
   * 相対パスを許可するかどうか
   */
  allowRelativePaths?: boolean;
  
  /**
   * 適用するJSONスキーマバージョン
   */
  jsonSchemaVersion?: 'draft-07' | 'draft-2019-09' | 'draft-2020-12';
}

/**
 * スキーマバリデーションを行うドメインサービス
 */
export class SchemaValidator {
  private uriHandler: UriHandlingService;
  
  /**
   * コンストラクタ
   * @param options バリデーションオプション
   */
  constructor(private options: SchemaValidationOptions = {}) {
    // デフォルト設定
    this.options = {
      normalizeResourceUris: true,
      allowRelativePaths: false,
      jsonSchemaVersion: 'draft-2020-12',
      ...options
    };
    
    // URIハンドリングサービスの初期化
    this.uriHandler = new UriHandlingService({
      allowRelativePaths: this.options.allowRelativePaths
    });
  }
  
  /**
   * スキーマファイルを検証する
   * @param filePath スキーマファイルのパス
   * @param options バリデーションオプション
   * @returns バリデーション結果とメタデータを含むオブジェクト
   */
  async validateSchema(filePath: string, options: {
    normalizeUris?: boolean;
    allowRelativePaths?: boolean;
  } = {}): Promise<{
    isValid: boolean;
    errors: string[];
    warnings: string[];
    fixableIssues?: Record<string, any>;
  }> {
    try {
      // ファイルを読み込む
      const fileContent = await Deno.readTextFile(filePath);
      const schema = JSON.parse(fileContent);
      
      // 設定を適用
      const validationOptions: SchemaValidationOptions = {
        normalizeResourceUris: options.normalizeUris ?? true,
        allowRelativePaths: options.allowRelativePaths ?? false,
      };
      
      // スキーマの検証を実行
      const result = this.validateFunctionMetaSchema(schema);
      
      // 修正可能な問題を特定
      const fixableIssues: Record<string, any> = {};
      if (!result.isValid && result.normalizedSchema) {
        fixableIssues.normalizedSchema = result.normalizedSchema;
      }
      
      return {
        isValid: result.isValid,
        errors: this.formatErrors(result.errors),
        warnings: [], // 現時点では警告は実装していません
        fixableIssues: Object.keys(fixableIssues).length > 0 ? fixableIssues : undefined
      };
    } catch (error) {
      // ファイル読み込みやパースのエラー
      return {
        isValid: false,
        errors: [`スキーマファイルの読み込みまたはパースに失敗しました: ${error instanceof Error ? error.message : 'Unknown error'}`],
        warnings: []
      };
    }
  }
  
  /**
   * スキーマの問題を修正する
   * @param filePath 対象のスキーマファイルパス
   * @param fixableIssues 修正可能な問題
   * @returns 修正結果
   */
  async fixSchemaIssues(filePath: string, fixableIssues: Record<string, any>): Promise<{
    success: boolean;
    outputPath: string;
    message?: string;
  }> {
    try {
      // 正規化されたスキーマを取得
      const normalizedSchema = fixableIssues.normalizedSchema;
      if (!normalizedSchema) {
        return {
          success: false,
          outputPath: filePath,
          message: '修正可能な問題がありません'
        };
      }
      
      // ファイルに保存
      const outputContent = JSON.stringify(normalizedSchema, null, 2);
      await Deno.writeTextFile(filePath, outputContent);
      
      return {
        success: true,
        outputPath: filePath
      };
    } catch (error) {
      return {
        success: false,
        outputPath: filePath,
        message: `問題の修正中にエラーが発生しました: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }
  
  /**
   * Function__Meta.jsonスキーマに対するバリデーション
   * @param schema バリデーション対象のスキーマオブジェクト
   * @returns バリデーション結果
   */
  validateFunctionMetaSchema(schema: any) {
    const errors: ValidationError[] = [];
    let normalizedSchema = schema;
    
    // スキーマが存在しない場合
    if (!schema) {
      errors.push({
        message: 'スキーマが提供されていません'
      });
      return { isValid: false, errors };
    }
    
    // 必須プロパティのチェック
    const requiredProps = ['title', 'type', 'signatures'];
    for (const prop of requiredProps) {
      if (schema[prop] === undefined) {
        errors.push({
          message: `必須プロパティ '${prop}' が存在しません`,
          propertyName: prop
        });
      }
    }
    
    // $schemaプロパティのバージョンチェック
    if (schema.$schema) {
      const expectedVersion = this.getExpectedSchemaUrl();
      if (schema.$schema !== expectedVersion) {
        errors.push({
          message: `$schemaプロパティが期待するバージョン (${expectedVersion}) と一致しません: ${schema.$schema}`,
          propertyName: '$schema'
        });
      }
    } else {
      errors.push({
        message: `$schemaプロパティが存在しません。'${this.getExpectedSchemaUrl()}' を使用してください`,
        propertyName: '$schema'
      });
    }
    
    // typeプロパティのチェック
    if (schema.type !== 'object') {
      errors.push({
        message: `typeプロパティは 'object' である必要があります: ${schema.type}`,
        propertyName: 'type'
      });
    }
    
    // URIの正規化とバリデーション
    if (this.options.normalizeResourceUris) {
      try {
        normalizedSchema = this.uriHandler.normalizeSchemaResourceUris(schema);
      } catch (error) {
        errors.push({
          message: `URI正規化中にエラーが発生しました: ${error instanceof Error ? error.message : 'Unknown error'}`,
          propertyName: 'resourceUri'
        });
      }
    }
    
    // シグネチャのバリデーション
    if (Array.isArray(schema.signatures)) {
      for (let i = 0; i < schema.signatures.length; i++) {
        const signature = schema.signatures[i];
        const signatureErrors = this.validateSignature(signature, `signatures[${i}]`);
        errors.push(...signatureErrors);
      }
    }
    
    // バリデーション結果の返却
    return {
      isValid: errors.length === 0,
      errors,
      normalizedSchema
    };
  }
  
  /**
   * シグネチャのバリデーション
   * @param signature シグネチャオブジェクト
   * @param basePath ベースパス（エラーメッセージ用）
   * @returns バリデーションエラーの配列
   */
  private validateSignature(signature: any, basePath: string): ValidationError[] {
    const errors: ValidationError[] = [];
    
    // 必須プロパティのチェック
    const requiredProps = ['id', 'parameterTypes', 'returnTypes'];
    for (const prop of requiredProps) {
      if (signature[prop] === undefined) {
        errors.push({
          message: `必須プロパティ '${prop}' が存在しません`,
          path: basePath,
          propertyName: prop
        });
      }
    }
    
    // parameterTypesのチェック
    if (signature.parameterTypes && typeof signature.parameterTypes === 'object') {
      if (!signature.parameterTypes.type) {
        errors.push({
          message: `parameterTypes.typeプロパティが必要です`,
          path: `${basePath}.parameterTypes`,
          propertyName: 'type'
        });
      }
    }
    
    // returnTypesのチェック
    if (signature.returnTypes && typeof signature.returnTypes === 'object') {
      if (!signature.returnTypes.type) {
        errors.push({
          message: `returnTypes.typeプロパティが必要です`,
          path: `${basePath}.returnTypes`,
          propertyName: 'type'
        });
      }
    }
    
    return errors;
  }
  
  /**
   * 期待される$schemaのURLを取得
   * @returns スキーマURLの文字列
   */
  private getExpectedSchemaUrl(): string {
    const version = this.options.jsonSchemaVersion;
    
    switch (version) {
      case 'draft-07':
        return 'http://json-schema.org/draft-07/schema#';
      case 'draft-2019-09':
        return 'https://json-schema.org/draft/2019-09/schema';
      case 'draft-2020-12':
      default:
        return 'https://json-schema.org/draft/2020-12/schema';
    }
  }
  
  /**
   * バリデーションエラーのフォーマット
   * @param errors エラーオブジェクトの配列
   * @returns フォーマットされたエラーメッセージの配列
   */
  formatErrors(errors: ValidationError[]): string[] {
    return errors.map(error => {
      const location = error.path 
        ? `at ${error.path}${error.propertyName ? `.${error.propertyName}` : ''}`
        : error.propertyName
          ? `at ${error.propertyName}`
          : '';
      
      return `${error.message} ${location}`.trim();
    });
  }
}
