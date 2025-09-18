/**
 * ResourceUriValidationService.ts
 * 
 * リソースURIのバリデーションと正規化を行うサービス
 */

import { ResourceUri, ResourceUriType } from './valueObjects/ResourceUri.ts';

export interface ResourceUriValidationResult {
  isValid: boolean;
  normalizedUri?: ResourceUri;
  errors?: string[];
}

/**
 * リソースURIのバリデーションと正規化を行うサービス
 */
export class ResourceUriValidationService {
  /**
   * リソースURIを検証して正規化する
   * @param uriString URIの文字列表現
   * @returns 検証結果
   */
  validate(uriString: string): ResourceUriValidationResult {
    const errors: string[] = [];

    if (!uriString) {
      errors.push('リソースURIは必須です');
      return { isValid: false, errors };
    }

    try {
      // 正規化とバリデーション
      const normalizedUri = ResourceUri.create(uriString);
      return { isValid: true, normalizedUri };
    } catch (error) {
      errors.push(error instanceof Error ? error.message : '無効なリソースURI形式です');
      return { isValid: false, errors };
    }
  }

  /**
   * 特定のスキーマファイルに対するリソースURIを構築する
   * @param filePath 対象ファイルのパス（絶対パスまたはURI形式）
   * @param schemaName スキーマの名前（オプション）
   * @returns 構築されたリソースURI
   */
  buildSchemaResourceUri(filePath: string, schemaName?: string): ResourceUri {
    try {
      const uri = ResourceUri.create(filePath);
      // スキーマ名が指定されている場合はフラグメント識別子を追加
      if (schemaName) {
        const baseUri = uri.value;
        return ResourceUri.create(`${baseUri}#${encodeURIComponent(schemaName)}`);
      }
      return uri;
    } catch (error) {
      // 相対パスの場合は例外をスローするのではなく、警告を出してからファイルURIに変換する
      if (filePath.startsWith('./') || filePath.startsWith('../')) {
        console.warn('相対パスの使用は推奨されません。将来のバージョンではサポートされなくなる可能性があります。');
        // 環境に依存する処理だが、例として実装
        const absolutePath = `/path/to/project/${filePath.replace(/^\.\//, '')}`;
        
        const uri = ResourceUri.fromAbsolutePath(absolutePath);
        if (schemaName) {
          return ResourceUri.create(`${uri.value}#${encodeURIComponent(schemaName)}`);
        }
        return uri;
      }
      
      throw error;
    }
  }

  /**
   * リソースURIからスキーマの詳細情報を抽出する
   * @param resourceUri リソースURI
   * @returns {Object} スキーマの詳細情報（ファイルパス、スキーマ名など）
   */
  extractSchemaInfo(resourceUri: ResourceUri): { filePath: string; schemaName?: string; type: ResourceUriType } {
    const uri = resourceUri.value;
    const type = resourceUri.type;
    
    // フラグメント識別子（#以降）の処理
    let filePath = uri;
    let schemaName: string | undefined = undefined;
    
    if (uri.includes('#')) {
      const [path, fragment] = uri.split('#');
      filePath = path;
      schemaName = decodeURIComponent(fragment);
    }
    
    // file URIの場合はファイルパスに変換
    if (type === ResourceUriType.FILE) {
      return {
        filePath: resourceUri.toFilePath(),
        schemaName,
        type
      };
    }
    
    return { filePath, schemaName, type };
  }
}
