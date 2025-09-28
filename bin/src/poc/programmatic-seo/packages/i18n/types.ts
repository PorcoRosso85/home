/**
 * Phase 1.1 - TypeScript型定義
 *
 * 国際化とURL管理のための厳密な型定義
 * - BCP47準拠言語タグ
 * - URL正規化対応
 * - JSON Schema validation統合
 */

/**
 * BCP47言語タグ（基本セット）
 *
 * @see https://tools.ietf.org/html/bcp47
 * @see https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry
 */
export type BCP47LanguageTag =
  // Primary languages
  | 'en'     // English
  | 'en-US'  // English (United States)
  | 'en-GB'  // English (United Kingdom)
  | 'ja'     // Japanese
  | 'ja-JP'  // Japanese (Japan)
  | 'zh'     // Chinese
  | 'zh-CN'  // Chinese (Simplified, China)
  | 'zh-TW'  // Chinese (Traditional, Taiwan)
  | 'ko'     // Korean
  | 'ko-KR'  // Korean (South Korea)
  | 'es'     // Spanish
  | 'es-ES'  // Spanish (Spain)
  | 'es-MX'  // Spanish (Mexico)
  | 'fr'     // French
  | 'fr-FR'  // French (France)
  | 'fr-CA'  // French (Canada)
  | 'de'     // German
  | 'de-DE'  // German (Germany)
  | 'it'     // Italian
  | 'it-IT'  // Italian (Italy)
  | 'pt'     // Portuguese
  | 'pt-BR'  // Portuguese (Brazil)
  | 'pt-PT'  // Portuguese (Portugal)
  | 'ru'     // Russian
  | 'ru-RU'  // Russian (Russia)
  | 'ar'     // Arabic
  | 'ar-SA'  // Arabic (Saudi Arabia)
  | 'hi'     // Hindi
  | 'hi-IN'  // Hindi (India)
  | 'x-default'; // Default/fallback language

/**
 * ISO 8601 UTC datetime string
 *
 * @example "2024-03-15T10:30:00Z"
 * @example "2024-03-15T10:30:00.123Z"
 */
export type ISO8601DateTime = string & { readonly __brand: unique symbol };

/**
 * 絶対URL文字列（正規化済み）
 *
 * 要件:
 * - 必ずhttps://またはhttp://で開始
 * - 末尾スラッシュは統一ルールに従う
 * - クエリパラメータとフラグメントは除外
 * - canonical URL限定
 */
export type AbsoluteURL = string & { readonly __brand: unique symbol };

/**
 * 代替言語URL情報
 */
export interface AlternateLanguageURL {
  /** BCP47言語タグ */
  lang: BCP47LanguageTag;
  /** 対応する絶対URL */
  loc: AbsoluteURL;
}

/**
 * URLソースエントリ（最小構造）
 *
 * sitemap.xmlとhreflang alternatesの両方に対応
 */
export interface URLSourceEntry {
  /** 必須: 絶対URL（正規化済み） */
  loc: AbsoluteURL;

  /** 必須: 最終更新日時（UTC ISO8601形式） */
  lastmod: ISO8601DateTime;

  /** 任意: 言語タグ（ページの主言語） */
  lang?: BCP47LanguageTag;

  /** 任意: 代替言語URL配列 */
  alternates?: AlternateLanguageURL[];
}

/**
 * URLソースデータベース
 *
 * scripts/url-source.json の型定義
 */
export interface URLSourceDatabase {
  /** データベースのバージョン */
  version: '1.1';

  /** 生成日時 */
  generated: ISO8601DateTime;

  /** デフォルト言語 */
  defaultLang: BCP47LanguageTag;

  /** URLエントリ配列 */
  urls: URLSourceEntry[];
}

/**
 * URL正規化設定
 */
export interface URLNormalizationConfig {
  /** 末尾スラッシュの統一ルール */
  trailingSlash: 'always' | 'never' | 'preserve';

  /** クエリパラメータの除去 */
  removeQuery: boolean;

  /** フラグメントの除去 */
  removeFragment: boolean;

  /** 許可されるプロトコル */
  allowedProtocols: ('https' | 'http')[];

