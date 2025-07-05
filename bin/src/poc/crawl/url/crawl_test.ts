import { assertEquals, assertExists, assert } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { URLCrawler, parseArgs, type CrawlOptions, type CrawlResult } from "./crawl.ts";

// URLクローラーの仕様をテストとして定義
// 実装前のTDD Redフェーズ

Deno.test("URLCrawler - 基本機能", async (t) => {
  await t.step("単一URLからリンクを抽出できる", async () => {
    const crawler = new URLCrawler("https://example.com");
    const results = await crawler.crawl();
    
    assertEquals(results.length, 1);
    assertEquals(results[0].url, "https://example.com");
    assert(Array.isArray(results[0].links));
  });

  await t.step("HTMLページのみを処理する", async () => {
    const crawler = new URLCrawler("https://example.com/image.jpg");
    const results = await crawler.crawl();
    
    assertEquals(results.length, 0); // 画像URLは処理されない
  });

  await t.step("相対URLを絶対URLに変換する", async () => {
    const crawler = new URLCrawler("https://example.com/page");
    const results = await crawler.crawl();
    
    // 相対リンク "/about" が "https://example.com/about" に変換される
    const links = results[0].links;
    assert(links.every(link => link.startsWith("http")));
  });
});

Deno.test("URLCrawler - 同一ホスト制限", async (t) => {
  await t.step("デフォルトでは同一ホストのみクロールする", async () => {
    const crawler = new URLCrawler("https://example.com");
    const results = await crawler.crawl();
    
    const allUrls = results.map(r => r.url);
    assert(allUrls.every(url => new URL(url).host === "example.com"));
  });

  await t.step("sameHost=falseで外部ホストもクロール可能", async () => {
    const crawler = new URLCrawler("https://example.com", { sameHost: false });
    const results = await crawler.crawl();
    
    const hosts = new Set(results.map(r => new URL(r.url).host));
    assert(hosts.size > 1); // 複数のホストが含まれる
  });
});

Deno.test("URLCrawler - パターンマッチング", async (t) => {
  await t.step("matchパターンに一致するURLのみクロールする", async () => {
    const crawler = new URLCrawler("https://docs.example.com", {
      match: ["/api/**", "/guide/**"]
    });
    const results = await crawler.crawl();
    
    const paths = results.map(r => new URL(r.url).pathname);
    assert(paths.every(path => 
      path.startsWith("/api/") || path.startsWith("/guide/")
    ));
  });

  await t.step("matchパターンが空の場合は全URLをクロール", async () => {
    const crawler = new URLCrawler("https://example.com", { match: [] });
    const results = await crawler.crawl();
    
    assert(results.length > 0);
  });

  await t.step("グロブパターンをサポートする", async () => {
    const crawler = new URLCrawler("https://example.com", {
      match: ["/blog/*/comments"]
    });
    const results = await crawler.crawl();
    
    // /blog/post1/comments, /blog/post2/comments などにマッチ
    const paths = results.map(r => new URL(r.url).pathname);
    assert(paths.every(path => /^\/blog\/[^\/]+\/comments$/.test(path)));
  });
});

Deno.test("URLCrawler - 並行処理", async (t) => {
  await t.step("concurrencyオプションで並行数を制御できる", async () => {
    const startTime = Date.now();
    const crawler = new URLCrawler("https://slow-example.com", {
      concurrency: 5
    });
    const results = await crawler.crawl();
    const duration = Date.now() - startTime;
    
    // 5並行なら10ページが2秒程度で完了するはず（1ページ1秒と仮定）
    assert(results.length >= 10);
    assert(duration < 3000);
  });

  await t.step("デフォルトの並行数は3", async () => {
    const crawler = new URLCrawler("https://example.com");
    assertEquals(crawler.options.concurrency, 3);
  });
});

