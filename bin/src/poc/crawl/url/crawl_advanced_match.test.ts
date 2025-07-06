import { assertEquals } from "https://deno.land/std@0.208.0/testing/asserts.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { URLCrawler } from "./crawl.ts";

Deno.test("URLCrawler - ベースパス制限と--matchのAND条件", async () => {
  const testPort = 8091;
  const baseUrl = `http://localhost:${testPort}/docs/`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/docs/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/guide/">Guide</a>
            <a href="/docs/api/">API</a>
            <a href="/docs/reference/">Reference</a>
            <a href="/blog/news">Blog</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    if (url.pathname.startsWith("/docs/")) {
      return new Response(`
        <html>
          <body>
            <h1>${url.pathname}</h1>
            <a href="/docs/guide/intro">Guide Intro</a>
            <a href="/docs/api/v2">API v2</a>
            <a href="/docs/reference/spec">Reference Spec</a>
            <a href="/api/external">External API</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`<html><body>${url.pathname}</body></html>`, 
      { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // ベースパス（/docs/）内で、かつ/api/を含むパスのみ
    const crawler = new URLCrawler(baseUrl, {
      match: ["/docs/api/**"],
    });
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("Crawled URLs:", crawledUrls);
    
    // 期待される動作：ベースパス（/docs/）内 AND matchパターン（/docs/api/**）
    assertEquals(crawledUrls.includes("/docs/"), true, "開始URLは含まれる");
    assertEquals(crawledUrls.includes("/docs/api/"), true, "/docs/api/は含まれる");
    assertEquals(crawledUrls.includes("/docs/api/v2"), true, "/docs/api/v2は含まれる");
    
    // 含まれないべきもの
    assertEquals(crawledUrls.includes("/docs/guide/"), false, "/docs/guide/は含まれない（matchパターン外）");
    assertEquals(crawledUrls.includes("/docs/reference/"), false, "/docs/reference/は含まれない（matchパターン外）");
    assertEquals(crawledUrls.includes("/api/external"), false, "/api/externalは含まれない（ベースパス外）");
    assertEquals(crawledUrls.includes("/blog/news"), false, "/blog/newsは含まれない（ベースパス外）");
    
  } finally {
    abortController.abort();
  }
});

Deno.test("URLCrawler - 相対パスmatchパターン", async () => {
  const testPort = 8092;
  const baseUrl = `http://localhost:${testPort}/docs/`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/docs/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/api/users">API Users</a>
            <a href="/docs/guide/api-usage">Guide API</a>
            <a href="/docs/reference/api">Reference API</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`<html><body>${url.pathname}</body></html>`, 
      { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // 相対パス "api/**" は /docs/api/** として解釈される
    const crawler = new URLCrawler(baseUrl, {
      match: ["api/**"],
    });
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("Relative pattern crawled:", crawledUrls);
    
    // /docs/配下の "api" を含むパスがマッチ
    assertEquals(crawledUrls.includes("/docs/api/users"), true, "api/usersは含まれる");
    assertEquals(crawledUrls.includes("/docs/guide/api-usage"), false, "guide/api-usageは含まれない（api/**にマッチしない）");
    assertEquals(crawledUrls.includes("/docs/reference/api"), false, "reference/apiは含まれない（api/**にマッチしない）");
    
  } finally {
    abortController.abort();
  }
});

Deno.test("URLCrawler - 否定パターン", async () => {
  const testPort = 8093;
  const baseUrl = `http://localhost:${testPort}/docs/`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/docs/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/guide/">Guide</a>
            <a href="/docs/test/">Test</a>
            <a href="/docs/api/">API</a>
            <a href="/docs/api/test">API Test</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`<html><body>${url.pathname}</body></html>`, 
      { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // "!**/test/**" と "!**/test" パターンでtestを含むパスを除外
    const crawler = new URLCrawler(baseUrl, {
      match: ["**", "!**/test/**", "!**/test"],
    });
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("Negation pattern crawled:", crawledUrls);
    
    // testを含まないパスは含まれる
    assertEquals(crawledUrls.includes("/docs/"), true);
    assertEquals(crawledUrls.includes("/docs/guide/"), true);
    assertEquals(crawledUrls.includes("/docs/api/"), true);
    
    // testを含むパスは除外される
    assertEquals(crawledUrls.includes("/docs/test/"), false, "/docs/test/は除外");
    assertEquals(crawledUrls.includes("/docs/api/test"), false, "/docs/api/testは除外");
    
  } finally {
    abortController.abort();
  }
});

Deno.test("URLCrawler - --with-rootオプション", async () => {
  const testPort = 8094;
  const baseUrl = `http://localhost:${testPort}/docs/`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/docs/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/guide/">Docs Guide</a>
            <a href="/api/v1/">API v1</a>
            <a href="/blog/news">Blog News</a>
            <a href="/">Home</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`<html><body>${url.pathname}</body></html>`, 
      { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // withRootでベースパス制限を解除
    const crawler = new URLCrawler(baseUrl, {
      withRoot: true,
    });
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("With root option:", crawledUrls);
    
    // すべてのパスがクロール可能
    assertEquals(crawledUrls.includes("/docs/"), true);
    assertEquals(crawledUrls.includes("/docs/guide/"), true);
    assertEquals(crawledUrls.includes("/api/v1/"), true, "/api/v1/も含まれる（ベースパス外）");
    assertEquals(crawledUrls.includes("/blog/news"), true, "/blog/newsも含まれる（ベースパス外）");
    assertEquals(crawledUrls.includes("/"), true, "ルートも含まれる");
    
  } finally {
    abortController.abort();
  }
});

Deno.test("URLCrawler - 末尾スラッシュなしURL", async () => {
  const testPort = 8095;
  const baseUrl = `http://localhost:${testPort}/docs`;  // 末尾スラッシュなし
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    // /docsは/docs/にリダイレクト（一般的な動作）
    if (url.pathname === "/docs") {
      return new Response(null, {
        status: 301,
        headers: { "Location": "/docs/" }
      });
    }
    
    if (url.pathname === "/docs/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/guide/">Guide</a>
            <a href="/docs-old/legacy">Legacy Docs</a>
            <a href="/documentation/new">New Documentation</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`<html><body>${url.pathname}</body></html>`, 
      { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // 末尾スラッシュなしでも/docs/配下として扱う
    const crawler = new URLCrawler(baseUrl);
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("No trailing slash URLs:", crawledUrls);
    
    // /docs/配下のみクロール
    assertEquals(crawledUrls.includes("/docs/"), true);
    assertEquals(crawledUrls.includes("/docs/guide/"), true);
    
    // /docs-oldや/documentationは含まれない（別パス）
    assertEquals(crawledUrls.includes("/docs-old/legacy"), false, "/docs-old/は別パス");
    assertEquals(crawledUrls.includes("/documentation/new"), false, "/documentation/は別パス");
    
  } finally {
    abortController.abort();
  }
});

Deno.test("URLCrawler - ファイルURLの扱い", async () => {
  const testPort = 8096;
  const baseUrl = `http://localhost:${testPort}/docs/index.html`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/docs/index.html") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/guide.html">Guide</a>
            <a href="/docs/api/">API Directory</a>
            <a href="/index.html">Root Index</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`<html><body>${url.pathname}</body></html>`, 
      { headers: { "content-type": "text/html" } });
  };

  const abortController = new AbortController();
  const serverPromise = serve(handler, { 
    port: testPort,
    signal: abortController.signal,
  });

  try {
    // .htmlで終わるURLは/docs/をベースパスとする
    const crawler = new URLCrawler(baseUrl);
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    console.log("File URL crawled:", crawledUrls);
    
    // /docs/配下のみクロール
    assertEquals(crawledUrls.includes("/docs/index.html"), true);
    assertEquals(crawledUrls.includes("/docs/guide.html"), true);
    assertEquals(crawledUrls.includes("/docs/api/"), true);
    
    // ルートのindex.htmlは含まれない
    assertEquals(crawledUrls.includes("/index.html"), false, "ルートのindex.htmlは含まれない");
    
  } finally {
    abortController.abort();
  }
});