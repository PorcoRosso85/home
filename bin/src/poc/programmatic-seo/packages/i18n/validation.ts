/**
 * Phase 1.1 - バリデーション機能実装
 *
 * URL正規化とJSON Schema validation統合
 * BCP47言語タグとISO8601日時の厳密なバリデーション
 */

import {
  type BCP47LanguageTag,
  type ISO8601DateTime,
  type AbsoluteURL,
  type URLSourceEntry,
  type URLSourceDatabase,
  type URLNormalizationConfig,
  type ValidationError,
  type ValidationResult,
  isBCP47LanguageTag,
  isISO8601DateTime,
  isAbsoluteURL,
  isURLSourceEntry
} from './types.js';

/**
 * デフォルトURL正規化設定
 */
export const DEFAULT_URL_NORMALIZATION: URLNormalizationConfig = {
  trailingSlash: 'never',
  removeQuery: true,
  removeFragment: true,
  allowedProtocols: ['https', 'http'],
  normalizePort: true
};

/**
 * 厳密URL正規化設定（canonical URL限定）
 */
export const STRICT_URL_NORMALIZATION: URLNormalizationConfig = {
  trailingSlash: 'never',
  removeQuery: true,
  removeFragment: true,
  allowedProtocols: ['https'], // HTTPSのみ
  normalizePort: true
};

/**
 * URL正規化エラーコード
 */
export const URL_VALIDATION_ERRORS = {
  INVALID_URL: 'INVALID_URL',
  RELATIVE_URL: 'RELATIVE_URL',
  UNSUPPORTED_PROTOCOL: 'UNSUPPORTED_PROTOCOL',
  INVALID_HOST: 'INVALID_HOST',
  TRAILING_SLASH_VIOLATION: 'TRAILING_SLASH_VIOLATION'
} as const;

/**
 * BCP47バリデーションエラーコード
 */
export const LANG_VALIDATION_ERRORS = {
  INVALID_LANG_TAG: 'INVALID_LANG_TAG',
  UNSUPPORTED_LANG: 'UNSUPPORTED_LANG',
  MALFORMED_TAG: 'MALFORMED_TAG'
} as const;

/**
 * 日時バリデーションエラーコード
 */
export const DATETIME_VALIDATION_ERRORS = {
  INVALID_ISO8601: 'INVALID_ISO8601',
  NOT_UTC: 'NOT_UTC',
  INVALID_DATE: 'INVALID_DATE',
  FUTURE_DATE: 'FUTURE_DATE'
} as const;

/**
 * URLを正規化
 *
 * @param url - 正規化対象URL
 * @param config - 正規化設定
 * @returns 正規化されたURL
 * @throws URLValidationError 不正なURLの場合
 */
