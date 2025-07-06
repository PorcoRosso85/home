#!/usr/bin/env -S deno run --allow-net

/**
 * URL Crawler - Extract links from websites
 * Inspired by sitefetch's crawling logic
 */

import {
  CONTENT_TYPE_HTML,
  DEFAULT_CONCURRENCY,
  DEFAULT_DEPTH,
  DEFAULT_SAME_HOST,
  FORMAT_JSON,
  FORMAT_TEXT,
} from "./variables/constants.ts";

export interface CrawlOptions {
  concurrency?: number;
  match?: string[];
  limit?: number;
  sameHost?: boolean;
  depth?: number;
  timeout?: number;
  headers?: Record<string, string>;
  retries?: number;
  retryDelay?: number;
  onProgress?: (completed: number, total: number) => void;
  withRoot?: boolean;
}

export interface CrawlResult {
  url: string;
  links: string[];
  error?: string;
  depth?: number;
}

export class URLCrawler {
  private visited = new Set<string>();
  private queue: string[] = [];
  private results: CrawlResult[] = [];
  private baseHost: string;
  private basePath: string;
  public options: CrawlOptions;

  constructor(
    private baseUrl: string,
    options: CrawlOptions = {},
  ) {
    const url = new URL(baseUrl);
    this.baseHost = url.host;
    
    // ベースパスの決定
    if (url.pathname.endsWith('/')) {
      // 既に末尾スラッシュがある
      this.basePath = url.pathname;
    } else if (url.pathname.match(/\.[^/]+$/)) {
      // ファイルっぽいURL（拡張子がある）
      // ディレクトリ部分を抽出
      const lastSlash = url.pathname.lastIndexOf('/');
      this.basePath = url.pathname.substring(0, lastSlash + 1);
    } else {
      // ディレクトリとして扱う（末尾スラッシュを追加）
      this.basePath = url.pathname + '/';
    }
    
    this.options = {
      concurrency: DEFAULT_CONCURRENCY,
      sameHost: DEFAULT_SAME_HOST,
      depth: DEFAULT_DEPTH,
      match: [],
      ...options,
    };
  }

  async crawl(): Promise<CrawlResult[]> {
    this.queue.push(this.baseUrl);

    while (this.queue.length > 0 && this.shouldContinue()) {
      const batch = this.queue.splice(0, this.options.concurrency!);
      const promises = batch.map((url) => this.processUrl(url));
      await Promise.all(promises);
    }

    return this.results;
  }

  private shouldContinue(): boolean {
    if (this.options.limit && this.visited.size >= this.options.limit) {
      return false;
    }
    return true;
  }

