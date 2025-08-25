#!/usr/bin/env node

/**
 * RSC 3環境の責務確認テストスクリプト
 * 
 * 各環境の責務:
 * - rsc: React Server Components のシリアライズ (React VDOM → RSC Stream)
 * - ssr: RSC Stream のデシリアライズとHTML生成 (RSC Stream → HTML)
 * - client: ブラウザでのハイドレーション (RSC Stream → DOM)
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync, existsSync, readdirSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('=== RSC 3環境の責務確認 ===\n');

// 1. RSC環境の確認
console.log('📦 RSC環境 (React Server Components)');
console.log('責務: React VDOM → RSC Stream のシリアライズ');
const rscIndexPath = join(__dirname, 'dist/rsc/index.js');
if (existsSync(rscIndexPath)) {
  const rscContent = readFileSync(rscIndexPath, 'utf-8');
  console.log('✅ RSCビルド成功');
  console.log(`  - ファイルサイズ: ${(rscContent.length / 1024).toFixed(2)} KB`);
  console.log(`  - renderToReadableStream含有: ${rscContent.includes('renderToReadableStream') ? '✅' : '❌'}`);
  
  // RSC環境の動的インポートテスト
  try {
    const rscModule = await import(rscIndexPath);
    console.log(`  - デフォルトエクスポート: ${typeof rscModule.default === 'function' ? '✅ function' : '❌'}`);
  } catch (e) {
    console.log(`  - モジュールロード: ⚠️ ブラウザ環境では実行不可`);
  }
} else {
  console.log('❌ RSCビルドが見つかりません');
}

console.log('\n📦 SSR環境 (Server-Side Rendering)');
console.log('責務: RSC Stream → HTML のレンダリング');
const ssrIndexPath = join(__dirname, 'dist/ssr/index.js');
if (existsSync(ssrIndexPath)) {
  const ssrContent = readFileSync(ssrIndexPath, 'utf-8');
  console.log('✅ SSRビルド成功');
  console.log(`  - ファイルサイズ: ${(ssrContent.length / 1024).toFixed(2)} KB`);
  console.log(`  - createFromReadableStream含有: ${ssrContent.includes('createFromReadableStream') ? '✅' : '❌'}`);
  console.log(`  - renderToReadableStream含有: ${ssrContent.includes('renderToReadableStream') ? '✅' : '❌'}`);
  
  // handleSsr関数の存在確認
  try {
    const ssrModule = await import(ssrIndexPath);
    console.log(`  - handleSsr関数: ${typeof ssrModule.handleSsr === 'function' ? '✅ function' : '❌'}`);
  } catch (e) {
    console.log(`  - モジュールロード: ⚠️ ブラウザ環境では実行不可`);
  }
} else {
  console.log('❌ SSRビルドが見つかりません');
}

console.log('\n📦 Client環境 (Browser)');
console.log('責務: RSC Stream → DOM のハイドレーション');
const clientIndexPath = join(__dirname, 'dist/client/assets');
if (existsSync(clientIndexPath)) {
  const files = readdirSync(clientIndexPath);
  const jsFiles = files.filter(f => f.endsWith('.js'));
  console.log('✅ Clientビルド成功');
  console.log(`  - JSファイル数: ${jsFiles.length}`);
  
  jsFiles.forEach(file => {
    const content = readFileSync(join(clientIndexPath, file), 'utf-8');
    console.log(`  - ${file}: ${(content.length / 1024).toFixed(2)} KB`);
    if (content.includes('hydrateRoot')) {
      console.log(`    → hydrateRoot含有: ✅`);
    }
    if (content.includes('createFromReadableStream')) {
      console.log(`    → createFromReadableStream含有: ✅`);
    }
  });
} else {
  console.log('❌ Clientビルドが見つかりません');
}

console.log('\n=== 責務の流れ ===');
console.log('1. RSC: React Component → RSC Stream (シリアライズ)');
console.log('2. SSR: RSC Stream → HTML (サーバーレンダリング)');
console.log('3. Client: RSC Stream → DOM (ハイドレーション)');