#!/usr/bin/env node

/**
 * Sitemap Validation Script for Programmatic SEO
 * Validates sitemap.xml existence, structure, and content
 */

const fs = require('fs');
const path = require('path');

class SitemapValidator {
  constructor(sitemapPath) {
    this.sitemapPath = sitemapPath;
    this.errors = [];
    this.warnings = [];
  }

  validateFileExists() {
    if (!fs.existsSync(this.sitemapPath)) {
      this.errors.push(`Sitemap file does not exist: ${this.sitemapPath}`);
      return false;
    }

    const stats = fs.statSync(this.sitemapPath);
    if (stats.size === 0) {
      this.errors.push('Sitemap file is empty');
      return false;
    }

    if (stats.size < 100) {
      this.warnings.push(`Sitemap file is very small (${stats.size} bytes) - might be incomplete`);
    }

    console.log(`✓ Sitemap file exists: ${this.sitemapPath} (${stats.size} bytes)`);
    return true;
  }

  validateXMLStructure() {
    try {
      const content = fs.readFileSync(this.sitemapPath, 'utf-8');

      // Basic XML validation
      if (!content.includes('<?xml version="1.0"')) {
        this.errors.push('Missing XML declaration');
      }

      if (!content.includes('<urlset')) {
        this.errors.push('Missing urlset root element');
      }

      if (!content.includes('xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"')) {
        this.errors.push('Missing or incorrect sitemap namespace');
      }

      if (!content.includes('</urlset>')) {
        this.errors.push('Missing closing urlset tag');
      }

      // Count URLs
      const urlMatches = content.match(/<url>/g);
      if (!urlMatches || urlMatches.length === 0) {
        this.errors.push('No URLs found in sitemap');
        return false;
      }

      const urlCount = urlMatches.length;
      console.log(`✓ Found ${urlCount} URLs in sitemap`);

      // Validate closing tags match
      const closingUrlMatches = content.match(/<\/url>/g);
      if (!closingUrlMatches || closingUrlMatches.length !== urlCount) {
        this.errors.push('Mismatched opening and closing <url> tags');
      }

      return urlCount > 0;
    } catch (error) {
      this.errors.push(`Failed to read sitemap file: ${error.message}`);
      return false;
    }
  }

  validateURLs() {
    try {
      const content = fs.readFileSync(this.sitemapPath, 'utf-8');

      // Extract and validate URLs
      const locMatches = content.match(/<loc>(.*?)<\/loc>/g);
      if (!locMatches) {
        this.errors.push('No <loc> elements found');
        return false;
      }

      let validUrls = 0;
      let invalidUrls = 0;

      for (const locMatch of locMatches) {
        const url = locMatch.replace(/<\/?loc>/g, '');

        // Basic URL validation
        try {
          new URL(url);
          validUrls++;
        } catch (error) {
          this.errors.push(`Invalid URL found: ${url}`);
          invalidUrls++;
        }
      }

      console.log(`✓ URL validation: ${validUrls} valid, ${invalidUrls} invalid`);

      if (invalidUrls > 0) {
        return false;
      }

      // Check for required elements
      const lastmodMatches = content.match(/<lastmod>/g);
      const changefreqMatches = content.match(/<changefreq>/g);
      const priorityMatches = content.match(/<priority>/g);

      if (lastmodMatches) {
        console.log(`✓ Found ${lastmodMatches.length} lastmod entries`);
      }

      if (changefreqMatches) {
        console.log(`✓ Found ${changefreqMatches.length} changefreq entries`);
      }

      if (priorityMatches) {
        console.log(`✓ Found ${priorityMatches.length} priority entries`);
      }

      return true;
    } catch (error) {
      this.errors.push(`Failed to validate URLs: ${error.message}`);
      return false;
    }
  }

  validateSitemapSize() {
    try {
      const content = fs.readFileSync(this.sitemapPath, 'utf-8');
      const size = Buffer.byteLength(content, 'utf8');

      // Sitemap size limits (50MB uncompressed, 50,000 URLs)
      const MAX_SIZE = 50 * 1024 * 1024; // 50MB
      const MAX_URLS = 50000;

      if (size > MAX_SIZE) {
        this.errors.push(`Sitemap exceeds size limit: ${size} bytes (max: ${MAX_SIZE})`);
      }

      const urlCount = (content.match(/<url>/g) || []).length;
      if (urlCount > MAX_URLS) {
        this.errors.push(`Sitemap exceeds URL limit: ${urlCount} URLs (max: ${MAX_URLS})`);
      }

      console.log(`✓ Size validation: ${size} bytes, ${urlCount} URLs`);
      return true;
    } catch (error) {
      this.errors.push(`Failed to validate sitemap size: ${error.message}`);
      return false;
    }
  }

  validate() {
    console.log('Starting sitemap validation...');
    console.log(`Target: ${this.sitemapPath}`);
    console.log('');

    let isValid = true;

    // Run all validations
    if (!this.validateFileExists()) {
      isValid = false;
    } else {
      if (!this.validateXMLStructure()) isValid = false;
      if (!this.validateURLs()) isValid = false;
      if (!this.validateSitemapSize()) isValid = false;
    }

    // Report results
    console.log('');
    console.log('=== Validation Results ===');

    if (this.errors.length > 0) {
      console.log('❌ ERRORS:');
      this.errors.forEach(error => console.log(`  - ${error}`));
    }

    if (this.warnings.length > 0) {
      console.log('⚠️  WARNINGS:');
      this.warnings.forEach(warning => console.log(`  - ${warning}`));
    }

    if (isValid && this.errors.length === 0) {
      console.log('✅ Sitemap validation passed');
      return true;
    } else {
      console.log('❌ Sitemap validation failed');
      return false;
    }
  }
}

// Main execution
function main() {
  const sitemapPath = process.argv[2] || './public/sitemap.xml';

  console.log('Programmatic SEO - Sitemap Validator');
  console.log('');

  const validator = new SitemapValidator(sitemapPath);
  const isValid = validator.validate();

  process.exit(isValid ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { SitemapValidator };
