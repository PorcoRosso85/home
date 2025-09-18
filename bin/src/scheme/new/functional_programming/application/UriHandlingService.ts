/**
 * UriHandlingService.ts
 * 
 * アプリケーション層のURIハンドリングサービス
 * スキーマとリソースURIの関連付けを管理
 */

import { ResourceUri } from '../domain/valueObjects/ResourceUri.ts';
import { ResourceUriValidationService } from '../domain/ResourceUriValidationService.ts';

/**
 * URIハンドリングサービスの設定オプション
 */
export interface UriHandlingServiceOptions {
  /**
   * 相対パスを許可するかどうか
   * (将来的には廃止され、常にfalseとなる予定)
   */
  allowRelativePaths?: boolean;
  
  /**
   * デフォルトのベースディレクトリ
   * 相対パスを解決する際に使用
   */
  baseDirectory?: string;
}

/**
 * アプリケーション層のURIハンドリングサービス
 * スキーマ生成時やパース時にURIを適切に処理
 */
export class UriHandlingService {
  private validationService: ResourceUriValidationService;
  private options: Required<UriHandlingServiceOptions>;
  
  /**
   * コンストラクタ
   * @param options 設定オプション
   */
  constructor(options: UriHandlingServiceOptions = {}) {
    this.validationService = new ResourceUriValidationService();
    
    // デフォルト設定とマージ
    this.options = {
      allowRelativePaths: false,
      baseDirectory: Deno.cwd(),
      ...options
    };
    
    // 相対パスをサポートする場合は警告を表示
    if (this.options.allowRelativePaths) {
      console.warn(
        '警告: 相対パスのサポートは将来のバージョンで削除される予定です。' +
        'URIスキーマ形式（file://）または絶対パスを使用することを推奨します。'
      );
    }
  }
  
  /**
   * 文字列からリソースURIを作成
   * @param uriString URI文字列
   * @returns 正規化されたResourceUriオブジェクト
   * @throws Error バリデーションエラー発生時
   */
  createResourceUri(uriString: string): ResourceUri {
    const result = this.validationService.validate(uriString);
    
    if (!result.isValid || !result.normalizedUri) {
      throw new Error(`リソースURIが無効です: ${result.errors?.join(', ')}`);
    }
    
    return result.normalizedUri;
  }
  
  /**
   * URIを正規化する
   * @param uriString 正規化するURI文字列
   * @param options 正規化オプション
   * @returns 正規化されたURI文字列
   */
  normalizeUri(uriString: string, options?: { allowRelative?: boolean }): string {
    const allowRelative = options?.allowRelative ?? this.options.allowRelativePaths;
    
    // 相対パスがサポートされていない場合の処理
    if (!allowRelative && (uriString.startsWith('./') || uriString.startsWith('../'))) {
      throw new Error('相対パスはサポートされていません。絶対パスまたはURI形式を使用してください。');
    }
    
    // ResourceUriを使用して正規化
    const resourceUri = this.createResourceUri(uriString);
    return resourceUri.value;
  }
  
  /**
   * スキーマファイルからリソースURIを構築
   * @param filePath ファイルパス
   * @param schemaName スキーマ名（オプション）
   * @returns リソースURI
   */
  buildSchemaResourceUri(filePath: string, schemaName?: string): ResourceUri {
    // 相対パスがサポートされていない場合の処理
    if (!this.options.allowRelativePaths && (filePath.startsWith('./') || filePath.startsWith('../'))) {
      throw new Error('相対パスはサポートされていません。絶対パスまたはURI形式を使用してください。');
    }
    
    return this.validationService.buildSchemaResourceUri(filePath, schemaName);
  }
  
  /**
   * Function__Meta.jsonファイルのrequiredUriプロパティを標準化
   * @param schemaObj スキーマオブジェクト
   * @returns 更新されたスキーマオブジェクト
   */
  normalizeSchemaResourceUris(schemaObj: any): any {
    // スキーマが存在しない場合は何もしない
    if (!schemaObj) return schemaObj;
    
    const updatedSchema = { ...schemaObj };
    
    // resourceUriプロパティがあれば標準化
    if (updatedSchema.resourceUri) {
      try {
        const normalizedUri = this.createResourceUri(updatedSchema.resourceUri);
        updatedSchema.resourceUri = normalizedUri.value;
      } catch (error) {
        // エラーの場合は警告を出して元の値を保持
        console.warn(`警告: resourceUriの正規化に失敗しました: ${updatedSchema.resourceUri}`);
      }
    }
    
    // externalDependenciesの$refプロパティを標準化
    if (Array.isArray(updatedSchema.externalDependencies)) {
      updatedSchema.externalDependencies = updatedSchema.externalDependencies.map(dep => {
        if (dep.$ref) {
          try {
            const normalizedRef = this.createResourceUri(dep.$ref);
            return { ...dep, $ref: normalizedRef.value };
          } catch (error) {
            // エラーの場合は警告を出して元の値を保持
            console.warn(`警告: 依存関係URIの正規化に失敗しました: ${dep.$ref}`);
            return dep;
          }
        }
        return dep;
      });
    }
    
    // 再帰的に処理
    // プロパティごとに再帰処理
    for (const key in updatedSchema) {
      const value = updatedSchema[key];
      
      // $refプロパティの処理
      if (key === '$ref' && typeof value === 'string') {
        try {
          const normalizedRef = this.createResourceUri(value);
          updatedSchema[key] = normalizedRef.value;
        } catch (error) {
          // エラーの場合は警告を出して元の値を保持
          console.warn(`警告: $refの正規化に失敗しました: ${value}`);
        }
      }
      // オブジェクトや配列の場合は再帰的に処理
      else if (typeof value === 'object' && value !== null) {
        if (Array.isArray(value)) {
          updatedSchema[key] = value.map(item => 
            typeof item === 'object' && item !== null ? this.normalizeSchemaResourceUris(item) : item
          );
        } else {
          updatedSchema[key] = this.normalizeSchemaResourceUris(value);
        }
      }
    }
    
    return updatedSchema;
  }
}
