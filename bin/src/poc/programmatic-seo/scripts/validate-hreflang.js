#!/usr/bin/env node

/**
 * Hreflang Validation Script for Programmatic SEO
 * Validates hreflang files and HTML for multilingual SEO compliance
 */

const fs = require('fs');
const path = require('path');

class HreflangValidator {
  constructor(targetPath) {
    this.targetPath = targetPath;
    this.errors = [];
    this.warnings = [];
    this.validLanguageCodes = new Set([
      'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ko',
      'ar', 'hi', 'th', 'vi', 'tr', 'pl', 'nl', 'sv', 'da', 'no',
      'fi', 'hu', 'cs', 'sk', 'ro', 'bg', 'hr', 'sl', 'et', 'lv',
      'lt', 'mt', 'ga', 'cy', 'is', 'mk', 'sq', 'bs', 'sr', 'mn',
      'x-default' // Special case for default language
    ]);
  }

  validateFileExists() {
    if (!fs.existsSync(this.targetPath)) {
      this.errors.push(`Target file does not exist: ${this.targetPath}`);
      return false;
    }

    const stats = fs.statSync(this.targetPath);
    if (stats.size === 0) {
      this.errors.push('Target file is empty');
      return false;
    }

    console.log(`✓ Target file exists: ${this.targetPath} (${stats.size} bytes)`);
    return true;
  }

