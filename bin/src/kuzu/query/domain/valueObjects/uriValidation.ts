import type { LocationUri, ParsedUri } from './uriValue';

/**
 * LocationUriバリデーション関数
 * @param uri 検証するURI文字列
 * @returns 解析結果とバリデーション結果
 */
export function validateLocationUri(uri: string): ParsedUri {
  try {
    // 基本的なURI形式チェック
    if (!uri || typeof uri !== 'string') {
      return {
        uri_id: '',
        scheme: '',
        authority: '',
        path: '',
        fragment: '',
        query: '',
        isValid: false,
        error: 'URI must be a non-empty string'
      };
    }

    // URIの解析
    const urlObject = new URL(uri);
    
    const locationUri: LocationUri = {
      uri_id: uri,
      scheme: urlObject.protocol.replace(':', ''),
      authority: urlObject.hostname + (urlObject.port ? ':' + urlObject.port : ''),
      path: urlObject.pathname,
      fragment: urlObject.hash.replace('#', ''),
      query: urlObject.search.replace('?', '')
    };

    return {
      ...locationUri,
      isValid: true
    };
  } catch (error) {
    // URLコンストラクタエラーの場合、単純なパス形式として処理
    if (uri.startsWith('/')) {
      return {
        uri_id: uri,
        scheme: 'path',
        authority: '',
        path: uri,
        fragment: '',
        query: '',
        isValid: true
      };
    }

    return {
      uri_id: uri,
      scheme: '',
      authority: '',
      path: '',
      fragment: '',
      query: '',
      isValid: false,
      error: 'Invalid URI format'
    };
  }
}

/**
 * LocationUriオブジェクトのバリデーション
 * @param locationUri 検証するLocationUriオブジェクト
 * @returns バリデーション結果
 */
export function validateLocationUriObject(locationUri: LocationUri): { isValid: boolean; error?: string } {
  const requiredFields = ['uri_id', 'scheme', 'path'];
  
  for (const field of requiredFields) {
    if (!locationUri[field as keyof LocationUri]) {
      return {
        isValid: false,
        error: `Required field '${field}' is missing or empty`
      };
    }
  }

  // 許可されたスキームの例
  const allowedSchemes = ['file', 'http', 'https', 'path'];
  if (!allowedSchemes.includes(locationUri.scheme)) {
    return {
      isValid: false,
      error: `Scheme '${locationUri.scheme}' is not allowed. Allowed schemes: ${allowedSchemes.join(', ')}`
    };
  }

  return { isValid: true };
}
