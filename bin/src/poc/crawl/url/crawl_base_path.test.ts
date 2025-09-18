import { assertEquals } from "https://deno.land/std@0.208.0/testing/asserts.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { URLCrawler } from "./crawl.ts";

Deno.test("URLCrawler - デフォルトで開始URLのパス配下のみクロール", async () => {
  const testPort = 8089;
  const baseUrl = `http://localhost:${testPort}/docs/guide/`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    // /docs/guide/ ページ
    if (url.pathname === "/docs/guide/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/guide/intro">Guide Intro</a>
            <a href="/docs/guide/advanced">Guide Advanced</a>
            <a href="/docs/api/reference">API Reference</a>
            <a href="/blog/news">Blog News</a>
            <a href="/">Home</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    // /docs/guide/ 配下のページ
    if (url.pathname.startsWith("/docs/guide/")) {
      return new Response(`
        <html>
          <body>
            <h1>${url.pathname}</h1>
            <a href="/docs/guide/tips">More Tips</a>
            <a href="/docs/api/v2">API v2</a>
            <a href="/about">About</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    // その他のページ
    return new Response(`
      <html>
        <body>
          <h1>${url.pathname}</h1>
          <a href="/docs/guide/return">Back to Guide</a>
        </body>
      </html>
    `, { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // デフォルト設定でクロール（matchオプションなし）
    const crawler = new URLCrawler(baseUrl);
    const results = await crawler.crawl();
    
    // クロールされたURLを取得
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("Base URL path:", new URL(baseUrl).pathname);
    console.log("Crawled URLs:", crawledUrls);
    
    // /docs/guide/ 配下のページのみがクロールされることを確認
    const withinBasePath = crawledUrls.filter(path => path.startsWith("/docs/guide/"));
    const outsideBasePath = crawledUrls.filter(path => !path.startsWith("/docs/guide/"));
    
    // 開始パス配下のページが存在することを確認
    assertEquals(withinBasePath.length > 0, true, "Should crawl pages within base path");
    
    // 開始パス配下以外のページがクロールされていないことを確認
    assertEquals(outsideBasePath.length, 0, `Should not crawl pages outside base path by default, but found: ${outsideBasePath.join(", ")}`);
    
    // 具体的に期待されるページを確認
    assertEquals(crawledUrls.includes("/docs/guide/"), true);
    assertEquals(crawledUrls.includes("/docs/guide/intro"), true);
    assertEquals(crawledUrls.includes("/docs/guide/advanced"), true);
    assertEquals(crawledUrls.includes("/docs/guide/tips"), true);
    
    // 期待されないページを確認
    assertEquals(crawledUrls.includes("/docs/api/reference"), false, "Should not crawl /docs/api/");
    assertEquals(crawledUrls.includes("/blog/news"), false, "Should not crawl /blog/");
    assertEquals(crawledUrls.includes("/"), false, "Should not crawl root");
    
  } finally {
    abortController.abort();
  }
});

Deno.test("URLCrawler - ルートURLの場合は全体をクロール", async () => {
  const testPort = 8090;
  const baseUrl = `http://localhost:${testPort}/`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/intro">Docs</a>
            <a href="/blog/news">Blog</a>
            <a href="/about">About</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`
      <html>
        <body>
          <h1>${url.pathname}</h1>
        </body>
      </html>
    `, { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // ルートURLからクロール
    const crawler = new URLCrawler(baseUrl);
    const results = await crawler.crawl();
    
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    // ルートURLの場合は全てのパスがクロール可能
    assertEquals(crawledUrls.includes("/"), true);
    assertEquals(crawledUrls.includes("/docs/intro"), true);
    assertEquals(crawledUrls.includes("/blog/news"), true);
    assertEquals(crawledUrls.includes("/about"), true);
    
  } finally {
    abortController.abort();
  }
});