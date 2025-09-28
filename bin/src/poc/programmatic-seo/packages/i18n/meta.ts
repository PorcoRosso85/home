/**
 * Phase 1.1 - メタデータ管理契約
 *
 * title/description生成ヘルパー契約、言語別メタデータ管理
 * TypeScript型安全なインターフェース
 */

import {
  type BCP47LanguageTag,
  type LocaleConfig,
  type I18nConfig,
  type AbsoluteURL
} from './types.js';

/**
 * ページメタデータテンプレート
 */
export interface MetaTemplate {
  /** ページタイトルテンプレート */
  title: string;
  /** メタディスクリプションテンプレート */
  description: string;
  /** キーワード（任意） */
  keywords?: string[];
  /** OGプロパティ（任意） */
  og?: {
    title?: string;
    description?: string;
    image?: AbsoluteURL;
    type?: 'website' | 'article' | 'product' | 'profile';
  };
  /** Twitterカード（任意） */
  twitter?: {
    card?: 'summary' | 'summary_large_image' | 'app' | 'player';
    title?: string;
    description?: string;
    image?: AbsoluteURL;
  };
}

/**
 * 言語別メタデータ
 */
export interface LocalizedMeta {
  /** 言語タグ */
  lang: BCP47LanguageTag;
  /** ページタイトル */
  title: string;
  /** メタディスクリプション */
  description: string;
  /** キーワード */
  keywords: string[];
  /** 正規URL */
  canonical: AbsoluteURL;
  /** 代替言語URL */
  alternates: Array<{
    lang: BCP47LanguageTag;
    url: AbsoluteURL;
  }>;
  /** OGメタデータ */
  og: {
    title: string;
    description: string;
    url: AbsoluteURL;
    image?: AbsoluteURL;
    type: 'website' | 'article' | 'product' | 'profile';
    locale: BCP47LanguageTag;
  };
  /** Twitterカード */
  twitter: {
    card: 'summary' | 'summary_large_image' | 'app' | 'player';
    title: string;
    description: string;
    image?: AbsoluteURL;
  };
}

/**
 * メタデータ生成パラメータ
 */
export interface MetaGenerationParams {
  /** ページURL */
  url: AbsoluteURL;
  /** ページタイプ */
  type: 'homepage' | 'category' | 'product' | 'article' | 'static';
  /** 動的パラメータ */
  params?: Record<string, string | number>;
  /** 代替言語URL情報 */
  alternates?: Array<{
    lang: BCP47LanguageTag;
    url: AbsoluteURL;
  }>;
  /** OG画像URL（任意） */
  ogImage?: AbsoluteURL;
}

/**
 * 言語別メタデータテンプレート辞書
 */