  private async processUrl(url: string): Promise<void> {
    if (this.visited.has(url)) return;
    this.visited.add(url);

    // 最初のURL（baseUrl）は常に処理する、それ以外はパターンマッチングを適用
    if (url !== this.baseUrl && !this.matchesPattern(url)) return;

    try {
      const response = await fetch(url, {
        redirect: "manual"  // リダイレクトを手動で処理
      });
      
      // リダイレクトの処理
      if (response.status >= 300 && response.status < 400) {
        const location = response.headers.get("location");
        if (location) {
          const redirectUrl = new URL(location, url);
          // リダイレクト先をキューに追加
          if (!this.visited.has(redirectUrl.href) && this.shouldCrawlLink(redirectUrl.href)) {
            this.queue.push(redirectUrl.href);
          }
        }
        await response.body?.cancel();
        return;
      }
      
      if (
        !response.ok ||
        !response.headers.get("content-type")?.includes(CONTENT_TYPE_HTML)
      ) {
        // レスポンスボディを消費してリークを防ぐ
        await response.body?.cancel();
        return;
      }

      const html = await response.text();
      const links = this.extractLinks(html, url);

      this.results.push({ url, links });

      // Add new links to queue
      for (const link of links) {
        if (!this.visited.has(link) && this.shouldCrawlLink(link)) {
          this.queue.push(link);
        }
      }
    } catch (error) {
      this.results.push({
        url,
        links: [],
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  private extractLinks(html: string, baseUrl: string): string[] {
    const linkRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>/gi;
    const links: string[] = [];
    let match;

    while ((match = linkRegex.exec(html)) !== null) {
      try {
        const href = match[1];
        const absoluteUrl = new URL(href, baseUrl);

        // httpまたはhttpsのURLのみを受け入れる
        if (
          absoluteUrl.protocol === "http:" || absoluteUrl.protocol === "https:"
        ) {
          // ハッシュフラグメントを除去して正規化（sitefetch互換）
          absoluteUrl.hash = '';
          links.push(absoluteUrl.href);
        }
      } catch {
        // Ignore invalid URLs
      }
    }

    return [...new Set(links)]; // Remove duplicates
  }

  private shouldCrawlLink(url: string): boolean {
    try {
      const linkUrl = new URL(url);

      // Check same host restriction
      if (this.options.sameHost && linkUrl.host !== this.baseHost) {
        return false;
      }

      // デフォルトでベースパス配下のみクロール（withRootが無効の場合）
      if (!this.options.withRoot) {
        if (!this.options.match || this.options.match.length === 0) {
          // ルートパス（"/"）の場合は全体をクロール可能
          if (this.basePath === '/') {
            return true;
          }
          // ベースパス配下のみ許可
          if (!linkUrl.pathname.startsWith(this.basePath)) {
            return false;
          }
        }
      }

      // Check match patterns
      if (!this.matchesPattern(url)) {
        return false;
      }

      return true;
    } catch {
      return false;
    }
  }

  private matchesPattern(url: string): boolean {
    if (!this.options.match || this.options.match.length === 0) {
      return true;
    }

    const urlPath = new URL(url).pathname;
    
    let included = false;
    let excluded = false;
    
    for (const pattern of this.options.match) {
      // 否定パターンの処理
      if (pattern.startsWith('!')) {
        const negPattern = pattern.slice(1);
        const regex = this.globToRegex(negPattern);
        if (regex.test(urlPath)) {
          excluded = true;
        }
      } else {
        // 通常のパターン（相対パスの処理を含む）
        let effectivePattern = pattern;
        
        // 相対パスの場合、ベースパスを前に付ける
        if (!pattern.startsWith('/')) {
          effectivePattern = this.basePath + pattern;
        }
        
        const regex = this.globToRegex(effectivePattern);
        if (regex.test(urlPath)) {
          included = true;
        }
      }
    }
    
    // 否定パターンが最優先
    if (excluded) return false;
    
    // 通常のパターンが1つでもあれば、それにマッチする必要がある
    const hasIncludePatterns = this.options.match.some(p => !p.startsWith('!'));
    if (hasIncludePatterns) {
      return included;
    }
    
    // 否定パターンのみの場合、除外されていなければOK
    return true;
  }

  private globToRegex(glob: string): RegExp {
    // まず特殊文字をエスケープ（ただし * と ? は除く）
    const escaped = glob.replace(/[.+^${}()|[\]\\]/g, "\\$&");
    
    // globパターンを正規表現に変換
    const pattern = escaped
      .replace(/\*\*/g, "@@DOUBLESTAR@@")  // ** を一時的に置換
      .replace(/\*/g, "[^/]*")              // * は / 以外の任意の文字
      .replace(/\?/g, "[^/]")               // ? は / 以外の1文字
      .replace(/@@DOUBLESTAR@@/g, ".*");   // ** は任意の文字（/ を含む）
      
    return new RegExp(`^${pattern}$`);
  }
}

// Parse CLI arguments
export function parseArgs(args: string[]): {
  url?: string;
  options?: CrawlOptions;
  format?: string;
  showHelp?: boolean;
  error?: string;
} {
  if (args.length === 0) {
    return { error: "URL is required" };
  }

  if (args.includes("--help") || args.includes("-h")) {
    return { showHelp: true };
  }

  let url: string | undefined;
  const options: CrawlOptions = {
    concurrency: DEFAULT_CONCURRENCY,
    match: [],
  };
  let format = FORMAT_TEXT;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case "-c":
      case "--concurrency":
        options.concurrency = parseInt(args[++i]);
        break;
      case "-m":
      case "--match":
        if (!options.match) options.match = [];
        options.match.push(args[++i]);
        break;
      case "-l":
      case "--limit":
        options.limit = parseInt(args[++i]);
        break;
      case "--json":
        format = FORMAT_JSON;
        break;
      case "--with-root":
        options.withRoot = true;
        break;
      default:
        // ダッシュで始まらない引数で、まだURLが設定されていない場合
        if (!arg.startsWith("-") && !url) {
          url = arg;
        }
        break;
    }
  }

  if (!url) {
    return { error: "URL is required" };
  }

  return { url, options, format };
}

// CLI Interface
async function main() {
  const args = Deno.args;

  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log(`
URL Crawler - Extract links from websites

Usage:
  crawl.ts <url> [options]

Options:
  -c, --concurrency <n>    Number of concurrent requests (default: 3)
  -m, --match <pattern>    Only crawl URLs matching pattern (can be repeated)
  -l, --limit <n>          Maximum number of pages to crawl
  --no-same-host           Allow crawling external hosts
  --with-root              Include root and all paths (remove base path restriction)
  --json                   Output as JSON
  -h, --help               Show this help

Examples:
  crawl.ts https://example.com
  crawl.ts https://docs.example.com -m "/api/**" -m "/guide/**"
  crawl.ts https://example.com/docs/ --with-root -m "/api/**"
  crawl.ts https://example.com --limit 10 --json
    `.trim());
    Deno.exit(0);
  }

  const url = args.find((arg) => !arg.startsWith("-"))!;
  const options: CrawlOptions = {
    concurrency: 3,
    match: [],
    sameHost: !args.includes("--no-same-host"),
    withRoot: args.includes("--with-root"),
  };

  // Parse options
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];

    switch (arg) {
      case "-c":
      case "--concurrency":
        options.concurrency = parseInt(args[++i]);
        break;
      case "-m":
      case "--match":
        options.match!.push(args[++i]);
        break;
      case "-l":
      case "--limit":
        options.limit = parseInt(args[++i]);
        break;
    }
  }

  // Crawl
  const crawler = new URLCrawler(url, options);
  const results = await crawler.crawl();

  // Output
  if (args.includes("--json")) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const result of results) {
      if (result.error) {
        console.error(`❌ ${result.url}: ${result.error}`);
      } else {
        console.log(`\n📄 ${result.url}`);
        console.log(`   Found ${result.links.length} links`);
        if (result.links.length > 0 && result.links.length <= 10) {
          result.links.forEach((link) => console.log(`   → ${link}`));
        }
      }
    }

    console.log(`\n✅ Crawled ${results.length} pages total`);
  }
}

if (import.meta.main) {
  main();
}