Deno.test("URLCrawler - 制限機能", async (t) => {
  await t.step("limitオプションでクロール数を制限できる", async () => {
    const crawler = new URLCrawler("https://large-site.com", {
      limit: 5
    });
    const results = await crawler.crawl();
    
    assertEquals(results.length, 5);
  });

  await t.step("深さ制限をサポートする", async () => {
    const crawler = new URLCrawler("https://example.com", {
      depth: 2
    });
    const results = await crawler.crawl();
    
    // ルートから2階層までのみクロール
    const depths = results.map(r => r.depth);
    assert(Math.max(...depths) <= 2);
  });
});

Deno.test("URLCrawler - エラーハンドリング", async (t) => {
  await t.step("ネットワークエラーを記録する", async () => {
    const crawler = new URLCrawler("https://non-existent-domain.com");
    const results = await crawler.crawl();
    
    assertEquals(results.length, 1);
    assertExists(results[0].error);
    assertEquals(results[0].links.length, 0);
  });

  await t.step("無効なURLはスキップする", async () => {
    const crawler = new URLCrawler("https://example.com");
    // ページ内に "javascript:void(0)" のようなリンクがある場合
    const results = await crawler.crawl();
    
    const allLinks = results.flatMap(r => r.links);
    assert(allLinks.every(link => {
      try {
        new URL(link);
        return true;
      } catch {
        return false;
      }
    }));
  });

  await t.step("タイムアウトをサポートする", async () => {
    const crawler = new URLCrawler("https://slow-site.com", {
      timeout: 1000 // 1秒
    });
    const results = await crawler.crawl();
    
    const timedOutResults = results.filter(r => r.error?.includes("timeout"));
    assert(timedOutResults.length > 0);
  });
});

Deno.test("URLCrawler - 出力形式", async (t) => {
  await t.step("CrawlResult型を返す", async () => {
    const crawler = new URLCrawler("https://example.com");
    const results = await crawler.crawl();
    
    results.forEach(result => {
      assertExists(result.url);
      assert(Array.isArray(result.links));
      // errorは任意
    });
  });

  await t.step("重複したURLは除外される", async () => {
    const crawler = new URLCrawler("https://example.com");
    const results = await crawler.crawl();
    
    const urls = results.map(r => r.url);
    const uniqueUrls = new Set(urls);
    assertEquals(urls.length, uniqueUrls.size);
  });
});

Deno.test("URLCrawler - 高度な機能", async (t) => {
  await t.step("カスタムヘッダーをサポートする", async () => {
    const crawler = new URLCrawler("https://api.example.com", {
      headers: {
        "User-Agent": "CustomBot/1.0",
        "Authorization": "Bearer token"
      }
    });
    const results = await crawler.crawl();
    
    assert(results.length > 0); // 認証が必要なAPIでも動作
  });

  await t.step("リトライ機能をサポートする", async () => {
    const crawler = new URLCrawler("https://flaky-site.com", {
      retries: 3,
      retryDelay: 100
    });
    const results = await crawler.crawl();
    
    // 一時的なエラーがあってもリトライで成功
    const successfulResults = results.filter(r => !r.error);
    assert(successfulResults.length > 0);
  });

  await t.step("進捗コールバックをサポートする", async () => {
    let progressCalls = 0;
    const crawler = new URLCrawler("https://example.com", {
      onProgress: (completed, total) => {
        progressCalls++;
        assert(completed <= total);
      }
    });
    
    await crawler.crawl();
    assert(progressCalls > 0);
  });
});

// CLI仕様のテスト
Deno.test("CLI - 引数パース", async (t) => {
  await t.step("URLが必須である", () => {
    const args = parseArgs([]);
    assertEquals(args.error, "URL is required");
  });

  await t.step("オプションを正しくパースする", () => {
    const args = parseArgs([
      "https://example.com",
      "-c", "5",
      "-m", "/api/**",
      "-m", "/docs/**",
      "--limit", "10",
      "--json"
    ]);
    
    assertEquals(args.url, "https://example.com");
    assertEquals(args.options.concurrency, 5);
    assertEquals(args.options.match, ["/api/**", "/docs/**"]);
    assertEquals(args.options.limit, 10);
    assertEquals(args.format, "json");
  });

  await t.step("ヘルプを表示する", () => {
    const args = parseArgs(["--help"]);
    assert(args.showHelp);
  });
});