  validateHTMLHreflang() {
    try {
      const content = fs.readFileSync(this.targetPath, 'utf-8');

      // Find hreflang links
      const hreflangRegex = /<link[^>]*rel=["']alternate["'][^>]*hreflang=["']([^"']+)["'][^>]*href=["']([^"']+)["'][^>]*>/gi;
      const matches = [...content.matchAll(hreflangRegex)];

      if (matches.length === 0) {
        this.errors.push('No hreflang links found in HTML');
        return false;
      }

      console.log(`✓ Found ${matches.length} hreflang links`);

      let validLinks = 0;
      let invalidLinks = 0;
      const foundLanguages = new Set();
      const foundUrls = new Set();
      let hasXDefault = false;

      for (const match of matches) {
        const hreflang = match[1];
        const href = match[2];

        // Validate hreflang code
        const langCode = hreflang.split('-')[0];
        if (hreflang === 'x-default') {
          hasXDefault = true;
        } else if (!this.validLanguageCodes.has(langCode)) {
          this.warnings.push(`Unknown language code: ${hreflang}`);
        }

        foundLanguages.add(hreflang);

        // Validate URL
        try {
          new URL(href);
          validLinks++;
          foundUrls.add(href);
        } catch (error) {
          this.errors.push(`Invalid URL in hreflang: ${href}`);
          invalidLinks++;
        }
      }

      console.log(`✓ Link validation: ${validLinks} valid, ${invalidLinks} invalid`);
      console.log(`✓ Found languages: ${Array.from(foundLanguages).sort().join(', ')}`);

      // Check for x-default
      if (!hasXDefault) {
        this.warnings.push('No x-default hreflang found - recommended for SEO');
      } else {
        console.log('✓ x-default hreflang found');
      }

      // Check for duplicate URLs
      if (foundUrls.size !== matches.length) {
        this.warnings.push(`Duplicate URLs found in hreflang (${matches.length} links, ${foundUrls.size} unique URLs)`);
      }

      return invalidLinks === 0;
    } catch (error) {
      this.errors.push(`Failed to validate HTML hreflang: ${error.message}`);
      return false;
    }
  }

  validateJSONHreflang() {
    try {
      const content = fs.readFileSync(this.targetPath, 'utf-8');
      const data = JSON.parse(content);

      if (!data.hreflangSets || !Array.isArray(data.hreflangSets)) {
        this.errors.push('Invalid JSON structure - missing hreflangSets array');
        return false;
      }

      console.log(`✓ Found ${data.hreflangSets.length} hreflang sets`);

      let totalLinks = 0;
      let validSets = 0;
      let invalidSets = 0;

      for (const set of data.hreflangSets) {
        if (!set.canonical || !set.alternates || !Array.isArray(set.alternates)) {
          this.errors.push('Invalid hreflang set structure');
          invalidSets++;
          continue;
        }

        // Validate canonical URL
        try {
          new URL(set.canonical);
        } catch (error) {
          this.errors.push(`Invalid canonical URL: ${set.canonical}`);
          invalidSets++;
          continue;
        }

        // Validate alternates
        let setValid = true;
        for (const alt of set.alternates) {
          if (!alt.hreflang || !alt.url) {
            this.errors.push('Missing hreflang or url in alternate');
            setValid = false;
            continue;
          }

          try {
            new URL(alt.url);
          } catch (error) {
            this.errors.push(`Invalid alternate URL: ${alt.url}`);
            setValid = false;
          }

          const langCode = alt.hreflang.split('-')[0];
          if (alt.hreflang !== 'x-default' && !this.validLanguageCodes.has(langCode)) {
            this.warnings.push(`Unknown language code: ${alt.hreflang}`);
          }

          totalLinks++;
        }

        if (setValid) {
          validSets++;
        } else {
          invalidSets++;
        }
      }

      console.log(`✓ Set validation: ${validSets} valid, ${invalidSets} invalid`);
      console.log(`✓ Total hreflang links: ${totalLinks}`);

      return invalidSets === 0;
    } catch (error) {
      this.errors.push(`Failed to validate JSON hreflang: ${error.message}`);
      return false;
    }
  }

  validateXMLHreflang() {
    try {
      const content = fs.readFileSync(this.targetPath, 'utf-8');

      // Basic XML validation
      if (!content.includes('<?xml version="1.0"')) {
        this.errors.push('Missing XML declaration');
      }

      if (!content.includes('<hreflang-sets>')) {
        this.errors.push('Missing hreflang-sets root element');
      }

      // Count sets and alternates
      const setMatches = content.match(/<hreflang-set/g);
      const alternateMatches = content.match(/<alternate/g);

      if (!setMatches || setMatches.length === 0) {
        this.errors.push('No hreflang sets found in XML');
        return false;
      }

      console.log(`✓ Found ${setMatches.length} hreflang sets`);

      if (alternateMatches) {
        console.log(`✓ Found ${alternateMatches.length} alternate links`);
      }

      // Validate href attributes
      const hrefMatches = content.match(/href=["']([^"']+)["']/g);
      if (hrefMatches) {
        let validUrls = 0;
        let invalidUrls = 0;

        for (const hrefMatch of hrefMatches) {
          const url = hrefMatch.match(/href=["']([^"']+)["']/)[1];
          try {
            new URL(url);
            validUrls++;
          } catch (error) {
            this.errors.push(`Invalid URL in XML: ${url}`);
            invalidUrls++;
          }
        }

        console.log(`✓ URL validation: ${validUrls} valid, ${invalidUrls} invalid`);
        return invalidUrls === 0;
      }

      return true;
    } catch (error) {
      this.errors.push(`Failed to validate XML hreflang: ${error.message}`);
      return false;
    }
  }

  validate() {
    console.log('Starting hreflang validation...');
    console.log(`Target: ${this.targetPath}`);
    console.log('');

    if (!this.validateFileExists()) {
      this.reportResults();
      return false;
    }

    let isValid = true;
    const ext = path.extname(this.targetPath).toLowerCase();

    // Determine validation method based on file extension
    switch (ext) {
      case '.html':
      case '.htm':
        if (!this.validateHTMLHreflang()) isValid = false;
        break;
      case '.json':
        if (!this.validateJSONHreflang()) isValid = false;
        break;
      case '.xml':
        if (!this.validateXMLHreflang()) isValid = false;
        break;
      default:
        // Try to detect format from content
        try {
          const content = fs.readFileSync(this.targetPath, 'utf-8');
          if (content.trim().startsWith('{')) {
            if (!this.validateJSONHreflang()) isValid = false;
          } else if (content.includes('<?xml')) {
            if (!this.validateXMLHreflang()) isValid = false;
          } else if (content.includes('<html') || content.includes('<link')) {
            if (!this.validateHTMLHreflang()) isValid = false;
          } else {
            this.errors.push('Unable to determine file format for validation');
            isValid = false;
          }
        } catch (error) {
          this.errors.push(`Failed to read file for format detection: ${error.message}`);
          isValid = false;
        }
    }

    this.reportResults();
    return isValid && this.errors.length === 0;
  }

  reportResults() {
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

    if (this.errors.length === 0) {
      console.log('✅ Hreflang validation passed');
    } else {
      console.log('❌ Hreflang validation failed');
    }
  }
}

// Main execution
function main() {
  const targetPath = process.argv[2] || './public/hreflang.html';

  console.log('Programmatic SEO - Hreflang Validator');
  console.log('');

  const validator = new HreflangValidator(targetPath);
  const isValid = validator.validate();

  process.exit(isValid ? 0 : 1);
}

if (require.main === module) {
  main();
}

module.exports = { HreflangValidator };
