import {
  assert,
  assertEquals,
} from "https://deno.land/std@0.224.0/assert/mod.ts";
import { parseArgs, URLCrawler } from "./crawl.ts";
import {
  DEFAULT_CONCURRENCY,
  FORMAT_JSON,
  FORMAT_TEXT,
} from "./variables/constants.ts";

// ユニットテスト（ネットワークアクセスなし）

Deno.test("URLCrawler - コンストラクタ", async (t) => {
  await t.step("基本的なインスタンス作成", () => {
    const crawler = new URLCrawler("https://example.com");
    assert(crawler instanceof URLCrawler);
    assertEquals(crawler.options.concurrency, DEFAULT_CONCURRENCY);
    assertEquals(crawler.options.sameHost, true);
  });

  await t.step("オプション指定でのインスタンス作成", () => {
    const crawler = new URLCrawler("https://example.com", {
      concurrency: 5,
      sameHost: false,
      limit: 10,
    });
    assertEquals(crawler.options.concurrency, 5);
    assertEquals(crawler.options.sameHost, false);
    assertEquals(crawler.options.limit, 10);
  });
});

Deno.test("parseArgs - 引数パース", async (t) => {
  await t.step("URLが必須である", () => {
    const args = parseArgs([]);
    assertEquals(args.error, "URL is required");
  });

  await t.step("URL引数のみの場合", () => {
    const args = parseArgs(["https://example.com"]);
    assertEquals(args.url, "https://example.com");
    assertEquals(args.options?.concurrency, DEFAULT_CONCURRENCY);
    assertEquals(args.format, FORMAT_TEXT);
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
    assertEquals(args.format, FORMAT_JSON);
  });

  await t.step("ヘルプフラグ", () => {
    const args = parseArgs(["--help"]);
    assert(args.showHelp);
  });

  await t.step("-hでもヘルプ", () => {
    const args = parseArgs(["-h"]);
    assert(args.showHelp);
  });

  await t.step("URLがダッシュで始まらない最初の引数", () => {
    const args = parseArgs(["-c", "5", "https://example.com", "--json"]);
    assertEquals(args.url, "https://example.com");
    assertEquals(args.options?.concurrency, 5);
    assertEquals(args.format, FORMAT_JSON);
  });
});