export const META_TEMPLATES: Partial<Record<BCP47LanguageTag, Record<string, MetaTemplate>>> = {
  'x-default': {
    homepage: {
      title: 'Programmatic SEO - Zero-Config Foundation',
      description: 'Lightweight programmatic SEO foundation with zero Cloudflare dependencies. Easy integration, measurement snippets, and rich structured data.',
      keywords: ['seo', 'programmatic', 'structured data', 'json-ld', 'measurement'],
      og: {
        title: 'Programmatic SEO - Zero-Config Foundation',
        description: 'Lightweight programmatic SEO foundation with zero Cloudflare dependencies.',
        type: 'website'
      },
      twitter: {
        card: 'summary_large_image',
        title: 'Programmatic SEO - Zero-Config Foundation',
        description: 'Lightweight programmatic SEO foundation with zero Cloudflare dependencies.'
      }
    },
    category: {
      title: '{categoryName} - Programmatic SEO',
      description: 'Explore {categoryName} resources and tools for programmatic SEO implementation.',
      keywords: ['seo', 'category', '{categoryName}'],
      og: {
        title: '{categoryName} - Programmatic SEO',
        description: 'Explore {categoryName} resources and tools for programmatic SEO.',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{categoryName} - Programmatic SEO',
        description: 'Explore {categoryName} resources and tools for programmatic SEO.'
      }
    },
    product: {
      title: '{productName} - SEO Tools',
      description: '{productName}: {productDescription}. Professional SEO tools for better search visibility.',
      keywords: ['seo', 'tools', '{productName}'],
      og: {
        title: '{productName} - SEO Tools',
        description: '{productName}: {productDescription}. Professional SEO tools.',
        type: 'product'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{productName} - SEO Tools',
        description: '{productName}: {productDescription}.'
      }
    },
    article: {
      title: '{articleTitle} - Programmatic SEO Blog',
      description: '{articleExcerpt}',
      keywords: ['seo', 'blog', 'article'],
      og: {
        title: '{articleTitle}',
        description: '{articleExcerpt}',
        type: 'article'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{articleTitle}',
        description: '{articleExcerpt}'
      }
    },
    static: {
      title: '{pageTitle} - Programmatic SEO',
      description: '{pageDescription}',
      keywords: ['seo'],
      og: {
        title: '{pageTitle} - Programmatic SEO',
        description: '{pageDescription}',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{pageTitle} - Programmatic SEO',
        description: '{pageDescription}'
      }
    }
  },
  'en': {
    homepage: {
      title: 'Programmatic SEO - Zero-Config Foundation',
      description: 'Lightweight programmatic SEO foundation with zero Cloudflare dependencies. Easy integration, measurement snippets, and rich structured data.',
      keywords: ['seo', 'programmatic', 'structured data', 'json-ld', 'measurement'],
      og: {
        title: 'Programmatic SEO - Zero-Config Foundation',
        description: 'Lightweight programmatic SEO foundation with zero Cloudflare dependencies.',
        type: 'website'
      },
      twitter: {
        card: 'summary_large_image',
        title: 'Programmatic SEO - Zero-Config Foundation',
        description: 'Lightweight programmatic SEO foundation with zero Cloudflare dependencies.'
      }
    },
    category: {
      title: '{categoryName} - Programmatic SEO',
      description: 'Explore {categoryName} resources and tools for programmatic SEO implementation.',
      keywords: ['seo', 'category', '{categoryName}'],
      og: {
        title: '{categoryName} - Programmatic SEO',
        description: 'Explore {categoryName} resources and tools for programmatic SEO.',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{categoryName} - Programmatic SEO',
        description: 'Explore {categoryName} resources and tools for programmatic SEO.'
      }
    },
    product: {
      title: '{productName} - SEO Tools',
      description: '{productName}: {productDescription}. Professional SEO tools for better search visibility.',
      keywords: ['seo', 'tools', '{productName}'],
      og: {
        title: '{productName} - SEO Tools',
        description: '{productName}: {productDescription}. Professional SEO tools.',
        type: 'product'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{productName} - SEO Tools',
        description: '{productName}: {productDescription}.'
      }
    },
    article: {
      title: '{articleTitle} - Programmatic SEO Blog',
      description: '{articleExcerpt}',
      keywords: ['seo', 'blog', 'article'],
      og: {
        title: '{articleTitle}',
        description: '{articleExcerpt}',
        type: 'article'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{articleTitle}',
        description: '{articleExcerpt}'
      }
    },
    static: {
      title: '{pageTitle} - Programmatic SEO',
      description: '{pageDescription}',
      keywords: ['seo'],
      og: {
        title: '{pageTitle} - Programmatic SEO',
        description: '{pageDescription}',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{pageTitle} - Programmatic SEO',
        description: '{pageDescription}'
      }
    }
  },
  'ja': {
    homepage: {
      title: 'プログラマティックSEO - ゼロ設定基盤',
      description: 'Cloudflare依存なしの軽量プログラマティックSEO基盤。簡単統合、計測スニペット、リッチ構造化データ対応。',
      keywords: ['seo', 'プログラマティック', '構造化データ', 'json-ld', '計測'],
      og: {
        title: 'プログラマティックSEO - ゼロ設定基盤',
        description: 'Cloudflare依存なしの軽量プログラマティックSEO基盤。',
        type: 'website'
      },
      twitter: {
        card: 'summary_large_image',
        title: 'プログラマティックSEO - ゼロ設定基盤',
        description: 'Cloudflare依存なしの軽量プログラマティックSEO基盤。'
      }
    },
    category: {
      title: '{categoryName} - プログラマティックSEO',
      description: 'プログラマティックSEO実装のための{categoryName}リソースとツールを探索。',
      keywords: ['seo', 'カテゴリ', '{categoryName}'],
      og: {
        title: '{categoryName} - プログラマティックSEO',
        description: 'プログラマティックSEO実装のための{categoryName}リソースとツール。',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{categoryName} - プログラマティックSEO',
        description: 'プログラマティックSEO実装のための{categoryName}リソースとツール。'
      }
    },
    product: {
      title: '{productName} - SEOツール',
      description: '{productName}: {productDescription}. 検索可視性向上のためのプロフェッショナルSEOツール。',
      keywords: ['seo', 'ツール', '{productName}'],
      og: {
        title: '{productName} - SEOツール',
        description: '{productName}: {productDescription}. プロフェッショナルSEOツール。',
        type: 'product'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{productName} - SEOツール',
        description: '{productName}: {productDescription}.'
      }
    },
    article: {
      title: '{articleTitle} - プログラマティックSEOブログ',
      description: '{articleExcerpt}',
      keywords: ['seo', 'ブログ', '記事'],
      og: {
        title: '{articleTitle}',
        description: '{articleExcerpt}',
        type: 'article'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{articleTitle}',
        description: '{articleExcerpt}'
      }
    },
    static: {
      title: '{pageTitle} - プログラマティックSEO',
      description: '{pageDescription}',
      keywords: ['seo'],
      og: {
        title: '{pageTitle} - プログラマティックSEO',
        description: '{pageDescription}',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{pageTitle} - プログラマティックSEO',
        description: '{pageDescription}'
      }
    }
  },
  'es': {
    homepage: {
      title: 'SEO Programático - Base de Configuración Cero',
      description: 'Base ligera de SEO programático sin dependencias de Cloudflare. Integración fácil, snippets de medición y datos estructurados ricos.',
      keywords: ['seo', 'programático', 'datos estructurados', 'json-ld', 'medición'],
      og: {
        title: 'SEO Programático - Base de Configuración Cero',
        description: 'Base ligera de SEO programático sin dependencias de Cloudflare.',
        type: 'website'
      },
      twitter: {
        card: 'summary_large_image',
        title: 'SEO Programático - Base de Configuración Cero',
        description: 'Base ligera de SEO programático sin dependencias de Cloudflare.'
      }
    },
    category: {
      title: '{categoryName} - SEO Programático',
      description: 'Explora recursos y herramientas de {categoryName} para implementación de SEO programático.',
      keywords: ['seo', 'categoría', '{categoryName}'],
      og: {
        title: '{categoryName} - SEO Programático',
        description: 'Explora recursos y herramientas de {categoryName} para SEO programático.',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{categoryName} - SEO Programático',
        description: 'Explora recursos y herramientas de {categoryName} para SEO programático.'
      }
    },
    product: {
      title: '{productName} - Herramientas SEO',
      description: '{productName}: {productDescription}. Herramientas SEO profesionales para mejor visibilidad en búsquedas.',
      keywords: ['seo', 'herramientas', '{productName}'],
      og: {
        title: '{productName} - Herramientas SEO',
        description: '{productName}: {productDescription}. Herramientas SEO profesionales.',
        type: 'product'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{productName} - Herramientas SEO',
        description: '{productName}: {productDescription}.'
      }
    },
    article: {
      title: '{articleTitle} - Blog de SEO Programático',
      description: '{articleExcerpt}',
      keywords: ['seo', 'blog', 'artículo'],
      og: {
        title: '{articleTitle}',
        description: '{articleExcerpt}',
        type: 'article'
      },
      twitter: {
        card: 'summary_large_image',
        title: '{articleTitle}',
        description: '{articleExcerpt}'
      }
    },
    static: {
      title: '{pageTitle} - SEO Programático',
      description: '{pageDescription}',
      keywords: ['seo'],
      og: {
        title: '{pageTitle} - SEO Programático',
        description: '{pageDescription}',
        type: 'website'
      },
      twitter: {
        card: 'summary',
        title: '{pageTitle} - SEO Programático',
        description: '{pageDescription}'
      }
    }
  }
} as const;

