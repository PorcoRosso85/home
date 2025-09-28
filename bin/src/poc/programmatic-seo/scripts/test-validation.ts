#!/usr/bin/env node
/**
 * Phase 1.1 - バリデーション機能のテスト
 *
 * 実装した機能の動作確認とサンプルデータの検証
 */

import { readFile } from 'fs/promises';
import { join } from 'path';
import {
  validateURL,
  validateLanguageTag,
  validateISO8601DateTime,
  validateURLSourceEntry,
  validateURLSourceDatabase,
  normalizeURL,
  DEFAULT_URL_NORMALIZATION,
  STRICT_URL_NORMALIZATION
} from '../packages/i18n/validation.js';

import {
  getLanguageFallbackChain,
  selectBestLanguage,
  getLanguageDisplayName,
  DEFAULT_I18N_CONFIG
} from '../packages/i18n/locales.js';

async function main() {
  console.log('🧪 Phase 1.1 バリデーション機能テスト\n');

  // 1. URL正規化テスト
  console.log('1. URL正規化テスト');
  console.log('==================');

  const testUrls = [
    'https://example.com/page/?utm_source=google#section',
    'http://example.com:80/path/',
    'https://example.com:443/page',
    'https://example.com/page',
    '/relative/path',  // エラーケース
    'ftp://example.com/file'  // エラーケース
  ];

  for (const url of testUrls) {
    try {
      const normalized = normalizeURL(url, DEFAULT_URL_NORMALIZATION);
      console.log(`✅ "${url}" → "${normalized}"`);
    } catch (error) {
      console.log(`❌ "${url}" → エラー: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  console.log('\n2. 言語タグバリデーション');
  console.log('=========================');

  const testLangs = ['en', 'ja-JP', 'x-default', 'invalid-lang', 'zh-CN'];

  for (const lang of testLangs) {
    const result = validateLanguageTag(lang);
    console.log(`${result.valid ? '✅' : '❌'} "${lang}": ${result.valid ? '有効' : result.errors?.[0]?.message}`);
  }

  console.log('\n3. ISO8601日時バリデーション');
  console.log('=============================');

  const testDatetimes = [
    '2024-03-15T10:30:00.000Z',
    '2024-03-15T10:30:00Z',
    '2024-13-45T25:70:00Z',  // 無効な日付
    '2024-03-15T10:30:00',   // タイムゾーンなし
    '2024-03-15 10:30:00'    // 無効な形式
  ];

  for (const datetime of testDatetimes) {
    const result = validateISO8601DateTime(datetime);
    console.log(`${result.valid ? '✅' : '❌'} "${datetime}": ${result.valid ? '有効' : result.errors?.[0]?.message}`);
  }

  console.log('\n4. 言語フォールバック機能');
  console.log('=========================');

  const testLangForFallback = ['en-US', 'ja-JP', 'zh-CN'];

  for (const lang of testLangForFallback) {
    const chain = getLanguageFallbackChain(lang as any, DEFAULT_I18N_CONFIG);
    console.log(`🔗 ${lang}: ${chain.join(' → ')}`);
  }

  console.log('\n5. 言語選択機能');
  console.log('================');

  const preferredLangs = [['zh-TW', 'zh', 'en'], ['de-DE', 'fr'], ['invalid-lang']];

  for (const preferred of preferredLangs) {
    const selected = selectBestLanguage(preferred as any, DEFAULT_I18N_CONFIG);
    console.log(`🎯 [${preferred.join(', ')}] → ${selected} (${getLanguageDisplayName(selected)})`);
  }

  console.log('\n6. URL-source.jsonバリデーション');
  console.log('=================================');

  try {
    const scriptPath = join(process.cwd(), 'scripts', 'url-source.json');
    const data = await readFile(scriptPath, 'utf-8');
    const parsed = JSON.parse(data);

    const result = validateURLSourceDatabase(parsed, STRICT_URL_NORMALIZATION);

    if (result.valid) {
      console.log('✅ url-source.json: バリデーション成功');
      console.log(`   - バージョン: ${result.data?.version}`);
      console.log(`   - エントリ数: ${result.data?.urls.length}`);
      console.log(`   - デフォルト言語: ${result.data?.defaultLang}`);
      console.log(`   - 生成日時: ${result.data?.generated}`);
    } else {
      console.log('❌ url-source.json: バリデーション失敗');
      result.errors?.forEach(error => {
        console.log(`   - ${error.path}: ${error.message}`);
      });
    }
  } catch (error) {
    console.log(`❌ ファイル読み込みエラー: ${error instanceof Error ? error.message : String(error)}`);
  }

  console.log('\n7. URLエントリバリデーション（サンプル）');
  console.log('=======================================');

  const sampleEntry = {
    loc: 'https://example.com/test-page',
    lastmod: '2024-03-15T10:00:00.000Z',
    lang: 'en',
    alternates: [
      { lang: 'ja', loc: 'https://example.com/ja/test-page' },
      { lang: 'x-default', loc: 'https://example.com/test-page' }
    ]
  };

  const entryResult = validateURLSourceEntry(sampleEntry);
  console.log(`${entryResult.valid ? '✅' : '❌'} サンプルエントリ: ${entryResult.valid ? 'バリデーション成功' : 'バリデーション失敗'}`);

  if (!entryResult.valid) {
    entryResult.errors?.forEach(error => {
      console.log(`   - ${error.path}: ${error.message}`);
    });
  }

  console.log('\n🎉 テスト完了');
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('テスト実行エラー:', error);
    process.exit(1);
  });
}