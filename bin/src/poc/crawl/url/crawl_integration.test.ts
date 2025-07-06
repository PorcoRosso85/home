import {
  assert,
  assertEquals,
  assertExists,
} from "https://deno.land/std@0.224.0/assert/mod.ts";
import { parseArgs, URLCrawler } from "./crawl.ts";

// 実際のテスト用HTTPサーバーを起動
async function startTestServer(): Promise<
  { server: Deno.HttpServer; port: number }
> {
  const port = 8000 + Math.floor(Math.random() * 1000);

  const handler = (req: Request): Response => {
    const url = new URL(req.url);

    switch (url.pathname) {
      case "/":
        return new Response(
          `
          <!DOCTYPE html>
          <html>
          <body>
            <a href="/about">About</a>
            <a href="/contact">Contact</a>
            <a href="https://external.com/link">External</a>
            <a href="javascript:void(0)">Invalid</a>
          </body>
          </html>
        `,
          { headers: { "content-type": "text/html" } },
        );

      case "/about":
        return new Response(
          `
          <!DOCTYPE html>
          <html>
          <body>
            <h1>About Page</h1>
            <a href="/">Home</a>
          </body>
          </html>
        `,
          { headers: { "content-type": "text/html" } },
        );

      case "/contact":
        return new Response(
          `
          <!DOCTYPE html>
          <html>
          <body>
            <h1>Contact Page</h1>
            <a href="/">Home</a>
            <a href="/about">About</a>
          </body>
          </html>
        `,
          { headers: { "content-type": "text/html" } },
        );

      case "/image.jpg":
        return new Response("", {
          headers: { "content-type": "image/jpeg" },
        });

      default:
        return new Response("Not Found", { status: 404 });
    }
  };

  const server = Deno.serve({ port, onListen: () => {} }, handler);

  // サーバーが起動するまで待機
  await new Promise((resolve) => setTimeout(resolve, 100));

  return { server, port };
}

// 統合テスト（実際のHTTPサーバーを使用）
Deno.test("URLCrawler - 実際のHTTPサーバーでの統合テスト", async (t) => {
  const { server, port } = await startTestServer();
  const baseUrl = `http://localhost:${port}`;

  try {
    await t.step("単一URLからリンクを抽出できる", async () => {
      const crawler = new URLCrawler(baseUrl);
      const results = await crawler.crawl();

      // 最初のページのみ検証（再帰的なクロールは別のテストで）
      const rootResult = results.find((r) => r.url === baseUrl);
      assertExists(rootResult);
      assert(Array.isArray(rootResult.links));
      // javascript:は除外されるが、外部リンクは抽出される（クロールはされない）
      assertEquals(rootResult.links.length, 3);
      assert(rootResult.links.includes(`${baseUrl}/about`));
      assert(rootResult.links.includes(`${baseUrl}/contact`));
      assert(rootResult.links.includes("https://external.com/link"));
    });

    await t.step("相対URLを絶対URLに変換する", async () => {
      const crawler = new URLCrawler(`${baseUrl}/about`);
      const results = await crawler.crawl();

      const aboutResult = results.find((r) => r.url === `${baseUrl}/about`);
      assertExists(aboutResult);
      const links = aboutResult.links;
      assert(links.includes(`${baseUrl}/`)); // "/" が baseUrl/ に変換される
      assert(links.every((link) => link.startsWith("http")));
    });

    await t.step("HTMLページのみを処理する", async () => {
      const crawler = new URLCrawler(`${baseUrl}/image.jpg`);
      const results = await crawler.crawl();

      assertEquals(results.length, 0); // 画像URLは処理されない
    });

    await t.step("同一ホストのみクロールする（デフォルト）", async () => {
      const crawler = new URLCrawler(baseUrl);
      // limitを設定して無限ループを防ぐ
      crawler.options.limit = 10;
      const results = await crawler.crawl();

      const urls = results.map((r) => r.url);
      assert(urls.includes(baseUrl));
      assert(urls.includes(`${baseUrl}/about`));
      assert(urls.includes(`${baseUrl}/contact`));
      // 外部リンクは含まれない
      assert(!urls.includes("https://external.com/link"));
    });

    await t.step("404エラーを適切に処理する", async () => {
      const crawler = new URLCrawler(`${baseUrl}/non-existent`);
      const results = await crawler.crawl();

      assertEquals(results.length, 0); // 404ページは処理されない
    });
  } finally {
    // テストサーバーを停止
    await server.shutdown();
  }
});

// CLIの引数パーステスト（モック不要）
Deno.test("CLI - 引数パース", async (t) => {
  await t.step("URLが必須である", () => {
    const args = parseArgs([]);
    assertEquals(args.error, "URL is required");
  });

  await t.step("オプションを正しくパースする", () => {
    const args = parseArgs([
      "https://example.com",
      "-c",
      "5",
      "-m",
      "/api/**",
      "-m",
      "/docs/**",
      "--limit",
      "10",
      "--json",
    ]);

    assertEquals(args.url, "https://example.com");
    assertEquals(args.options?.concurrency, 5);
    assertEquals(args.options?.match, ["/api/**", "/docs/**"]);
    assertEquals(args.options?.limit, 10);
    assertEquals(args.format, "json");
  });

  await t.step("ヘルプを表示する", () => {
    const args = parseArgs(["--help"]);
    assert(args.showHelp);
  });
});
