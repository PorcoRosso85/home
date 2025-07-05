import { assertEquals } from "https://deno.land/std@0.208.0/testing/asserts.ts";
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { URLCrawler } from "./crawl.ts";

Deno.test("URLCrawler respects match patterns - only crawls matching paths", async () => {
  const testPort = 8086;
  const baseUrl = `http://localhost:${testPort}`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    // ルートページ
    if (url.pathname === "/") {
      return new Response(`
        <html>
          <body>
            <a href="/docs/intro">Docs Intro</a>
            <a href="/docs/api">Docs API</a>
            <a href="/blog/news">Blog News</a>
            <a href="/about">About</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    // /docs/配下のページ
    if (url.pathname.startsWith("/docs/")) {
      return new Response(`
        <html>
          <body>
            <h1>${url.pathname}</h1>
            <a href="/docs/advanced">Advanced Docs</a>
            <a href="/blog/update">Blog Update</a>
            <a href="/">Home</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    // その他のページ
    return new Response(`
      <html>
        <body>
          <h1>${url.pathname}</h1>
          <a href="/docs/guide">Docs Guide</a>
          <a href="/contact">Contact</a>
        </body>
      </html>
    `, { headers: { "content-type": "text/html" } });
  };

  const server = serve(handler, { port: testPort });

  try {
    // /docs/** パターンでクロール
    const crawler = new URLCrawler(baseUrl, {
      match: ["/docs/**"],
      sameHost: true,
    });
    
    const results = await crawler.crawl();
    
    // クロールされたURLを取得
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    // /docs/配下のページのみがクロールされることを確認
    const docsPages = crawledUrls.filter(path => path.startsWith("/docs/"));
    const nonDocsPages = crawledUrls.filter(path => !path.startsWith("/docs/"));
    
    // /docs/配下のページが存在することを確認
    assertEquals(docsPages.length > 0, true, "Should crawl at least one /docs/ page");
    
    // /docs/配下以外のページがクロールされていないことを確認
    assertEquals(nonDocsPages.length, 0, `Should not crawl non-/docs/ pages, but found: ${nonDocsPages.join(", ")}`);
    
    // 具体的にクロールされたページを確認
    console.log("Crawled pages:", crawledUrls);
    
  } finally {
    await server.shutdown();
  }
});

Deno.test("URLCrawler with multiple match patterns", async () => {
  const testPort = 8087;
  const baseUrl = `http://localhost:${testPort}`;
  
  const handler = (req: Request) => {
    const url = new URL(req.url);
    
    if (url.pathname === "/") {
      return new Response(`
        <html>
          <body>
            <a href="/api/v1/users">API Users</a>
            <a href="/api/v2/posts">API Posts</a>
            <a href="/guide/intro">Guide Intro</a>
            <a href="/guide/advanced">Guide Advanced</a>
            <a href="/blog/news">Blog News</a>
          </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response(`
      <html>
        <body>
          <h1>${url.pathname}</h1>
          <a href="/">Home</a>
        </body>
      </html>
    `, { headers: { "content-type": "text/html" } });
  };

  const server = serve(handler, { port: testPort });

  try {
    // /api/** と /guide/** の両方を許可
    const crawler = new URLCrawler(baseUrl, {
      match: ["/api/**", "/guide/**"],
      sameHost: true,
    });
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    // /api/ と /guide/ のページがクロールされることを確認
    const apiPages = crawledUrls.filter(path => path.startsWith("/api/"));
    const guidePages = crawledUrls.filter(path => path.startsWith("/guide/"));
    const otherPages = crawledUrls.filter(path => 
      !path.startsWith("/api/") && !path.startsWith("/guide/")
    );
    
    assertEquals(apiPages.length > 0, true, "Should crawl /api/ pages");
    assertEquals(guidePages.length > 0, true, "Should crawl /guide/ pages");
    assertEquals(otherPages.length, 0, `Should not crawl other pages, but found: ${otherPages.join(", ")}`);
    
  } finally {
    await server.shutdown();
  }
});

Deno.test("URLCrawler without match patterns crawls all pages", async () => {
  const testPort = 8088;
  const baseUrl = `http://localhost:${testPort}`;
  
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

  const server = serve(handler, { port: testPort });

  try {
    // matchパターンなしでクロール
    const crawler = new URLCrawler(baseUrl, {
      sameHost: true,
    });
    
    const results = await crawler.crawl();
    const crawledUrls = results.map(r => new URL(r.url).pathname).sort();
    
    // すべてのパスがクロールされることを確認
    assertEquals(crawledUrls.includes("/"), true);
    assertEquals(crawledUrls.includes("/docs/intro"), true);
    assertEquals(crawledUrls.includes("/blog/news"), true);
    assertEquals(crawledUrls.includes("/about"), true);
    
  } finally {
    await server.shutdown();
  }
});