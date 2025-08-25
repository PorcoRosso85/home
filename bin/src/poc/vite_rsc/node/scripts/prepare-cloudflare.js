#!/usr/bin/env node
/**
 * Cloudflare Workers用のビルド準備スクリプト
 * Vite RSCのビルド結果をCloudflare Workers用に変換
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

// 1. Vite RSCビルドを実行
console.log('Building Vite RSC...');
execSync('npm run build', { stdio: 'inherit' });

// 2. Cloudflare Workers用エントリーポイント作成
const workerEntry = `
// Cloudflare Workers Entry Point
import { renderToReadableStream } from 'react-dom/server.edge';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // 静的アセットの処理
    if (url.pathname.startsWith('/assets/')) {
      // CDNまたはR2から配信
      return new Response('Not Found', { status: 404 });
    }
    
    // RSC/SSRの処理
    try {
      // TODO: 実際のRSCハンドラーの実装
      const html = \`
        <!DOCTYPE html>
        <html>
          <head>
            <title>Vite RSC on Cloudflare</title>
          </head>
          <body>
            <div id="root">
              <h1>Vite RSC on Cloudflare Workers</h1>
              <p>Path: \${url.pathname}</p>
            </div>
          </body>
        </html>
      \`;
      
      return new Response(html, {
        headers: {
          'content-type': 'text/html;charset=UTF-8',
        },
      });
    } catch (error) {
      return new Response('Internal Server Error', { status: 500 });
    }
  },
};
`;

// 3. ワーカーファイルを作成
fs.mkdirSync('dist-cloudflare', { recursive: true });
fs.writeFileSync('dist-cloudflare/worker.js', workerEntry);

// 4. wrangler.toml生成
const wranglerConfig = `
name = "vite-rsc-app"
main = "dist-cloudflare/worker.js"
compatibility_date = "2024-01-01"

[site]
bucket = "./dist/client"

[[routes]]
pattern = "example.com/*"
zone_name = "example.com"

[env.production]
name = "vite-rsc-app-production"
`;

fs.writeFileSync('wrangler.toml', wranglerConfig.trim());

console.log('✅ Cloudflare Workers準備完了');
console.log('📝 生成されたファイル:');
console.log('  - dist-cloudflare/worker.js');
console.log('  - wrangler.toml');
console.log('\n次のステップ:');
console.log('  1. wrangler.tomlのroutes設定を更新');
console.log('  2. wrangler deployでデプロイ');