/**
 * テンプレート文字列内のプレースホルダーを置換
 *
 * @param template - テンプレート文字列
 * @param params - 置換パラメータ
 * @returns 置換済み文字列
 */
export function replacePlaceholders(template: string, params: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    const value = params[key];
    return value !== undefined ? String(value) : match;
  });
}

/**
 * 言語別メタデータを生成
 *
 * @param lang - 対象言語
 * @param params - 生成パラメータ
 * @param config - 国際化設定
 * @returns 言語別メタデータ
 */
export function generateLocalizedMeta(
  lang: BCP47LanguageTag,
  params: MetaGenerationParams,
  config: I18nConfig
): LocalizedMeta {
  // 対象言語のテンプレートを取得（フォールバック対応）
  let langTemplates = META_TEMPLATES[lang];
  if (!langTemplates) {
    // フォールバック: x-default -> en
    langTemplates = META_TEMPLATES['x-default'] || META_TEMPLATES['en'];
  }

  if (!langTemplates) {
    throw new Error(`No templates found for language: ${lang} and no fallback available`);
  }

  const template = langTemplates[params.type];
  if (!template) {
    throw new Error(`Template not found for type: ${params.type}, language: ${lang}`);
  }

  const dynamicParams = params.params || {};

  // プレースホルダー置換
  const title = replacePlaceholders(template.title, dynamicParams);
  const description = replacePlaceholders(template.description, dynamicParams);
  const keywords = template.keywords?.map(k => replacePlaceholders(k, dynamicParams)) || [];

  // OGメタデータ生成
  const ogTitle = template.og?.title ?
    replacePlaceholders(template.og.title, dynamicParams) : title;
  const ogDescription = template.og?.description ?
    replacePlaceholders(template.og.description, dynamicParams) : description;

  // Twitterカード生成
  const twitterTitle = template.twitter?.title ?
    replacePlaceholders(template.twitter.title, dynamicParams) : title;
  const twitterDescription = template.twitter?.description ?
    replacePlaceholders(template.twitter.description, dynamicParams) : description;

  return {
    lang,
    title,
    description,
    keywords,
    canonical: params.url,
    alternates: params.alternates || [],
    og: {
      title: ogTitle,
      description: ogDescription,
      url: params.url,
      image: params.ogImage || template.og?.image,
      type: template.og?.type || 'website',
      locale: lang
    },
    twitter: {
      card: template.twitter?.card || 'summary',
      title: twitterTitle,
      description: twitterDescription,
      image: params.ogImage || template.twitter?.image
    }
  };
}

