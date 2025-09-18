#!/usr/bin/env node

/**
 * RSC Production Server
 * ビルド済みのRSC/SSR/Clientアセットを使用してサーバーを起動
 */

import { createServer } from 'http';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ビルド済みモジュールのインポート
const rscHandler = (await import('./dist/rsc/index.js')).default;
const { handleSsr } = await import('./dist/ssr/index.js');

const PORT = process.env.PORT || 3000;

const server = createServer(async (req, res) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  
  try {
    // Static assets (Client-side JavaScript)
    if (req.url?.startsWith('/assets/')) {
      const filePath = join(__dirname, 'dist/client', req.url);
      try {
        const content = readFileSync(filePath);
        const contentType = req.url.endsWith('.js') ? 'application/javascript' : 
                          req.url.endsWith('.css') ? 'text/css' : 
                          'application/octet-stream';
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content);
        return;
      } catch (e) {
        res.writeHead(404);
        res.end('Not Found');
        return;
      }
    }
    
    // RSC Stream Request (.rsc endpoint)
    if (req.url?.endsWith('.rsc')) {
      console.log('  → RSC環境: React → RSC Stream');
      const request = new Request(`http://localhost:${PORT}${req.url}`, {
        method: req.method,
        headers: req.headers,
      });
      
      const response = await rscHandler(request);
      
      res.writeHead(response.status, {
        'Content-Type': 'text/x-component;charset=utf-8',
        'Cache-Control': 'no-cache',
      });
      
      if (response.body) {
        const reader = response.body.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          res.write(value);
        }
      }
      res.end();
      return;
    }
    
    // HTML Request (default)
    console.log('  → RSC環境: React → RSC Stream');
    const request = new Request(`http://localhost:${PORT}${req.url}`, {
      method: req.method,
      headers: req.headers,
    });
    
    // Step 1: RSC環境でReact VDOMをRSC Streamに変換
    const rscResponse = await rscHandler(request);
    
    if (rscResponse.headers.get('Content-Type')?.includes('text/html')) {
      // RSCハンドラーが直接HTMLを返す場合
      res.writeHead(rscResponse.status, {
        'Content-Type': 'text/html',
      });
      
      if (rscResponse.body) {
        const reader = rscResponse.body.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          res.write(value);
        }
      }
      res.end();
    } else {
      // Step 2: SSR環境でRSC StreamをHTMLに変換
      console.log('  → SSR環境: RSC Stream → HTML');
      
      // ブートストラップスクリプトの生成
      const bootstrapScriptContent = `
        <script type="module">
          import { hydrateRoot } from '/assets/index-DVUYCpzz.js';
          // Hydration logic would go here
        </script>
      `;
      
      const htmlStream = await handleSsr(rscResponse.body, bootstrapScriptContent);
      
      res.writeHead(200, {
        'Content-Type': 'text/html',
      });
      
      const reader = htmlStream.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(value);
      }
      res.end();
      
      console.log('  → Client環境: HTMLをブラウザに送信（ハイドレーション待機）');
    }
    
  } catch (error) {
    console.error('Server error:', error);
    res.writeHead(500);
    res.end('Internal Server Error');
  }
});

server.listen(PORT, () => {
  console.log(`
╔════════════════════════════════════════════╗
║         RSC Production Server              ║
╠════════════════════════════════════════════╣
║  Server running at:                        ║
║  http://localhost:${PORT}                     ║
║                                            ║
║  Endpoints:                                ║
║  - /        : HTML (SSR)                   ║
║  - /.rsc    : RSC Stream                   ║
║  - /assets/* : Client JS/CSS               ║
║                                            ║
║  責務の流れ:                               ║
║  1. RSC: React → RSC Stream               ║
║  2. SSR: RSC Stream → HTML                ║
║  3. Client: HTML → Hydration              ║
╚════════════════════════════════════════════╝
  `);
});