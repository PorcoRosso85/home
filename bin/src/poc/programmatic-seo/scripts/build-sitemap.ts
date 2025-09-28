#!/usr/bin/env node

/**
 * Build Sitemap Generator for Programmatic SEO Phase 1.1
 * Generates sitemap.xml from scripts/url-source.json
 *
 * Features:
 * - XML Sitemaps Protocol compliance
 * - UTC ISO 8601 lastmod format
 * - No priority/changefreq (non-recommended fields)
 * - TypeScript type safety
 * - URL normalization
 * - Validation functions
 */

// Node.js requires for CommonJS environment
const fs = require('fs');
const path = require('path');

// Node.js global type declarations
declare const process: {
  argv: string[];
  exit: (code?: number) => never;
};

declare const require: {
  main: any;
  (id: string): any;
};

declare const module: {
  exports: any;
};

declare const console: {
  log: (...args: any[]) => void;
  error: (...args: any[]) => void;
  warn: (...args: any[]) => void;
};

declare const URL: {
  new (url: string): {
    toString(): string;
    hash: string;
  };
};

declare const Date: {
  new (): {
    toISOString(): string;
    getTime(): number;
  };
  new (dateString: string): {
    toISOString(): string;
    getTime(): number;
  };
};

interface URLAlternate {
  lang: string;
  loc: string;
}

interface URLEntry {
  loc: string;
  lastmod: string;
  lang?: string;
  alternates?: URLAlternate[];
}

interface URLSourceData {
  version: string;
  generated: string;
  defaultLang: string;
  urls: URLEntry[];
}

interface SitemapURL {
  loc: string;
  lastmod: string;
}

class SitemapBuilder {
  private sourceData: URLSourceData;
  private urls: SitemapURL[] = [];

  constructor(sourcePath: string) {
    try {
      const sourceContent = fs.readFileSync(sourcePath, 'utf-8');
      this.sourceData = JSON.parse(sourceContent);
      console.log(`Loaded URL source: ${this.sourceData.urls.length} entries from ${sourcePath}`);
    } catch (error) {
      console.error(`Failed to load URL source from ${sourcePath}:`, error);
      process.exit(1);
    }
  }

  /**
   * Normalize URL for sitemap
   * - Ensure proper encoding
   * - Remove fragments
   * - Validate URL format
   */
  private normalizeURL(url: string): string {
    try {
      const parsed = new URL(url);
      // Remove fragment
      parsed.hash = '';
      return parsed.toString();
    } catch (error) {
      console.warn(`Invalid URL skipped: ${url}`);
      return '';
    }
  }

  /**
   * Validate and format lastmod to UTC ISO 8601
   */
  private formatLastMod(lastmod: string): string {
    try {
      const date = new Date(lastmod);
      if (isNaN(date.getTime())) {
        throw new Error('Invalid date');
      }
      return date.toISOString();
    } catch (error) {
      console.warn(`Invalid lastmod date: ${lastmod}, using current time`);
      return new Date().toISOString();
    }
  }

  /**
   * Process URL source data into sitemap URLs
   */
  public processURLs(): void {
    console.log('Processing URLs for sitemap generation...');

    for (const urlEntry of this.sourceData.urls) {
      const normalizedURL = this.normalizeURL(urlEntry.loc);
      if (!normalizedURL) {
        continue; // Skip invalid URLs
      }

      const formattedLastMod = this.formatLastMod(urlEntry.lastmod);

      this.urls.push({
        loc: normalizedURL,
        lastmod: formattedLastMod
      });
    }

    // Sort URLs for consistent output
    this.urls.sort((a, b) => a.loc.localeCompare(b.loc));

    console.log(`Processed ${this.urls.length} valid URLs`);
  }

