#!/usr/bin/env -S deno run --allow-net

/**
 * URL Crawler - Extract links from websites
 * Inspired by sitefetch's crawling logic
 */

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
  public options: CrawlOptions;

  constructor(
    private baseUrl: string,
    options: CrawlOptions = {}
  ) {
    const url = new URL(baseUrl);
    this.baseHost = url.host;
    this.options = {
      concurrency: 3,
      sameHost: true,
      depth: -1, // unlimited
      ...options,
    };
  }

  async crawl(): Promise<CrawlResult[]> {
    this.queue.push(this.baseUrl);
    
    while (this.queue.length > 0 && this.shouldContinue()) {
      const batch = this.queue.splice(0, this.options.concurrency!);
      const promises = batch.map(url => this.processUrl(url));
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

    if (!this.matchesPattern(url)) return;

    try {
      const response = await fetch(url);
      if (!response.ok || !response.headers.get('content-type')?.includes('text/html')) {
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
        error: error instanceof Error ? error.message : String(error) 
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
        const absoluteUrl = new URL(href, baseUrl).href;
        links.push(absoluteUrl);
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
    return this.options.match.some(pattern => {
      const regex = this.globToRegex(pattern);
      return regex.test(urlPath);
    });
  }

  private globToRegex(glob: string): RegExp {
    const escaped = glob.replace(/[.+?^${}()|[\]\\]/g, '\\$&');
    const pattern = escaped
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.');
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

  if (args.includes('--help') || args.includes('-h')) {
    return { showHelp: true };
  }

  const url = args.find(arg => !arg.startsWith('-'));
  if (!url) {
    return { error: "URL is required" };
  }

  const options: CrawlOptions = {
    concurrency: 3,
    match: [],
  };

  let format = 'text';

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '-c':
      case '--concurrency':
        options.concurrency = parseInt(args[++i]);
        break;
      case '-m':
      case '--match':
        if (!options.match) options.match = [];
        options.match.push(args[++i]);
        break;
      case '-l':
      case '--limit':
        options.limit = parseInt(args[++i]);
        break;
      case '--json':
        format = 'json';
        break;
    }
  }

  return { url, options, format };
}

// CLI Interface
async function main() {
  const args = Deno.args;
  
  if (args.length === 0 || args.includes('--help') || args.includes('-h')) {
    console.log(`
URL Crawler - Extract links from websites

Usage:
  crawl.ts <url> [options]

Options:
  -c, --concurrency <n>    Number of concurrent requests (default: 3)
  -m, --match <pattern>    Only crawl URLs matching pattern (can be repeated)
  -l, --limit <n>          Maximum number of pages to crawl
  --no-same-host           Allow crawling external hosts
  --json                   Output as JSON
  -h, --help               Show this help

Examples:
  crawl.ts https://example.com
  crawl.ts https://docs.example.com -m "/api/**" -m "/guide/**"
  crawl.ts https://example.com --limit 10 --json
    `.trim());
    Deno.exit(0);
  }

  const url = args.find(arg => !arg.startsWith('-'))!;
  const options: CrawlOptions = {
    concurrency: 3,
    match: [],
    sameHost: !args.includes('--no-same-host'),
  };

  // Parse options
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    
    switch (arg) {
      case '-c':
      case '--concurrency':
        options.concurrency = parseInt(args[++i]);
        break;
      case '-m':
      case '--match':
        options.match!.push(args[++i]);
        break;
      case '-l':
      case '--limit':
        options.limit = parseInt(args[++i]);
        break;
    }
  }

  // Crawl
  const crawler = new URLCrawler(url, options);
  const results = await crawler.crawl();

  // Output
  if (args.includes('--json')) {
    console.log(JSON.stringify(results, null, 2));
  } else {
    for (const result of results) {
      if (result.error) {
        console.error(`❌ ${result.url}: ${result.error}`);
      } else {
        console.log(`\n📄 ${result.url}`);
        console.log(`   Found ${result.links.length} links`);
        if (result.links.length > 0 && result.links.length <= 10) {
          result.links.forEach(link => console.log(`   → ${link}`));
        }
      }
    }
    
    console.log(`\n✅ Crawled ${results.length} pages total`);
  }
}

if (import.meta.main) {
  main();
}