  /** ポート番号の正規化 */
  normalizePort: boolean;
}

/**
 * バリデーションエラー
 */
export interface ValidationError {
  /** エラーコード */
  code: string;

  /** エラーメッセージ */
  message: string;

  /** エラーが発生したフィールドのパス */
  path?: string;

  /** 検証対象の値 */
  value?: unknown;
}

/**
 * バリデーション結果
 */
export interface ValidationResult<T = unknown> {
  /** バリデーション成功フラグ */
  valid: boolean;

  /** バリデーション済みデータ（成功時） */
  data?: T;

  /** エラー配列（失敗時） */
  errors?: ValidationError[];
}

/**
 * 言語設定
 */
export interface LocaleConfig {
  /** 言語タグ */
  tag: BCP47LanguageTag;

  /** 表示名（英語） */
  displayName: string;

  /** ネイティブ表示名 */
  nativeName: string;

  /** 文字方向 */
  direction: 'ltr' | 'rtl';

  /** フォールバック言語 */
  fallback?: BCP47LanguageTag;
}

/**
 * 国際化設定
 */
export interface I18nConfig {
  /** デフォルト言語 */
  defaultLang: BCP47LanguageTag;

  /** サポート言語一覧 */
  supportedLangs: BCP47LanguageTag[];

  /** 言語設定詳細 */
  locales: Record<BCP47LanguageTag, LocaleConfig>;

  /** フォールバック戦略 */
  fallbackStrategy: 'default' | 'hierarchy' | 'none';
}

// Type guards for runtime validation

/**
 * BCP47言語タグの型ガード
 */
export function isBCP47LanguageTag(value: unknown): value is BCP47LanguageTag {
  if (typeof value !== 'string') return false;

  const validTags: BCP47LanguageTag[] = [
    'en', 'en-US', 'en-GB', 'ja', 'ja-JP', 'zh', 'zh-CN', 'zh-TW',
    'ko', 'ko-KR', 'es', 'es-ES', 'es-MX', 'fr', 'fr-FR', 'fr-CA',
    'de', 'de-DE', 'it', 'it-IT', 'pt', 'pt-BR', 'pt-PT',
    'ru', 'ru-RU', 'ar', 'ar-SA', 'hi', 'hi-IN', 'x-default'
  ];

  return validTags.includes(value as BCP47LanguageTag);
}

/**
 * ISO8601日時文字列の型ガード
 */
export function isISO8601DateTime(value: unknown): value is ISO8601DateTime {
  if (typeof value !== 'string') return false;

  // Basic ISO8601 format validation (with Z timezone)
  const iso8601Regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/;
  if (!iso8601Regex.test(value)) return false;

  // Validate that it's a valid date
  const date = new Date(value);
  return !isNaN(date.getTime()) && date.toISOString() === value;
}

/**
 * 絶対URLの型ガード
 */
export function isAbsoluteURL(value: unknown): value is AbsoluteURL {
  if (typeof value !== 'string') return false;

  try {
    const url = new URL(value);
    return url.protocol === 'https:' || url.protocol === 'http:';
  } catch {
    return false;
  }
}

/**
 * URLSourceEntryの型ガード
 */
export function isURLSourceEntry(value: unknown): value is URLSourceEntry {
  if (!value || typeof value !== 'object') return false;

  const entry = value as Record<string, unknown>;

  // 必須フィールドのチェック
  if (!isAbsoluteURL(entry.loc) || !isISO8601DateTime(entry.lastmod)) {
    return false;
  }

  // 任意フィールドのチェック
  if (entry.lang !== undefined && !isBCP47LanguageTag(entry.lang)) {
    return false;
  }

  if (entry.alternates !== undefined) {
    if (!Array.isArray(entry.alternates)) return false;

    for (const alt of entry.alternates) {
      if (!alt || typeof alt !== 'object') return false;
      const altObj = alt as Record<string, unknown>;
      if (!isBCP47LanguageTag(altObj.lang) || !isAbsoluteURL(altObj.loc)) {
        return false;
      }
    }
  }

  return true;
}