  /**
   * Escape XML special characters
   */
  private escapeXML(text: string): string {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /**
   * Generate XML sitemap content
   */
  public generateXML(): string {
    const header = '<?xml version="1.0" encoding="UTF-8"?>\n';
    const urlsetOpen = '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';

    const urlElements = this.urls.map(url =>
      `  <url>\n` +
      `    <loc>${this.escapeXML(url.loc)}</loc>\n` +
      `    <lastmod>${url.lastmod}</lastmod>\n` +
      `  </url>`
    ).join('\n');

    const urlsetClose = '\n</urlset>';

    return header + urlsetOpen + urlElements + urlsetClose;
  }

  /**
   * Validate generated sitemap
   */
  public validateSitemap(xml: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Check basic XML structure
    if (!xml.includes('<?xml version="1.0" encoding="UTF-8"?>')) {
      errors.push('Missing XML declaration');
    }

    if (!xml.includes('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')) {
      errors.push('Missing or incorrect urlset namespace');
    }

    if (!xml.includes('</urlset>')) {
      errors.push('Missing urlset closing tag');
    }

    // Check URL count
    const urlCount = (xml.match(/<url>/g) || []).length;
    if (urlCount === 0) {
      errors.push('No URLs found in sitemap');
    } else if (urlCount !== this.urls.length) {
      errors.push(`URL count mismatch: expected ${this.urls.length}, found ${urlCount}`);
    }

    // Validate ISO 8601 format in lastmod elements
    const lastmodMatches = xml.match(/<lastmod>([^<]+)<\/lastmod>/g);
    if (lastmodMatches) {
      for (const match of lastmodMatches) {
        const dateStr = match.replace(/<\/?lastmod>/g, '');
        const iso8601Regex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/;
        if (!iso8601Regex.test(dateStr)) {
          errors.push(`Invalid ISO 8601 date format: ${dateStr}`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Write sitemap to file
   */
  public writeSitemap(outputPath: string): void {
    const xml = this.generateXML();

    // Validate before writing
    const validation = this.validateSitemap(xml);
    if (!validation.valid) {
      console.error('Sitemap validation failed:');
      validation.errors.forEach(error => console.error(`  - ${error}`));
      process.exit(1);
    }

    // Ensure output directory exists
    const outputDir = path.dirname(outputPath);
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
      console.log(`Created output directory: ${outputDir}`);
    }

    try {
      fs.writeFileSync(outputPath, xml, 'utf-8');
      const stats = fs.statSync(outputPath);

      console.log(`✓ Sitemap written to ${outputPath}`);
      console.log(`✓ File size: ${stats.size} bytes`);
      console.log(`✓ URL count: ${this.urls.length}`);
      console.log(`✓ Validation passed`);
    } catch (error) {
      console.error(`Failed to write sitemap to ${outputPath}:`, error);
      process.exit(1);
    }
  }

  /**
   * Get statistics about the sitemap
   */
  public getStats(): { urlCount: number; fileSize?: number; outputPath?: string } {
    return {
      urlCount: this.urls.length
    };
  }
}

/**
 * Main execution function
 */
function main(): void {
  const sourcePath = process.argv[2] || './scripts/url-source.json';
  const outputPath = process.argv[3] || './public/sitemap.xml';

  console.log('=== Programmatic SEO - Sitemap Builder Phase 1.1 ===');
  console.log(`Source: ${sourcePath}`);
  console.log(`Output: ${outputPath}`);
  console.log('');

  // Validate source file exists
  if (!fs.existsSync(sourcePath)) {
    console.error(`Source file not found: ${sourcePath}`);
    process.exit(1);
  }

  try {
    const builder = new SitemapBuilder(sourcePath);
    builder.processURLs();
    builder.writeSitemap(outputPath);

    const stats = builder.getStats();
    console.log('');
    console.log('=== Build Summary ===');
    console.log(`✓ Processed ${stats.urlCount} URLs`);
    console.log(`✓ XML Sitemaps Protocol compliant`);
    console.log(`✓ UTC ISO 8601 timestamps`);
    console.log(`✓ No deprecated priority/changefreq fields`);
    console.log('');
    console.log('Sitemap generation completed successfully');

  } catch (error) {
    console.error('Sitemap generation failed:', error);
    process.exit(1);
  }
}

// Execute if run directly
if (require.main === module) {
  main();
}

export { SitemapBuilder, URLSourceData, SitemapURL };