/**
 * 複数言語のメタデータを一括生成
 *
 * @param languages - 対象言語リスト
 * @param baseParams - 基本生成パラメータ
 * @param config - 国際化設定
 * @returns 言語別メタデータマップ
 */
export function generateMultilingualMeta(
  languages: BCP47LanguageTag[],
  baseParams: Omit<MetaGenerationParams, 'url'>,
  urlMap: Partial<Record<BCP47LanguageTag, AbsoluteURL>>,
  config: I18nConfig
): Partial<Record<BCP47LanguageTag, LocalizedMeta>> {
  const result: Partial<Record<BCP47LanguageTag, LocalizedMeta>> = {};

  for (const lang of languages) {
    const url = urlMap[lang];
    if (!url) {
      console.warn(`URL not found for language: ${lang}`);
      continue;
    }

    // 代替言語URL配列を構築
    const alternates = Object.entries(urlMap)
      .filter(([altLang]) => altLang !== lang)
      .map(([altLang, altUrl]) => ({
        lang: altLang as BCP47LanguageTag,
        url: altUrl
      }));

    const params: MetaGenerationParams = {
      ...baseParams,
      url,
      alternates
    };

    result[lang] = generateLocalizedMeta(lang, params, config);
  }

  return result;
}

/**
 * HTMLメタタグ文字列を生成
 *
 * @param meta - 言語別メタデータ
 * @returns HTMLメタタグ文字列
 */
export function generateMetaTags(meta: LocalizedMeta): string {
  const tags: string[] = [];

  // 基本メタタグ
  tags.push(`<title>${escapeHtml(meta.title)}</title>`);
  tags.push(`<meta name="description" content="${escapeHtml(meta.description)}">`);
  if (meta.keywords.length > 0) {
    tags.push(`<meta name="keywords" content="${escapeHtml(meta.keywords.join(', '))}">`);
  }

  // 言語とcanonical
  tags.push(`<html lang="${meta.lang}">`);
  tags.push(`<link rel="canonical" href="${meta.canonical}">`);

  // 代替言語URL
  for (const alt of meta.alternates) {
    tags.push(`<link rel="alternate" hreflang="${alt.lang}" href="${alt.url}">`);
  }

  // OGタグ
  tags.push(`<meta property="og:title" content="${escapeHtml(meta.og.title)}">`);
  tags.push(`<meta property="og:description" content="${escapeHtml(meta.og.description)}">`);
  tags.push(`<meta property="og:url" content="${meta.og.url}">`);
  tags.push(`<meta property="og:type" content="${meta.og.type}">`);
  tags.push(`<meta property="og:locale" content="${meta.og.locale}">`);
  if (meta.og.image) {
    tags.push(`<meta property="og:image" content="${meta.og.image}">`);
  }

  // Twitterカード
  tags.push(`<meta name="twitter:card" content="${meta.twitter.card}">`);
  tags.push(`<meta name="twitter:title" content="${escapeHtml(meta.twitter.title)}">`);
  tags.push(`<meta name="twitter:description" content="${escapeHtml(meta.twitter.description)}">`);
  if (meta.twitter.image) {
    tags.push(`<meta name="twitter:image" content="${meta.twitter.image}">`);
  }

  return tags.join('\n');
}

/**
 * HTMLエスケープ
 */
function escapeHtml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// テンプレートを他言語でも拡張する場合の空のプレースホルダー
(META_TEMPLATES as any)['en-US'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['en-GB'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ja-JP'] = META_TEMPLATES['ja'];
(META_TEMPLATES as any)['es-ES'] = META_TEMPLATES['es'];
(META_TEMPLATES as any)['es-MX'] = META_TEMPLATES['es'];
(META_TEMPLATES as any)['fr'] = META_TEMPLATES['en']; // フォールバック
(META_TEMPLATES as any)['fr-FR'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['fr-CA'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['de'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['de-DE'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['it'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['it-IT'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['pt'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['pt-BR'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['pt-PT'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ru'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ru-RU'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ar'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ar-SA'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['hi'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['hi-IN'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['zh'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['zh-CN'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['zh-TW'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ko'] = META_TEMPLATES['en'];
(META_TEMPLATES as any)['ko-KR'] = META_TEMPLATES['en'];
