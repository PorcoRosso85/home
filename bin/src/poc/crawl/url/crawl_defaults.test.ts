import { assertEquals } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { URLCrawler } from "./crawl.ts";
import { DEFAULT_CONCURRENCY } from "./variables/constants.ts";

// デフォルト値のテスト（ネットワークアクセス不要）

Deno.test("URLCrawler - デフォルト値", async (t) => {
  await t.step("デフォルトの並行数は3", () => {
    const crawler = new URLCrawler("https://example.com");
    assertEquals(crawler.options.concurrency, DEFAULT_CONCURRENCY);
  });

  await t.step("デフォルトで同一ホスト制限が有効", () => {
    const crawler = new URLCrawler("https://example.com");
    assertEquals(crawler.options.sameHost, true);
  });

  await t.step("デフォルトでmatchは空配列", () => {
    const crawler = new URLCrawler("https://example.com");
    assertEquals(crawler.options.match, []);
  });
});