export function normalizeURL(
  url: string,
  config: URLNormalizationConfig = DEFAULT_URL_NORMALIZATION
): AbsoluteURL {
  try {
    const urlObj = new URL(url);

    // プロトコルチェック
    if (!config.allowedProtocols.includes(urlObj.protocol.slice(0, -1) as 'https' | 'http')) {
      throw new Error(`Unsupported protocol: ${urlObj.protocol}`);
    }

    // ポート正規化
    if (config.normalizePort) {
      if ((urlObj.protocol === 'https:' && urlObj.port === '443') ||
          (urlObj.protocol === 'http:' && urlObj.port === '80')) {
        urlObj.port = '';
      }
    }

    // クエリとフラグメント除去
    if (config.removeQuery) {
      urlObj.search = '';
    }
    if (config.removeFragment) {
      urlObj.hash = '';
    }

    // 末尾スラッシュ処理
    let pathname = urlObj.pathname;
    switch (config.trailingSlash) {
      case 'always':
        if (!pathname.endsWith('/')) pathname += '/';
        break;
      case 'never':
        if (pathname.endsWith('/') && pathname.length > 1) {
          pathname = pathname.slice(0, -1);
        }
        break;
      // 'preserve' の場合は変更なし
    }
    urlObj.pathname = pathname;

    return urlObj.toString() as AbsoluteURL;

  } catch (error) {
    throw new Error(`URL normalization failed: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * URLバリデーション
 *
 * @param url - バリデーション対象URL
 * @param config - 正規化設定
 * @returns バリデーション結果
 */
export function validateURL(
  url: unknown,
  config: URLNormalizationConfig = DEFAULT_URL_NORMALIZATION
): ValidationResult<AbsoluteURL> {
  if (typeof url !== 'string') {
    return {
      valid: false,
      errors: [{
        code: URL_VALIDATION_ERRORS.INVALID_URL,
        message: 'URL must be a string',
        value: url
      }]
    };
  }

  try {
    const urlObj = new URL(url);

    // 相対URLチェック
    if (!urlObj.protocol || !urlObj.host) {
      return {
        valid: false,
        errors: [{
          code: URL_VALIDATION_ERRORS.RELATIVE_URL,
          message: 'Relative URLs are not allowed. Use absolute URLs only.',
          value: url
        }]
      };
    }

    const normalizedURL = normalizeURL(url, config);

    return {
      valid: true,
      data: normalizedURL
    };

  } catch (error) {
    return {
      valid: false,
      errors: [{
        code: URL_VALIDATION_ERRORS.INVALID_URL,
        message: error instanceof Error ? error.message : 'Invalid URL format',
        value: url
      }]
    };
  }
}

/**
 * BCP47言語タグバリデーション
 *
 * @param lang - バリデーション対象言語タグ
 * @param supportedLangs - サポート言語リスト（任意）
 * @returns バリデーション結果
 */
export function validateLanguageTag(
  lang: unknown,
  supportedLangs?: BCP47LanguageTag[]
): ValidationResult<BCP47LanguageTag> {
  if (typeof lang !== 'string') {
    return {
      valid: false,
      errors: [{
        code: LANG_VALIDATION_ERRORS.INVALID_LANG_TAG,
        message: 'Language tag must be a string',
        value: lang
      }]
    };
  }

  if (!isBCP47LanguageTag(lang)) {
    return {
      valid: false,
      errors: [{
        code: LANG_VALIDATION_ERRORS.MALFORMED_TAG,
        message: `Invalid BCP47 language tag: ${lang}`,
        value: lang
      }]
    };
  }

  if (supportedLangs && !supportedLangs.includes(lang)) {
    return {
      valid: false,
      errors: [{
        code: LANG_VALIDATION_ERRORS.UNSUPPORTED_LANG,
        message: `Unsupported language: ${lang}`,
        value: lang
      }]
    };
  }

  return {
    valid: true,
    data: lang
  };
}

/**
 * ISO8601日時バリデーション
 *
 * @param datetime - バリデーション対象日時
 * @param allowFuture - 未来日時許可フラグ
 * @returns バリデーション結果
 */
export function validateISO8601DateTime(
  datetime: unknown,
  allowFuture: boolean = true
): ValidationResult<ISO8601DateTime> {
  if (typeof datetime !== 'string') {
    return {
      valid: false,
      errors: [{
        code: DATETIME_VALIDATION_ERRORS.INVALID_ISO8601,
        message: 'DateTime must be a string',
        value: datetime
      }]
    };
  }

  if (!isISO8601DateTime(datetime)) {
    return {
      valid: false,
      errors: [{
        code: DATETIME_VALIDATION_ERRORS.INVALID_ISO8601,
        message: `Invalid ISO8601 UTC datetime format: ${datetime}`,
        value: datetime
      }]
    };
  }

  // 未来日時チェック
  if (!allowFuture) {
    const date = new Date(datetime);
    const now = new Date();
    if (date > now) {
      return {
        valid: false,
        errors: [{
          code: DATETIME_VALIDATION_ERRORS.FUTURE_DATE,
          message: `Future dates are not allowed: ${datetime}`,
          value: datetime
        }]
      };
    }
  }

  return {
    valid: true,
    data: datetime
  };
}

/**
 * URLSourceEntryバリデーション
 *
 * @param entry - バリデーション対象エントリ
 * @param config - URL正規化設定
 * @param supportedLangs - サポート言語リスト
 * @returns バリデーション結果
 */
export function validateURLSourceEntry(
  entry: unknown,
  config: URLNormalizationConfig = DEFAULT_URL_NORMALIZATION,
  supportedLangs?: BCP47LanguageTag[]
): ValidationResult<URLSourceEntry> {
  if (!entry || typeof entry !== 'object') {
    return {
      valid: false,
      errors: [{
        code: 'INVALID_ENTRY',
        message: 'Entry must be an object',
        value: entry
      }]
    };
  }

  const entryObj = entry as Record<string, unknown>;
  const errors: ValidationError[] = [];

  // 必須フィールド: loc
  const locResult = validateURL(entryObj.loc, config);
  if (!locResult.valid) {
    errors.push(...(locResult.errors || []).map(err => ({
      ...err,
      path: 'loc'
    })));
  }

  // 必須フィールド: lastmod
  const lastmodResult = validateISO8601DateTime(entryObj.lastmod, false);
  if (!lastmodResult.valid) {
    errors.push(...(lastmodResult.errors || []).map(err => ({
      ...err,
      path: 'lastmod'
    })));
  }

  // 任意フィールド: lang
  if (entryObj.lang !== undefined) {
    const langResult = validateLanguageTag(entryObj.lang, supportedLangs);
    if (!langResult.valid) {
      errors.push(...(langResult.errors || []).map(err => ({
        ...err,
        path: 'lang'
      })));
    }
  }

  // 任意フィールド: alternates
  if (entryObj.alternates !== undefined) {
    if (!Array.isArray(entryObj.alternates)) {
      errors.push({
        code: 'INVALID_ALTERNATES',
        message: 'alternates must be an array',
        path: 'alternates',
        value: entryObj.alternates
      });
    } else {
      entryObj.alternates.forEach((alt, index) => {
        if (!alt || typeof alt !== 'object') {
          errors.push({
            code: 'INVALID_ALTERNATE',
            message: 'Alternate entry must be an object',
            path: `alternates[${index}]`,
            value: alt
          });
          return;
        }

        const altObj = alt as Record<string, unknown>;

        const altLangResult = validateLanguageTag(altObj.lang, supportedLangs);
        if (!altLangResult.valid) {
          errors.push(...(altLangResult.errors || []).map(err => ({
            ...err,
            path: `alternates[${index}].lang`
          })));
        }

        const altLocResult = validateURL(altObj.loc, config);
        if (!altLocResult.valid) {
          errors.push(...(altLocResult.errors || []).map(err => ({
            ...err,
            path: `alternates[${index}].loc`
          })));
        }
      });
    }
  }

  if (errors.length > 0) {
    return {
      valid: false,
      errors
    };
  }

  // Type guard validation (最終チェック)
  if (!isURLSourceEntry(entry)) {
    return {
      valid: false,
      errors: [{
        code: 'TYPE_GUARD_FAILED',
        message: 'Entry failed type guard validation',
        value: entry
      }]
    };
  }

  return {
    valid: true,
    data: entry as URLSourceEntry
  };
}

/**
 * URLSourceDatabaseバリデーション
 *
 * @param database - バリデーション対象データベース
 * @param config - URL正規化設定
 * @returns バリデーション結果
 */
export function validateURLSourceDatabase(
  database: unknown,
  config: URLNormalizationConfig = DEFAULT_URL_NORMALIZATION
): ValidationResult<URLSourceDatabase> {
  if (!database || typeof database !== 'object') {
    return {
      valid: false,
      errors: [{
        code: 'INVALID_DATABASE',
        message: 'Database must be an object',
        value: database
      }]
    };
  }

  const dbObj = database as Record<string, unknown>;
  const errors: ValidationError[] = [];

  // バージョンチェック
  if (dbObj.version !== '1.1') {
    errors.push({
      code: 'INVALID_VERSION',
      message: `Unsupported version: ${dbObj.version}. Expected: 1.1`,
      path: 'version',
      value: dbObj.version
    });
  }

  // generated フィールド
  const generatedResult = validateISO8601DateTime(dbObj.generated, true);
  if (!generatedResult.valid) {
    errors.push(...(generatedResult.errors || []).map(err => ({
      ...err,
      path: 'generated'
    })));
  }

  // defaultLang フィールド
  const defaultLangResult = validateLanguageTag(dbObj.defaultLang);
  if (!defaultLangResult.valid) {
    errors.push(...(defaultLangResult.errors || []).map(err => ({
      ...err,
      path: 'defaultLang'
    })));
  }

  // urls配列
  if (!Array.isArray(dbObj.urls)) {
    errors.push({
      code: 'INVALID_URLS',
      message: 'urls must be an array',
      path: 'urls',
      value: dbObj.urls
    });
  } else {
    // 各URLエントリをバリデーション
    dbObj.urls.forEach((url, index) => {
      const urlResult = validateURLSourceEntry(url, config);
      if (!urlResult.valid) {
        errors.push(...(urlResult.errors || []).map(err => ({
          ...err,
          path: `urls[${index}]${err.path ? '.' + err.path : ''}`
        })));
      }
    });
  }

  if (errors.length > 0) {
    return {
      valid: false,
      errors
    };
  }

  return {
    valid: true,
    data: database as URLSourceDatabase
  };
}

/**
 * JSON Schema (基本版)
 *
 * より厳密なバリデーションには外部のJSON Schemaライブラリを使用可能
 */
export const URL_SOURCE_JSON_SCHEMA = {
  type: 'object',
  required: ['version', 'generated', 'defaultLang', 'urls'],
  properties: {
    version: {
      type: 'string',
      enum: ['1.1']
    },
    generated: {
      type: 'string',
      pattern: '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$'
    },
    defaultLang: {
      type: 'string'
    },
    urls: {
      type: 'array',
      items: {
        type: 'object',
        required: ['loc', 'lastmod'],
        properties: {
          loc: {
            type: 'string',
            format: 'uri'
          },
          lastmod: {
            type: 'string',
            pattern: '^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(\\.\\d{3})?Z$'
          },
          lang: {
            type: 'string'
          },
          alternates: {
            type: 'array',
            items: {
              type: 'object',
              required: ['lang', 'loc'],
              properties: {
                lang: { type: 'string' },
                loc: { type: 'string', format: 'uri' }
              }
            }
          }
        }
      }
    }
  }
} as const;
