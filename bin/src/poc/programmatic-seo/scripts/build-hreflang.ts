#!/usr/bin/env node

/**
 * Phase 1.1 - Hreflang Build Script
 *
 * scripts/url-source.jsonを入力として読み込み
 * <link rel="alternate" hreflang>生成
 * 相互参照完全性検証
 * HTML/JSON/XML形式での出力対応
 */

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';

// 型定義をインポート
import {
  type BCP47LanguageTag,
  type URLSourceDatabase,
  type URLSourceEntry,
  type AbsoluteURL,
  isBCP47LanguageTag,
  isAbsoluteURL,
  isURLSourceEntry
} from '../packages/i18n/types';

/**
 * Hreflang情報
 */
interface HreflangLink {
  /** 言語タグ */
  hreflang: BCP47LanguageTag;
  /** URL */
  href: AbsoluteURL;
}

/**
 * ページごとのHreflang情報
 */
interface PageHreflang {
  /** ページのURL */
  url: AbsoluteURL;
  /** ページの言語 */
  lang?: BCP47LanguageTag;
  /** 自己参照を含む代替言語リンク */
  links: HreflangLink[];
}

/**
 * Hreflang生成結果
 */
interface HreflangGenerationResult {
  /** 生成日時 */
  generated: string;
  /** ページごとのHreflang情報 */
  pages: PageHreflang[];
  /** 検証結果 */
  validation: {
    /** 検証成功フラグ */
    success: boolean;
    /** 警告メッセージ */
    warnings: string[];
    /** エラーメッセージ */
    errors: string[];
  };
}

/**
 * BCP47言語タグの妥当性検証
 */
function validateBCP47(lang: string): { valid: boolean; message?: string } {
  if (!isBCP47LanguageTag(lang)) {
    return {
      valid: false,
      message: `Invalid BCP47 language tag: ${lang}. Must be one of the supported language tags.`
    };
  }

  // 基本フォーマットチェック（追加の厳密性）
  if (lang !== 'x-default') {
    const parts = lang.split('-');
    if (parts.length > 3) {
      return {
        valid: false,
        message: `BCP47 tag too complex: ${lang}. Maximum 3 parts supported.`
      };
    }

    // 言語コード（最初の部分）は2-3文字
    const langCode = parts[0];
    if (!/^[a-z]{2,3}$/.test(langCode)) {
      return {
        valid: false,
        message: `Invalid language code in BCP47 tag: ${langCode} in ${lang}`
      };
    }

    // 地域コード（2番目の部分）は2文字の大文字
    if (parts.length >= 2) {
      const regionCode = parts[1];
      if (!/^[A-Z]{2}$/.test(regionCode)) {
        return {
          valid: false,
          message: `Invalid region code in BCP47 tag: ${regionCode} in ${lang}`
        };
      }
    }
  }

  return { valid: true };
}

/**
 * x-defaultルールの検証
 * x-defaultは「デフォルト言語のトップURLのみ」に付与
 */
function validateXDefaultRules(pages: PageHreflang[], database: URLSourceDatabase): string[] {
  const warnings: string[] = [];

  // x-defaultを持つページを探す
  const xDefaultPages = pages.filter(page =>
    page.links.some(link => link.hreflang === 'x-default')
  );

  if (xDefaultPages.length === 0) {
    warnings.push('No x-default hreflang found. Consider adding x-default for better international SEO.');
    return warnings;
  }

  // x-defaultは1つのURLのみに付与されるべき
  const xDefaultUrls = new Set<string>();
  xDefaultPages.forEach(page => {
    page.links.forEach(link => {
      if (link.hreflang === 'x-default') {
        xDefaultUrls.add(link.href);
      }
    });
  });

  if (xDefaultUrls.size > 1) {
    warnings.push(`Multiple URLs with x-default found: ${Array.from(xDefaultUrls).join(', ')}. x-default should point to one canonical default URL.`);
  }

  // デフォルト言語のトップレベルURLかチェック
  const defaultLang = database.defaultLang;
  const topLevelPages = pages.filter(page => {
    try {
      const url = new URL(page.url);
      const pathSegments = url.pathname.split('/').filter(segment => segment.length > 0);
      return pathSegments.length <= 1; // ルートまたは1階層のみ
    } catch {
      return false;
    }
  });

  const xDefaultInTopLevel = topLevelPages.some(page =>
    page.links.some(link => link.hreflang === 'x-default')
  );

  if (!xDefaultInTopLevel) {
    warnings.push('x-default should be assigned to top-level URLs for better SEO practices.');
  }

  return warnings;
}

