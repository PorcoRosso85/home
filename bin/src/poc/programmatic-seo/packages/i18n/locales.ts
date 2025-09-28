/**
 * Phase 1.1 - 言語設定実装
 *
 * BCP47準拠言語タグとx-default対応設計
 * デフォルト言語設定とフォールバック機能
 */

import {
  type BCP47LanguageTag,
  type LocaleConfig,
  type I18nConfig
} from './types.js';

/**
 * サポート言語の詳細設定
 *
 * 各言語の表示名、ネイティブ名、文字方向、フォールバック戦略を定義
 */
export const LOCALE_CONFIGS: Record<BCP47LanguageTag, LocaleConfig> = {
  // Default/Universal
  'x-default': {
    tag: 'x-default',
    displayName: 'Default',
    nativeName: 'Default',
    direction: 'ltr',
    fallback: undefined // No fallback for default
  },

  // English variants
  'en': {
    tag: 'en',
    displayName: 'English',
    nativeName: 'English',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'en-US': {
    tag: 'en-US',
    displayName: 'English (United States)',
    nativeName: 'English (United States)',
    direction: 'ltr',
    fallback: 'en'
  },
  'en-GB': {
    tag: 'en-GB',
    displayName: 'English (United Kingdom)',
    nativeName: 'English (United Kingdom)',
    direction: 'ltr',
    fallback: 'en'
  },

  // Japanese variants
  'ja': {
    tag: 'ja',
    displayName: 'Japanese',
    nativeName: '日本語',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'ja-JP': {
    tag: 'ja-JP',
    displayName: 'Japanese (Japan)',
    nativeName: '日本語 (日本)',
    direction: 'ltr',
    fallback: 'ja'
  },

  // Chinese variants
  'zh': {
    tag: 'zh',
    displayName: 'Chinese',
    nativeName: '中文',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'zh-CN': {
    tag: 'zh-CN',
    displayName: 'Chinese (Simplified, China)',
    nativeName: '中文 (简体，中国)',
    direction: 'ltr',
    fallback: 'zh'
  },
  'zh-TW': {
    tag: 'zh-TW',
    displayName: 'Chinese (Traditional, Taiwan)',
    nativeName: '中文 (繁體，台灣)',
    direction: 'ltr',
    fallback: 'zh'
  },

  // Korean variants
  'ko': {
    tag: 'ko',
    displayName: 'Korean',
    nativeName: '한국어',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'ko-KR': {
    tag: 'ko-KR',
    displayName: 'Korean (South Korea)',
    nativeName: '한국어 (대한민국)',
    direction: 'ltr',
    fallback: 'ko'
  },

  // Spanish variants
  'es': {
    tag: 'es',
    displayName: 'Spanish',
    nativeName: 'Español',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'es-ES': {
    tag: 'es-ES',
    displayName: 'Spanish (Spain)',
    nativeName: 'Español (España)',
    direction: 'ltr',
    fallback: 'es'
  },
  'es-MX': {
    tag: 'es-MX',
    displayName: 'Spanish (Mexico)',
    nativeName: 'Español (México)',
    direction: 'ltr',
    fallback: 'es'
  },

  // French variants
  'fr': {
    tag: 'fr',
    displayName: 'French',
    nativeName: 'Français',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'fr-FR': {
    tag: 'fr-FR',
    displayName: 'French (France)',
    nativeName: 'Français (France)',
    direction: 'ltr',
    fallback: 'fr'
  },
  'fr-CA': {
    tag: 'fr-CA',
    displayName: 'French (Canada)',
    nativeName: 'Français (Canada)',
    direction: 'ltr',
    fallback: 'fr'
  },

  // German variants
  'de': {
    tag: 'de',
    displayName: 'German',
    nativeName: 'Deutsch',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'de-DE': {
    tag: 'de-DE',
    displayName: 'German (Germany)',
    nativeName: 'Deutsch (Deutschland)',
    direction: 'ltr',
    fallback: 'de'
  },

  // Italian variants
  'it': {
    tag: 'it',
    displayName: 'Italian',
    nativeName: 'Italiano',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'it-IT': {
    tag: 'it-IT',
    displayName: 'Italian (Italy)',
    nativeName: 'Italiano (Italia)',
    direction: 'ltr',
    fallback: 'it'
  },

  // Portuguese variants
  'pt': {
    tag: 'pt',
    displayName: 'Portuguese',
    nativeName: 'Português',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'pt-BR': {
    tag: 'pt-BR',
    displayName: 'Portuguese (Brazil)',
    nativeName: 'Português (Brasil)',
    direction: 'ltr',
    fallback: 'pt'
  },
  'pt-PT': {
    tag: 'pt-PT',
    displayName: 'Portuguese (Portugal)',
    nativeName: 'Português (Portugal)',
    direction: 'ltr',
    fallback: 'pt'
  },

  // Russian variants
  'ru': {
    tag: 'ru',
    displayName: 'Russian',
    nativeName: 'Русский',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'ru-RU': {
    tag: 'ru-RU',
    displayName: 'Russian (Russia)',
    nativeName: 'Русский (Россия)',
    direction: 'ltr',
    fallback: 'ru'
  },

  // Arabic variants
  'ar': {
    tag: 'ar',
    displayName: 'Arabic',
    nativeName: 'العربية',
    direction: 'rtl',
    fallback: 'x-default'
  },
  'ar-SA': {
    tag: 'ar-SA',
    displayName: 'Arabic (Saudi Arabia)',
    nativeName: 'العربية (المملكة العربية السعودية)',
    direction: 'rtl',
    fallback: 'ar'
  },

  // Hindi variants
  'hi': {
    tag: 'hi',
    displayName: 'Hindi',
    nativeName: 'हिन्दी',
    direction: 'ltr',
    fallback: 'x-default'
  },
  'hi-IN': {
    tag: 'hi-IN',
    displayName: 'Hindi (India)',
    nativeName: 'हिन्दी (भारत)',
    direction: 'ltr',
    fallback: 'hi'
  }
};

/**
 * デフォルト国際化設定
 *
 * 一般的なユースケースに適した設定
 */
export const DEFAULT_I18N_CONFIG: I18nConfig = {
  defaultLang: 'x-default',
  supportedLangs: ['x-default', 'en', 'ja'],
  locales: LOCALE_CONFIGS,
  fallbackStrategy: 'hierarchy'
};

/**
 * 多言語対応国際化設定（例）
 *
 * グローバルサイト向けの拡張設定
 */
export const MULTILINGUAL_I18N_CONFIG: I18nConfig = {
  defaultLang: 'en',
  supportedLangs: [
    'x-default', 'en', 'en-US', 'en-GB',
    'ja', 'ja-JP', 'zh', 'zh-CN', 'zh-TW',
    'ko', 'ko-KR', 'es', 'es-ES', 'es-MX',
    'fr', 'fr-FR', 'fr-CA', 'de', 'de-DE',
    'it', 'it-IT', 'pt', 'pt-BR', 'pt-PT',
    'ru', 'ru-RU', 'ar', 'ar-SA', 'hi', 'hi-IN'
  ],
  locales: LOCALE_CONFIGS,
  fallbackStrategy: 'hierarchy'
};

/**
 * 言語フォールバックチェーンを取得
 *
 * @param lang - 対象言語タグ
 * @param config - 国際化設定
 * @returns フォールバック言語チェーン（優先度順）
 */
export function getLanguageFallbackChain(
  lang: BCP47LanguageTag,
  config: I18nConfig = DEFAULT_I18N_CONFIG
): BCP47LanguageTag[] {
  const chain: BCP47LanguageTag[] = [lang];
  const visited = new Set<BCP47LanguageTag>([lang]);

  let current = lang;
  while (current) {
    const localeConfig = config.locales[current];
    if (!localeConfig?.fallback || visited.has(localeConfig.fallback)) {
      break;
    }

    current = localeConfig.fallback;
    chain.push(current);
    visited.add(current);
  }

  // デフォルト言語が含まれていない場合は追加
  if (!chain.includes(config.defaultLang)) {
    chain.push(config.defaultLang);
  }

  return chain;
}

/**
 * 言語タグから基本言語を取得
 *
 * @param lang - 言語タグ（例: 'en-US'）
 * @returns 基本言語（例: 'en'）
 */
export function getBaseLang(lang: BCP47LanguageTag): BCP47LanguageTag {
  if (lang === 'x-default') return lang;

  const parts = lang.split('-');
  return parts[0] as BCP47LanguageTag;
}

/**
 * 言語方向を取得
 *
 * @param lang - 言語タグ
 * @param config - 国際化設定
 * @returns 文字方向
 */
export function getLanguageDirection(
  lang: BCP47LanguageTag,
  config: I18nConfig = DEFAULT_I18N_CONFIG
): 'ltr' | 'rtl' {
  const localeConfig = config.locales[lang];
  return localeConfig?.direction ?? 'ltr';
}

/**
 * サポート言語かどうかを判定
 *
 * @param lang - 言語タグ
 * @param config - 国際化設定
 * @returns サポート状況
 */
export function isSupportedLanguage(
  lang: BCP47LanguageTag,
  config: I18nConfig = DEFAULT_I18N_CONFIG
): boolean {
  return config.supportedLangs.includes(lang);
}

/**
 * 利用可能な言語リストを取得
 *
 * @param config - 国際化設定
 * @returns 言語設定の配列
 */
export function getAvailableLanguages(
  config: I18nConfig = DEFAULT_I18N_CONFIG
): LocaleConfig[] {
  return config.supportedLangs.map(lang => config.locales[lang]);
}

/**
 * 言語表示名を取得
 *
 * @param lang - 言語タグ
 * @param nativeName - ネイティブ名使用フラグ
 * @param config - 国際化設定
 * @returns 表示名
 */
export function getLanguageDisplayName(
  lang: BCP47LanguageTag,
  nativeName: boolean = false,
  config: I18nConfig = DEFAULT_I18N_CONFIG
): string {
  const localeConfig = config.locales[lang];
  if (!localeConfig) return lang;

  return nativeName ? localeConfig.nativeName : localeConfig.displayName;
}

/**
 * 最適な言語を選択
 *
 * Accept-Languageヘッダーやユーザー設定から最適な言語を選択
 *
 * @param preferredLangs - 優先言語リスト
 * @param config - 国際化設定
 * @returns 選択された言語タグ
 */
export function selectBestLanguage(
  preferredLangs: BCP47LanguageTag[],
  config: I18nConfig = DEFAULT_I18N_CONFIG
): BCP47LanguageTag {
  // 優先度順でサポート言語をチェック
  for (const preferred of preferredLangs) {
    if (isSupportedLanguage(preferred, config)) {
      return preferred;
    }

    // 完全一致しない場合、基本言語をチェック
    const baseLang = getBaseLang(preferred);
    if (baseLang !== preferred && isSupportedLanguage(baseLang, config)) {
      return baseLang;
    }
  }

  // デフォルト言語を返す
  return config.defaultLang;
}