/**
 * 相互参照完全性の検証
 * 自己参照を含む相互参照完全性チェック（抜けがあるペアは警告）
 */
function validateCrossReferences(pages: PageHreflang[]): string[] {
  const warnings: string[] = [];
  const urlToPage = new Map<string, PageHreflang>();

  // URLマップを構築
  pages.forEach(page => {
    urlToPage.set(page.url, page);
  });

  for (const page of pages) {
    // 自己参照チェック
    const selfReference = page.links.find(link => link.href === page.url);
    if (!selfReference) {
      warnings.push(`Missing self-reference for ${page.url}. Each page should include itself in hreflang links.`);
    } else if (page.lang && selfReference.hreflang !== page.lang) {
      warnings.push(`Self-reference language mismatch for ${page.url}. Expected ${page.lang}, got ${selfReference.hreflang}.`);
    }

    // 各代替言語への相互参照チェック
    for (const link of page.links) {
      if (link.href === page.url) continue; // 自己参照はスキップ

      const targetPage = urlToPage.get(link.href);
      if (!targetPage) {
        warnings.push(`Target page not found for hreflang link: ${link.href} referenced from ${page.url}`);
        continue;
      }

      // 相互参照の存在確認
      const backReference = targetPage.links.find(backLink => backLink.href === page.url);
      if (!backReference) {
        warnings.push(`Missing back-reference: ${link.href} does not link back to ${page.url}. Hreflang should be bidirectional.`);
      } else if (page.lang && backReference.hreflang !== page.lang) {
        warnings.push(`Back-reference language mismatch: ${link.href} links to ${page.url} with hreflang="${backReference.hreflang}", expected "${page.lang}".`);
      }
    }

    // 重複言語チェック
    const langCounts = new Map<string, number>();
    page.links.forEach(link => {
      const count = langCounts.get(link.hreflang) || 0;
      langCounts.set(link.hreflang, count + 1);
    });

    for (const [lang, count] of langCounts) {
      if (count > 1) {
        warnings.push(`Duplicate hreflang "${lang}" found for ${page.url}. Each language should appear only once.`);
      }
    }
  }

  return warnings;
}

/**
 * Canonical URL とhreflang整合性チェック
 * 1スロット=1言語1URL の確認
 */
function validateCanonicalConsistency(pages: PageHreflang[]): string[] {
  const warnings: string[] = [];
  const langToUrls = new Map<string, Set<string>>();

  // 言語ごとのURL収集
  pages.forEach(page => {
    page.links.forEach(link => {
      if (!langToUrls.has(link.hreflang)) {
        langToUrls.set(link.hreflang, new Set());
      }
      langToUrls.get(link.hreflang)!.add(link.href);
    });
  });

  // 1言語に複数URLが割り当てられていないかチェック
  for (const [lang, urls] of langToUrls) {
    if (urls.size > 1) {
      warnings.push(`Multiple URLs found for language "${lang}": ${Array.from(urls).join(', ')}. Each language should have one canonical URL per content slot.`);
    }
  }

  return warnings;
}

/**
 * URLSourceDatabaseからHreflang情報を生成
 */
function generateHreflang(database: URLSourceDatabase): HreflangGenerationResult {
  const pages: PageHreflang[] = [];
  const warnings: string[] = [];
  const errors: string[] = [];

  for (const entry of database.urls) {
    try {
      // URL妥当性チェック
      if (!isAbsoluteURL(entry.loc)) {
        errors.push(`Invalid URL: ${entry.loc}`);
        continue;
      }

      // 言語タグ妥当性チェック
      if (entry.lang) {
        const langValidation = validateBCP47(entry.lang);
        if (!langValidation.valid) {
          errors.push(`${langValidation.message} in entry: ${entry.loc}`);
          continue;
        }
      }

      const links: HreflangLink[] = [];

      // 自己参照を追加
      if (entry.lang) {
        links.push({
          hreflang: entry.lang,
          href: entry.loc
        });
      }

      // 代替言語リンクを追加
      if (entry.alternates) {
        for (const alt of entry.alternates) {
          // 代替言語の妥当性チェック
          const altLangValidation = validateBCP47(alt.lang);
          if (!altLangValidation.valid) {
            warnings.push(`${altLangValidation.message} in alternate for ${entry.loc}`);
            continue;
          }

          if (!isAbsoluteURL(alt.loc)) {
            warnings.push(`Invalid alternate URL: ${alt.loc} for ${entry.loc}`);
            continue;
          }

          links.push({
            hreflang: alt.lang,
            href: alt.loc
          });
        }
      }

      // x-defaultルールの適用
      // x-defaultは明示的に代替に含まれている場合のみ追加
      const hasXDefault = entry.alternates?.some(alt => alt.lang === 'x-default') ||
                         entry.lang === 'x-default';

      pages.push({
        url: entry.loc,
        lang: entry.lang,
        links: links.sort((a, b) => {
          // x-defaultを最初に、その後アルファベット順
          if (a.hreflang === 'x-default') return -1;
          if (b.hreflang === 'x-default') return 1;
          return a.hreflang.localeCompare(b.hreflang);
        })
      });

    } catch (error) {
      errors.push(`Error processing entry ${entry.loc}: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // 検証実行
  warnings.push(...validateXDefaultRules(pages, database));
  warnings.push(...validateCrossReferences(pages));
  warnings.push(...validateCanonicalConsistency(pages));

  return {
    generated: new Date().toISOString(),
    pages,
    validation: {
      success: errors.length === 0,
      warnings,
      errors
    }
  };
}

/**
 * HTML形式での出力
 */
function generateHTML(result: HreflangGenerationResult): string {
  const lines: string[] = [];

  lines.push('<!DOCTYPE html>');
  lines.push('<html lang="en">');
  lines.push('<head>');
  lines.push('    <meta charset="UTF-8">');
  lines.push('    <meta name="viewport" content="width=device-width, initial-scale=1.0">');
  lines.push('    <title>Hreflang Links Reference</title>');
  lines.push('    <style>');
  lines.push('        body { font-family: Arial, sans-serif; margin: 20px; }');
  lines.push('        .page { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }');
  lines.push('        .url { font-weight: bold; color: #0066cc; }');
  lines.push('        .links { margin: 10px 0; }');
  lines.push('        .link { display: block; margin: 2px 0; font-family: monospace; }');
  lines.push('        .warning { color: #ff8800; }');
  lines.push('        .error { color: #cc0000; }');
  lines.push('    </style>');
  lines.push('</head>');
  lines.push('<body>');
  lines.push('    <h1>Hreflang Links Reference</h1>');
  lines.push(`    <p>Generated: ${result.generated}</p>`);

  // 検証結果
  if (result.validation.errors.length > 0) {
    lines.push('    <h2 class="error">Errors</h2>');
    lines.push('    <ul>');
    result.validation.errors.forEach(error => {
      lines.push(`        <li class="error">${escapeHtml(error)}</li>`);
    });
    lines.push('    </ul>');
  }

  if (result.validation.warnings.length > 0) {
    lines.push('    <h2 class="warning">Warnings</h2>');
    lines.push('    <ul>');
    result.validation.warnings.forEach(warning => {
      lines.push(`        <li class="warning">${escapeHtml(warning)}</li>`);
    });
    lines.push('    </ul>');
  }

  // ページごとのHreflang
  lines.push('    <h2>Hreflang Links by Page</h2>');
  result.pages.forEach(page => {
    lines.push('    <div class="page">');
    lines.push(`        <div class="url">${escapeHtml(page.url)}</div>`);
    if (page.lang) {
      lines.push(`        <div>Page Language: ${page.lang}</div>`);
    }
    lines.push('        <div class="links">');
    page.links.forEach(link => {
      lines.push(`            <div class="link">&lt;link rel="alternate" hreflang="${link.hreflang}" href="${escapeHtml(link.href)}" /&gt;</div>`);
    });
    lines.push('        </div>');
    lines.push('    </div>');
  });

  lines.push('</body>');
  lines.push('</html>');

  return lines.join('\n');
}

/**
 * JSON形式での出力
 */
function generateJSON(result: HreflangGenerationResult): string {
  return JSON.stringify(result, null, 2);
}

/**
 * XML形式での出力
 */
function generateXML(result: HreflangGenerationResult): string {
  const lines: string[] = [];

  lines.push('<?xml version="1.0" encoding="UTF-8"?>');
  lines.push(`<hreflang generated="${result.generated}">`);

  // 検証結果
  lines.push('  <validation>');
  lines.push(`    <success>${result.validation.success}</success>`);

  if (result.validation.errors.length > 0) {
    lines.push('    <errors>');
    result.validation.errors.forEach(error => {
      lines.push(`      <error>${escapeXml(error)}</error>`);
    });
    lines.push('    </errors>');
  }

  if (result.validation.warnings.length > 0) {
    lines.push('    <warnings>');
    result.validation.warnings.forEach(warning => {
      lines.push(`      <warning>${escapeXml(warning)}</warning>`);
    });
    lines.push('    </warnings>');
  }

  lines.push('  </validation>');

  // ページ情報
  lines.push('  <pages>');
  result.pages.forEach(page => {
    const langAttr = page.lang ? ` lang="${page.lang}"` : '';
    lines.push(`    <page url="${escapeXml(page.url)}"${langAttr}>`);
    page.links.forEach(link => {
      lines.push(`      <link hreflang="${link.hreflang}" href="${escapeXml(link.href)}" />`);
    });
    lines.push('    </page>');
  });
  lines.push('  </pages>');

  lines.push('</hreflang>');

  return lines.join('\n');
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

/**
 * XMLエスケープ
 */
function escapeXml(unsafe: string): string {
  return unsafe
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

/**
 * メイン処理
 */
function main() {
  try {
    console.log('Building hreflang links...');

    // 入力ファイルの読み込み
    const inputPath = resolve(process.cwd(), 'scripts/url-source.json');
    const inputData = readFileSync(inputPath, 'utf8');

    let database: URLSourceDatabase;
    try {
      database = JSON.parse(inputData) as URLSourceDatabase;
    } catch (error) {
      throw new Error(`Failed to parse URL source JSON: ${error instanceof Error ? error.message : String(error)}`);
    }

    // 基本妥当性チェック
    if (!database.urls || !Array.isArray(database.urls)) {
      throw new Error('Invalid URL source format: missing or invalid urls array');
    }

    console.log(`Processing ${database.urls.length} URL entries...`);

    // Hreflang生成
    const result = generateHreflang(database);

    // 出力ディレクトリ作成
    const outputDir = resolve(process.cwd(), 'public');
    mkdirSync(outputDir, { recursive: true });

    // 各形式での出力
    const htmlOutput = generateHTML(result);
    const jsonOutput = generateJSON(result);
    const xmlOutput = generateXML(result);

    writeFileSync(resolve(outputDir, 'hreflang.html'), htmlOutput);
    writeFileSync(resolve(outputDir, 'hreflang.json'), jsonOutput);
    writeFileSync(resolve(outputDir, 'hreflang.xml'), xmlOutput);

    // 結果レポート
    console.log('\n📊 Hreflang Generation Results:');
    console.log(`   Pages processed: ${result.pages.length}`);
    console.log(`   Total hreflang links: ${result.pages.reduce((sum, page) => sum + page.links.length, 0)}`);

    if (result.validation.errors.length > 0) {
      console.log(`\n❌ Errors (${result.validation.errors.length}):`);
      result.validation.errors.forEach(error => console.log(`   - ${error}`));
    }

    if (result.validation.warnings.length > 0) {
      console.log(`\n⚠️  Warnings (${result.validation.warnings.length}):`);
      result.validation.warnings.forEach(warning => console.log(`   - ${warning}`));
    }

    console.log('\n📁 Output files:');
    console.log(`   - public/hreflang.html (${htmlOutput.length} bytes)`);
    console.log(`   - public/hreflang.json (${jsonOutput.length} bytes)`);
    console.log(`   - public/hreflang.xml (${xmlOutput.length} bytes)`);

    // x-default情報の表示
    const xDefaultPages = result.pages.filter(page =>
      page.links.some(link => link.hreflang === 'x-default')
    );

    if (xDefaultPages.length > 0) {
      console.log('\n🌍 x-default assignments:');
      xDefaultPages.forEach(page => {
        const xDefaultLink = page.links.find(link => link.hreflang === 'x-default');
        if (xDefaultLink) {
          console.log(`   - ${xDefaultLink.href} (from ${page.url})`);
        }
      });
    }

    if (result.validation.success) {
      console.log('\n✅ Hreflang generation completed successfully!');
      process.exit(0);
    } else {
      console.log('\n❌ Hreflang generation completed with errors. Please check the output above.');
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Error building hreflang:');
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

// スクリプトが直接実行された場合のみmainを実行
if (require.main === module) {
  main();
}
